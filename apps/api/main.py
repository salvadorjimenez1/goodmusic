from fastapi import FastAPI, Depends, HTTPException, Body, status, Query, Request, APIRouter, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from schemas import ( 
                     UserCreate, 
                     ReviewCreate, 
                     ReviewResponse, 
                     UserAlbumStatusCreate, 
                     UserAlbumStatusResponse, 
                     UserDetailResponse, 
                     DeleteResponse,
                     PaginatedResponse,
                     ErrorResponse,
                     UserOut,
                     Token,
                     StatusEnum,
                     UserAlbumStatusUpdate,
                     FollowListResponse)

from db import get_db, engine, Base
from models import Review, UserAlbumStatus, User, Follow
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from auth_utils import verify_password, get_password_hash, create_access_token, create_refresh_token
from jose import JWTError, jwt
from config import SECRET_KEY, ALGORITHM, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI, MAIL_USERNAME, MAIL_PASSWORD, MAIL_PORT, MAIL_SERVER
import httpx, base64, time
from datetime import datetime, timedelta, timezone
from fastapi.middleware.cors import CORSMiddleware
import re
import os, shutil
import aiosmtplib
from email.mime.text import MIMEText


DEFAULT_ERROR_RESPONSES = {
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
}

USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9._]+$')
UPLOAD_DIR = "uploads/profile_pics"

os.makedirs(UPLOAD_DIR, exist_ok=True)

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

async def send_verification_email(email: str, token: str):
    # Build the verification link
    link = f"http://localhost:3000/verify?token={token}"  # later replace with FRONTEND_URL
    body = f"""
    🎶 Welcome to GoodMusic!

    Please verify your account by clicking this link:
    {link}

    If you didn’t sign up, you can ignore this email.
    """

    # Construct MIME email
    msg = MIMEText(body, "plain")
    msg["From"] = MAIL_USERNAME
    msg["To"] = email
    msg["Subject"] = "Verify your GoodMusic account"

    # Send via SMTP
    await aiosmtplib.send(
        msg,
        hostname=MAIL_SERVER,
        port=MAIL_PORT,
        username=MAIL_USERNAME,
        password=MAIL_PASSWORD,
        start_tls=True
    )

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

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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

def create_verification_token(user_id: int):
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    to_encode = {"sub": str(user_id), "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},  # don't cast to string
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
@app.get("/users", response_model=PaginatedResponse[UserOut], responses=DEFAULT_ERROR_RESPONSES, tags=["Users"])
async def list_users(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=100, description="Number of users per page"),
    offset: int = Query(0, ge=0, description="How many users to skip"),
    q: str | None = Query(None, description="Optional search term to filter by username"),
):
    # Base query
    query = select(User)

    # If search term provided, filter by username
    if q:
        query = query.where(User.username.ilike(f"%{q}%"))

    # Count total for pagination (after filtering)
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    # Apply pagination
    result = await db.execute(query.offset(offset).limit(limit))
    users = result.scalars().all()
    return {"total": total, "items": users}
    
@app.get("/users/{user_id}",
         response_model=UserDetailResponse,
         responses=DEFAULT_ERROR_RESPONSES,
         tags=["Users"],
         description="Get detailed information about a user, including their reviews and statuses."
         )
async def get_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
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

    follow_check = await db.execute(
        select(Follow).where(
            Follow.follower_id == current_user.id,
            Follow.following_id == user_id
        )
    )
    is_following = follow_check.scalar_one_or_none() is not None

    followers_count = (await db.execute(
        select(func.count()).select_from(Follow).where(Follow.following_id == user_id)
    )).scalar()

    following_count = (await db.execute(
        select(func.count()).select_from(Follow).where(Follow.follower_id == user_id)
    )).scalar()

    mutuals_query = await db.execute(
        select(User).join(Follow, Follow.follower_id == User.id)
        .where(Follow.following_id == user_id)   # follows profile user
        .where(User.id.in_(
            select(Follow.follower_id).where(Follow.following_id == current_user.id)
        ))
    )
    mutuals = mutuals_query.scalars().all()
    mutual_followers_count = len(mutuals)
    mutual_followers_preview = mutuals[:3]  # limit to 3

    user.is_following = is_following
    user.followers_count = followers_count
    user.following_count = following_count
    user.mutual_followers = mutual_followers_preview
    user.mutual_followers_count = mutual_followers_count

    return user

@app.get("/users/by-username/{username}",
         response_model=UserDetailResponse,
         responses=DEFAULT_ERROR_RESPONSES,
         tags=["Users"],
         description="Get detailed user info by username, including reviews, statuses, follow info, and counts."
         )
async def get_user_by_username(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Find user by username
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.reviews),
            selectinload(User.statuses),
        )
        .where(User.username == username)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check follow status
    follow_check = await db.execute(
        select(Follow).where(
            Follow.follower_id == current_user.id,
            Follow.following_id == user.id
        )
    )
    is_following = follow_check.scalar_one_or_none() is not None

    # Count followers
    followers_count = (await db.execute(
        select(func.count()).select_from(Follow).where(Follow.following_id == user.id)
    )).scalar()

    # Count following
    following_count = (await db.execute(
        select(func.count()).select_from(Follow).where(Follow.follower_id == user.id)
    )).scalar()

    # Mutual followers
    mutuals_query = await db.execute(
        select(User).join(Follow, Follow.follower_id == User.id)
        .where(Follow.following_id == user.id)
        .where(User.id.in_(
            select(Follow.follower_id).where(Follow.following_id == current_user.id)
        ))
    )
    mutuals = mutuals_query.scalars().all()
    mutual_followers_count = len(mutuals)
    mutual_followers_preview = mutuals[:3]

    # Attach fields
    user.is_following = is_following
    user.followers_count = followers_count
    user.following_count = following_count
    user.mutual_followers = mutual_followers_preview
    user.mutual_followers_count = mutual_followers_count

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
        .options(selectinload(Review.user))
        .where(Review.user_id == user_id)
        .offset(offset)
        .limit(limit)
    )
    user_reviews = result.scalars().all()

    return {"total": total, "items": user_reviews}

