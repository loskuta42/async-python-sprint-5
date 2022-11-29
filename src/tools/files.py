import io
import logging.config
import os.path
import tarfile
import zipfile
from io import BytesIO

import py7zr
from fastapi import HTTPException, status
from fastapi_cache.backends.redis import RedisCacheBackend
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import LOGGING
from src.models.models import File
from src.schemas import file as file_schema
from src.services.base import directory_crud, file_crud

from .base import get_full_path
from .cache import get_cache_or_data


logging.config.dictConfig(LOGGING)
logger = logging.getLogger('tools-files')


def is_downloadable(file_info: dict):
    if not file_info.get('is_downloadable'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='You can not download this file.'
        )


async def get_file_info(
        db: AsyncSession,
        path: str
):
    if path.find('/') != -1:
        file_info = await file_crud.get_file_info_by_path(
            db=db,
            file_path=path
        )
    else:
        file_info = await file_crud.get_file_info_by_id(
            db=db,
            file_id=path
        )
    if not file_info:
        logger.error('Raise 404 for file with path/id %s', path)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='File not found'
        )
    return file_info


def is_file(path: str) -> bool:
    return os.path.isfile(path)


def get_files_paths_by_folder(full_path: str) -> list:
    return [
        os.path.join(full_path, f)
        for f in os.listdir(full_path)
        if os.path.isfile(os.path.join(full_path, f))
    ]


async def get_path_by_id(
        db: AsyncSession,
        obj_id: str,
        cache: RedisCacheBackend,
) -> str:
    redis_key = f'path_for_obj_id_{obj_id}'
    file_info = await get_cache_or_data(
        redis_key=redis_key,
        cache=cache,
        db_func_obj=file_crud.get_file_info_by_id,
        data_schema=file_schema.ObjPath,
        db_func_args=(db, obj_id),
        cache_expire=3600
    )
    if not file_info:
        dir_info = await get_cache_or_data(
            redis_key=redis_key,
            cache=cache,
            db_func_obj=directory_crud.get_dir_info_by_id,
            data_schema=file_schema.ObjPath,
            db_func_args=(db, obj_id),
            cache_expire=3600
        )
        if not dir_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Directory or file not found'
            )
        return dir_info.get()
    return file_info.get('path')


def zip_files(io_obj: BytesIO, full_path: str) -> tuple[io.BytesIO, str]:
    with zipfile.ZipFile(io_obj, mode='w', compression=zipfile.ZIP_DEFLATED) as zip_io:
        if is_file(full_path):
            zip_io.write(full_path)
        else:
            files_paths = get_files_paths_by_folder(full_path)
            for file_path in files_paths:
                zip_io.write(file_path)
        zip_io.close()
    return io_obj, 'application/x-zip-compressed'


def tar_files(io_obj: BytesIO, full_path: str) -> tuple[io.BytesIO, str]:
    with tarfile.open(fileobj=io_obj, mode='w:gz') as tar:
        if is_file(full_path):
            tar.add(full_path)
        else:
            files_paths = get_files_paths_by_folder(full_path)
            for file_path in files_paths:
                tar.add(file_path)
        tar.close()
    return io_obj, 'application/x-gtar'


def seven_zip_files(io_obj: BytesIO, full_path: str) -> tuple[io.BytesIO, str]:
    with py7zr.SevenZipFile(io_obj, mode='w') as seven_zip:
        if is_file(full_path):
            seven_zip.write(full_path)
        else:
            files_paths = get_files_paths_by_folder(full_path)
            for file_path in files_paths:
                seven_zip.write(file_path)
    return io_obj, 'application/x-7z-compressed'


COMPRESSION_TO_FUNC = {
    'zip': zip_files,
    'tar': tar_files,
    '7z': seven_zip_files
}


def compress(
        io_obj: BytesIO,
        path: str,
        compression_type: str
):
    full_path = get_full_path(path=path)
    io_obj, media_type = COMPRESSION_TO_FUNC[compression_type](io_obj, full_path)
    return io_obj, media_type
