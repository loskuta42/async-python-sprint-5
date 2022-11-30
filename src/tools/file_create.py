import os.path
from datetime import datetime
from typing import Callable, Type

from aioshutil import copyfileobj
from fastapi import File as FileObj
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import File as FileModel, User as UserModel
from ..core.config import app_settings


async def write_to_file(
        file_obj: FileObj,
        full_file_path: str,
):
    with open(full_file_path, 'wb') as buffer:
        await copyfileobj(file_obj.file, buffer)


async def create_file(
        db: AsyncSession,
        file_path: str,
        full_file_path: str,
        create_dir_info: Callable,
        file_obj: FileObj,
        model: Type[FileModel],
        user_obj: Type[UserModel]
):
    path = app_settings.files_folder_path
    for dir_name in file_path.split('/')[1:-1]:
        path = os.path.join(path, dir_name)
        if os.path.exists(path):
            continue
        else:
            os.mkdir(path)
            await create_dir_info(db=db, path=path)
    await write_to_file(
        file_obj=file_obj,
        full_file_path=full_file_path
    )
    size = os.path.getsize(full_file_path)
    new_file = model(
        name=file_obj.filename,
        path=file_path,
        size=size,
        is_downloadable=True,
        user=user_obj
    )
    db.add(new_file)
    await db.commit()
    await db.refresh(new_file)
    return new_file


async def put_file(
        db: AsyncSession,
        file_obj: FileObj,
        full_file_path: str,
        file_info: Type[FileModel]
):
    await write_to_file(
        file_obj=file_obj,
        full_file_path=full_file_path
    )
    size = os.path.getsize(full_file_path)
    file_info.size = size
    file_info.created_at = datetime.utcnow()
    await db.commit()
    await db.refresh(file_info)
    return file_info
