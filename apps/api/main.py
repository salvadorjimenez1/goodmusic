from fastapi import FastAPI, Depends, HTTPException, Body, status, Query, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from sqlalchemy.orm import selectinload
from schemas import ( 
                     UserCreate, 
                     UserResponse, 
                     AlbumCreate, 
                     AlbumResponse, 
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
                     StatusEnum,)

from db import get_db, engine, Base
from models import Album, Artist, Review, UserAlbumStatus, User
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from auth_utils import verify_password, get_password_hash, create_access_token, create_refresh_token
from jose import JWTError, jwt
from config import SECRET_KEY, ALGORITHM


DEFAULT_ERROR_RESPONSES = {
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist with the async engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

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

# Album endpoints
@app.get("/albums",
         response_model=PaginatedResponse[AlbumResponse],
         responses=DEFAULT_ERROR_RESPONSES, tags=["Albums"],
         description="Get a paginated list of albums with optional filtering by artist or year."
         )
async def get_albums(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    offset: int = Query(0, ge=0, description="How many items to skip"),
    artist: str | None = Query(None, description="Filter by artist name"),
    year: int | None = Query(None, description="Filter by album year"),
    ):
    
    query = select(Album).options(selectinload(Album.artist))
    
    if artist:
        query = query.join(Album.artist).where(Artist.name.ilike(f"%{artist}%"))
    if year:
        query = query.where(Album.year == year)
        
    # Count total albums
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()
    
    # Fetch paginated albums
    result = await db.execute(query.offset(offset).limit(limit))
    albums = result.scalars().all()
    return {"total": total, "items": albums}

@app.get("/albums/{album_id}", response_model=AlbumResponse, responses=DEFAULT_ERROR_RESPONSES, tags=["Albums"])
async def get_album(album_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Album).options(selectinload(Album.artist)).where(Album.id == album_id)
    )
    album = result.scalar_one_or_none()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    return album

@app.post("/albums", response_model=AlbumResponse, responses=DEFAULT_ERROR_RESPONSES, tags=["Albums"])
async def create_album(
    payload: AlbumCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User= Depends(get_current_user)):
    # Find or create artist by name
    result = await db.execute(select(Artist).where(Artist.name == payload.artist))
    artist_obj = result.scalar_one_or_none()
    if not artist_obj:
        artist_obj = Artist(name=payload.artist)
        db.add(artist_obj)
        await db.flush()

    # Create album
    new_album = Album(
        title=payload.title,
        year=payload.year,
        cover_url=payload.cover_url,
        artist=artist_obj,
    )
    db.add(new_album)
    await db.commit()
    await db.refresh(new_album)

    # Re-query with artist eagerly loaded
    result = await db.execute(
        select(Album).options(selectinload(Album.artist)).where(Album.id == new_album.id)
    )
    album = result.scalar_one()
    return album

@app.patch("/albums/{album_id}", response_model=AlbumResponse, responses=DEFAULT_ERROR_RESPONSES, tags=["Albums"])
async def update_album(
    album_id: int,
    title: str | None = None,
    artist: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Album).options(selectinload(Album.artist)).where(Album.id == album_id)
    )
    album = result.scalar_one_or_none()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    if title:
        album.title = title
    if artist:
        ar_res = await db.execute(select(Artist).where(Artist.name == artist))
        artist_obj = ar_res.scalar_one_or_none()
        if not artist_obj:
            artist_obj = Artist(name=artist)
            db.add(artist_obj)
            await db.flush()
        album.artist = artist_obj

    await db.commit()
    await db.refresh(album)
    return album

