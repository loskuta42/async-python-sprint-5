import logging.config
from typing import Any

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.db import get_session
from src.schemas import user as user_schema
from src.core.logger import LOGGING
from src.services.base import user_crud

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
) -> Any:
    """
    Create new user.
    """
    user_from_db = await user_crud.get_by_username(db=db, obj_in=user_in)
    if user_from_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='User with this username exists.'
        )
    user = await user_crud.create(db=db, obj_in=user_in)
    logger.info(
        'Create user - %s for %s', user.username
    )
    return user
