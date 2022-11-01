from multiprocessing import Queue

shared_queue = Queue()
shared_queue_client = Queue()

def put_message(message: str) -> None:
    shared_queue.put(message)
    print(f'Put message: {message}')
    
def put_message_client(message: str) -> None:
    shared_queue_client.put(message)
    print(f'Put message: {message}')