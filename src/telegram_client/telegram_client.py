import os
import random
import requests
import re
from dotenv import load_dotenv

from telegram.ext import CallbackContext, CallbackQueryHandler, Updater, CommandHandler, Filters, MessageHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from telegram.update import Update

from src.telebot import registered_operators
from src.shared_message_queue import shared_queue_client

conn_map = {}
conn_map_inv = {}


load_dotenv()

dont_die = True

def encode(s: int) -> str:
    return str(s) + "TEL"

def decode(s: str) -> int:
    return int(s[:-3])

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
    keyboard = [[InlineKeyboardButton('Greetings', callback_data='greetings')],
                [InlineKeyboardButton('Basic Information', callback_data='basic_info')]]
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
    r = requests.post(f"http://localhost:{os.getenv('PORT', 8080)}/api/v2t/chat", json={"sentence": update.message.text, 'first_name': update.effective_user.first_name, 'last_name': update.effective_user.last_name, 'sender_id': encode(update.effective_user.id)})
    print(r.json())
    update.message.reply_text(r.json()['text'])
    
def terminate() -> None:
    global dont_die
    dont_die = False

def main() -> None:
    updater = Updater(token=os.getenv("TELEGRAM_CLIENT_ACCESS_TOKEN"), use_context=True)
    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("menu", menu))
    updater.dispatcher.add_handler(CallbackQueryHandler(greetings, pattern="greetings"))
    updater.dispatcher.add_handler(CallbackQueryHandler(basic_info, pattern="basic_info"))

    updater.dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), chat))
    
    updater.start_polling()
    
    while dont_die:
        try:
            if not shared_queue_client.empty():
                message = shared_queue_client.get()
                is_shutdown = re.match(r"^SHUTDOWN$", message)
                if is_shutdown:
                    terminate()
                    break
        except KeyboardInterrupt:
            terminate()
            break
    
    print("Shutting down the client telegram bot...")
    updater.stop()
    
    print("Client telegram bot shut down.")
    exit(0)