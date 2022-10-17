import enum
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

class ExpiringDict(expiringdict.ExpiringDict):
    def __init__(self, max_len: int, max_age_seconds: int, items=None, *args, **kwargs):
        super().__init__(max_len=max_len, max_age_seconds=max_age_seconds, items=items, *args, **kwargs)
    
    def __delitem__(self, key):
        super().__delitem__(key)
        UserIterations.rem(key)
        

class TTLDurations(enum.Enum):
    MINUTE = 60
