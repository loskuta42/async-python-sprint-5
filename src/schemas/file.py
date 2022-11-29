from datetime import datetime
from typing import List, Union

from pydantic import BaseModel


class File(BaseModel):
    id: str
    name: str
    created_at: Union[datetime, str]
    path: str
    size: int
    is_downloadable: bool

    class Config:
        orm_mode = True


class FilesList(BaseModel):
    account_id: str
    files: List[File]

    class Config:
        orm_mode = True


class ObjPath(BaseModel):
    path: str

    class Config:
        orm_mode = True
