from fastapi import FastAPI, Depends, HTTPException, Body
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
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
                     DeleteResponse )

from db import get_db, engine, Base
from models import Album, Artist, Review, UserAlbumStatus, User


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist with the async engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)


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
@app.get("/albums", response_model=list[AlbumResponse])
async def get_albums(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Album).options(selectinload(Album.artist))  # eager-load artist
    )
    albums = result.scalars().all()
    return albums

@app.get("/albums/{album_id}", response_model=AlbumResponse)
async def get_album(album_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Album).options(selectinload(Album.artist)).where(Album.id == album_id)
    )
    album = result.scalar_one_or_none()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    return album

@app.post("/albums", response_model=AlbumResponse)
async def create_album(payload: AlbumCreate, db: AsyncSession = Depends(get_db)):
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

@app.patch("/albums/{album_id}", response_model=AlbumResponse)
async def update_album(
    album_id: int,
    title: str | None = None,
    artist: str | None = None,
    db: AsyncSession = Depends(get_db),
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

@app.delete("/albums/{album_id}", response_model=DeleteResponse)
async def delete_album(album_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Album).where(Album.id == album_id))
    album = result.scalar_one_or_none()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    await db.delete(album)
    await db.commit()
    return DeleteResponse(status="deleted", id=album_id)

# User Endpoints
@app.get("/users", response_model=list[UserResponse])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users
    
@app.get("/users/{user_id}", response_model=UserDetailResponse)
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

@app.get("/users/{user_id}/reviews", response_model=UserDetailResponse)
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

@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # check if user exists
    result = await db.execute(select(User).where(User.username == user.username))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user = User(username=user.username)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@app.post("/users/{user_id}/albums/{album_id}/status", response_model=UserAlbumStatusResponse)
async def add_status(user_id: int, album_id: int, status: str, db: AsyncSession = Depends(get_db)):
    # Ensure user exists
    user_res = await db.execute(select(User).where(User.id == user_id))
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Ensure album exists
    album_res = await db.execute(select(Album).where(Album.id == album_id))
    album = album_res.scalar_one_or_none()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    # Create status entry
    new_status = UserAlbumStatus(user=user, album=album, status=status)
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
    status_obj = result.scalar_one()
    return status_obj
    
@app.delete("/users/{user_id}", response_model=DeleteResponse)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(s)
    await db.commit()
    return DeleteResponse(status="deleted", id=user_id)

# Review Endpoints
@app.get("/reviews", response_model=list[ReviewResponse])
async def get_reviews(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Review).options(
            selectinload(Review.user),
            selectinload(Review.album).selectinload(Album.artist)
        )
    )
    reviews = result.scalars().all()
    return reviews

@app.get("/reviews/{review_id}", response_model=ReviewResponse)
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

@app.get("/albums/{album_id}/reviews", response_model=list[ReviewResponse])
async def get_album_reviews(album_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Review)
        .where(Review.album_id == album_id)
        .options(selectinload(Review.album).selectinload(Album.artist),
                 selectinload(Review.user))
    )
    return result.scalars().all()

@app.post("/albums/{album_id}/reviews", response_model=ReviewResponse)
async def add_review(album_id: int, payload: ReviewCreate, db: AsyncSession = Depends(get_db)):
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
    return review

@app.post("/reviews", response_model=ReviewResponse)
async def create_review(payload: ReviewCreate, db: AsyncSession = Depends(get_db)):
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
    
@app.delete("/reviews/{review_id}", response_model=DeleteResponse)
async def delete_review(review_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    await db.delete(review)
    await db.commit()
    return DeleteResponse(status="deleted", id=review_id)

# User Album Status Endpoints

@app.post("/statuses", response_model=UserAlbumStatusResponse)
async def create_status(payload: UserAlbumStatusCreate, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, payload.user_id)
    album = await db.get(Album, payload.album_id)
    if not user or not album:
        raise HTTPException(status_code=404, detail="User or Album not found")

    new_status = UserAlbumStatus(user=user, album=album, status=payload.status)
    db.add(new_status)
    await db.commit()
    await db.refresh(new_status)
    return new_status

@app.get("/users/{user_id}/statuses", response_model=list[UserAlbumStatusResponse])
async def get_user_statuses(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserAlbumStatus)
        .options(
            selectinload(UserAlbumStatus.user),
            selectinload(UserAlbumStatus.album).selectinload(Album.artist)
        )
        .where(UserAlbumStatus.user_id == user_id)
    )
    statuses = result.scalars().all()
    return statuses
    
@app.get("/albums/{album_id}/statuses", response_model=list[UserAlbumStatusResponse])
async def get_album_statuses(album_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserAlbumStatus)
        .options(
            selectinload(UserAlbumStatus.user),
            selectinload(UserAlbumStatus.album).selectinload(Album.artist)
        )
        .where(UserAlbumStatus.album_id == album_id)
        .order_by(UserAlbumStatus.created_at.asc())
    )
    statuses = result.scalars().all()
    return statuses

@app.post("/albums/{album_id}/statuses", response_model=UserAlbumStatusResponse)
async def add_status(album_id: int, payload: UserAlbumStatusCreate, db: AsyncSession = Depends(get_db)):
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

    # Reload with relationships
    result = await db.execute(
        select(UserAlbumStatus)
        .options(
            selectinload(UserAlbumStatus.user),
            selectinload(UserAlbumStatus.album).selectinload(Album.artist)
        )
        .where(UserAlbumStatus.id == new_status.id)
    )
    return result.scalar_one()

@app.patch("/statuses/{status_id}", response_model=UserAlbumStatusResponse)
async def update_status(
    status_id: int,
    status: str = Body(...),
    db: AsyncSession = Depends(get_db),
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

    s.status = status
    await db.commit()
    await db.refresh(s)
    return s

@app.delete("/statuses/{status_id}", response_model=DeleteResponse)
async def delete_status(status_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserAlbumStatus).where(UserAlbumStatus.id == status_id))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Status not found")

    await db.delete(s)
    await db.commit()
    return DeleteResponse(status="deleted", id=status_id)