from src.shared_message_queue import put_message, put_message_client

def notifyTelegram(message):
    put_message(message)
    
def notifyTelegramClient(message):
    put_message_client(message)