import asyncio
from client2 import Client


if __name__ == '__main__':
    c = Client()
    asyncio.run(c.connect())