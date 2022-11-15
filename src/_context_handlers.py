from src.mysqlquery import create_connection, destroy_connection, end_commit, execute_query, start_commit
from src.wrappers import UserIterations

import pickle
import os
import requests
import logging
import json

from keras.models import load_model
from src.classify import classify
from src.tasks import notifyTelegram

with open('misc/yesno/words.pkl', 'rb') as f:
    words = pickle.load(f)
with open('misc/yesno/classes.pkl', 'rb') as f:
    classes = pickle.load(f)
    
load_path = os.path.join('models', 'yesno')
yesno_model = load_model(load_path)

with open('misc/survey_data/rules.json', 'r') as f:
    rules = json.load(f)
    
scores = {}

def handle_course_recommendation(sender_psid: str, sentence: str, access_token: str | None=None, telegram: bool=False, telegram_data: dict | None=None) -> tuple[str, bool]:
    # some codes
    
    def add_score(input_score: dict, option: int, section: str):
        print(input_score['cs'], input_score['tn'], input_score['ec'])
        input_score['cs'] = input_score['cs'] + rules['data_cs'][section][str(option)]
        input_score['tn'] = input_score['tn'] + rules['data_tn'][section][str(option)]
        input_score['ec'] = input_score['ec'] + rules['data_ec'][section][str(option)]
        print(input_score)
        
        # return input_score
    
    if UserIterations.get(sender_psid) is None:
        UserIterations.inc(sender_psid)

        result = classify(yesno_model, sentence=sentence, words=words, classes=classes, threshold=0.5)
        if result == [] or result[0][0] == 'answer.maybe' or result[0][0] == 'answer.no':
            return "Alright. I will respect your choice.", True
        else:
            scores[sender_psid] = {'cs': 0, 'tn': 0, 'ec': 0}
            return "Alright. Let's start with the first question. On the scale of 1-5, how much do you like coding?", False
    else:
        if UserIterations.get(sender_psid) == 0:
            if sentence.isdigit() and int(sentence) >= 1 and int(sentence) <= 5:
                UserIterations.inc(sender_psid)
                add_score(scores[sender_psid], int(sentence), '~coding')
                return "On the scale of 1-5, how much do you like marketing?", False
            else:
                return "Please enter a number between 1 and 5.", False
        elif UserIterations.get(sender_psid) == 1:
            if sentence.isdigit() and int(sentence) >= 1 and int(sentence) <= 5:
                UserIterations.inc(sender_psid)
                add_score(scores[sender_psid], int(sentence), '~marketing')
                return "On the scale of 1-5, how much do you like networking (BGP, managing routers, ...)?", False
            else:
                return "Please enter a number between 1 and 5.", False
        elif UserIterations.get(sender_psid) == 2:
            if sentence.isdigit() and int(sentence) >= 1 and int(sentence) <= 5:
                UserIterations.inc(sender_psid)
                add_score(scores[sender_psid], int(sentence), '~networking')
                return "On the scale of 1-5, how much do you like solving problems?", False
            else:
                return "Please enter a number between 1 and 5.", False
        elif UserIterations.get(sender_psid) == 3:
            if sentence.isdigit() and int(sentence) >= 1 and int(sentence) <= 5:
                UserIterations.inc(sender_psid)
                add_score(scores[sender_psid], int(sentence), '~problem solving')
                return "On the scale of 1-5, how much do you like math?", False
            else:
                return "Please enter a number between 1 and 5.", False
        elif UserIterations.get(sender_psid) == 4:
            if sentence.isdigit() and int(sentence) >= 1 and int(sentence) <= 5:
                UserIterations.inc(sender_psid)
                add_score(scores[sender_psid], int(sentence), '~math')
                return "On the scale of 1-5, how much do you like physics?", False
            else:
                return "Please enter a number between 1 and 5.", False
        elif UserIterations.get(sender_psid) == 5:
            if sentence.isdigit() and int(sentence) >= 1 and int(sentence) <= 5:
                UserIterations.inc(sender_psid)
                add_score(scores[sender_psid], int(sentence), '~physics')
                return "On the scale of 1-5, how much do you value soft skills?", False
            else:
                return "Please enter a number between 1 and 5.", False
        elif UserIterations.get(sender_psid) == 6:
            if sentence.isdigit() and int(sentence) >= 1 and int(sentence) <= 5:
                UserIterations.inc(sender_psid)
                add_score(scores[sender_psid], int(sentence), '~softskill')
                return "On the scale of 1-5, how much do you like creating software?", False
            else:
                return "Please enter a number between 1 and 5.", False
        elif UserIterations.get(sender_psid) == 7:
            if sentence.isdigit() and int(sentence) >= 1 and int(sentence) <= 5:
                UserIterations.inc(sender_psid)
                add_score(scores[sender_psid], int(sentence), '~create software')
                return "On the scale of 1-5, how much do you like content creation (making posters and such)?", False
            else:
                return "Please enter a number between 1 and 5.", False
        elif UserIterations.get(sender_psid) == 8:
            if sentence.isdigit() and int(sentence) >= 1 and int(sentence) <= 5:
                UserIterations.inc(sender_psid)
                add_score(scores[sender_psid], int(sentence), '~content creation')
                return "On the scale of 1-5, how much do you like physical networking (hooking up servers, setting up routers, ...)?", False
            else:
                return "Please enter a number between 1 and 5.", False
        elif UserIterations.get(sender_psid) == 9:
            if sentence.isdigit() and int(sentence) >= 1 and int(sentence) <= 5:
                UserIterations.inc(sender_psid)
                add_score(scores[sender_psid], int(sentence), '~physical networking')
                return "Choose an answer by typing the number. Do you prefer to be the code developer or the product manager when you are creating application?\n\n1. Code Developer\n2. Product Manager\n3. Either/Neither", False
            else:
                return "Please enter a number between 1 and 5.", False
        elif UserIterations.get(sender_psid) == 10:
            if sentence.isdigit() and int(sentence) >= 1 and int(sentence) <= 3:
                UserIterations.inc(sender_psid)
                add_score(scores[sender_psid], int(sentence), '!coder or manager')
                return "Do you prefer to plan for everything before building your project, or do you prefer to build it as you plan it out?\n\n1. Plan for everything before building\n2. Build while planning", False
            else:
                return "Please enter a number between 1 and 3.", False
        elif UserIterations.get(sender_psid) == 11:
            if sentence.isdigit() and int(sentence) >= 1 and int(sentence) <= 2:
                UserIterations.inc(sender_psid)
                add_score(scores[sender_psid], int(sentence), '!build planning')
                return "How often did you do coding?\n\n1. Rarely (< once / month)\n2. Occasionally (>= once / month)\n3. Sometimes (>= once / week)\n4. Often (daily)", False
            else:
                return "Please enter a number between 1 and 2.", False
        elif UserIterations.get(sender_psid) == 12:
            if sentence.isdigit() and int(sentence) >= 1 and int(sentence) <= 4:
                UserIterations.rem(sender_psid)
                add_score(scores[sender_psid], int(sentence), '!coding often')
                
                max_entries = [(key, value) for key, value in scores[sender_psid].items() if value == max(scores[sender_psid].values())]
                max_entries_sorted = sorted(max_entries, key=lambda x: x[0])
                
                entry = max_entries_sorted[0][0]
                
                if entry == 'cs':
                    fullname = 'Computer Science'
                elif entry == 'ec':
                    fullname = 'E-Commerce'
                elif entry == 'tn':
                    fullname = 'Telecoms and Networking'
                else:
                    fullname = '??? (error)'
        
    score = scores[sender_psid].copy()
    del scores[sender_psid]
    return f"Alright, I have calculated the scores, and the course that I recommend is: {fullname}!\n\nBTW, here's your score for each course:\nCS: {score['cs']}\nTN: {score['tn']}\nEC: {score['ec']}", True

