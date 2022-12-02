from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, validator


class ORM(BaseModel):
    class Config:
        orm_mode = True


class FileBase(ORM):
    id: UUID
    name: str
    created_at: datetime
    path: str
    size: int
    is_downloadable: bool


class FileInDB(FileBase):

    @validator('created_at')
    def datetime_to_str(cls, value):
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        else:
            return value


class File(FileBase):

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
