from multiprocessing import Queue

shared_queue = Queue()

def put_message(message: str) -> None:
    shared_queue.put(message)
    print(f'Put message: {message}')