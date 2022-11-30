from datetime import datetime
from typing import List, Union
from uuid import UUID

from pydantic import BaseModel, validator


class ORM(BaseModel):
    class Config:
        orm_mode = True


class FileInDB(ORM):
    id: UUID
    name: str
    created_at: datetime
    path: str
    size: int
    is_downloadable: bool

    @validator('created_at')
    def datetime_to_str(cls, value):
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        else:
            return value


class File(ORM):
    id: UUID
    name: str
    created_at: datetime
    path: str
    size: int
    is_downloadable: bool

    @validator('created_at', pre=True)
    def datetime_to_str(cls, value):
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        else:
            return value


class FilesList(ORM):
    account_id: UUID
    files: List


class ObjPath(ORM):
    path: str

    class Config:
        orm_mode = True
