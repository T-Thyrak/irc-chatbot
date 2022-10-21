from src.wrappers import UserIterations

import pickle
import os
import requests

from keras.models import load_model
from src.classify import classify
from src.tasks import notifyTelegram

with open('misc/yesno/words.pkl', 'rb') as f:
    words = pickle.load(f)
with open('misc/yesno/classes.pkl', 'rb') as f:
    classes = pickle.load(f)
    
load_path = os.path.join('models', 'yesno')
yesno_model = load_model(load_path)

def handle_course_recommendation(sender_psid: str, sentence: str, access_token: str) -> tuple[str, bool]:
    # some codes
    
    if UserIterations.get(sender_psid) is None:
        UserIterations.inc(sender_psid)

        result = classify(yesno_model, sentence=sentence, words=words, classes=classes, threshold=0.5)
        if result == [] or result[0][0] == 'answer.maybe' or result[0][0] == 'answer.no':
            return "Alright. I will respect your choice.", True
        else:
            return "Alright. Let's start with the first question. On the scale of 1-5, how much do you like coding?", False
    else:
        UserIterations.rem(sender_psid)
        
    return "Alright, take this with a truckload of salt, but I recommend: <A course>", True

def handle_request_human(sender_psid: str, sentence: str, access_token: str) -> tuple[str, bool]:
    if UserIterations.get(sender_psid) is None:
        UserIterations.inc(sender_psid)
        
        result = classify(yesno_model, sentence=sentence, words=words, classes=classes, threshold=0.5)
        UserIterations.rem(sender_psid)
        if result == [] or result[0][0] == 'answer.maybe' or result[0][0] == 'answer.no':
            return "I see, I will respect your choice. :)", True
        else:
            r = requests.get(f"https://graph.facebook.com/v2.6/{sender_psid}?access_token={access_token}")
            data = r.json()
            print(data)
            notifyTelegram(f"L3ID{sender_psid}MSG\nA person named {data['first_name']} {data['last_name']} with the ID {sender_psid} has requested for a human to contact them on Messenger.\n\nPlease respond back to them ASAP.")
            return "Alright, I will connect you to a human agent. You can still talk to me in the meanwhile. :)", True

        
    return "", True