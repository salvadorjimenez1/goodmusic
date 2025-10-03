from fastapi import FastAPI, Depends, HTTPException, Body, status, Query, Request, APIRouter
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from sqlalchemy.orm import selectinload
from schemas import ( 
                     UserCreate, 
                     UserResponse, 
                     ReviewCreate, 
                     ReviewResponse, 
                     UserAlbumStatusCreate, 
                     UserAlbumStatusResponse, 
                     UserDetailResponse, 
                     UserReviewsResponse,
                     DeleteResponse,
                     PaginatedResponse,
                     ErrorResponse,
                     UserOut,
                     Token,
                     StatusEnum,
                     SpotifyAlbumImport,
                     UserAlbumStatusUpdate,)

from db import get_db, engine, Base
from models import Review, UserAlbumStatus, User
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from auth_utils import verify_password, get_password_hash, create_access_token, create_refresh_token
from jose import JWTError, jwt
from config import SECRET_KEY, ALGORITHM, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI
import httpx, base64, time
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware


DEFAULT_ERROR_RESPONSES = {
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
}


_spotify_app_token: str | None = None
_spotify_token_expiry: float = 0

async def get_spotify_app_token() -> str:
    """Fetch & cache a Spotify client credentials token"""
    global _spotify_app_token, _spotify_token_expiry

    if _spotify_app_token and time.time() < _spotify_token_expiry:
        return _spotify_app_token

    auth_header = base64.b64encode(
        f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()
    ).decode()

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            headers={"Authorization": f"Basic {auth_header}"}
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to get Spotify token")

    data = resp.json()
    _spotify_app_token = data["access_token"]
    _spotify_token_expiry = time.time() + data["expires_in"] - 60  # renew 1m early
    return _spotify_app_token


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist with the async engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # your frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # allow POST, GET, OPTIONS, etc.
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Always emit {"detail": "..."} using your ErrorResponse schema
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(detail=str(exc.detail)).model_dump(),
    )

@app.get("/spotify/login", tags=["Spotify"])
async def spotify_login():
    url = (
        "https://accounts.spotify.com/authorize"
        f"?client_id={SPOTIFY_CLIENT_ID}"
        "&response_type=code"
        f"&redirect_uri={SPOTIFY_REDIRECT_URI}"
        "&scope=user-read-email user-library-read"
    )
    return {"auth_url": url}

@app.get("/spotify/callback", tags=["Spotify"])
async def spotify_callback(code: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": SPOTIFY_REDIRECT_URI,
                "client_id": SPOTIFY_CLIENT_ID,
                "client_secret": SPOTIFY_CLIENT_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Spotify auth failed")

    tokens = resp.json()
    current_user.spotify_access_token = tokens["access_token"]
    current_user.spotify_refresh_token = tokens.get("refresh_token")
    current_user.spotify_token_expires = datetime.utcnow() + timedelta(seconds=tokens["expires_in"])
    db.add(current_user)
    await db.commit()
    return {"status": "linked", "expires_in": tokens["expires_in"]}

async def refresh_spotify_token(user: User, db: AsyncSession):
    if user.spotify_refresh_token is None:
        raise HTTPException(status_code=400, detail="No refresh token")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": user.spotify_refresh_token,
                "client_id": SPOTIFY_CLIENT_ID,
                "client_secret": SPOTIFY_CLIENT_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Spotify refresh failed")

    tokens = resp.json()
    user.spotify_access_token = tokens["access_token"]
    user.spotify_token_expires = datetime.utcnow() + timedelta(seconds=tokens["expires_in"])
    db.add(user)
    await db.commit()
    return user.spotify_access_token

@app.get("/spotify/search", tags=["Spotify"])
async def search_spotify_albums(query: str):
    token = await get_spotify_app_token()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.spotify.com/v1/search",
            params={"q": query, "type": "album"},
            headers={"Authorization": f"Bearer {token}"}
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

@app.get("/spotify/albums/{spotify_album_id}", tags=["Spotify"])
async def get_spotify_album(spotify_album_id: str):
    token = await get_spotify_app_token()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api.spotify.com/v1/albums/{spotify_album_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

@app.get("/")
async def read_root():
    return {"message": "API is running 🎶"}

@app.get("/ping-db")
async def ping_db(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# User Endpoints
@app.get("/users", response_model=PaginatedResponse[UserResponse], responses=DEFAULT_ERROR_RESPONSES, tags=["Users"])
async def list_users(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=100, description="Number of users per page"),
    offset: int = Query(0, ge=0, description="How many users to skip"),
    ):
    # Count total users
    total_result = await db.execute(select(func.count()).select_from(User))
    total = total_result.scalar()
    
    result = await db.execute(
        select(User)
        .offset(offset)
        .limit(limit))
    users = result.scalars().all()
    return {"total": total, "items": users}
    
@app.get("/users/{user_id}",
         response_model=UserDetailResponse,
         responses=DEFAULT_ERROR_RESPONSES,
         tags=["Users"],
         description="Get detailed information about a user, including their reviews and statuses."
         )
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.reviews),
            selectinload(User.statuses),
        )
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

