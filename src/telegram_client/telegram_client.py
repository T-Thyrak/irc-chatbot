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

prompts_en = [
    PromptGroup('Greetings', 'greetings_en', [
        "Hello",
        "Hi there",
        "How are you doing",
    ]),
    PromptGroup('Basic Info', 'basic_info_en', [
        "What is CADT?",
        "What is the purpose of CADT?",
        "What is the purpose of this chatbot?",
    ]),
]

prompts_km = [
    PromptGroup('សួស្តី', 'greetings_km', [
        "សួស្តី",
        "សួស្តីអ្នក",
    ]),
    PromptGroup('ព័ត៌មានមូលដ្ឋាន', 'basic_info_km', [
        "តើ CADT គឺជាអ្វី?",
        "តើគោលបំណងនៃ CADT គឺជាអ្វី?",
        "តើគោលបំណងនៃកម្មវិធីនេះគឺជាអ្វី?",
    ]),
]

load_dotenv()

dont_die = True

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("""Hi! I am an information and recommendation chatbot for CADT.
I can answer questions about the institute, its courses, and its facilities.
To get started, type `/menu` to see the list of intents that I can recognize.
Note: All messages are logged.

ជម្រាបសួរ! ខ្ញុំជាកម្មវិធីសន្ទនាដើម្បីផ្ដល់ព័ត៌មានផ្សេងៗ និងជំនួយប្រាប់ទិស របស់ CADT។
ខ្ញុំអាចឆ្លើយនូវសំណួរអំពីស្ថាប័ន វគ្គសិក្សា និងសេវាកម្មរបស់យើង។
ដើម្បីចាប់ផ្តើម សូមបញ្ចូល `/menu` ដើម្បីមើលបញ្ជីនៃសំណួរដែលខ្ញុំអាចស្គាល់។
ចំណាំ: សារទាំងអស់គឺត្រូវបានកត់ត្រាទុក។
""")
    
    
def menu(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(text=menu_message(), reply_markup=menu_keyboard())
    
def menu_message() -> str:
    return """Please select an intent from the list below. This will send a random prompt of the corresponding intent.
Remember, you can also just type your question in the chatbox too.

ចូរអ្នករើសយកប្រភេទសំណួរណាមួយពីក្នុងបញ្ជីខាងក្រោម។ វានឹងផ្ញើសំណួរមួយដែលត្រូវនឹងប្រភេទសំណួរនេះ។
ចំណាំ: អ្នកក៏អាចបញ្ចូលសំណួររបស់អ្នកនៅក្នុងប្រអប់សារបានផងដែរ។
"""

def menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [[InlineKeyboardButton("English", callback_data='menu_en')],
                [InlineKeyboardButton("Khmer", callback_data='menu_km')]]
    return InlineKeyboardMarkup(keyboard)

def menu_en_message():
    return """Please select an intent from the list below. This will send a random prompt of the corresponding intent."""

def menu_en_keyboard():
    keyboard = [[InlineKeyboardButton(prompt_group.name, callback_data=prompt_group.label)] for prompt_group in prompts_en]
    return InlineKeyboardMarkup(keyboard)
    
def menu_en(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    query.edit_message_text(text=menu_en_message(), reply_markup=menu_en_keyboard())

def menu_km_message():
    return """ចូរអ្នករើសយកប្រភេទសំណួរណាមួយពីក្នុងបញ្ជីខាងក្រោម។ វានឹងផ្ញើសំណួរមួយដែលត្រូវនឹងប្រភេទសំណួរនេះ។"""

def menu_km_keyboard():
    keyboard = [[InlineKeyboardButton(prompt_group.name, callback_data=prompt_group.label)] for prompt_group in prompts_km]
    return InlineKeyboardMarkup(keyboard)
def menu_km(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    query.edit_message_text(text=menu_km_message(), reply_markup=menu_km_keyboard())

def chat(update: Update, context: CallbackContext) -> None:
    forward_user = dual_map.get(encode(update.effective_user.id))
    if forward_user:
        context.bot.send_message(chat_id=decode(forward_user), text=update.message.text)
    
    if is_registered_operator(update.effective_user.id):
        return
    
    r = requests.post(f"http://localhost:{os.getenv('PORT', 8080)}/api/v2t/chat", json={"sentence": update.message.text, 'first_name': update.effective_user.first_name, 'last_name': update.effective_user.last_name, 'sender_id': encode(update.effective_user.id)})
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

បញ្ជីនៃពាក្យបញ្ជា:
/start - ចាប់ផ្ដើមការប្រើប្រាស់ bot
/menu - បង្ហាញបញ្ជីនៃប្រភេទសំណួរដែលខ្ញុំអាចស្គាល់
/help - បង្ហាញសារនេះ

អ្នកក៏អាចបញ្ចូលសំណួររបស់អ្នកនៅក្នុងប្រអប់សារបានផងដែរ។
ខ្ញុំនឹងព្យាយាមឆ្លើយតបឱ្យអស់នឹងសមត្ថភាព។
ឧទាហរណ៍: តើអ្នកអាចធ្វើអ្វីបាន?
ចម្លើយ: ខ្ញុំអាចឆ្លើយសំណួរអំពីវិទ្យាស្ថាន វគ្គសិក្សារបស់វានិងសេវាកម្មរបស់យើងបាន។
""")

def terminate() -> None:
    global dont_die
    dont_die = False    

def main() -> None:
    updater = Updater(token=os.getenv("TELEGRAM_CLIENT_ACCESS_TOKEN"), use_context=True)
    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("menu", menu))
    updater.dispatcher.add_handler(CommandHandler("help", help))
    
    updater.dispatcher.add_handler(CallbackQueryHandler(menu_en, pattern='^menu_en$'))
    updater.dispatcher.add_handler(CallbackQueryHandler(menu_km, pattern='^menu_km$'))
    
    for prompt_group in prompts_en:
        updater.dispatcher.add_handler(CallbackQueryHandler(dyn_func(prompt_group, updater), pattern=prompt_group.label))
    
    for prompt_group in prompts_km:
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
                if not is_valid:
                    continue
                
                if command == "ASSIGN":
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