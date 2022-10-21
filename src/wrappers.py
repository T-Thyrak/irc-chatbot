from __future__ import annotations

import enum
from typing import Any, Callable, Generic, OrderedDict, TypeVar
import expiringdict

class UserIterations:
    __iteration_dict = {}
    
    @staticmethod
    def iteration_dict():
        return UserIterations.__iteration_dict

    @staticmethod
    def get(user_id: str):
        return UserIterations.__iteration_dict.get(user_id)
    
    @staticmethod
    def inc(user_id: str):
        if user_id in UserIterations.__iteration_dict:
            UserIterations.__iteration_dict[user_id] += 1
        else:
            UserIterations.__iteration_dict[user_id] = 0
        
        return UserIterations.__iteration_dict[user_id]
            
    @staticmethod
    def rem(user_id: str):
        if user_id in UserIterations.__iteration_dict:
            UserIterations.__iteration_dict.pop(user_id)

K = TypeVar('K')
V = TypeVar('V')

class ExpiringDict(expiringdict.ExpiringDict, Generic[K, V]):
    def __init__(self, max_len: int, max_age_seconds: int, items: dict[K, V] | OrderedDict[K, V] | Any | ExpiringDict | None = None, callback: Callable[[K, V], None]=None, *args, **kwargs):
        super().__init__(max_len=max_len, max_age_seconds=max_age_seconds, items=items, *args, **kwargs)
        self.callback = callback
    
    def __delitem__(self, key):
        val = self[key]
        super().__delitem__(key)
        if self.callback:
            self.callback(key, val)
        

class TTLDurations(enum.Enum):
    MINUTE = 60


class Action(enum.Enum):
    IRC_LOCK = 0
    IRC_UNLOCK = 1