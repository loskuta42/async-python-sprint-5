import logging.config
from typing import Any, Optional
from io import BytesIO

from fastapi import APIRouter, Depends, status, HTTPException, Query, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import app_settings
from src.db.db import get_session
from src.schemas import user as user_schema, file as file_schema
from src.core.logger import LOGGING
from src.services.base import file_crud
from src.services.auth import get_current_user
from src.tools.files import is_downloadable, compress, get_file_info, get_path_by_id
from src.tools.base import get_full_path


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
        current_user: user_schema.CurrentUser = Depends(get_current_user)
) -> Any:
    files = await file_crud.get_list_by_user_object(db=db, user_obj=current_user)
    return JSONResponse(content={
        'account_id': current_user.id,
        'files': files
    })


@router.post(
    '/upload',
    response_model=file_schema.File,
    status_code=status.HTTP_201_CREATED,
    description='Upload file.'
)
async def upload_file(
        *,
        path: str,
        db: AsyncSession = Depends(get_session),
        current_user: user_schema.CurrentUser = Depends(get_current_user),
        file: UploadFile = File(...)
) -> Any:
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
        path: str = Query(description='Query of file path OR file id.'),
        compression_type: Optional[str] = Query(default=None,
                                                description='Query of compression type (zip, 7z, tar) (Optional).')
) -> Any:
    if not compression_type:
        file_info = await get_file_info(db=db, path=path)
        is_downloadable(file_info=file_info)
        full_path = get_full_path(file_info.path)
        return FileResponse(path=full_path, filename=file_info.name)
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
            obj_id=path
        )
    refreshed_io, media_type = compress(
        io_obj=io_obj,
        path=path,
        compression_type=compression_type
    )
    return StreamingResponse(
        iter([refreshed_io.getvalue()]),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment;filename={file_name}'}
    )
