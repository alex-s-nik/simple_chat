import aiohttp
import asyncio

from config import logger


class Client:
    def __init__(self, server_host="127.0.0.1", server_port=8000):
        self.url = f'http://{server_host}:{server_port}'
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.main())

    def send(self, message=""):
        pass

    async def main(self):

        async with aiohttp.ClientSession() as session:
            while True:
                action = input().split()
                if action:
                    command = action[0]
                else:
                    command = ''
                action_args = action[1:]

                if command == '/quit':
                    break

                elif command == '/register':
                    pass

                elif command == '/connect':
                    pass

                elif command == '/status':
                    pass

                elif command == 'msg':
                    pass

                elif command == '/strike':
                    pass
                    
                else:
                    logger.error('%s is not supported.', command)
                    continue

                async with session.post(self.url, data={'message': 'hey!'}) as response:

                    print("Status:", response.status)
                    print("Content-type:", response.headers['content-type'])

                    html = response.text
                    print("Body:", html)

                    
