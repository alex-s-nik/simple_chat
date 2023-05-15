import asyncio
import json

from asyncio.streams import StreamReader, StreamWriter
from config import logger

from models.client import Client
from models.user import User

class Server:
    def __init__(self, host="127.0.0.1", port=8000):
        self.host = host
        self.port = port

        self.users = {}
        self.users_online = set()
        self.clients_online = []
        self.client_counter = {}

        self.messages = []


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
        writer.write('Hello! Welcome to our chat-server. You can register or connect.'.encode('utf-8'))

        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    break
                decoded_data = data.decode('utf-8')
                logger.info(decoded_data)
                decoded_data = json.loads(decoded_data)

                command = decoded_data['command']
                args = decoded_data['args']

                if command == 'register' or command == 'connect':
                    try:
                        nick, password = args
                    except Exception as e:
                        writer.write(f'{e}\nWrong command format'.encode('utf-8'))
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
                            writer.write(f'Hello, {nick}! You are registered! Welcome!'.encode('utf-8'))
                            logger.info(f'Hello, {nick}! You are registered! Welcome!')
                            # send N last messages
                        else:
                            writer.write('This nickname is taken already'.encode('utf-8'))
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
                            writer.write(f'Hello, {nick}! You are logged in! Welcome!'.encode('utf-8'))
                            logger.info(f'Hello, {nick}! You are logged in! Welcome!')
                            # send N last messages
                        else:
                            writer.write('Wrong nickname or password'.encode('utf-8'))
                            continue
                elif command == 'message':
                    if user and not user.is_banned:
                        message = f'[{user.nickname} says] {args}'
                        for client in self.clients_online:
                            #if client != curr_client:
                            client.writer.write(message.encode('utf-8'))
                        self.messages.append(message)
                        logger.info(message)
                elif command == 'strike':
                    if user and not user.is_banned:
                        striked_nickname = args
                        if striked_nickname not in self.users:
                            curr_client.writer.write('There is no such user'.encode('utf-8'))
                            continue
                        if self.users[striked_nickname].is_banned:
                            curr_client.writer.write('User is already banned'.encode('utf-8'))
                            continue
                        self.users[striked_nickname].strikes += 1
                        if self.users[striked_nickname].strikes >= 3:
                            self.users[striked_nickname].strikes = 0
                            self.users[striked_nickname].is_banned = True
                else:
                    writer.write('Unknown command'.encode('utf-8'))
                    continue
                await writer.drain()
        except ConnectionError:
            logger.info('Client from %s has been disconnected', address)
            if curr_client:
                # remove from online clients
                self.clients_online.remove(curr_client)
                # decrease counter of clients
                user = curr_client.user
                self.client_counter[user.nickname] = self.client_counter.get(user.nickname, 1) - 1
                # remove from users online
                if not self.client_counter[user.nickname]:
                    self.users_online.remove(user.nickname)
                
        writer.close()
