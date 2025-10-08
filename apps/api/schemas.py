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
    id: int
    username: str
    profile_picture: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

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
    id: int
    user: UserOut
    spotify_album_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

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
    id: int
    created_at: datetime
    spotify_album_id: str
    user: Optional[UserOut] = None
    model_config = ConfigDict(from_attributes=True)

class UserAlbumStatusUpdate(BaseModel):
    status: Optional[StatusEnum] = None
    is_favorite: Optional[bool] = None

# ---------- FOLLOWS ----------

class FollowListResponse(BaseModel):
    total: int
    users: list[UserOut]

class MutualFollower(UserOut):
    pass

# ---------- USER DETAIL RESPONSE ----------

class UserDetailResponse(UserOut):
    reviews: list[ReviewResponse] = []
    statuses: list[UserAlbumStatusResponse] = []
    is_following: Optional[bool] = None
    followers_count: int = 0
    following_count: int = 0
    mutual_followers: list[MutualFollower] = []
    mutual_followers_count: int = 0  

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