@app.get("/users/{user_id}/reviews", response_model=PaginatedResponse[ReviewResponse], responses=DEFAULT_ERROR_RESPONSES, tags=["Users"])
async def get_user_reviews(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=100, description="Number of reviews per page"),
    offset: int = Query(0, ge=0, description="How many reviews to skip"),
):
    # Count total reviews by this user
    total_result = await db.execute(
        select(func.count()).select_from(Review).where(Review.user_id == user_id)
    )
    total = total_result.scalar()

    # Fetch paginated reviews
    result = await db.execute(
        select(Review)
        .options(
            selectinload(Review.album).selectinload(Album.artist),
            selectinload(Review.user),
        )
        .where(Review.user_id == user_id)
        .offset(offset)
        .limit(limit)
    )
    user_reviews = result.scalars().all()
    if not user_reviews:
        raise HTTPException(status_code=404, detail="User not found")

    return {"total": total, "items": user_reviews}
    
@app.delete("/users/{user_id}", response_model=DeleteResponse, responses=DEFAULT_ERROR_RESPONSES, tags=["Users"])
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="This user not allowed to delete this user")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()
    return DeleteResponse(status="deleted", id=user_id)

# Review Endpoints
@app.get("/reviews",
         response_model=PaginatedResponse[ReviewResponse],
         responses=DEFAULT_ERROR_RESPONSES,
         tags=["Reviews"],
         description="Get a paginated list of all reviews with optional filtering by user or album."
         )
async def get_reviews(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    offset: int = Query(0, ge=0, description="How many reviews to skip"),
    user_id: int | None = Query(None, description="Filter by user ID"),
    spotify_album_id: str | None = Query(None),
):
    query = select(Review).options(selectinload(Review.user))
    if user_id:
        query = query.where(Review.user_id == user_id)
    if spotify_album_id:
        query = query.where(Review.spotify_album_id == spotify_album_id)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    result = await db.execute(query.offset(offset).limit(limit))
    return {"total": total, "items": result.scalars().all()}

@app.get("/reviews/{review_id}", response_model=ReviewResponse, responses=DEFAULT_ERROR_RESPONSES, tags=["Reviews"])
async def get_all_reviews(review_id: int, db: AsyncSession = Depends(get_db)):
    review = await db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review

