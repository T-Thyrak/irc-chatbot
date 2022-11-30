from src.mysqlquery import create_connection, destroy_connection, end_commit, execute_query, start_commit
from src.wrappers import UserIterations

import pickle
import os
import requests
import logging
import json

from keras.models import load_model, Model
from src.classify import classify
from src.tasks import notifyTelegram
from src.translate.tr import __

with open('misc/yesno/words.pkl', 'rb') as f:
    words = pickle.load(f)
with open('misc/yesno/classes.pkl', 'rb') as f:
    classes = pickle.load(f)
    
load_path = os.path.join('models', 'yesno')
yesno_model: Model = load_model(load_path)  # type: ignore

with open('misc/survey_data/rules.json', 'r') as f:
    rules = json.load(f)
    
scores = {}

def handle_course_recommendation(sender_psid: str, sentence: str, access_token: str | None=None, telegram: bool=False, telegram_data: dict | None=None, lang: str='en') -> tuple[str, bool]:
    # some codes
    
    def add_score(input_score: dict, option: int, section: str):
        input_score['cs'] = input_score['cs'] + rules['data_cs'][section][str(option)]
        input_score['tn'] = input_score['tn'] + rules['data_tn'][section][str(option)]
        input_score['ec'] = input_score['ec'] + rules['data_ec'][section][str(option)]
        
        # return input_score
    
    if UserIterations.get(sender_psid) is None:
        UserIterations.inc(sender_psid)

        result, class_lang = classify(yesno_model, sentence=sentence, words=words, classes=classes, threshold=0.5)
        if result == [] or result[0][0] == 'answer.maybe' or result[0][0] == 'answer.no':
            return __('choice.respect', lang), True
        else:
            scores[sender_psid] = {'cs': 0, 'tn': 0, 'ec': 0}
            return __('questions.~coding', lang), False
    else:
        if UserIterations.get(sender_psid) == 0:
            if sentence.isdigit() and int(sentence) >= 1 and int(sentence) <= 5:
                UserIterations.inc(sender_psid)
                add_score(scores[sender_psid], int(sentence), '~coding')
                return __('questions.~marketing', lang), False
            else:
                return __('questions.enter', lang).format(range_min=1, range_max=5), False
        elif UserIterations.get(sender_psid) == 1:
            if sentence.isdigit() and int(sentence) >= 1 and int(sentence) <= 5:
                UserIterations.inc(sender_psid)
                add_score(scores[sender_psid], int(sentence), '~marketing')
                return __('questions.~networking', lang), False
            else:
                return __('questions.enter', lang).format(range_min=1, range_max=5), False
        elif UserIterations.get(sender_psid) == 2:
            if sentence.isdigit() and int(sentence) >= 1 and int(sentence) <= 5:
                UserIterations.inc(sender_psid)
                add_score(scores[sender_psid], int(sentence), '~networking')
                return __('questions.~solve_problems', lang), False
            else:
                return __('questions.enter', lang).format(range_min=1, range_max=5), False
        elif UserIterations.get(sender_psid) == 3:
            if sentence.isdigit() and int(sentence) >= 1 and int(sentence) <= 5:
                UserIterations.inc(sender_psid)
                add_score(scores[sender_psid], int(sentence), '~problem solving')
                return __('questions.~math', lang), False
            else:
                return __('questions.enter', lang).format(range_min=1, range_max=5), False
        elif UserIterations.get(sender_psid) == 4:
            if sentence.isdigit() and int(sentence) >= 1 and int(sentence) <= 5:
                UserIterations.inc(sender_psid)
                add_score(scores[sender_psid], int(sentence), '~math')
                return __('questions.~physics', lang), False
            else:
                return __('questions.enter', lang).format(range_min=1, range_max=5), False
        elif UserIterations.get(sender_psid) == 5:
            if sentence.isdigit() and int(sentence) >= 1 and int(sentence) <= 5:
                UserIterations.inc(sender_psid)
                add_score(scores[sender_psid], int(sentence), '~physics')
                return __('questions.~soft_skills', lang), False
            else:
                return __('questions.enter', lang).format(range_min=1, range_max=5), False
        elif UserIterations.get(sender_psid) == 6:
            if sentence.isdigit() and int(sentence) >= 1 and int(sentence) <= 5:
                UserIterations.inc(sender_psid)
                add_score(scores[sender_psid], int(sentence), '~softskill')
                return __('questions.~create_software', lang), False
            else:
                return __('questions.enter', lang).format(range_min=1, range_max=5), False
        elif UserIterations.get(sender_psid) == 7:
            if sentence.isdigit() and int(sentence) >= 1 and int(sentence) <= 5:
                UserIterations.inc(sender_psid)
                add_score(scores[sender_psid], int(sentence), '~create software')
                return __('questions.~create_content', lang), False
            else:
                return __('questions.enter', lang).format(range_min=1, range_max=5), False
        elif UserIterations.get(sender_psid) == 8:
            if sentence.isdigit() and int(sentence) >= 1 and int(sentence) <= 5:
                UserIterations.inc(sender_psid)
                add_score(scores[sender_psid], int(sentence), '~content creation')
                return __('questions.~physical_networking', lang), False
            else:
                return __('questions.enter', lang).format(range_min=1, range_max=5), False
        elif UserIterations.get(sender_psid) == 9:
            if sentence.isdigit() and int(sentence) >= 1 and int(sentence) <= 5:
                UserIterations.inc(sender_psid)
                add_score(scores[sender_psid], int(sentence), '~physical networking')
                return __('questions.!code_dev', lang), False
            else:
                return __('questions.enter', lang).format(range_min=1, range_max=5), False
        elif UserIterations.get(sender_psid) == 10:
            if sentence.isdigit() and int(sentence) >= 1 and int(sentence) <= 3:
                UserIterations.inc(sender_psid)
                add_score(scores[sender_psid], int(sentence), '!coder or manager')
                return __('questions.!build_planning', lang), False
            else:
                return __('questions.enter', lang).format(range_min=1, range_max=3), False
        elif UserIterations.get(sender_psid) == 11:
            if sentence.isdigit() and int(sentence) >= 1 and int(sentence) <= 2:
                UserIterations.inc(sender_psid)
                add_score(scores[sender_psid], int(sentence), '!build planning')
                return __('questions.!coding_often', lang), False
            else:
                return __('questions.enter', lang).format(range_min=1, range_max=2), False
        elif UserIterations.get(sender_psid) == 12:
            if sentence.isdigit() and int(sentence) >= 1 and int(sentence) <= 4:
                UserIterations.rem(sender_psid)
                add_score(scores[sender_psid], int(sentence), '!coding often')
                
                max_entries = [(key, value) for key, value in scores[sender_psid].items() if value == max(scores[sender_psid].values())]
                max_entries_sorted = sorted(max_entries, key=lambda x: x[0])
                
                entry = max_entries_sorted[0][0]
                
                fullname = __(f'courses.{entry}', lang)
            else:
                return __('questions.enter', lang).format(range_min=1, range_max=4), False
        else:
            logging.warning('Unreacheable code was reached at: handle_course_recommendation, iteration = ' + str(UserIterations.get(sender_psid)))
            return "Unreachable code", True
        
    score = scores[sender_psid].copy()
    del scores[sender_psid]
    return __('questions.score_calc', lang).format(fullname=fullname, cs_score=score['cs'], ec_score=score['ec'], tn_score=score['tn']), True

