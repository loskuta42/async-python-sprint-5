import os

import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi_cache import caches, close_caches
from fastapi_cache.backends.redis import CACHE_KEY, RedisCacheBackend
from fastapi.staticfiles import StaticFiles

from src.api.v1 import base
from src.core.config import app_settings
from src.db.db import async_session
from src.services.base import directory_crud


app = FastAPI(
    title=app_settings.app_title,
    docs_url='/api/openapi',
    openapi_url='/api/openapi.json',
    default_response_class=ORJSONResponse,
    swagger_ui_oauth2_redirect_url='/authorization/token'
)

app.include_router(base.api_router, prefix='/api/v1')
app.mount('/files', StaticFiles(directory='files'), name='files')


@app.on_event('startup')
async def on_startup() -> None:
    rc = RedisCacheBackend(app_settings.redis_url)
    caches.set(CACHE_KEY, rc)


@app.on_event('shutdown')
async def on_shutdown() -> None:
    await close_caches()


if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host=app_settings.project_host,
        port=app_settings.project_port,
    )
