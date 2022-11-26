import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import Directory


async def create_dir_info(
        db: AsyncSession,
        path: str
) -> Directory:
    dir_id = str(uuid.uuid1())
    dir_info_obj = Directory(
        id=dir_id,
        path=path
    )
    db.add(dir_info_obj)
    await db.commit()
    await db.refresh(dir_info_obj)
    return dir_info_obj