@app.delete("/albums/{album_id}", response_model=DeleteResponse, responses=DEFAULT_ERROR_RESPONSES, tags=["Albums"])
async def delete_album(
    album_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Album).where(Album.id == album_id))
    album = result.scalar_one_or_none()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    await db.delete(album)
    await db.commit()
    return DeleteResponse(status="deleted", id=album_id)

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
            selectinload(User.reviews).selectinload(Review.album).selectinload(Album.artist),
            selectinload(User.statuses).selectinload(UserAlbumStatus.album).selectinload(Album.artist),
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
    album_id: int | None = Query(None, description="Filter by album ID"),
    ):
    query = select(Review).options(
        selectinload(Review.user),
        selectinload(Review.album).selectinload(Album.artist)
    )
    
    if user_id:
        query = query.where(Review.user_id == user_id)
    if album_id:
        query = query.where(Review.album_id == album_id)
    
    # Count total albums
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()
    
    # Fetch paginated reviews with eager-loading
    result = await db.execute(query.offset(offset).limit(limit))
    reviews = result.scalars().all()

    return {"total": total, "items": reviews}

@app.get("/reviews/{review_id}", response_model=ReviewResponse, responses=DEFAULT_ERROR_RESPONSES, tags=["Reviews"])
async def get_all_reviews(review_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
    select(Review)
    .options(
        selectinload(Review.user),
        selectinload(Review.album).selectinload(Album.artist)
    )
    .where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review

@app.get("/albums/{album_id}/reviews", response_model=PaginatedResponse[ReviewResponse], responses=DEFAULT_ERROR_RESPONSES, tags=["Reviews"])
async def get_album_reviews(
    album_id: int, 
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=100, description="Number of reviews per page"),
    offset: int = Query(0, ge=0, description="How many reviews to skip"),
    ):
    # Count total reviews for this album
    total_result = await db.execute(
        select(func.count()).select_from(Review).where(Review.album_id == album_id)
    )
    total = total_result.scalar()
    
    result = await db.execute(
        select(Review)
        .where(Review.album_id == album_id)
        .options(selectinload(Review.album).selectinload(Album.artist),
                 selectinload(Review.user))
        .offset(offset)
        .limit(limit)
    )
    reviews = result.scalars().all()
    return {"total": total, "items": reviews}

