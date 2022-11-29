import logging.config
from io import BytesIO
from typing import Any, Optional

from fastapi import (APIRouter, Depends, File, HTTPException, Query,
                     UploadFile, status)
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi_cache.backends.redis import RedisCacheBackend
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import app_settings
from src.core.logger import LOGGING
from src.db.db import get_session
from src.schemas import file as file_schema
from src.schemas import user as user_schema
from src.services.auth import get_current_user
from src.services.base import file_crud
from src.tools.base import get_full_path
from src.tools.cache import (get_cache, get_cache_or_data, redis_cache,
                             set_cache)
from src.tools.files import (compress, get_file_info, get_path_by_id,
                             is_downloadable)


router = APIRouter()

logging.config.dictConfig(LOGGING)
logger = logging.getLogger('files')


@router.get(
    '/list',
    response_model=file_schema.FilesList,
    description='Get files list of current user.'
)
async def get_list(
        *,
        db: AsyncSession = Depends(get_session),
        current_user: user_schema.CurrentUser = Depends(get_current_user),
        cache: RedisCacheBackend = Depends(redis_cache)
) -> Any:
    redis_key = f'files_list_for_{current_user.id}'
    data = await get_cache(cache, redis_key)
    if not data:
        files = await file_crud.get_list_by_user_object(db=db, user_obj=current_user)
        files_lst = [file_schema.File.from_orm(file).dict() for file in files]
        data = {
            'account_id': current_user.id,
            'files': files_lst
        }
        await set_cache(cache, data, redis_key)
    logger.info('Send list of files of %s', current_user.id)
    return JSONResponse(content=jsonable_encoder(data, exclude={'user_id'}))


@router.post(
    '/upload',
    response_model=file_schema.File,
    status_code=status.HTTP_201_CREATED,
    description='Upload file.'
)
async def upload_file(
        *,
        path: str = Query(description='Enter path to directory OR file, '
                                      'both start with /'),
        db: AsyncSession = Depends(get_session),
        current_user: user_schema.CurrentUser = Depends(get_current_user),
        file: UploadFile = File(...)
) -> Any:
    if not path.startswith('/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Path must starts with / .'
        )
    if path.split('/')[-1] == file.filename:
        full_path = path
    else:
        full_path = path + '/' + file.filename
    file_obj = await file_crud.create_or_put_file(
        db=db,
        user_obj=current_user,
        file_obj=file,
        file_path=full_path
    )
    logger.info('Upload/put file %s from %s', full_path, current_user.id)
    return file_obj


@router.get(
    '/download',
    status_code=status.HTTP_200_OK,
    description='Download file by path.'
)
async def download_file_by_path_or_id(
        *,
        db: AsyncSession = Depends(get_session),
        current_user: user_schema.CurrentUser = Depends(get_current_user),
        path: str = Query(description='Query of file path (starts with /) OR file id, '
                                      'for compression available directory path OR '
                                      'directory id'),
        compression_type: Optional[str] = Query(default=None,
                                                description='Query of compression type '
                                                            '(zip, 7z, tar) (Optional).'),
        cache: RedisCacheBackend = Depends(redis_cache)
) -> Any:
    if not compression_type:
        file_info_redis_key = f'file_info_for_{path}'
        file_info = await get_cache_or_data(
            redis_key=file_info_redis_key,
            cache=cache,
            db_func_obj=get_file_info,
            data_schema=file_schema.File,
            db_func_args=(db, path)
        )
        is_downloadable(file_info=file_info)
        full_path = get_full_path(file_info.get('path'))
        return FileResponse(path=full_path, filename=file_info.get('name'))
    if compression_type not in app_settings.compression_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Specified compression type is not supported.'
        )
    io_obj = BytesIO()
    file_name = 'archive' + '.' + compression_type
    if path.find('/') == -1:
        path = await get_path_by_id(
            db=db,
            obj_id=path,
            cache=cache
        )
    if not path.startswith('/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Path must starts with / .'
        )
    refreshed_io, media_type = compress(
        io_obj=io_obj,
        path=path,
        compression_type=compression_type
    )
    logger.info('User %s download file %s', current_user.id, path)
    return StreamingResponse(
        iter([refreshed_io.getvalue()]),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment;filename={file_name}'}
    )
