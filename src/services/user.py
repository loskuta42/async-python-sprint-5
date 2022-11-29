from typing import Generic, Optional, Type, TypeVar
from uuid import uuid1

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.db.db import Base
from src.tools.password import get_password_hash


class Repository:
    def get_by_username(self, *args, **kwargs):
        raise NotImplementedError

    def create(self, *args, **kwargs):
        raise NotImplementedError


ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)


class RepositoryUserDB(
    Repository,
    Generic[
        ModelType,
        CreateSchemaType
    ]
):
    def __init__(
            self,
            model: Type[ModelType]
    ):
        self._model = model

    async def get_by_username(
            self,
            db: AsyncSession,
            obj_in: CreateSchemaType
    ) -> Optional[ModelType]:
        obj_in_data = jsonable_encoder(obj_in)
        statement = select(
            self._model
        ).where(
            self._model.username == obj_in_data['username']
        )
        results = await db.execute(statement=statement)
        return results.scalar_one_or_none()

    def create_obj(self, obj_in_data: dict):
        extra_obj_info = {}
        user_id = str(uuid1())
        extra_obj_info['id'] = user_id
        password = obj_in_data.pop('password')
        extra_obj_info['hashed_password'] = get_password_hash(password)
        obj_in_data.update(extra_obj_info)
        return self._model(**obj_in_data)

    async def create(
            self,
            db: AsyncSession,
            *,
            obj_in: CreateSchemaType
    ) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.create_obj(obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
