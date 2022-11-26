from datetime import datetime

from pydantic import BaseModel


class File(BaseModel):
    id: str
    name: str
    created_at: datetime
    path: str
    size: int
    is_downloadable: bool

    class Config:
        orm_mode = True


class FilesList(BaseModel):
    account_id: str
    files: list
