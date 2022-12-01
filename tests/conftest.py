import asyncio
import multiprocessing
import shutil
import time
from pathlib import Path

import pytest
import pytest_asyncio
import uvicorn
from fastapi_cache import caches
from fastapi_cache.backends.redis import RedisCacheBackend
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.core.config import app_settings
from src.main import app
from src.db.db import Base, get_session
from src.tools.cache import redis_cache


DATABASE_URL = "sqlite+aiosqlite:///./test.db"


def server(host, port):
    uvicorn.run(
        'conftest:app',
        host=host,
        port=port,
    )


def get_test_engine():
    return create_async_engine(DATABASE_URL, echo=True, future=True)


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def engine():
    engine = get_test_engine()
    yield engine
    engine.sync_engine.dispose()


@pytest.fixture(scope="session")
def async_session(engine):
    return sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest_asyncio.fixture(scope="session")
async def create_base(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="session")
async def test_app(engine, create_base):
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async def get_test_session() -> AsyncSession:
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session

    rc = RedisCacheBackend(app_settings.local_redis_url)
    caches.set('TEST_REDIS', rc)

    def redis_test_cache():
        return caches.get('TEST_REDIS')

    app.dependency_overrides[redis_cache] = redis_test_cache
    yield app


@pytest_asyncio.fixture(scope="session")
async def auth_async_client(test_app):
    test_user = 'test1'
    test_password = test_user
    async with AsyncClient(app=test_app, base_url='http://127.0.0.1:8080/api/v1') as ac:
        await ac.post(
            '/register/',
            json={
                'username': test_user,
                'password': test_password
            }
        )
        response_success = await ac.post(
            '/authorization/auth',
            json={
                'username': test_user,
                'password': test_password
            }
        )
        token = 'Bearer ' + response_success.json()['access_token']
        ac.headers = {'Authorization': token}
        yield ac


@pytest_asyncio.fixture(scope="session")
async def auth_async_client_with_file(auth_async_client):
    path_of_upload_file = Path('file_for_test.txt')
    file = {'file': path_of_upload_file.open('rb')}
    await auth_async_client.post(
        '/files/upload',
        params={
            'path': '/test'
        },
        files=file,
    )
    yield auth_async_client
    shutil.rmtree(app_settings.files_folder_path + '/test')


@pytest.fixture(autouse=True, scope='session')
def start_server():
    process = multiprocessing.Process(target=server, args=('127.0.0.1', 8080))
    process.start()
    time.sleep(4)
    yield
    process.terminate()
