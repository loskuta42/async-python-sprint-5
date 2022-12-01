from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, validator

from .file import File


class ORM(BaseModel):
    class Config:
        orm_mode = True


class Token(ORM):
    access_token: str


class TokenUI(Token):
    pass


class TokenData(ORM):
    username: Optional[str] = None


class User(ORM):
    username: str


class UserRegisterResponse(User):
    created_at: datetime


class UserRegister(User):
    password: str


class UserAuth(UserRegister):
    pass


class CurrentUser(User):
    id: UUID
    created_at: datetime

    @validator('created_at', pre=True)
    def datetime_to_str(cls, value):
        if isinstance(value, str):
            return datetime.fromisoformat(value)


class UserInDB(CurrentUser):
    hashed_password: str
    files: list[File] = []
