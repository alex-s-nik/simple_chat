from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    nickname: str
    password: str
    strikes: int = 0
    is_banned: bool = False
    ban_till: Optional[datetime] = None
