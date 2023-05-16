import asyncio
import pytest

from client import Client
from exceptions import (
    UserAlreadyExistsChatException,
    UserIsBannedException,
    UserNotLoggedInException,
    WrongUsernameOrPasswordException,
)
from server import Server


def test_register(
        server,
        first_user,
        mocked_stream_writer,
        mocked_stream_reader
    ):
    assert server.users == {}, 'server after start has users'
    assert server.users_online == set(), 'server after start has online users'
    assert server.clients_online == [], 'server after start has online clients'
    assert server.client_counter == {}, 'server after start has non-empty client counter'
    assert server.banned_users == [], 'server after start has banned users'
    assert server.messages == [], 'server after start has messages'

    _ = server.command_register(
        first_user.nickname,
        first_user.password,
        asyncio.streams.StreamReader(),
        asyncio.streams.StreamWriter()
    )

    assert len(server.users) == 1, 'user has been not wrote in server-users list'
    assert first_user.nickname in server.users, 'user has been wrote in server-users list with wrong nick'
    assert len(server.clients_online) == 1, 'current client was not added to online clients'

    with pytest.raises(UserAlreadyExistsChatException):
        _ = server.command_register(
        first_user.nickname,
        first_user.password,
        asyncio.streams.StreamReader(),
        asyncio.streams.StreamWriter()
    )
        
    assert len(server.users) == 1, 'userlist has been damadged after adding duplicate user'
    assert len(server.clients_online) == 1, ' online clients list has been damadged after adding duplicate user'

def test_connect(
        server,
        first_user,
        second_user,
        mocked_stream_writer,
        mocked_stream_reader
    ):

    _ = server.command_register(
        first_user.nickname,
        first_user.password,
        asyncio.streams.StreamReader(),
        asyncio.streams.StreamWriter()
    )

    with pytest.raises(WrongUsernameOrPasswordException):
        _ = server.command_connect(
        first_user.nickname,
        second_user.password,
        asyncio.streams.StreamReader(),
        asyncio.streams.StreamWriter()
    )

    with pytest.raises(WrongUsernameOrPasswordException):
        _ = server.command_connect(
            second_user.nickname,
            first_user.password,
            asyncio.streams.StreamReader(),
            asyncio.streams.StreamWriter()
        )

def test_command_message(
        server,
        first_user,
        mocked_stream_writer,
        mocked_stream_reader
):
    _ = server.command_register(
        first_user.nickname,
        first_user.password,
        asyncio.streams.StreamReader(),
        asyncio.streams.StreamWriter()
    )

    with pytest.raises(UserNotLoggedInException):
        server.command_message(
            None,
            'test_message1'
        )

    server.command_message(
        first_user,
        'test_message2'
    )

    assert len(server.messages) == 1, 'message was not added to server message list'
    assert server.messages[0].split()[-1] == 'test_message2', 'wrong message was added to server message list'

    first_user.is_banned = True

    with pytest.raises(UserIsBannedException):
        server.command_message(
            first_user,
            'test_message3'
        )

    assert len(server.messages) == 1, 'message from banned user was added to server message list'