@app.post("/albums/{album_id}/reviews", response_model=ReviewResponse)
async def add_review(
    album_id: int,
    payload: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    album = await db.get(Album, album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    user = await db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    review = Review(content=payload.content, user=user, album=album)
    db.add(review)
    await db.commit()
    await db.refresh(review)
    result = await db.execute(
        select(Review)
        .options(
            selectinload(Review.user),
            selectinload(Review.album).selectinload(Album.artist),
        )
        .where(Review.id == review.id)
    )
    return result.scalar_one()

@app.post("/reviews", response_model=ReviewResponse, responses=DEFAULT_ERROR_RESPONSES, tags=["Reviews"])
async def create_review(
    payload: ReviewCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    # Ensure user exists
    user_res = await db.execute(select(User).where(User.id == payload.user_id))
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Ensure album exists
    album_res = await db.execute(select(Album).where(Album.id == payload.album_id))
    album = album_res.scalar_one_or_none()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    # Create review
    new_review = Review(content=payload.content, user=user, album=album)
    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)

    # Reload with relationships
    result = await db.execute(
        select(Review)
        .options(
            selectinload(Review.user),
            selectinload(Review.album).selectinload(Album.artist)
        )
        .where(Review.id == new_review.id)
    )
    return result.scalar_one()
    
@app.delete("/reviews/{review_id}", response_model=DeleteResponse, responses=DEFAULT_ERROR_RESPONSES, tags=["Reviews"])
async def delete_review(
    review_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    if review.user != current_user.id:
        raise HTTPException(status_code=403, detail="This user not allowed to delete this review")

    await db.delete(review)
    await db.commit()
    return DeleteResponse(status="deleted", id=review_id)

# User Album Status Endpoints

@app.post("/statuses", response_model=UserAlbumStatusResponse)
async def create_status(
    payload: UserAlbumStatusCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    user = await db.get(User, payload.user_id)
    album = await db.get(Album, payload.album_id)
    if not user or not album:
        raise HTTPException(status_code=404, detail="User or Album not found")

    new_status = UserAlbumStatus(user=user, album=album, status=payload.status)
    db.add(new_status)
    await db.commit()
    result = await db.execute(
        select(UserAlbumStatus)
        .options(
            selectinload(UserAlbumStatus.user),
            selectinload(UserAlbumStatus.album).selectinload(Album.artist),
        )
        .where(UserAlbumStatus.id == new_status.id)
    )
    return result.scalar_one()

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
    query = (
        select(UserAlbumStatus)
        .options(
            selectinload(UserAlbumStatus.user),
            selectinload(UserAlbumStatus.album).selectinload(Album.artist)
        )
        .where(UserAlbumStatus.user_id == user_id)
    )

    # optional filter
    if status:
        query = query.where(UserAlbumStatus.status == status)

    # count total
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    # fetch page
    result = await db.execute(query.offset(offset).limit(limit))
    statuses = result.scalars().all()
    return {"total": total, "items": statuses}
    
@app.get("/albums/{album_id}/statuses", response_model=PaginatedResponse[UserAlbumStatusResponse], responses=DEFAULT_ERROR_RESPONSES, tags=["Statuses"])
async def get_album_statuses(
    album_id: int, 
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=100, description="Number of statuses per page"),
    offset: int = Query(0, ge=0, description="How many statuses to skip"),
    ):
    # Count total statuses for this album
    total_result = await db.execute(
        select(func.count()).select_from(UserAlbumStatus).where(UserAlbumStatus.album_id == album_id)
    )
    total = total_result.scalar()
    
    result = await db.execute(
        select(UserAlbumStatus)
        .options(
            selectinload(UserAlbumStatus.user),
            selectinload(UserAlbumStatus.album).selectinload(Album.artist)
        )
        .where(UserAlbumStatus.album_id == album_id)
        .order_by(UserAlbumStatus.created_at.asc())
        .offset(offset)
        .limit(limit)
    )
    statuses = result.scalars().all()
    return  {"total": total, "items": statuses}

@app.post("/albums/{album_id}/statuses", response_model=UserAlbumStatusResponse, responses=DEFAULT_ERROR_RESPONSES, tags=["Statuses"])
async def add_status(
    album_id: int,
    payload: UserAlbumStatusCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Ensure album exists
    album_res = await db.execute(select(Album).where(Album.id == album_id))
    album = album_res.scalar_one_or_none()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    # Ensure user exists
    user_res = await db.execute(select(User).where(User.id == payload.user_id))
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create status entry
    new_status = UserAlbumStatus(user=user, album=album, status=payload.status)
    db.add(new_status)
    await db.commit()
    await db.refresh(new_status)

    # Reload with relationships for nested schema
    result = await db.execute(
        select(UserAlbumStatus)
        .options(
            selectinload(UserAlbumStatus.user),
            selectinload(UserAlbumStatus.album).selectinload(Album.artist)
        )
        .where(UserAlbumStatus.id == new_status.id)
    )
    return result.scalar_one()

@app.patch("/statuses/{status_id}", response_model=UserAlbumStatusResponse, responses=DEFAULT_ERROR_RESPONSES, tags=["Statuses"])
async def update_status(
    status_id: int,
    status: str = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(UserAlbumStatus)
        .options(
            selectinload(UserAlbumStatus.user),
            selectinload(UserAlbumStatus.album).selectinload(Album.artist)
        )
        .where(UserAlbumStatus.id == status_id)
    )
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Status not found")

    if s.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="This user not allowed to update this status")

    s.status = status
    await db.commit()
    await db.refresh(s)
    return s

@app.delete("/statuses/{status_id}", response_model=DeleteResponse, responses=DEFAULT_ERROR_RESPONSES, tags=["Statuses"])
async def delete_status(
    status_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ):
    result = await db.execute(select(UserAlbumStatus).where(UserAlbumStatus.id == status_id))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Status not found")

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