@app.post("/reviews", response_model=ReviewResponse, responses=DEFAULT_ERROR_RESPONSES, tags=["Reviews"])
async def create_review(
    payload: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = await db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    review = Review(
        content=payload.content,
        user=user,
        spotify_album_id=payload.spotify_album_id
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review
    
@app.delete("/reviews/{review_id}", response_model=DeleteResponse, responses=DEFAULT_ERROR_RESPONSES, tags=["Reviews"])
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    review = await db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to delete this review")

    await db.delete(review)
    await db.commit()
    return DeleteResponse(status="deleted", id=review_id)

# User Album Status Endpoints

@app.post("/statuses", response_model=UserAlbumStatusResponse, tags=["Statuses"])
async def create_status(
    payload: UserAlbumStatusCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ):
    user = await db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    status = UserAlbumStatus(
        user=user,
        spotify_album_id=payload.spotify_album_id,
        status=payload.status,
        is_favorite=payload.is_favorite
    )
    db.add(status)
    await db.commit()
    await db.refresh(status)
    return status

@app.get("/users/{user_id}/statuses",
         response_model=PaginatedResponse[UserAlbumStatusResponse],
         responses=DEFAULT_ERROR_RESPONSES,
         tags=["Users"],
         description="Get a paginated list of statuses for a given user. You can filter by status type."
         )
async def get_user_statuses(
    user_id: int, 
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=100, description="Number of statuses per page"),
    offset: int = Query(0, ge=0, description="How many statuses to skip"),
    status: StatusEnum | None = Query(None, description="Filter by status"),
    ):
    query = select(UserAlbumStatus).options(selectinload(UserAlbumStatus.user)).where(UserAlbumStatus.user_id == user_id)
    if status:
        query = query.where(UserAlbumStatus.status == status)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    result = await db.execute(query.offset(offset).limit(limit))
    return {"total": total, "items": result.scalars().all()}
    
@app.get("/spotify/albums/{spotify_album_id}/statuses", response_model=PaginatedResponse[UserAlbumStatusResponse], tags=["Statuses"])
async def get_album_statuses(
    spotify_album_id: int, 
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=100, description="Number of statuses per page"),
    offset: int = Query(0, ge=0, description="How many statuses to skip"),
    ):
    query = select(UserAlbumStatus).options(selectinload(UserAlbumStatus.user)).where(UserAlbumStatus.spotify_album_id == spotify_album_id)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    result = await db.execute(query.offset(offset).limit(limit))
    return {"total": total, "items": result.scalars().all()}

@app.patch("/statuses/{status_id}", response_model=UserAlbumStatusResponse, responses=DEFAULT_ERROR_RESPONSES, tags=["Statuses"])
async def update_status(
    status_id: int,
    payload: UserAlbumStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    s = await db.get(UserAlbumStatus, status_id)
    if not s:
        raise HTTPException(status_code=404, detail="Status not found")
    if s.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to update")

    if payload.status is not None:
        s.status = payload.status
    if payload.is_favorite is not None:
        s.is_favorite = payload.is_favorite

    await db.commit()
    await db.refresh(s)
    return s

@app.delete("/statuses/{status_id}", response_model=DeleteResponse, responses=DEFAULT_ERROR_RESPONSES, tags=["Statuses"])
async def delete_status(
    status_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ):
    s = await db.get(UserAlbumStatus, status_id)
    if not s:
        raise HTTPException(status_code=404, detail="Status not found")
    if s.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to delete")

    await db.delete(s)
    await db.commit()
    return DeleteResponse(status="deleted", id=status_id)

# Auth endpoints

@app.post("/register", response_model=UserOut, responses=DEFAULT_ERROR_RESPONSES, tags=["Auth"])
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user.username))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_pw = get_password_hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed_pw)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@app.post(
    "/login",
    response_model=Token,
    responses=DEFAULT_ERROR_RESPONSES,
    tags=["Auth"],
    description="Authenticate with username and password to receive access and refresh tokens."
    )
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == form_data.username))
    db_user = result.scalar_one_or_none()
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(data={"sub": db_user.username})
    refresh_token = create_refresh_token(data={"sub": db_user.username})
    return {"access_token": access_token, 
            "refresh_token": refresh_token,
            "token_type": "bearer"}
    
@app.post("/refresh", responses=DEFAULT_ERROR_RESPONSES, tags=["Auth"])
async def refresh_token(refresh_token: str = Body(...)):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # issue new short-lived access token
        new_access_token = create_access_token({"sub": username})
        return {"access_token": new_access_token, "token_type": "bearer"}

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@app.get("/me", response_model=UserOut, responses=DEFAULT_ERROR_RESPONSES, tags=["Auth"])
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
