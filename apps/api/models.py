from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, func
from sqlalchemy.orm import relationship
from db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)

    # Relationships
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    statuses = relationship("UserAlbumStatus", back_populates="user", cascade="all, delete-orphan")

    
class Artist(Base):
    __tablename__ = "artists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    albums = relationship("Album", back_populates="artist", cascade="all, delete-orphan")


class Album(Base):
    __tablename__ = "albums"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    year = Column(Integer, nullable=True)
    cover_url = Column(String, nullable=True)

    artist_id = Column(Integer, ForeignKey("artists.id", ondelete="CASCADE"), nullable=False)
    artist = relationship("Artist", back_populates="albums")

    reviews = relationship("Review", back_populates="album", cascade="all, delete-orphan")
    statuses = relationship("UserAlbumStatus", back_populates="album", cascade="all, delete-orphan")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    album_id = Column(Integer, ForeignKey("albums.id", ondelete="CASCADE"), nullable=False)

    user = relationship("User", back_populates="reviews")
    album = relationship("Album", back_populates="reviews")


class UserAlbumStatus(Base):
    __tablename__ = "user_album_status"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, nullable=False)  # e.g. "listened", "want-to-listen", "favorite"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user_id = Column(Integer, ForeignKey("users.id"))
    album_id = Column(Integer, ForeignKey("albums.id", ondelete="CASCADE"))

    user = relationship("User", back_populates="statuses")
    album = relationship("Album", back_populates="statuses")