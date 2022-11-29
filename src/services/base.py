from src.models.models import Directory as DirectoryModel
from src.models.models import File as FileModel
from src.models.models import User as UserModel
from src.schemas.user import UserRegister

from .directory import RepositoryDirectoryDB
from .file import RepositoryFileDB
from .user import RepositoryUserDB


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
