from fastapi import FastAPI, Depends, HTTPException, Body
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from sqlalchemy.orm import selectinload

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
@app.get("/albums")
async def get_albums(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(Album).options(selectinload(Album.artist))
        )
        albums = result.scalars().all()
        return [
            {
                "id": a.id,
                "title": a.title,
                "artist": a.artist.name if a.artist else None,
                "coverUrl": a.cover_url,
            }
            for a in albums
        ]
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/albums/{album_id}")
async def get_album(album_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Album).options(selectinload(Album.artist)).where(Album.id == album_id)
    )
    album = result.scalar_one_or_none()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    return {
        "id": album.id,
        "title": album.title,
        "artist": album.artist.name if album.artist else None,
        "coverUrl": album.cover_url,
    }
    
@app.get("/albums/{album_id}/reviews")
async def get_reviews(album_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Review).where(Review.album_id == album_id)
        .options(selectinload(Review.album), selectinload(Review.user))
    )
    reviews = result.scalars().all()
    return [
        {"review_id": r.id, 
         "content": r.content,
         "user_id": r.user_id, 
         "user": r.user.username if r.user else None, 
         "album": r.album.title if r.album else None
         } for r in reviews
        ]

@app.post("/albums")
async def create_album(title: str, artist: str, db: AsyncSession = Depends(get_db)):
    # Find or create artist by name
    result = await db.execute(select(Artist).where(Artist.name == artist))
    artist_obj = result.scalar_one_or_none()
    if not artist_obj:
        artist_obj = Artist(name=artist)
        db.add(artist_obj)
        await db.flush()  # assign PK before using in relationship

    new_album = Album(title=title, artist=artist_obj)
    db.add(new_album)
    await db.commit()
    # Re-load with artist for response
    result = await db.execute(
        select(Album).options(selectinload(Album.artist)).where(Album.id == new_album.id)
    )
    album = result.scalar_one()
    return {
        "id": album.id,
        "title": album.title,
        "artist": album.artist.name if album.artist else None,
        "coverUrl": album.cover_url,
    }

@app.post("/albums/{album_id}/status")
async def add_status(album_id: int, status: str, user_id: int = 1, db: AsyncSession = Depends(get_db)):
    # Insert a new status row
    new_status = UserAlbumStatus(user_id=user_id, album_id=album_id, status=status)
    db.add(new_status)
    await db.commit()
    await db.refresh(new_status)
    return {
        "album_id": album_id,
        "status": new_status.status,
        "created_at": new_status.created_at
    }
@app.patch("/albums/{album_id}")
async def update_album(
    album_id: int,
    title: str | None = None,
    artist: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Album).where(Album.id == album_id))
    album = result.scalar_one_or_none()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    if title is not None:
        album.title = title

    if artist is not None:
        ar_res = await db.execute(select(Artist).where(Artist.name == artist))
        artist_obj = ar_res.scalar_one_or_none()
        if not artist_obj:
            artist_obj = Artist(name=artist)
            db.add(artist_obj)
            await db.flush()
        album.artist = artist_obj

    await db.commit()

    # Reload with artist eager-loaded
    result = await db.execute(
        select(Album).options(selectinload(Album.artist)).where(Album.id == album_id)
    )
    album = result.scalar_one()
    return {
        "id": album.id,
        "title": album.title,
        "artist": album.artist.name if album.artist else None,
        "coverUrl": album.cover_url,
    }

@app.delete("/albums/{album_id}")
async def delete_album(album_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Album).where(Album.id == album_id))
    album = result.scalar_one_or_none()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    await db.delete(album)
    await db.commit()
    return {"status": "deleted", "id": album_id}

@app.delete("/albums/status/{status_id}")
async def delete_status(status_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserAlbumStatus).where(UserAlbumStatus.id == status_id))
    status = result.scalar_one_or_none()
    if not status:
        raise HTTPException(status_code=404, detail="Status not found")
    await db.delete(status)
    await db.commit()
    return {"status": "deleted", "id": status_id}

# User Endpoints
@app.get("/users")
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "username": u.username,
        }
        for u in users
    ]
    
@app.get("/users/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.reviews).selectinload(Review.album),
            selectinload(User.statuses).selectinload(UserAlbumStatus.album),
        )
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "username": user.username,
        "reviews": [
            {
                "id": r.id,
                "content": r.content,
                "album": r.album.title if r.album else None,
            }
            for r in user.reviews
        ],
        "statuses": [
            {
                "id": s.id,
                "status": s.status,
                "album": s.album.title if s.album else None,
            }
            for s in user.statuses
        ],
    }
    
