import os.path
import shutil
from http import HTTPStatus
from datetime import datetime
from pathlib import Path

import requests


def test_register(start_server):
    test = datetime.utcnow()
    response_create = requests.post(
        'http://127.0.0.1:8080/api/v1/register/',
        json={
            'username': f'test{test}',
            'password': f'test{test}'
        }
    )
    assert response_create.status_code == HTTPStatus.CREATED
    assert 'created_at' in response_create.json()

    response_recreate = requests.post(
        'http://127.0.0.1:8080/api/v1/register/',
        json={
            'username': f'test{test}',
            'password': f'test{test}'
        }
    )
    assert response_recreate.status_code == HTTPStatus.BAD_REQUEST


def test_auth(start_server, username_and_pass_for_test):
    response_success = requests.post(
        'http://127.0.0.1:8080/api/v1/authorization/auth/',
        json={
            'username': username_and_pass_for_test,
            'password': username_and_pass_for_test
        }
    )
    assert response_success.status_code == HTTPStatus.OK
    assert 'access_token' in response_success.json()

    response_failed = requests.post(
        'http://127.0.0.1:8080/api/v1/authorization/auth/',
        json={
            'username': username_and_pass_for_test,
            'password': username_and_pass_for_test + '1'
        }
    )

    assert response_failed.status_code == HTTPStatus.UNAUTHORIZED


def test_ping(start_server):
    response = requests.get(
        'http://127.0.0.1:8080/api/v1/ping/'
    )
    assert response.status_code == HTTPStatus.OK
    assert 'db' in response.json()
    assert 'redis' in response.json()


def test_upload_file(start_server, auth_token):
    path_of_upload_file = Path('./README.md')
    file = {'file': path_of_upload_file.open('rb')}
    response = requests.post(
        'http://127.0.0.1:8080/api/v1/files/upload',
        headers={
            'Authorization': auth_token
        },
        params={
            'path': '/test'
        },
        files=file,
    )
    assert response.status_code == HTTPStatus.CREATED
    assert 'id' in response.json()


def test_download_file(start_server, auth_token):
    response = requests.get(
        'http://127.0.0.1:8080/api/v1/files/download',
        headers={
            'Authorization': auth_token
        },
        params={
            'path': '/test/README.md'
        },
        stream=True
    )
    assert response.status_code == HTTPStatus.OK
    result_path = './file_test/README.md'
    with open(result_path, 'wb') as file:
        response.raw.decode_content = True
        shutil.copyfileobj(response.raw, file)
    assert os.path.exists(result_path)
    assert os.path.getsize(result_path) > 5


def test_download_compressed_file(start_server, auth_token):
    response = requests.get(
        'http://127.0.0.1:8080/api/v1/files/download',
        headers={
            'Authorization': auth_token
        },
        params={
            'path': '/test/README.md',
            'compression_type': 'zip'
        },
        stream=True
    )
    assert response.status_code == HTTPStatus.OK
    result_path = './file_test/test.zip'
    with open(result_path, 'wb') as file:
        response.raw.decode_content = True
        shutil.copyfileobj(response.raw, file)
    assert os.path.exists(result_path)
    assert os.path.getsize(result_path) > 5
