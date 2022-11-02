import os
import dill

from multiprocessing import Queue


shared_queue = Queue()
shared_queue_client = Queue()

if os.path.exists('misc/registered_operators.dill'):
    with open('misc/registered_operators.dill', 'rb') as f:
        registered_operators = dill.load(f)
else:
    registered_operators = []
    with open('misc/registered_operators.dill', 'wb') as f:
        dill.dump(registered_operators, f)

def put_message(message: str) -> None:
    shared_queue.put(message)
    print(f'Put message: {message}')
    
def put_message_client(message: str) -> None:
    shared_queue_client.put(message)
    print(f'Put message: {message}')
    
def is_registered_operator(operator_id: int) -> bool:
    print(registered_operators)
    print(operator_id)
    return str(operator_id) in registered_operators