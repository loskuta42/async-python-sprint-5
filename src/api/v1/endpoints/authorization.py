import logging.config
import os

from dotenv import load_dotenv
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import LOGGING
from src.db.db import get_session
from src.schemas import user as user_schema
from src.services.auth import get_token


router = APIRouter()

logging.config.dictConfig(LOGGING)
logger = logging.getLogger('auth')

load_dotenv('.env')

ACCESS_TOKEN_EXPIRE_MINUTES = float(os.environ['ACCESS_TOKEN_EXPIRE_MINUTES'])


@router.post(
    '/token',
    response_model=user_schema.TokenUI,
    description='Auth form for Swagger UI'
)
async def login_ui_for_access_token(
        *,
        db: AsyncSession = Depends(get_session),
        form_data: OAuth2PasswordRequestForm = Depends()
):
    access_token = await get_token(
        db=db,
        username=form_data.username,
        password=form_data.password
    )
    logger.info(f'Send token for {form_data.username}')
    return {'access_token': access_token, 'token_type': 'bearer'}


@router.post(
    '/auth',
    response_model=user_schema.Token,
    description='Get token for user.'
)
async def get_token_for_user(
        *,
        db: AsyncSession = Depends(get_session),
        obj_in: user_schema.UserAuth
):
    obj_in_data = jsonable_encoder(obj_in)
    username, password = obj_in_data['username'], obj_in_data['password']
    access_token = await get_token(
        db=db,
        username=username,
        password=password
    )
    logger.info('Send token for %s', username)
    return {'access_token': access_token}
