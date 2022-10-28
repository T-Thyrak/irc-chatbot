from src.mysqlquery import create_connection, destroy_connection, end_commit, execute_query, start_commit
from src.wrappers import UserIterations

import pickle
import os
import requests
import logging

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
        
        r = requests.get(f"https://graph.facebook.com/v2.6/{sender_psid}?access_token={access_token}")
        data = r.json()
        print(data)
        notifyTelegram(f"L3ID{sender_psid}MSG\nA person named {data['first_name']} {data['last_name']} with the ID {sender_psid} has requested for a human to contact them on Messenger.\n\nPlease respond back to them ASAP.")
        return "Alright, I will connect you to a human agent. You can still talk to me in the meanwhile. :)", True

        
    return "", True

def handle_send_feedback(sender_psid: str, sentence: str, access_token: str) -> tuple[str, bool]:
    if not hasattr(handle_send_feedback, 'feedback_type'):
        handle_send_feedback.feedback_type = None
        
    print(UserIterations.get(sender_psid))
    
    if UserIterations.get(sender_psid) is None:
        logging.info("Should be hit, 1st time")
        
        UserIterations.inc(sender_psid)
        
        result = classify(yesno_model, sentence=sentence, words=words, classes=classes, threshold=0.5)
        if result == [] or result[0][0] == 'answer.maybe' or result[0][0] == 'answer.no':
            return "I see, I will respect your choice. :)", True
        
        return "Alright, what type of feedback do you want to send? (Please use the number)\n\n1. Bug Report\n2. Improvement", False

    if UserIterations.get(sender_psid) == 0:
        logging.info("Should be hit, 2nd time")
        UserIterations.inc(sender_psid)
        
        if sentence == '1':
            handle_send_feedback.feedback_type = 'Bug'
            return "Alright, please describe the bug you found.", False
        elif sentence == '2':
            handle_send_feedback.feedback_type = 'Improvement'
            return "Alright, please describe the improvement you want to suggest.", False
        else:
            UserIterations.rem(sender_psid)
            return "I'm sorry, that is not a valid type of feedback. Please retype it again.", False
    
    if UserIterations.get(sender_psid) == 1:
        logging.info("Should be hit, 3rd time")
        UserIterations.inc(sender_psid)
        
        r = requests.get(f"https://graph.facebook.com/v2.6/{sender_psid}?access_token={access_token}")
        data = r.json()
        
        sql = "INSERT INTO `feedbacks` (`sender_id`, `name`, `feedback_type`, `feedback`) VALUES (%s, %s, %s, %s)"
        val = (sender_psid, f"{data['first_name']} {data['last_name']}", handle_send_feedback.feedback_type, sentence)
        
        db_conn = create_connection()
        if db_conn is None:
            return "I'm sorry, I am unable to connect to the database. Please try again later.", True
        
        start_commit(db_conn)
        print("start commit")
        print(f"executing query: {sql % val} ")
        execute_query(query=sql, values=val, db_conn=db_conn)
        print("executed query")
        end_commit(db_conn=db_conn)
        print("end commit")
        destroy_connection(db_conn)
        print("destroyed connection")
    
        return "Thank you so much for your feedback! :)", True
    
    if UserIterations.get(sender_psid) == 2:
        logging.info("Should be hit, 4th time")
        UserIterations.rem(sender_psid)
        return "Thank you so much for your feedback! :)", True
    
    logging.info("Should be unreachable")
    return "", True
    