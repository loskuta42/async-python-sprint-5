import os.path
from datetime import datetime
from typing import Generic, Optional, Type, TypeVar
from uuid import uuid1

from aioshutil import copyfileobj
from fastapi import File as FileObj
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.core.config import app_settings
from src.db.db import Base
from src.tools.base import get_full_path
from src.tools.directory import create_dir_info


class Repository:
    def get_file_info_by_path(self, *args, **kwargs):
        raise NotImplementedError

    def get_file_info_by_id(self, *args, **kwargs):
        raise NotImplementedError

    def get_list_by_user_object(self, *args, **kwargs):
        raise NotImplementedError

    def create_or_put_file(self, *args, **kwargs):
        raise NotImplementedError


ModelType = TypeVar("ModelType", bound=Base)


class RepositoryFileDB(
    Repository,
    Generic[
        ModelType
    ]
):
    def __init__(
            self,
            model: Type[ModelType]
    ):
        self._model = model

    async def get_file_info_by_path(
            self,
            db: AsyncSession,
            file_path: str
    ) -> Optional[ModelType]:
        if not file_path.startswith('/'):
            file_path = '/' + file_path
        statement = select(self._model).where(self._model.path == file_path)
        result = await db.execute(statement=statement)
        return result.scalar_one_or_none()

    async def get_file_info_by_id(
            self,
            db: AsyncSession,
            file_id: str
    ) -> Optional[ModelType]:
        statement = select(self._model).where(self._model.id == file_id)
        result = await db.execute(statement=statement)
        return result.scalar_one_or_none()

    async def get_list_by_user_object(
            self,
            db: AsyncSession,
            user_obj: ModelType,
    ) -> list[ModelType]:
        statement = select(self._model).where(self._model.user_id == user_obj.id)
        results = await db.execute(statement=statement)
        return results.scalars().all()

    async def create_or_put_file(
            self,
            db: AsyncSession,
            user_obj: ModelType,
            file_obj: FileObj,
            file_path: str
    ) -> Optional[ModelType]:
        file_in_storage = await self.get_file_info_by_path(
            db=db,
            file_path=file_path
        )
        full_file_path = get_full_path(file_path)
        if file_in_storage:
            with open(full_file_path, 'wb') as buffer:
                await copyfileobj(file_obj.file, buffer)
            size = os.path.getsize(full_file_path)
            file_in_storage.size = size
            file_in_storage.created_at = datetime.utcnow()
            await db.commit()
            await db.refresh(file_in_storage)
            return file_in_storage
        else:
            path = app_settings.files_folder_path
            for dir_name in file_path.split('/')[1:-1]:
                path = os.path.join(path, dir_name)
                if os.path.exists(path):
                    continue
                else:
                    os.mkdir(path)
                    await create_dir_info(db=db, path=path)
            with open(full_file_path, 'wb') as buffer:
                await copyfileobj(file_obj.file, buffer)
            size = os.path.getsize(full_file_path)
            new_file = self._model(
                id=str(uuid1()),
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
