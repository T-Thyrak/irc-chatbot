import os
import pickle
import json
import random

from rich.console import Console
console = Console()

from flask import Flask, request, jsonify, render_template, url_for
from flask_cors import CORS
from keras.models import Model, load_model
from dotenv import load_dotenv
from polyglot.detect import Detector

from src.shared_message_queue import put_message_client
from src.ext.prompt_group import PromptGroup
from src.helper import context_handlers, handle_message, xor, verify_hash, shutdown_server, get_user_data, log_message
from src.service import call_sender_API
from src.tasks import notifyTelegram
from src.wrappers import UserIterations, ExpiringDict

from src.classify import classify
from src.mysqlquery import *

from time import time

SUPPORTED_LANGUAGES = (
    'en',
    'km'
)


app = Flask(__name__)
CORS(app)


load_dotenv(dotenv_path=os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/.env')


load_path = os.path.join('models', 'chatbot')
model: Model = load_model(load_path)
with open('misc/chatbot/words.pkl', 'rb') as f:
    words = pickle.load(f)
with open('misc/chatbot/classes.pkl', 'rb') as f:
    classes = pickle.load(f)
with open('misc/intents.json') as f:
    intents = json.load(f)
    

contexts = ExpiringDict(max_len=int(os.getenv('MAX_LEN', 500)), max_age_seconds=30 * 60, callback=lambda key, _: UserIterations.rem(key))
locks = ExpiringDict(max_len=int(os.getenv('MAX_LEN', 500)), max_age_seconds=60 * 60, callback=lambda key, _: notifyTelegram(f'L1ID{key}MSG\nLock on `{key}` has expired.'))

open('misc/comfile', 'w').close()
comfile_lock_path = 'misc/comfile.lock'

# comfile_lock = filelock.FileLock(comfile_lock_path)

# telegram_process_handle = subprocess.Popen(['python', '-m', 'src.telebot'], shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# print(telegram_process_handle)
# queue_pc = Thread(target=sender.run, args=(msg_queue, comfile_lock))

@app.get('/api/v2/chat')
def chat_v2_get():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if mode and token:
        if mode == "subscribe" and token == os.getenv('VERIFY_TOKEN'):
            print("WEBHOOK_VERIFIED")
            return challenge, 200
        
        return "403 Forbidden", 403
    
    return "400 Bad Request", 400

@app.post('/api/v2/chat')
def chat_v2_post():
    body = request.get_json()
    if body['object'] == 'page':
        try:
            for entry in body['entry']:
                event = entry['messaging'][0]
                sender_psid = event['sender']['id']
                
                if locks.get(sender_psid):
                    continue
                
                print(f"Received message from {sender_psid}")
                if event.get('message'):
                    message = handle_message(sender_psid, event['message'])
                    response = {}
                    
                    if contexts.get(sender_psid) is None:
                        results, lang = classify(model, message, words, classes)
                        if lang not in SUPPORTED_LANGUAGES:
                            lang = 'en'
                        
                        userdata = get_user_data(sender_psid, os.getenv('PAGE_ACCESS_TOKEN'))
                        username = f"{userdata['first_name']} {userdata['last_name']}"
                        log_message(sender_psid, username, message, lang)
                        
                        if results == []:
                            response['text'] = random.choice(intents['default_intent']['responses'][lang])
                        else:
                            for intent in intents['intents']:
                                if intent['tag'] == results[0][0]:
                                    if 'context_filter' in intent:
                                        if contexts.get(sender_psid) == intent['context_filter']:
                                            response['text'] = random.choice(intent['responses'][lang])
                                            if 'context_set' in intent:
                                                contexts[sender_psid] = intent['context_set']
                                    else:
                                        response['text'] = random.choice(intent['responses'][lang])
                                        if 'context_set' in intent:
                                            contexts[sender_psid] = intent['context_set']
                                    
                                    break
                    else:
                        if contexts.get(sender_psid) == 'request_human' and UserIterations.get(sender_psid) is not None:
                            continue
                        else:
                            context = contexts[sender_psid]
                            handler = context_handlers[context]
                            
                            try:
                                lang = Detector(message, quiet=True).language.code
                            except Exception as e:
                                lang = 'en'
                            
                            response['text'], context_should_drop = handler(sender_psid, message, os.getenv('PAGE_ACCESS_TOKEN'), lang=lang)
                            
                            if context_should_drop:
                                print(f"Dropping context for {sender_psid}: {context}")
                                contexts.pop(sender_psid)
                        
                    call_sender_API(sender_psid, response, os.getenv('PAGE_ACCESS_TOKEN'))
        except Exception:
            console.print_exception(show_locals=True)
        finally: 
            return "EVENT_RECEIVED", 200
    return "404 Not Found", 404

@app.post('/api/v2t/chat')
def chat_v2t():
    body = request.get_json()
    print(body)
    try:
        sentence = body['sentence']
        xsender_id = body['sender_id']
        
        if locks.get(xsender_id):
            return jsonify({'error': 'locked'}), 403
        
        print(f"Received message from {xsender_id}")
        
        response = {}
        if contexts.get(xsender_id) is None:
            results, lang = classify(model, sentence, words, classes)
            
            if lang not in SUPPORTED_LANGUAGES:
                lang = 'en'
                
            username = f"{body['first_name']} {body['last_name']}"
            log_message(xsender_id, username, sentence, lang)
            
            if results == []:
                response['text'] = random.choice(intents['default_intent']['responses'][lang])
            
            else:
                for intent in intents['intents']:
                    if intent['tag'] == results[0][0]:
                        if 'context_filter' in intent:
                            if contexts.get(xsender_id) == intent['context_filter']:
                                response['text'] = random.choice(intent['responses'][lang])
                                if 'context_set' in intent:
                                    contexts[xsender_id] = intent['context_set']
                        
                        else:
                            response['text'] = random.choice(intent['responses'][lang])
                            if 'context_set' in intent:
                                contexts[xsender_id] = intent['context_set']
                        
                        break
        else:
            if contexts.get(xsender_id) == 'request_human' and UserIterations.get(xsender_id) is not None:
                return jsonify({'error': 'locked'}), 403
            else:
                context = contexts[xsender_id]
                handler = context_handlers[context]
                data = {
                    'first_name': body['first_name'],
                    'last_name': body['last_name'],
                }
                
                try:
                    lang = Detector(sentence, quiet=True).language.code
                except Exception as e:
                    lang = 'en'
                
                response['text'], context_should_drop = handler(xsender_id, sentence, telegram=True, telegram_data=data, lang=lang)
                
                if context_should_drop:
                    print(f"Dropping context for {xsender_id}: {context}")
                    contexts.pop(xsender_id)
    except KeyError as e:
        console.print_exception(show_locals=True)
        return jsonify({'error': 'invalid request', 'message': 'missing keys'}), 400
    except Exception as e:
        console.print_exception(show_locals=True)

        return jsonify({'error': 'internal server error'}), 500
    
    return jsonify(response), 200


@app.route('/api/v1/chat', methods=['POST'])
def chat():
    try:
        sentence = request.json['sentence']
    except KeyError:
        return jsonify({"tag": "error", "response": "No sentence provided."}), 400
    
    print(request.json)
    
    if contexts.get(request.json['uid']) is None:
        results, lang = classify(model, sentence, words, classes, threshold=0.75)
    
        response = {}
        
        if results == []:
            response['tag'] = 'default_intent'
            response['message'] = random.choice(intents['default_intent']['responses'])
        else:
            response['tag'] = results[0][0]
            for intent in intents['intents']:
                if intent['tag'] == response['tag']:
                    if 'context_filter' in intent:
                        if intent['context_filter'] == contexts.get(response['uid'], None):
                            response['message'] = random.choice(intent['responses'])
                            if 'context_set' in intent:
                                contexts[request.json['uid']] = intent['context_set']
                    else:    
                        response['message'] = random.choice(intent['responses'])
                        if 'context_set' in intent:
                            contexts[request.json['uid']] = intent['context_set']
                            print(f"Context set to {contexts[request.json['uid']]}")
                    
                    break
                
        return jsonify(response), 200
    else:
        context = contexts[request.json['uid']]
        handler = context_handlers[context]
        response = {}
        
        response['tag'] = context
        response['message'], context_should_drop = handler("0", sentence, "0")
        
        if context_should_drop:
            contexts[request.json['uid']] = None
            print(f"Context dropped.")
        
        return jsonify(response), 200
        

@app.route('/')
def homepage():
    url = url_for('chat')
    groups = [
        PromptGroup('Greetings', 'Greetings', [
            "Hello",
            "Hi there",
            "How are you doing",
        ]),
        PromptGroup('What can you do', 'What can do', [
            "What can you do",
            "What are your functions",
        ]),
    ]
    return render_template('index.html', url=url, groups=groups)

@app.route('/api/v2/lock', methods=['POST'])
def lock():
    body = request.json
    sender_psid = body['sender_psid']
    verify_token = body['verify_token']
    
    true_verify_token = xor(verify_token, os.getenv('HASH_NUT'))
    if true_verify_token != os.getenv('VERIFY_TOKEN'):
        return jsonify({"error": "Invalid verify token."}), 403
    
    if locks.get(sender_psid) is None:
        locks[sender_psid] = True
        return jsonify({"success": True}), 200
    
    return jsonify({"error": "Already locked."}), 403

@app.route('/api/v2/unlock', methods=['POST'])
def unlock():
    body = request.json
    sender_psid = body['sender_psid']
    verify_token = body['verify_token']
    
    true_verify_token = xor(verify_token, os.getenv('HASH_NUT'))
    if true_verify_token != os.getenv('VERIFY_TOKEN'):
        return jsonify({"error": "Invalid verify token."}), 403
    
    if locks.get(sender_psid) is not None:
        locks.pop(sender_psid)
        return jsonify({"success": True}), 200
    
    return jsonify({"error": "Not locked."}), 403

@app.route('/api/v2/test', methods=['GET'])
def test():
    put_message_client("DEASSIGN?USER=31337&OPERATOR=-25000")
    return jsonify({"success": True}), 200
    
@app.route('/api/v2/shutdown', methods=['POST'])
def shutdown_post():
    print(request.json)
    body = request.json
    
    # should receive a hash of the shutdown token and the poison token
    shutdown_hash = body['hash']
    token = body['token']
    
    # verify the hash
    if (verify_hash(shutdown_hash, token)):
        # if the hash is valid, shutdown the server
        shutdown_server()
        return jsonify({"message": "Server shutting down..."}), 200
    
    return jsonify({"message": "Invalid hash."}), 403
    
@app.get('/api/v2/acknowledge')
def ack():
    print("message ACK")
    return jsonify({"message": "ACK"}), 200

@app.post('/api/v2/acknowledge')
def ack_post():
    body = request.json
    print(body)
    return jsonify({"message": "ACK"}), 200
    
def graceful_shutdown():
    print("Shutting down server...")
    # telegram_process_handle.kill()
    # sender.terminate()
    # queue_pc.join()
    
    
# if __name__ == "__main__":
#     try:
#         # queue_pc.start()
#         app.run(port=int(os.getenv('PORT', 8080)))
#     except KeyboardInterrupt:
#         print("Keyboard interrupt detected. Shutting down...")
#         sender.terminate()
#         # queue_pc.join()
#         graceful_shutdown() 