from src.shared_message_queue import put_message

def notifyTelegram(message):
    put_message(message)