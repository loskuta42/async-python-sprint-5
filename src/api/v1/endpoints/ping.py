import logging.config
from datetime import datetime

import redis.asyncio as redis
from fastapi import APIRouter, status

from src.core.logger import LOGGING
from src.db.db import engine
from src.schemas import ping as ping_schema


router = APIRouter()

logging.config.dictConfig(LOGGING)
logger = logging.getLogger('ping')


@router.get(
    '/',
    response_model=ping_schema.Ping,
    description='Access time for services.',
    status_code=status.HTTP_200_OK,
)
async def get_ping():
    start_db = datetime.utcnow()
    async with engine.begin() as conn:
        finish_db = datetime.utcnow()

    time_db = (finish_db - start_db).total_seconds()

    redis_connection = redis.Redis()
    start_redis = datetime.utcnow()
    await redis_connection.ping()
    finish_redis = datetime.utcnow()

    time_redis = (finish_redis - start_redis).total_seconds()
    logger.info('Send ping.')
    return {
        'db': time_db,
        'redis': time_redis
    }