@app.post("/users/{user_id}/profile-picture")
async def upload_profile_picture(
    user_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    save_path = os.path.join(UPLOAD_DIR, f"user_{user_id}_{file.filename}")

    # Save file to disk
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Build a public URL (what we store in DB)
    file_url = f"/uploads/profile_pics/user_{user_id}_{file.filename}"

    # Update DB ORM-style
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.profile_picture = file_url
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {"message": "Profile picture updated", "profile_picture": file_url}
    
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

@app.get("/albums/{spotify_album_id}/average-rating", tags=["Albums"])
async def get_album_average_rating(spotify_album_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(func.avg(Review.rating)).where(Review.spotify_album_id == spotify_album_id)
    )
    avg = result.scalar()
    return {"average": round(avg, 1) if avg else None}

@app.post("/reviews", response_model=ReviewResponse, responses=DEFAULT_ERROR_RESPONSES, tags=["Reviews"])
async def create_or_update_review(
    payload: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if this user already reviewed this album
    result = await db.execute(
        select(Review).where(
            Review.user_id == current_user.id,
            Review.spotify_album_id == payload.spotify_album_id
        )
    )
    review = result.scalar_one_or_none()

    if review:
        # Update existing review
        review.content = payload.content
        review.rating = payload.rating
    else:
        # Create a new review
        review = Review(
            content=payload.content,
            user=current_user,
            spotify_album_id=payload.spotify_album_id,
            rating=payload.rating,
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

# Album Status Endpoints

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
    result = await db.execute(select(User).where(func.lower(User.username) == user.username.lower()))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=[{"loc": ["body", "username"], "msg": "Username not available"}],
        )

    if len(user.username) < 3:
        raise HTTPException(
            status_code=400,
            detail=[{"loc": ["body", "username"], "msg": "Username must be at least 3 characters"}],
        )
        
    if not USERNAME_REGEX.match(user.username):
        raise HTTPException(
        status_code=400,
        detail=[{"loc": ["body", "username"], "msg": "Username may only contain letters, numbers, periods, or underscores"}],
    )
    
    if len(user.username) > 30:
        raise HTTPException(
            status_code=400,
            detail=[{"loc": ["body", "username"], "msg": "Username too long"}],
        )
        
    if len(user.password) < 6:
        raise HTTPException(
            status_code=400,
            detail=[{"loc": ["body", "password"], "msg": "Password too short (min 6 chars)"}],
        )
        
    if len(user.password) > 100:
        raise HTTPException(
            status_code=400,
            detail=[{"loc": ["body", "password"], "msg": "Password too long"}],
        )
        
    if user.password != user.confirm_password:
        raise HTTPException(
            status_code=400,
            detail=[{"loc": ["body", "confirm_password"], "msg": "Passwords do not match"}],
        )
    
    email_check = await db.execute(select(User).where(func.lower(User.email) == user.email.lower()))
    if email_check.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=[{"loc": ["body", "email"], "msg": "Email already registered"}],
        )

    hashed_pw = get_password_hash(user.password)
    new_user = User(username=user.username.lower(),
                    email=user.email.lower(),
                    hashed_password=hashed_pw,
                    is_verified=False)
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    token = create_verification_token(new_user.id)
    await send_verification_email(new_user.email, token)
    
    return new_user

@app.get("/verify", tags=["Auth"])
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            return {"status": "invalid"}

        user = await db.get(User, int(user_id))
        if not user:
            return {"status": "invalid"}

        if user.is_verified:
            return {"status": "already_verified"}

        user.is_verified = True
        db.add(user)
        await db.commit()
        return {"status": "success"}

    except jwt.ExpiredSignatureError:
        return {"status": "expired"}
    except JWTError:
        return {"status": "invalid"}
    except Exception:
        return {"status": "error"}

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
    
    if not db_user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

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

# Follower Endpoints

@app.post("/users/{user_id}/follow")
async def follow_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You can't follow yourself")

    follow = Follow(follower_id=current_user.id, following_id=user_id)
    db.add(follow)
    try:
        await db.commit()
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Already following this user")
    return {"message": "Followed successfully"}

@app.delete("/users/{user_id}/unfollow")
async def unfollow_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = await db.execute(
        select(Follow).where(Follow.follower_id == current_user.id, Follow.following_id == user_id)
    )
    follow = query.scalar_one_or_none()
    if not follow:
        raise HTTPException(status_code=404, detail="Not following this user")

    await db.delete(follow)
    await db.commit()
    return {"message": "Unfollowed successfully"}

@app.get("/users/{user_id}/followers", response_model=FollowListResponse)
async def get_followers(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).join(Follow, Follow.follower_id == User.id).where(Follow.following_id == user_id)
    )
    users = result.scalars().all()

    total = len(users)
    return {"total": total, "users": users}

@app.get("/users/{user_id}/following", response_model=FollowListResponse)
async def get_following(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).join(Follow, Follow.following_id == User.id).where(Follow.follower_id == user_id)
    )
    users = result.scalars().all()

    total = len(users)
    return {"total": total, "users": users}