from src.models.models import (
    User as UserModel,
    File as FileModel,
    Directory as DirectoryModel
)
from src.schemas.user import UserRegister
from .user import RepositoryUserDB
from .file import RepositoryFileDB
from .directory import RepositoryDirectoryDB


class RepositoryUser(
    RepositoryUserDB[
        UserModel,
        UserRegister,
    ]
):
    pass


class RepositoryFile(
    RepositoryFileDB[
        FileModel
    ]
):
    pass


class RepositoryDirectory(
    RepositoryDirectoryDB[
        FileModel
    ]
):
    pass


user_crud = RepositoryUser(UserModel)
file_crud = RepositoryFile(FileModel)
directory_crud = RepositoryDirectory(DirectoryModel)
