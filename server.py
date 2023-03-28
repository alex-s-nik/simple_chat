import asyncio

from asyncio.streams import StreamReader, StreamWriter
from typing import Union

from config import logger
from models.client import Client


class Server:
    def __init__(self, host="127.0.0.1", port=8000):
        self.host = host
        self.port = port

        self.messages = []
        # change to dict ?
        self.clients_online: set[Client] = set()

        self.users = (
            'nick1',
            'nick2',
            'nick3',
        )

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

    async def send_message(self, client: Union[Client, StreamWriter], message: str, end='\n'):
        stream_writer = client
        if isinstance(client, Client):
            stream_writer = client.writer
        stream_writer.write(f'{message}{end}'.encode('utf-8'))
        await stream_writer.drain()

    async def send_to_clients(self, message: str, from_client: Client):
        for client in self.clients_online:
            if client == from_client:
                continue
            await self.send_message(client, message)

    async def ask_for_nickname(
        self,
        client_reader: StreamReader,
        client_writer: StreamWriter
    ) -> str:
        await self.send_message(client_writer, 'Tell us what is your nick >>> ', end='')

        while True:
            client_nick = (await client_reader.read(1024)).decode('utf-8').strip()
            if client_nick in self.users:
                break
            logger.warning('Try to enter as %s', client_nick)
            await self.send_message(client_writer, 'There is no such user. Try again >>>', end='')

        await self.send_message(client_writer, f'Hello, {client_nick}! Lets start to chat!')

        return client_nick
    
    async def send_last_N_messages(self, n: int, to_client: Client):
        # if message wrote by curr_client prefix must be 'I say' instead 'Says'
        if not self.messages:
            message = 'There is no message history'
        else:
            message = '\n'.join(self.messages[-n:])

        await self.send_message(to_client, message)

    async def serve_client(self, client: Client):
        while True:
            data = await client.reader.read(1024)
            if not data:
                break
            message = data.decode('utf-8').strip()
            prepared_message = f'{client.nickname} says: {message}'
            self.messages.append(message)
            logger.info(prepared_message)
            await self.send_to_clients(message=prepared_message, from_client=client)

    async def client_connected(
            self, reader: StreamReader,
            writer: StreamWriter
        ):
        address = writer.get_extra_info('peername')
        logger.info('Client connected from %s', address)

        nickname = await self.ask_for_nickname(reader, writer)

        current_client = Client(nickname, address, writer, reader)
        self.clients_online.add(current_client)

        await self.send_last_N_messages(4, current_client)

        await self.serve_client(current_client)

        logger.info('Client from %s has been disconnected', address)
        self.clients_online.remove(current_client)
        writer.close()