def handle_request_human(sender_psid: str, sentence: str, access_token: str | None=None, telegram: bool=False, telegram_data: dict | None=None, lang: str='en') -> tuple[str, bool]:
    if UserIterations.get(sender_psid) is None:
        UserIterations.inc(sender_psid)
        
        result, class_lang = classify(yesno_model, sentence=sentence, words=words, classes=classes, threshold=0.5)
        UserIterations.rem(sender_psid)
        if result == [] or result[0][0] == 'answer.maybe' or result[0][0] == 'answer.no':
            return __('choice.respect', lang), True
        
        if not telegram:
            r = requests.get(f"https://graph.facebook.com/v2.6/{sender_psid}?access_token={access_token}")
            data = r.json()
        else:
            data = telegram_data
        
        notifyTelegram(f"L3ID{sender_psid}MSG\nA person named {data['first_name']} {data['last_name']} with the ID {sender_psid} has requested for a human to contact them on Messenger.\n\nPlease respond back to them ASAP.")
        return __("request_human.confirm", lang), True

        
    return "", True

def handle_send_feedback(sender_psid: str, sentence: str, access_token: str | None=None, telegram: bool=False, telegram_data: dict | None=None, lang: str='en') -> tuple[str, bool]:
    if not hasattr(handle_send_feedback, 'feedback_type'):
        handle_send_feedback.feedback_type = None
        
    if UserIterations.get(sender_psid) is None:
        logging.info("Should be hit, 1st time")
        
        UserIterations.inc(sender_psid)
        
        result, class_lang = classify(yesno_model, sentence=sentence, words=words, classes=classes, threshold=0.5)
        if result == [] or result[0][0] == 'answer.maybe' or result[0][0] == 'answer.no':
            return __('choice.respect', lang), True
        
        return __('feedback.type', lang), False

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
        execute_query(query=sql, values=val, db_conn=db_conn)
        end_commit(db_conn=db_conn)
        destroy_connection(db_conn)
    
        return "Thank you so much for your feedback! :)", True
    
    if UserIterations.get(sender_psid) == 2:
        logging.info("Should be hit, 4th time")
        UserIterations.rem(sender_psid)
        return "Thank you so much for your feedback! :)", True
    
    logging.info("Should be unreachable")
    return "", True
    