from multiprocessing.dummy import Process
from src.server import app
from src.telebot.telebot import init, terminate, run
from src.server import graceful_shutdown
from src.telegram_client.telegram_client import main as client_main, terminate as client_terminate

import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    server_process = Process(target=app.run, kwargs={'port': int(os.getenv('PORT', 8080)), })
    telegram_process = Process(target=run)
    client_telegram_process = Process(target=client_main)
    
    try:
        init()
        server_process.start()
        telegram_process.start()
        client_telegram_process.start()
    except KeyboardInterrupt:
        pass
    
    while True:
        try:
            if telegram_process.is_alive() or client_telegram_process.is_alive():
                pass
        except KeyboardInterrupt:
            break
    
    print("before terminate")
    terminate()
    print("after terminate")
    print("before graceful_shutdown")
    graceful_shutdown()
    print("after graceful_shutdown")
    print("before client_terminate")
    client_terminate()
    print("after client_terminate")
    
    while telegram_process.is_alive() or client_telegram_process.is_alive():
        pass
    
    os._exit(0)
    