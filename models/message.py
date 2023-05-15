from dataclasses import dataclass
from datetime import datetime

from models.user import User

@dataclass
class Message:
    id: int
    message: str
    chat_id: int = None
    author: User
    to_msg: 'Message' = None
    created_date: datetime
    date_to_send: datetime
