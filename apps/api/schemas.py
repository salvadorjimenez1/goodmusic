from pydantic import BaseModel, ConfigDict
from typing import Optional, List

# ---------- USERS ----------
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- ARTISTS ----------
class ArtistBase(BaseModel):
    name: str

class ArtistResponse(ArtistBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- ALBUMS ----------
class AlbumBase(BaseModel):
    title: str
    year: Optional[int] = None
    cover_url: Optional[str] = None

class AlbumCreate(AlbumBase):
    artist: str  # name of artist

class AlbumResponse(AlbumBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    artist: Optional[ArtistResponse] = None   # <-- now nested instead of str


# ---------- REVIEWS ----------
class ReviewBase(BaseModel):
    content: str

class ReviewCreate(ReviewBase):
    user_id: int
    album_id: int

class ReviewResponse(ReviewBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user: Optional[UserResponse] = None       # <-- nested UserResponse
    album: Optional[AlbumResponse] = None     # <-- nested AlbumResponse


# ---------- USER ALBUM STATUS ----------
class UserAlbumStatusBase(BaseModel):
    status: str

class UserAlbumStatusCreate(UserAlbumStatusBase):
    user_id: int
    album_id: int

class UserAlbumStatusResponse(UserAlbumStatusBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user: Optional[UserResponse] = None       # <-- nested UserResponse
    album: Optional[AlbumResponse] = None     # <-- nested AlbumResponse
    

# ---------- USER DETAIL RESPONSE ----------    
class UserDetailResponse(UserResponse):
    reviews: list[ReviewResponse] = []
    statuses: list[UserAlbumStatusResponse] = []


# ---------- DELETE RESPONSE ----------    
class DeleteResponse(BaseModel):
    status: str
    id: int