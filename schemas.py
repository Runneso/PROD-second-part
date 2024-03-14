from pydantic import BaseModel
from pydantic import Field
from typing import *


class Country(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Полное название страны")
    alpha2: str = Field(..., min_length=2, max_length=2, pattern="[a-zA-Z]{2}",
                        description="Двухбуквенный код, уникально идентифицирующий страну")
    alpha3: str = Field(..., min_length=3, max_length=3, pattern="[a-zA-Z]{3}", description="Трехбуквенный код страны")
    region: Optional[str] = Field(None)


class User(BaseModel):
    login: str = Field(..., min_length=1, max_length=30, pattern="[a-zA-Z0-9-]+", )
    password: str = Field(..., min_length=6, max_length=100)
    email: str = Field(..., min_length=1, max_length=50)
    countryCode: str = Field(..., min_length=2, max_length=2, pattern="[a-zA-Z]{2}",
                             description="Двухбуквенный код, уникально идентифицирующий страну")
    isPublic: bool
    phone: Optional[str] = Field(None, max_length=20, pattern="\+[\d]+")
    image: Optional[str] = Field(None, min_length=1, max_length=100)


class UserProfile(BaseModel):
    login: str = Field(..., min_length=1, max_length=30, pattern="[a-zA-Z0-9-]+")
    email: str = Field(..., min_length=1, max_length=50)
    countryCode: str = Field(..., min_length=2, max_length=2, pattern="[a-zA-Z]{2}",
                             description="Двухбуквенный код, уникально идентифицирующий страну")
    isPublic: bool
    phone: Optional[str] = Field(None, max_length=20, pattern="\+[\d]+")
    image: Optional[str] = Field(None, min_length=1, max_length=100)


class UserProfileWithoutImage(BaseModel):
    login: str = Field(..., min_length=1, max_length=30, pattern="[a-zA-Z0-9-]+")
    email: str = Field(..., min_length=1, max_length=50)
    countryCode: str = Field(..., min_length=2, max_length=2, pattern="[a-zA-Z]{2}",
                             description="Двухбуквенный код, уникально идентифицирующий страну")
    isPublic: bool
    phone: Optional[str] = Field(None, max_length=20, pattern="\+[\d]+")


class UserProfileWithoutPhone(BaseModel):
    login: str = Field(..., min_length=1, max_length=30, pattern="[a-zA-Z0-9-]+")
    email: str = Field(..., min_length=1, max_length=50)
    countryCode: str = Field(..., min_length=2, max_length=2, pattern="[a-zA-Z]{2}",
                             description="Двухбуквенный код, уникально идентифицирующий страну")
    isPublic: bool
    image: Optional[str] = Field(None, min_length=1, max_length=100)


class UserProfileWithoutImageAndPhone(BaseModel):
    login: str = Field(..., min_length=1, max_length=30, pattern="[a-zA-Z0-9-]+")
    email: str = Field(..., min_length=1, max_length=50)
    countryCode: str = Field(..., min_length=2, max_length=2, pattern="[a-zA-Z]{2}",
                             description="Двухбуквенный код, уникально идентифицирующий страну")
    isPublic: bool


class UpdateProfile(BaseModel):
    countryCode: Optional[str] = Field(None, min_length=2, max_length=2, pattern="[a-zA-Z]{2}",
                                       description="Двухбуквенный код, уникально идентифицирующий страну")
    isPublic: Optional[bool] = None
    phone: Optional[str] = Field(None, max_length=20, pattern="\+[\d]+")
    image: Optional[str] = Field(None, min_length=1, max_length=100)


class UpdatePassword(BaseModel):
    oldPassword: str = Field(..., min_length=6, max_length=100)
    newPassword: str = Field(..., min_length=6, max_length=100)


class Status(BaseModel):
    status: str


class Token(BaseModel):
    token: str


class SingInUser(BaseModel):
    login: str = Field(..., min_length=1, max_length=30, pattern="[a-zA-Z0-9-]+")
    password: str = Field(..., min_length=6, max_length=100)


class Profile(BaseModel):
    profile: Union[UserProfile, UserProfileWithoutImage, UserProfileWithoutPhone, UserProfileWithoutImageAndPhone]


class Friend(BaseModel):
    login: str = Field(..., min_length=1, max_length=30, pattern="[a-zA-Z0-9-]+")
    addedAt: str


class AddFriend(BaseModel):
    login: str = Field(..., min_length=1, max_length=30, pattern="[a-zA-Z0-9-]+")


class RemoveFriend(BaseModel):
    login: str = Field(..., min_length=1, max_length=30, pattern="[a-zA-Z0-9-]+")


class Post(BaseModel):
    id: str = Field(..., max_length=100)
    content: str = Field(..., max_length=1000)
    author: str = Field(..., min_length=1, max_length=30, pattern="[a-zA-Z0-9-]+")
    tags: List[str]
    createdAt: str
    likesCount: int = Field(..., gt=-1)
    dislikesCount: int = Field(..., gt=-1)


class AddPost(BaseModel):
    content: str = Field(..., max_length=1000)
    tags: List[str]


class ErrorResponse(BaseModel):
    reason: str = Field(..., min_length=5)