def handle_request_human(sender_psid: str, sentence: str, access_token: str | None=None, telegram: bool=False, telegram_data: dict | None=None) -> tuple[str, bool]:
    if UserIterations.get(sender_psid) is None:
        UserIterations.inc(sender_psid)
        
        result = classify(yesno_model, sentence=sentence, words=words, classes=classes, threshold=0.5)
        UserIterations.rem(sender_psid)
        if result == [] or result[0][0] == 'answer.maybe' or result[0][0] == 'answer.no':
            return "I see, I will respect your choice. :)", True
        
        if not telegram:
            r = requests.get(f"https://graph.facebook.com/v2.6/{sender_psid}?access_token={access_token}")
            data = r.json()
            print(data)
        else:
            data = telegram_data
        
        notifyTelegram(f"L3ID{sender_psid}MSG\nA person named {data['first_name']} {data['last_name']} with the ID {sender_psid} has requested for a human to contact them on Messenger.\n\nPlease respond back to them ASAP.")
        return "Alright, I will connect you to a human agent. You can still talk to me in the meanwhile. :)", True

        
    return "", True

def handle_send_feedback(sender_psid: str, sentence: str, access_token: str | None=None, telegram: bool=False, telegram_data: dict | None=None) -> tuple[str, bool]:
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
        
        if not telegram:
            r = requests.get(f"https://graph.facebook.com/v2.6/{sender_psid}?access_token={access_token}")
            data = r.json()
        else:
            data = telegram_data
            
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
    