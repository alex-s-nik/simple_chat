from asyncio.streams import StreamReader, StreamWriter
from dataclasses import dataclass

from models.user import User


@dataclass
class Client:
    user: User
    writer: StreamWriter
    reader: StreamReader
