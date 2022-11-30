import os
from logging import config as logging_config

from pydantic import BaseSettings, Field, PostgresDsn

from .logger import LOGGING


logging_config.dictConfig(LOGGING)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUMBER_OF_DELETED_SYMBOLS = len(BASE_DIR.split('/')[-1]) + 1


class AppSettings(BaseSettings):
    app_title: str = 'FileStorageApp'
    database_dsn: PostgresDsn
    project_name: str = Field('FileStorage', env='PROJECT_NAME')
    project_host: str = Field('127.0.0.1', env='PROJECT_HOST')
    project_port: int = Field(8080, env='PROJECT_PORT')
    base_dir: str = Field(BASE_DIR, env='BASE_DIR')
    token_expire_minutes: int = Field(60, env='ACCESS_TOKEN_EXPIRE_MINUTES')

    files_folder_path: str = Field(
        os.path.join(
            BASE_DIR[:((-1) * NUMBER_OF_DELETED_SYMBOLS)],
            'files'
        ),
        env='FILES_BASE_DIR'
    )
    compression_types: list = Field(
        ['zip', '7z', 'tar'],
        env='COMPRESSION_TYPES'
    )

    class Config:
        env_file = '.env'


app_settings = AppSettings()
