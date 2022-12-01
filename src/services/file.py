from typing import Generic, Optional, Type, TypeVar

from fastapi import File as FileObj
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.db.db import Base
from src.tools.base import get_full_path
from src.tools.directory import create_dir_info
from src.tools.file_create import put_file, create_file


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
            return await put_file(
                db=db,
                full_file_path=full_file_path,
                file_info=file_in_storage,
                file_obj=file_obj
            )
        else:
            return await create_file(
                db=db,
                file_path=file_path,
                full_file_path=full_file_path,
                create_dir_info=create_dir_info,
                file_obj=file_obj,
                model=self._model,
                user_obj=user_obj
            )
