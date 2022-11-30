import multiprocessing
import os
import time

import pytest
import uvicorn
from fastapi.testclient import TestClient
from dotenv import load_dotenv

from src.main import app


load_dotenv('../.env')


@pytest.fixture
def username_and_pass_for_test():
    return 'test1'


def server(host, port):
    uvicorn.run(
        'conftest:app',
        host=host,
        port=port,
    )


@pytest.fixture(autouse=True, scope='session')
def start_server():
    process = multiprocessing.Process(target=server, args=('127.0.0.1', 8080))
    process.start()
    time.sleep(4)
    yield
    process.terminate()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_token():
    return 'Bearer ' + os.environ.get('TEST_TOKEN')
