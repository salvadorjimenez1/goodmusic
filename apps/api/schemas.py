from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Generic, TypeVar
from enum import Enum
from datetime import datetime

# ---------- USERS ----------
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    confirm_password: str
    
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

# ---------- REVIEWS ----------
class ReviewBase(BaseModel):
    content: str = Field(..., min_length=5, max_length=1000)
    rating: Optional[float] = Field(
        None, ge=1.0, le=5.0, multiple_of=0.5
    ) 

class ReviewCreate(ReviewBase):
    user_id: int
    spotify_album_id: str

class ReviewResponse(ReviewBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user: Optional[UserResponse] = None
    spotify_album_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: UserOut

# ---------- USER ALBUM STATUS ----------
class StatusEnum(str, Enum):
    listened = "listened"
    want_to_listen = "want-to-listen"

class UserAlbumStatusBase(BaseModel):
    status: StatusEnum
    is_favorite: bool = False

class UserAlbumStatusCreate(UserAlbumStatusBase):
    user_id: int
    spotify_album_id: str

class UserAlbumStatusResponse(UserAlbumStatusBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    user: Optional[UserResponse] = None
    spotify_album_id: str

class UserAlbumStatusUpdate(BaseModel):
    status: Optional[StatusEnum] = None
    is_favorite: Optional[bool] = None

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

# ---------- SPOTIFY ----------
class SpotifyAlbumImport(BaseModel):
    spotify_album_id: str