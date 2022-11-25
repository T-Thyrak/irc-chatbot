import os
import random
import requests

from telegram import Update
from telegram.ext import CallbackContext, Updater
from typing import Callable

from src.ext.prompt_group import PromptGroup
from src.helper import encode

def dyn_func(prompt_group: PromptGroup, updater: Updater) -> Callable[[Update, CallbackContext], None]:
    def func(update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        query.answer()
        
        query.edit_message_text(text=f"Sending message/កំពុងផ្ញើសារ...")
        
        choices = prompt_group.prompts
        sentence = random.choice(choices)
        
        r = requests.post(f"http://localhost:{os.getenv('PORT', 8080)}/api/v2t/chat", json={"sentence": sentence, 'first_name': update.effective_user.first_name, 'last_name': update.effective_user.last_name, 'sender_id': encode(update.effective_user.id)})
    
        query.edit_message_text(
            text=f"Equivalent prompt: `{sentence}`"
        )
        
        updater.bot.send_message(chat_id=update.effective_user.id, text=r.json()['text'])
        
    return func