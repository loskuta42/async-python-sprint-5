from src.core.config import app_settings


def get_full_path(path: str):
    return app_settings.files_folder_path + path
