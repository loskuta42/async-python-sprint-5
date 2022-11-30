import logging
from datetime import datetime, timedelta
from typing import Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.db.db import get_session
from src.models.models import User
from src.schemas import user as user_schema
from src.tools.password import verify_password
from src.core.config import app_settings


logging.getLogger('services_auth')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='v1/authorization/token')


async def get_user(db: AsyncSession, username: str):
    statement = select(
        User
    ).where(
        User.username == username
    )
    results = await db.execute(statement=statement)
    return results.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await get_user(db=db, username=username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        app_settings.secret_key,
        algorithm=app_settings.algorithm
    )
    return encoded_jwt


async def get_current_user(db: AsyncSession = Depends(get_session), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            app_settings.secret_key,
            algorithms=[app_settings.algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = user_schema.TokenData(username=username)
    except JWTError:
        logging.exception('Exception at get_current func')
        raise credentials_exception
    user = await get_user(db=db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_token(db: AsyncSession, username: str, password: str):
    user: Union[User, bool] = await authenticate_user(db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=app_settings.token_expire_minutes)
    token =  create_access_token(
        data={'sub': user.username}, expires_delta=access_token_expires
    )
    return {'access_token': token, 'token_type': 'bearer'}