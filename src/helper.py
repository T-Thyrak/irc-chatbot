from hashlib import sha512
from multiprocessing import Queue
import secrets
import string
from time import sleep, time
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
        
        
def safe_compare(a: str, b: str, timeout: float = 1.5):
    start_time = time()
    has_failed = False
    
    if len(a) != len(b):
        has_failed = True
        
    for i in range(len(a)):
        if a[i] != b[i]:
            has_failed = True
            
    while time() - start_time < timeout:
        pass
    
    return not has_failed
    

def verify_hash(hash: str, token: str):
    return safe_compare(hash, sha512(xor(token, os.getenv('SECRET_KEY')).encode('utf-8')).hexdigest())


def shutdown_server():
    # generate a Ctrl+C event
    from win32.win32api import GenerateConsoleCtrlEvent
    
    GenerateConsoleCtrlEvent(0, 0)