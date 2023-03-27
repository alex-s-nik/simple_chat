import asyncio

from asyncio.streams import StreamReader, StreamWriter

from config import logger


class Server:
    def __init__(self, host="127.0.0.1", port=8000):
        self.host = host
        self.port = port

        self.messages = []
        self.clients_online = set()

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

    async def send_to_clients(self, msg: str, from_client_name: str):
        for client in self.clients_online:
            if client == from_client_name:
                continue
            client[1].write(msg.encode('utf-8'))
            await client[1].drain()

    async def client_connected(
            self, reader: StreamReader,
            writer: StreamWriter
        ):
        address = writer.get_extra_info('peername')
        logger.info('Start serving %s', address)
        current_client = (address, writer, reader)
        self.clients_online.add(current_client)
        # send last N messages
        N = 4
        writer.write(('\n'.join(self.messages[-N:]).encode('utf-8')))
        await writer.drain()

        while True:
            data = await reader.read(1024)
            if not data:
                break
            message = f'{address} says: ' + data.decode('utf-8').strip()
            logger.info(message)
            self.messages.append(message)
            await self.send_to_clients(message, current_client)

        logger.info('Stop serving %s', address)
        self.clients_online.remove(current_client)
        writer.close()
