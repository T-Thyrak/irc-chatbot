import os
import random
import requests
import re

from dotenv import load_dotenv
from expiringdict import ExpiringDict

from telegram.ext import CallbackContext, CallbackQueryHandler, Updater, CommandHandler, Filters, MessageHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from telegram.update import Update

from src.helper import encode, decode
from src.shared_message_queue import shared_queue_client, is_registered_operator
from src.ext.dual_map import DualMap
from src.ext.prompt_group import PromptGroup
from src.telegram_client.dyn_func import dyn_func

MAX_LEN = int(os.getenv("MAX_LEN", 500))
op_to_user_map = ExpiringDict(max_len=MAX_LEN, max_age_seconds=60*30)
user_to_op_map = ExpiringDict(max_len=MAX_LEN, max_age_seconds=60*30)

dual_map = DualMap()

prompts = [
    PromptGroup('Greetings', 'greetings', [
        "Hello",
        "Hi there",
        "How are you doing",
    ]),
    PromptGroup('Basic Info', 'basic_info', [
        "What is CADT?",
        "What is the purpose of CADT?",
        "What is the purpose of this chatbot?",
    ]),
]

load_dotenv()

dont_die = True

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("""Hi! I am an information and recommendation chatbot for CADT.
I can answer questions about the institute, its courses, and its facilities.
To get started, type `/menu` to see the list of intents that I can recognize.
""")
    
    
def menu(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(text=menu_message(), reply_markup=menu_keyboard())
    
def menu_message() -> str:
    return "Please select an intent from the list below. This will send a random prompt of the corresponding intent.\nRemember, you can also just type your question in the chatbox too."

def menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [[InlineKeyboardButton(prompt_group.name, callback_data=prompt_group.label)] for prompt_group in prompts]
    return InlineKeyboardMarkup(keyboard)

def greetings(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    random_greetings = ["Hi", "Hello", "Hey", "Hi there", "Hello there", "Hey there"]
    sent = random.choice(random_greetings)
    r = requests.post(f"http://localhost:{os.getenv('PORT')}/api/v2t/chat", json={"sentence": sent, 'first_name': update.effective_user.first_name, 'last_name': update.effective_user.last_name, 'sender_id': encode(update.effective_user.id)})

    query.edit_message_text(
        text=f"Prompt: `{sent}`\n\n" + r.json()['text']
    )
    
def basic_info(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    random_basic_info = ["What is CADT?", "What are the courses offered?", "What are the facilities offered?", "What is the address of CADT?", "What is the contact number of CADT?"]
    sent = random.choice(random_basic_info)
    r = requests.post(f"http://localhost:{os.getenv('PORT', 8080)}/api/v2t/chat", json={"sentence": sent, 'first_name': update.effective_user.first_name, 'last_name': update.effective_user.last_name, 'sender_id': encode(update.effective_user.id)})

    query.edit_message_text(
        text=f"Prompt: `{sent}`\n" + r.json()['text']
    )
    
def chat(update: Update, context: CallbackContext) -> None:
    forward_user = dual_map.get(encode(update.effective_user.id))
    if forward_user:
        context.bot.send_message(chat_id=decode(forward_user), text=update.message.text)
    
    if is_registered_operator(update.effective_user.id):
        return
    
    r = requests.post(f"http://localhost:{os.getenv('PORT', 8080)}/api/v2t/chat", json={"sentence": update.message.text, 'first_name': update.effective_user.first_name, 'last_name': update.effective_user.last_name, 'sender_id': encode(update.effective_user.id)})
    print(r.json())
    if r.json().get('error') == 'locked':
        return

    update.message.reply_text(r.json()['text'])
    
def help(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("""List of commands:
/start - Start the bot
/menu - Show the list of intents I support
/help - Show this message

You can also just type your question in the chatbox too.
I will try to answer it as best as I can.
Example: What can you do?
Answer: I can answer questions about the institute, its courses, and its facilities.
""")

def terminate() -> None:
    global dont_die
    dont_die = False

def main() -> None:
    updater = Updater(token=os.getenv("TELEGRAM_CLIENT_ACCESS_TOKEN"), use_context=True)
    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("menu", menu))
    updater.dispatcher.add_handler(CommandHandler("help", help))
    # updater.dispatcher.add_handler(CallbackQueryHandler(greetings, pattern="greetings"))
    # updater.dispatcher.add_handler(CallbackQueryHandler(basic_info, pattern="basic_info"))
    
    for prompt_group in prompts:
        updater.dispatcher.add_handler(CallbackQueryHandler(dyn_func(prompt_group, updater), pattern=prompt_group.label))
    
    updater.dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), chat))
    
    updater.dispatcher.bot.set_my_commands([
        ("help", "Show the list of commands"),
        ("menu", "Show the list of intents"),
        ("start", "Start the bot"),
    ])
    
    updater.start_polling()
    
    while dont_die:
        try:
            if not shared_queue_client.empty():
                message = shared_queue_client.get()
                is_shutdown = re.match(r"^SHUTDOWN$", message)
                if is_shutdown:
                    terminate()
                    break
                
                is_valid, command, user_id, operator_id = parse_message(message)
                print(is_valid, command, user_id, operator_id)
                if not is_valid:
                    continue
                
                if command == "ASSIGN":
                    print(f"Assigning {user_id} to {operator_id}")
                    assign_op_to_user(user_id, operator_id)
                elif command == "UNASSIGN":
                    unassign_op_to_user(user_id)
                
        except KeyboardInterrupt:
            terminate()
            break
    
    print("Shutting down the client telegram bot...")
    updater.stop()
    
    print("Client telegram bot shut down.")
    exit(0)

def parse_message(message: str) -> tuple[bool, str, str, str]:
    is_valid = re.match(r"^((?:|UN)ASSIGN)\?USER=((?:(?:|-)\d+)TEL)&OPERATOR=((?:(?:|-)\d+)TEL)$", message)
    
    if not is_valid:
        return False, None, None, None
    
    command = is_valid.group(1)
    user_id = is_valid.group(2)
    operator = is_valid.group(3)
    
    print(command, user_id, operator)
    
    return True, command, user_id, operator


def assign_op_to_user(user_id: str, operator_id: str) -> None:
    op_to_user_map[operator_id] = user_id
    user_to_op_map[user_id] = operator_id
    dual_map[user_id] = operator_id
    
def unassign_op_to_user(user_id: str) -> None:
    operator_id = user_to_op_map[user_id]
    del op_to_user_map[operator_id]
    del user_to_op_map[user_id]
    del dual_map[user_id]