from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Generic, TypeVar
from enum import Enum
from datetime import datetime

# ---------- USERS ----------
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)
    
class UserOut(BaseModel):
    id:int
    username:str
    model_config= ConfigDict(from_attributes=True)
    
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- ARTISTS ----------
class ArtistBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class ArtistResponse(ArtistBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- ALBUMS ----------
class AlbumBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    year: Optional[int] = Field(None, ge=1900, le=2100) 
    cover_url: Optional[str] = None

class AlbumCreate(AlbumBase):
    artist: str = Field(..., min_length=1, max_length=100)  # name of artist

class AlbumResponse(AlbumBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    artist: Optional[ArtistResponse] = None   # <-- now nested instead of str


# ---------- REVIEWS ----------
class ReviewBase(BaseModel):
    content: str = Field(..., min_length=5, max_length=1000)

class ReviewCreate(ReviewBase):
    user_id: int
    album_id: int

class ReviewResponse(ReviewBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user: Optional[UserResponse] = None       # <-- nested UserResponse
    album: Optional[AlbumResponse] = None     # <-- nested AlbumResponse


# ---------- USER ALBUM STATUS ----------
class StatusEnum(str, Enum):
    listened = "listened"
    want_to_listen = "want-to-listen"
    favorite = "favorite"

class UserAlbumStatusBase(BaseModel):
    status: StatusEnum

class UserAlbumStatusCreate(UserAlbumStatusBase):
    user_id: int
    album_id: int

class UserAlbumStatusResponse(UserAlbumStatusBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    user: Optional[UserResponse] = None       # <-- nested UserResponse
    album: Optional[AlbumResponse] = None     # <-- nested AlbumResponse
    

# ---------- USER DETAIL RESPONSE ----------    
class UserDetailResponse(UserResponse):
    reviews: list[ReviewResponse] = []
    statuses: list[UserAlbumStatusResponse] = []


class UserReviewsResponse(BaseModel):
    reviews: list[ReviewResponse]


# ---------- DELETE RESPONSE ----------    
class DeleteResponse(BaseModel):
    status: str
    id: int

# ---------- PAGINATION RESPONSE ----------   
T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    items: list[T]

# ---------- ERROR RESPONSE ----------
class ErrorResponse(BaseModel):
    detail: str
