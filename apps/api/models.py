from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Text, DateTime, func, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    is_verified = Column(Boolean, default=False)

    profile_picture = Column(String, nullable=True)  # store image URL or path
    
    # Relationships
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    statuses = relationship("UserAlbumStatus", back_populates="user", cascade="all, delete-orphan")
    
    # Spotify OAuth tokens
    spotify_access_token = Column(String, nullable=True)
    spotify_refresh_token = Column(String, nullable=True)
    spotify_token_expires = Column(DateTime(timezone=True), nullable=True)


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    rating = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    spotify_album_id = Column(String, nullable=False)

    user = relationship("User", back_populates="reviews")


class UserAlbumStatus(Base):
    __tablename__ = "user_album_status"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, nullable=False)  # e.g. "listened", "want-to-listen", "favorite"
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_id = Column(Integer, ForeignKey("users.id"))
    spotify_album_id = Column(String, nullable=False)

    user = relationship("User", back_populates="statuses")
    
class Follow(Base):
    __tablename__ = "follows"

    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    following_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("follower_id", "following_id", name="unique_follow"),)