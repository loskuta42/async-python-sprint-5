import logging.config
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_cache.backends.redis import RedisCacheBackend
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import LOGGING
from src.db.db import get_session
from src.schemas import user as user_schema
from src.services.base import user_crud
from src.tools.cache import get_cache_or_data, redis_cache


router = APIRouter()

logging.config.dictConfig(LOGGING)
logger = logging.getLogger('register')


@router.post(
    '/',
    response_model=user_schema.UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    description='Create new user.'
)
async def create_user(
        *,
        db: AsyncSession = Depends(get_session),
        user_in: user_schema.UserRegister,
        cache: RedisCacheBackend = Depends(redis_cache)
) -> Any:
    """
    Create new user.
    """
    redis_key = f'register_username_{user_in.username}'
    user_obj = await get_cache_or_data(
        redis_key=redis_key,
        cache=cache,
        db_func_obj=user_crud.get_by_username,
        data_schema=user_schema.UserRegisterResponse,
        db_func_args=(db, user_in),
        cache_expire=3600
    )
    if user_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='User with this username exists.'
        )
    user = await user_crud.create(db=db, obj_in=user_in)
    logger.info('Create user - %s', user.username)
    return user
