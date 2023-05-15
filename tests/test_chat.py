import asyncio
import pytest

from client import Client
from server import Server


server = Server()

@pytest.mark.asyncio
async def test_server():
    try:
        reader, writer = await asyncio.open_connection(
            '127.0.0.1',
            8000)
    except ConnectionRefusedError:
        assert False, 'Server is not running'
    message = await reader.read(1024)
    assert message.decode() == 'Server started at 127.0.0.1:8000'