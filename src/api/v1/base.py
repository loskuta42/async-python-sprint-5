from fastapi import APIRouter

from .endpoints import authorization, files, ping, register


api_router = APIRouter()


api_router.include_router(
    register.router,
    prefix='/register',
    tags=['user_register']
)

api_router.include_router(
    authorization.router,
    prefix='/authorization',
    tags=['authorization']
)

api_router.include_router(
    files.router,
    prefix='/files',
    tags=['files']
)

api_router.include_router(
    ping.router,
    prefix='/ping',
    tags=['ping']
)