@app.post("/users")
async def create_user(username: str, db: AsyncSession = Depends(get_db)):
    user = User(username=username)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"id": user.id, "username": user.username}

@app.post("/users/{user_id}/albums/{album_id}/status")
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

    return {
        "id": new_status.id,
        "user": user.username,
        "album": album.title,
        "status": new_status.status,
        "created_at": new_status.created_at
    }
    
@app.delete("/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(s)
    await db.commit()
    return {"status": "deleted", "id": user_id}

# Review Endpoints

@app.post("/albums/{album_id}/reviews")
async def add_review(album_id: int, content: str, db: AsyncSession = Depends(get_db)):
    # Check album exists
    result = await db.execute(select(Album).where(Album.id == album_id))
    album = result.scalar_one_or_none()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    review = Review(content=content, album_id=album_id)
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return {"id": review.id, "content": review.content}

@app.post("/reviews")
async def create_review(
    user_id: int,
    album_id: int,
    content: str,
    db: AsyncSession = Depends(get_db),
):
    # check user exists
    user_res = await db.execute(select(User).where(User.id == user_id))
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # check album exists
    album_res = await db.execute(select(Album).where(Album.id == album_id))
    album = album_res.scalar_one_or_none()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    new_review = Review(content=content, user=user, album=album)
    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)

    return {
        "review_id": new_review.id,
        "content": new_review.content,
        "user": user.username,
        "album": album.title,
    }
 
@app.get("/users/{user_id}/reviews")
async def get_user_reviews(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Review).options(selectinload(Review.album)).where(Review.user_id == user_id)
    )
    reviews = result.scalars().all()
    return [
        {
            "id": r.id,
            "content": r.content,
            "album": r.album.title if r.album else None,
        }
        for r in reviews
    ]
    
@app.delete("/reviews/{review_id}")
async def delete_review(review_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    await db.delete(review)
    await db.commit()
    return {"status": "deleted", "id": review_id}

# UserAlbumStatus Endpoints

@app.post("/statuses")
async def create_status(
    user_id: int,
    album_id: int,
    status: str,
    db: AsyncSession = Depends(get_db),
):
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

    new_status = UserAlbumStatus(user_id=user_id, album_id=album_id, status=status)
    db.add(new_status)
    await db.commit()
    await db.refresh(new_status)

    return {
        "staus_id": new_status.id,
        "status": new_status.status,
        "user_id": new_status.user_id,
        "album_id": new_status.album_id,
    }

@app.get("/users/{user_id}/statuses")
async def get_user_statuses(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserAlbumStatus).where(UserAlbumStatus.user_id == user_id)
        .options(selectinload(UserAlbumStatus.album), selectinload(UserAlbumStatus.user))
    )
    statuses = result.scalars().all()
    return [
        {
            "album_id": s.album_id,
            "album_name": s.album.title if s.album else None,
            "user": s.user.username if s.user else None,
            "status": s.status,
            "created_at": s.created_at
        }
        for s in statuses
    ]
    
@app.get("/albums/{album_id}/statuses")
async def get_album_statuses(album_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserAlbumStatus).where(UserAlbumStatus.album_id == album_id).order_by(UserAlbumStatus.created_at.asc())
        .options(selectinload(UserAlbumStatus.album))
    )
    statuses = result.scalars().all()
    return [
        {
            "status_id": s.id,
            "status": s.status,
            "user_id": s.user_id,
            "created_at": s.created_at,
            "album_name": s.album.title if s.album else None
        }
        for s in statuses
        ]
    
@app.patch("/statuses/{status_id}")
async def update_status(
    status_id: int,
    status: str = Body(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(UserAlbumStatus).where(UserAlbumStatus.id == status_id)
                              .options(selectinload(UserAlbumStatus.album)))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Status not found")

    s.status = status
    await db.commit()
    await db.refresh(s)
    return {
        "status_id": s.id,
        "status": s.status,
        "user_id": s.user_id,
        "album_id": s.album_id,
        "album": s.album.title
    }

@app.delete("/statuses/{status_id}")
async def delete_status(status_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserAlbumStatus).where(UserAlbumStatus.id == status_id))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Status not found")

    await db.delete(s)
    await db.commit()
    return {"status": "deleted", "id": status_id}