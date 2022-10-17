from multiprocessing import Queue
import secrets
import string
from time import sleep
# from filelock import FileLock
import expiringdict

from nltk.stem.lancaster import LancasterStemmer

from src.wrappers import TTLDurations
stemmer = LancasterStemmer()

from src._context_handlers import *

context_handlers = {
    'course_recommendation': handle_course_recommendation,
    'request_human': handle_request_human,
}

token_storage_minute = expiringdict.ExpiringDict(max_len=1000, max_age_seconds=TTLDurations.MINUTE.value)
alphanumerics = string.ascii_uppercase + string.ascii_lowercase + string.digits
alpha_only = string.ascii_uppercase + string.ascii_lowercase

def handle_message(sender_psid: str, recv_message: dict):
    if recv_message.get('text'):
        message = recv_message['text']
        return message
    else:
        return None
    

def xor(msg: str, key: str):
    # get length of both message and key
    msg_len = len(msg)
    key_len = len(key)
    
    # if key is smaller than message, then
    # repeat key until it is the same length as message
    # if key is larger than message, then
    # cut key to the same length as message
    if key_len < msg_len:
        key = key * (msg_len // key_len + 1)
    
    key = key[:msg_len]
    
    # xor each character of message with key
    # and return the result
    return ''.join(chr(ord(msg[i]) ^ ord(key[i])) for i in range(msg_len))

class QueueFiller:
    def __init__(self, queue: Queue):
        self.queue = queue
        
    def fill(self, msg: str):
        self.queue.put(msg)

class QueueSender:
    def __init__(self):
        self.terminate = False
        
    # def run(self, queue: Queue, lock: FileLock):
    #     while not self.terminate:
    #         if queue.empty():
    #             continue
    #         else:
    #             with lock:
    #                 with open('misc/comfile', 'a') as f:
    #                     f.write(queue.get() + '\n')
            
    #         sleep(0.01)
    
    def terminate(self):
        self.terminate = True
        

def generate_token(ttl: TTLDurations):
    if ttl == TTLDurations.MINUTE:
        token = secrets.token_hex(32)
        token_storage_minute[token] = True
        return token
    
def generate_name():
    return secrets.choice(alpha_only) + ''.join(secrets.choice(alphanumerics) for _ in range(15))
