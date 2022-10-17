import os
import re
import requests
import expiringdict
import dill

from dotenv import load_dotenv
from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler

from src.helper import xor
from src.shared_message_queue import shared_queue

# def readline() -> str:
#     try:
#         return asyncio.run(asyncio.wait_for(aioconsole.ainput(), timeout=0.1))
#     except asyncio.TimeoutError:
#         return ''
    
if os.path.exists('misc/lockables.dill'):
    with open('misc/lockables.dill', 'rb') as f:
        lockables = dill.load(f)
else:
    lockables = expiringdict.ExpiringDict(max_len=int(os.getenv('MAX_LEN', 500)), max_age_seconds=60*60*24*7)

# flock = filelock.FileLock('misc/comfile.lock')

# load .env file
load_dotenv()

def send_message(message: str) -> None:
    updater.bot.send_message(chat_id=int(CHAT_ID), text=message)
    
def help(update: Update, context: CallbackContext) -> None:
    if update.effective_chat.id != int(CHAT_ID):
        return

    send_message(
"""
Supported commands:

/lock <sender_psid> - Locks the specified sender_psid
/unlock <sender_psid> - Unlocks the specified sender_psid
/help - Shows this message
"""
    )

def lock(update: Update, context: CallbackContext) -> None:
    if update.effective_chat.id != int(CHAT_ID):
        return
    
    if len(context.args) != 1:
        send_message('Usage: /lock <password>')
        return
    
    if lockables.get(context.args[0]) is None:
        send_message(f'Error: `{context.args[0]}` has never requested a human, so it cannot be locked.')
    
    PORT = os.getenv('PORT', 8080)
    url = f"http://localhost:{PORT}/api/v2/lock"
    body = {
        "sender_psid": context.args[0],
        "verify_token": xor(os.getenv('VERIFY_TOKEN'), os.getenv('HASH_NUT'))
    }
    
    response = requests.post(url, json=body).json()
    
    if 'error' in response:
        send_message(f'Error: {response["error"]}')
    else:
        send_message(f'`{context.args[0]}` locked successfully.')
        
def unlock(update: Update, context: CallbackContext) -> None:
    if update.effective_chat.id != int(CHAT_ID):
        return
    
    if len(context.args) != 1:
        send_message('Usage: /unlock <password>')
        return
    
    if lockables.get(context.args[0]) is None:
        send_message(f'Error: `{context.args[0]}` has never requested a human, so it cannot be unlocked.')
    
    PORT = os.getenv('PORT', 8080)
    url = f"http://localhost:{PORT}/api/v2/unlock"
    body = {
        "sender_psid": context.args[0],
        "verify_token": xor(os.getenv('VERIFY_TOKEN'), os.getenv('HASH_NUT'))
    }
    
    response = requests.post(url, json=body).json()
    
    if 'error' in response:
        send_message(f'Error: {response["error"]}')
    else:
        send_message(f'`{context.args[0]}` unlocked successfully.')

def handle_shutdown() -> None:
    print('Shutting down Telegram bots...')
    print('Saving lockables...')
    with open('misc/lockables.dill', 'wb') as f:
        dill.dump(lockables, f)
    
    print('Saving lockables to file...')
    print('Done.')
    
    print('Stopping updater...')
    updater.stop()
    
    print('Done.')
    print('Exiting...')
    exit(0)
        
def try_parse_command(com: str) -> tuple[str | None, str | None, bool, bool]:
    is_valid = re.match(r'^L(\d*)ID(\d*)MSG$', com)
    if not is_valid:
        is_shutdown = re.match(r'^SHUTDOWN$', com)
        if is_shutdown:
            return None, None, False, True
        return None, None, False, False
    
    line_count = re.search(r'L(\d*)ID(\d*)MSG', com).group(1)
    sender_id = re.search(r'L(\d*)ID(\d*)MSG', com).group(2)
    
    return line_count, sender_id, True, False

# startup bot
CHAT_ID = os.getenv('CHAT_ID')
updater = Updater(token=os.getenv('TELEGRAM_ACCESS_TOKEN'), use_context=True)
updater.dispatcher.add_handler(CommandHandler('help', help))
updater.dispatcher.add_handler(CommandHandler('lock', lock))
updater.dispatcher.add_handler(CommandHandler('unlock', unlock))

def init():
    print('Bot is running...')
    updater.start_polling()

dont_die = True

def terminate():
    global dont_die
    dont_die = False

def run():
    while dont_die:
        print('Waiting for command...')
        # requests.get(f"http://localhost:{os.getenv('PORT', 8080)}/api/v2/acknowledge")
        try:
            # requests.post(f'http://localhost:{os.getenv("PORT", 8080)}/api/v2/acknowledge', json={ "empty": shared_queue.empty() })
            if not shared_queue.empty():
                message = shared_queue.get()
                split_message = message.split("\n")
                _, sender_id, is_valid, is_shutdown = try_parse_command(split_message[0])
                if not is_valid:
                    if is_shutdown:
                        terminate()
                        break
                
                if lockables.get(sender_id) is None:
                    lockables[sender_id] = 1
                    
                send_message("\n".join(split_message[1:]))
                # requests.get(f"http://localhost:{os.getenv('PORT', 8080)}/api/v2/acknowledge")
            
        #     with flock.acquire(blocking=False):
        #         with open(f'misc/comfile', 'r+') as f:
        #             com = f.readline()
        #             if com == '':
        #                 continue
        #             elif com == '\n' or com == '\r\n':
        #                 f.seek(0)
        #                 src = f.readlines()
        #                 skiplines = 1
        #             else:
        #                 line_count, sender_id, is_valid, is_shutdown = try_parse_command(com)
        #                 if not is_valid:
        #                     if is_shutdown:
        #                         dont_die = False
        #                         break
                            
        #                     f.seek(0)
        #                     src = f.readlines()
        #                     skiplines = 1
        #                 else:
        #                     lockables[sender_id] = True
                                
        #                     strbuf = ''
        #                     for _ in range(int(line_count)):
        #                         strbuf += f.readline()
                            
        #                     send_message(strbuf)
                            
        #                     print("now writing")
        #                     f.seek(0)
        #                     src = f.readlines()
        #                     skiplines = 1 + int(line_count)
                        
        #         with open(f'misc/comfile_new', 'w+') as f:
        #             f.writelines(src[skiplines:])
                
        #         shutil.move('misc/comfile_new', 'misc/comfile')
        # except filelock.Timeout:
        #     sleep(0.1)
        #     continue
        except KeyboardInterrupt:
            handle_shutdown()
            
    handle_shutdown()
    
# handle_shutdown()
            
# shutdown
# print('Bot is shutting down...')