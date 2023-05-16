import asyncio
import json
import heapq

from asyncio.streams import StreamReader, StreamWriter
from datetime import datetime, timedelta

from config import logger, NUMBER_OF_HISTORY_MESSAGES, TIME_TO_BAN
from models.client import Client
from models.user import User


class Server:
    """Chat server.
    Clients may be connected to the server on <host>:<port>.
    Client support next commands:
        /register <nick> <pass> - register on the server.
        /connect <nick> <pass> - connect to the chat.
        /msg <message> - send message <message> to the chat.
        /strike <nickname> - report a user with nickname <nickname>
        /quit - close the connetcion to the server and close client."""
    def __init__(self, host="127.0.0.1", port=8000):
        self.host: str = host
        self.port: int = port

        self.users: dict[str, User] = {}  # <nickname>: <user>
        self.users_online: set[User] = set()
        self.clients_online: list[Client] = []
        self.client_counter: dict[str, int] = {}  # <nickname>:<count> how much online clients of the user

        self.banned_users: list[tuple[datetime, User]] = []

        self.messages: list[str] = []
        self.n_last_messages: int = NUMBER_OF_HISTORY_MESSAGES

        try:
            asyncio.run(self.listen())
        except OSError as err:
            logger.fatal(err)

    async def listen(self):
        srv = await asyncio.start_server(
            self.client_connected,
            self.host,
            self.port
        )
        logger.info('Server started at %s:%s' % (self.host, self.port))
        async with srv:
            await srv.serve_forever()

    async def client_connected(
            self,
            reader: StreamReader,
            writer: StreamWriter
    ):
        address = writer.get_extra_info('peername')
        logger.info('Client connected from %s', address)
        curr_client = None
        user = None
        self.send_message(writer, 'Hello! Welcome to our chat-server. You can register or connect.')

        try:
            while data := await reader.readline():

                decoded_data = data.decode('utf-8').strip()
                logger.info(decoded_data)

                try:
                    decoded_data = json.loads(decoded_data)
                except json.decoder.JSONDecodeError:
                    self.send_message(writer, 'The using data transfer protocol is not supported.')

                command = decoded_data['command']
                args = decoded_data['args']

                if command == 'register' or command == 'connect':
                    try:
                        nick, password = args
                    except ValueError as e:
                        self.send_message(writer, f'{e}\nWrong command format.')
                        continue

                    if command == 'register':
                        if nick not in self.users:
                            user = User(
                                nickname=nick,
                                password=password
                            )
                            self.users[nick] = user
                            self.users_online.add(nick)
                            self.client_counter[nick] = self.client_counter.get(nick, 0) + 1
                            curr_client = Client(
                                user=user,
                                writer=writer,
                                reader=reader
                            )
                            self.clients_online.append(curr_client)
                            self.send_message(writer, f'Hello, {nick}! You are registered! Welcome!')
                            logger.info('%s has been registered.', nick)
                            # send N last messages
                            self.send_N_last_messages(writer)
                        else:
                            self.send_message(writer, 'This nickname is taken already.')
                            continue
                    elif command == 'connect':
                        if nick in self.users and self.users[nick].password == password:
                            user = self.users[nick]
                            self.users_online.add(nick)
                            self.client_counter[nick] = self.client_counter.get(nick, 0) + 1
                            curr_client = Client(
                                user=user,
                                writer=writer,
                                reader=reader
                            )
                            self.clients_online.append(curr_client)
                            self.send_message(writer, f'Hello, {nick}! You are logged in! Welcome!')
                            logger.info('%s has been logged in', nick)
                            # send N last messages
                            self.send_N_last_messages(writer)
                        else:
                            self.send_message(writer, 'Wrong nickname or password.')
                            continue
                elif command == 'message':
                    if not user:
                        self.send_message(writer, 'You are not logged in. Your message is not delivered.')
                        continue
                    if user.is_banned:
                        self.send_message(curr_client.writer, 'You are banned.')
                        continue
                    message = f'[{user.nickname} says] {args}'
                    for client in self.clients_online:
                        self.send_message(client.writer, message)
                    self.messages.append(message)
                    logger.info(message)
                elif command == 'strike':
                    if user and not user.is_banned:
                        striked_nickname = args
                        if striked_nickname not in self.users:
                            self.send_message(curr_client.writer, 'There is no such user.')
                            continue
                        if self.users[striked_nickname].is_banned:
                            self.send_message(curr_client.writer, 'User is already banned.')
                            continue
                        self.users[striked_nickname].strikes += 1
                        # ban actions
                        if self.users[striked_nickname].strikes >= 3:
                            # if there are no banned users
                            # then coro for unban or not started never or has already been executed
                            # that means the coro must be start again

                            need_to_start_unban = not bool(self.banned_users)
                            heapq.heappush(
                                self.banned_users,
                                (datetime.now() + timedelta(seconds=TIME_TO_BAN),
                                self.users[striked_nickname])
                            )
                            if need_to_start_unban:
                                asyncio.create_task(self.unban())

                            self.users[striked_nickname].is_banned = True
                else:
                    self.send_message(writer, 'Unknown command.')
                    continue
                await writer.drain()
        except ConnectionError:
            logger.info('Client from %s has been disconnected.', address)
            if curr_client:
                # remove current client from online clients
                self.clients_online.remove(curr_client)
                # decrease counter of the clients
                user = curr_client.user
                self.client_counter[user.nickname] = self.client_counter.get(user.nickname, 1) - 1
                # remove the user from users online
                if not self.client_counter[user.nickname]:
                    self.users_online.remove(user.nickname)
        writer.close()

    def send_message(self, writer: StreamWriter, message: str):
        writer.write(f'{message}\n'.encode('utf-8'))

    def send_N_last_messages(self, writer: StreamWriter):
        messages = '\n'.join(self.messages[-self.n_last_messages:])
        self.send_message(writer, messages)


    async def unban(self):
        """It using next idea for unban.
        If the user been banned he is placed to the heap. 
        On each step the app takes user with closer time to unban from heap
        and unban him."""
        while self.banned_users:
            banned_until, banned_user = heapq.heappop(self.banned_users)
            time_to_unban = banned_until - datetime.now()
            await asyncio.sleep(time_to_unban.total_seconds())
            banned_user.strikes = 0
            banned_user.is_banned = False
