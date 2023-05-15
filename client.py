import asyncio
import json

import aioconsole

from config import logger


class Client:
    def __init__(self, server_host="127.0.0.1", server_port=8000):
        self.server_host = server_host
        self.server_port = server_port
        self.url = f'http://{server_host}:{server_port}'
        asyncio.run(self.connect())

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(
            self.server_host,
            self.server_port
        )
        await asyncio.gather(
            self.send_messages(),
            self.get_messages()
        )

    def send(self, message=""):
        self.writer.write(message.encode())

    def quit(self):
        asyncio.get_event_loop().stop()

    async def get_messages(self):
        while True:
            data = await self.reader.read(1024)
            logger.info(data.decode('utf-8'))

    async def send_messages(self):
        while True:

            action = await aioconsole.ainput()
            action = action.split()

            if len(action) == 1:
                command = action[0]
                action_args = None
            elif len(action) > 1:
                command = action[0]
                action_args = action[1:]
            else:
                logger.info('Wrong command format: empty command')
                continue

            if command == '/quit':
                self.quit()

            elif command == '/register':
                if len(action_args) != 2:
                    logger.info(action_args)
                    logger.error(
                        'Register command needs exactly two args, nickname and password'
                    )
                    continue
                payload = {
                    'command': 'register',
                    'args': action_args
                }

            elif command == '/connect':
                if len(action_args) != 2:
                    logger.error(
                        'Connect command needs exactly two args, nickname and password'
                    )
                    continue
                payload = {
                    'command': 'connect',
                    'args': action_args
                }

            elif command == '/msg':
                if not action_args:
                    logger.error('Empty message is not supported')
                    continue
                payload = {
                    'command': 'message',
                    'args': ' '.join(action_args)
                }

            elif command == '/strike':
                if not action_args:
                    logger.error('Strike command must have nickname')
                    continue
                payload = {
                    'command': 'strike',
                    'args': action_args[0]
                }

            else:
                logger.error('%s is not supported.', command)
                continue
            self.send(json.dumps(payload))
            await self.writer.drain()
