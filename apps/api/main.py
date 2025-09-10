from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db, engine, Base
from sqlalchemy import text
from models import Album

# Ensure tables exist
Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "API is running 🎶"}

@app.get("/ping-db")
def ping_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/albums")
def get_albums(db: Session = Depends(get_db)):
    try:
        # In SQLAlchemy 2.x, queries must be explicit
        albums = db.query(Album).all()
        return [{"id": a.id, "title": a.title, "artist": a.artist} for a in albums]
    except Exception as e:
        return {"status": "error", "detail": str(e)}
    
@app.get("/albums/{album_id}")
def get_album(album_id: int, db: Session = Depends(get_db)):
    album = db.query(Album).filter(Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    return {"id": album.id, "title": album.title, "artist": album.artist}

@app.post("/albums")
def create_album(title: str, artist: str, db: Session = Depends(get_db)):
    new_album = Album(title=title, artist=artist)
    db.add(new_album)
    db.commit()
    db.refresh(new_album)
    return {"id": new_album.id, "title": new_album.title, "artist": new_album.artist}

@app.patch("/albums/{album_id}")
def update_album(album_id: int, title: str = None, artist: str = None, db: Session = Depends(get_db)):
    album = db.query(Album).filter(Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    if title:
        album.title = title
    if artist:
        album.artist = artist
    db.commit()
    db.refresh(album)
    return {"id": album.id, "title": album.title, "artist": album.artist}

@app.delete("/albums/{album_id}")
def delete_album(album_id: int, db: Session = Depends(get_db)):
    album = db.query(Album).filter(Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    db.delete(album)
    db.commit()
    return {"status": "deleted", "id": album_id}