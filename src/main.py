#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

from rich.traceback import install
install(show_locals=True)


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
    