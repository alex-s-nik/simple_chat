import asyncio
from client import Client


if __name__ == '__main__':
    c = Client()
    asyncio.run(c.connect())