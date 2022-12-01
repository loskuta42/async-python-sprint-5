import logging.config
from typing import Any, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status
)
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi_cache.backends.redis import RedisCacheBackend
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import app_settings
from src.db.db import get_session
from src.schemas import file as file_schema
from src.schemas import user as user_schema
from src.services.auth import get_current_user
from src.services.base import file_crud
from src.tools.cache import (
    get_cache,
    get_cache_or_data,
    redis_cache,
    set_cache
)
from src.tools.files import (
    get_file_info,
    is_downloadable,
    get_compressed_file_with_media_type
)

router = APIRouter()

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
    redis_key = f'files_list_for_{str(current_user.id)}'
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
    return data


@router.post(
    '/upload',
    response_model=file_schema.FileInDB,
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
        file_url = app_settings.static_url + file_info.get('path')
        return RedirectResponse(file_url)
    if compression_type not in app_settings.compression_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Specified compression type is not supported.'
        )
    refreshed_io, media_type = await get_compressed_file_with_media_type(
        db=db,
        cache=cache,
        path=path,
        compression_type=compression_type
    )
    file_name = 'archive' + '.' + compression_type
    logger.info('User %s download file %s', current_user.id, path)
    return StreamingResponse(
        iter([refreshed_io.getvalue()]),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment;filename={file_name}'}
    )
