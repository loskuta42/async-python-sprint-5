from datetime import datetime
from typing import Union

from pydantic import BaseModel

from .file import File


class Token(BaseModel):
    access_token: str


class TokenUI(Token):
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class User(BaseModel):
    username: str


class UserRegisterResponse(User):
    created_at: Union[datetime, str]

    class Config:
        orm_mode = True


class UserRegister(User):
    password: str

    class Config:
        orm_mode = True


class UserAuth(UserRegister):
    pass


class CurrentUser(User):
    id: str
    created_at: Union[datetime, str]

    class Config:
        orm_mode = True


class UserInDB(CurrentUser):
    hashed_password: str
    files: list[File] = []

    class Config:
        orm_mode = True
