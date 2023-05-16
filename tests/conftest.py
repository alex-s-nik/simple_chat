import asyncio.streams as streams

import pytest


from server import Server

from models.client import Client
from models.user import User

@pytest.fixture
def server():
    return Server()

@pytest.fixture
def first_user():
    return User(
        nickname='testnick',
        password='testP@ss'
    )

@pytest.fixture
def second_user():
    return User(
        nickname='testnick2',
        password='testP@ss2'
    )

@pytest.fixture
def client(first_user):
    return Client(
        user=first_user,
        writer=None,
        reader=None
    )

class MockedStream:
    def write(self, msg):
        print(msg)

    def read(self):
        return 'test_msg'

@pytest.fixture
def mocked_stream_writer(monkeypatch):
    def mock_writer(*args, **kwargs):
        return MockedStream()
    
    monkeypatch.setattr(streams, 'StreamWriter', mock_writer)

@pytest.fixture
def mocked_stream_reader(monkeypatch):
    def mock_reader(*args, **kwargs):
        return MockedStream()
    
    monkeypatch.setattr(streams, 'StreamReader', mock_reader)
