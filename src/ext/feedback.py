from __future__ import annotations

from dataclasses import dataclass
import datetime

@dataclass
class Feedback:
    id: int
    sender_psid: str
    name: str
    type: str
    message: str
    status: str
    created_at: datetime.datetime
    
    @staticmethod
    def from_tuple(tuple: tuple) -> Feedback:
        return Feedback(tuple[0], tuple[1], tuple[2], tuple[3], tuple[4], tuple[5], tuple[6])
    
    def to_tuple(self) -> tuple:
        return (self.id, self.sender_psid, self.name, self.type, self.message, self.status, self.created_at)