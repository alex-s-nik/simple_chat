from asyncio.streams import StreamReader, StreamWriter
from typing import Any

class Client:
    def __init__(
            self,
            nickname: str,
            address: Any,
            writer: StreamWriter,
            reader: StreamReader
        ):
        self.nickname = nickname
        self.address = address
        self.writer = writer
        self.reader = reader
    