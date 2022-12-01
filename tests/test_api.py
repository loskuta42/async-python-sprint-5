import os.path
from http import HTTPStatus
from datetime import datetime
from pathlib import Path

import aiofile
import pytest
from httpx import AsyncClient
from src.core.config import app_settings


@pytest.mark.asyncio
async def test_register(test_app):
    async with AsyncClient(app=test_app, base_url='http://127.0.0.1:8080/api/v1') as ac:
        test = datetime.utcnow()
        response_create = await ac.post(
            '/register/',
            json={
                'username': f'test{test}',
                'password': f'test{test}'
            }
        )
        assert response_create.status_code == HTTPStatus.CREATED
        assert 'created_at' in response_create.json()

        response_recreate = await ac.post(
            '/register/',
            json={
                'username': f'test{test}',
                'password': f'test{test}'
            }
        )
        assert response_recreate.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_auth(test_app):
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
        assert response_success.status_code == HTTPStatus.OK
        assert 'access_token' in response_success.json()

        response_failed = await ac.post(
            '/authorization/auth',
            json={
                'username': test_user,
                'password': test_password + '1'
            }
        )

        assert response_failed.status_code == HTTPStatus.UNAUTHORIZED

@pytest.mark.asyncio
async def test_ping(test_app):
    async with AsyncClient(app=test_app, base_url='http://127.0.0.1:8080/api/v1') as ac:
        response = await ac.get(
            '/ping/'
        )
        assert response.status_code == HTTPStatus.OK
        assert 'db' in response.json()
        assert 'redis' in response.json()


@pytest.mark.asyncio
async def test_upload_file(auth_async_client):
    path_of_upload_file = Path('file_for_test.txt')
    file = {'file': path_of_upload_file.open('rb')}
    response = await auth_async_client.post(
        '/files/upload',
        params={
            'path': '/test'
        },
        files=file,
    )
    assert response.status_code == HTTPStatus.CREATED
    assert 'id' in response.json()


@pytest.mark.asyncio
async def test_download_file(auth_async_client_with_file):
    req = auth_async_client_with_file.build_request(
        'GET',
        '/files/download',
        params={
            'path': '/test/file_for_test.txt'
        },
        headers=auth_async_client_with_file.headers
    )
    response = await auth_async_client_with_file.send(req, stream=True)
    assert response.status_code == HTTPStatus.TEMPORARY_REDIRECT
    location = response.headers['Location']
    assert location == app_settings.static_url + '/test/file_for_test.txt'


@pytest.mark.asyncio
async def test_download_compressed_file(auth_async_client_with_file):
    req = auth_async_client_with_file.build_request(
        'GET',
        '/files/download',
        params={
            'path': '/test/file_for_test.txt',
            'compression_type': 'zip'
        },
        headers=auth_async_client_with_file.headers
    )
    response = await auth_async_client_with_file.send(req, stream=True)
    assert response.status_code == HTTPStatus.OK
    result_path = '../file_test/test.zip'
    async with aiofile.async_open(result_path, "wb+") as afp:
        async for chunk in response.aiter_bytes():
            await afp.write(chunk)
    assert os.path.exists(result_path)
    assert os.path.getsize(result_path) > 5
    os.remove(result_path)
