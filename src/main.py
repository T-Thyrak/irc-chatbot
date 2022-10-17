from multiprocessing.dummy import Process
from src.server import app
from src.telebot import init, terminate, run
from src.server import graceful_shutdown

import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    server_process = Process(target=app.run, kwargs={'port': int(os.getenv('PORT', 8080)), })
    telegram_process = Process(target=run)
    
    try:
        init()
        server_process.start()
        telegram_process.start()
    except KeyboardInterrupt:
        pass
    
    while True:
        try:
            if not server_process.is_alive() or not telegram_process.is_alive():
                break
        except KeyboardInterrupt:
            break
    
    print("before terminate")
    terminate()
    print("after terminate")
    print("before graceful_shutdown")
    graceful_shutdown()
    print("after graceful_shutdown")
    
    while telegram_process.is_alive():
        pass
    
    os._exit(0)
    