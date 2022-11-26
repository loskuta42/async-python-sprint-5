import uvicorn
from fastapi import FastAPI, Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

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


@app.on_event('startup')
async def startup_event():
    async with async_session() as db:
        root_dir = await directory_crud.get_dir_info_by_path(
            db=db,
            dir_path=app_settings.files_folder_path
        )
        if root_dir:
            return
        await directory_crud.create_dir_info(
            db=db,
            path=app_settings.files_folder_path
        )

if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host=app_settings.project_host,
        port=app_settings.project_port,
    )
