import os
import pickle
import json
import random

from flask import Flask, request, jsonify, render_template, url_for
from flask_cors import CORS
from keras.models import Model, load_model
from dotenv import load_dotenv
from multiprocessing import Queue
from src.prompt_group import PromptGroup

from src.helper import context_handlers, generate_name, generate_token, handle_message, xor, QueueSender, QueueFiller
from src.service import call_sender_API
from src.tasks import notifyTelegram
from src.wrappers import TTLDurations, UserIterations, ExpiringDict

from src.classify import classify


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

msg_queue = Queue()

filler = QueueFiller(msg_queue)
sender = QueueSender()

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
                        results = classify(model, message, words, classes)
                        
                        if results == []:
                            response['text'] = random.choice(intents['default_intent']['responses'])
                        else:
                            for intent in intents['intents']:
                                if intent['tag'] == results[0][0]:
                                    if 'context_filter' in intent:
                                        if contexts.get(sender_psid) == intent['context_filter']:
                                            response['text'] = random.choice(intent['responses'])
                                            if 'context_set' in intent:
                                                contexts[sender_psid] = intent['context_set']
                                    else:
                                        response['text'] = random.choice(intent['responses'])
                                        if 'context_set' in intent:
                                            contexts[sender_psid] = intent['context_set']
                                    
                                    break
                    else:
                        if contexts.get(sender_psid) == 'request_human' and UserIterations.get(sender_psid) is not None:
                            continue
                        else:
                            context = contexts[sender_psid]
                            handler = context_handlers[context]
                            
                            response['text'], context_should_drop = handler(sender_psid, message, os.getenv('PAGE_ACCESS_TOKEN'))
                            
                            if context_should_drop:
                                contexts.pop(sender_psid)
                        
                    call_sender_API(sender_psid, response, os.getenv('PAGE_ACCESS_TOKEN'))
        except Exception as e:
            e.printStackTrace()
        finally: 
            return "EVENT_RECEIVED", 200
    return "404 Not Found", 404


@app.route('/api/v1/chat', methods=['POST'])
def chat():
    try:
        sentence = request.json['sentence']
    except KeyError:
        return jsonify({"tag": "error", "response": "No sentence provided."}), 400
    
    print(request.json)
    
    if contexts.get(request.json['uid']) is None:
        results = classify(model, sentence, words, classes, threshold=0.75)
    
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
    # print(telegram_process_handle)
    # telegram_process_handle.poll()
    # filler.fill('L2ID1337MSG\nThe person `name` with ID `1337` has requested a human interaction!\n\nPlease respond to the user ASAP.')
    notifyTelegram('L3ID1337MSG\nThe person `name` with ID `1337` has requested a human interaction!\n\nPlease respond to the user ASAP.')
    
    # return jsonify({"message": telegram_process_handle.__str__()}), 200
    return jsonify({"message": "OK"}), 200
    
@app.get('/api/v2/shutdown')
def shutdown_get():
    url = url_for('shutdown_post')
    token = generate_token(ttl=TTLDurations.MINUTE)
    random_var_name = generate_name()
    return render_template('shutdown.html', url=url, secure_name=random_var_name, token=token)

@app.post('/api/v2/shutdown')
def shutdown_post():
    body = request.json
    
    # should receive a token, and a hash
    token = body['token']
    shutdown_hash = body['hash']
    
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
    
    
if __name__ == "__main__":
    try:
        # queue_pc.start()
        app.run(port=int(os.getenv('PORT', 8080)))
    except KeyboardInterrupt:
        print("Keyboard interrupt detected. Shutting down...")
        sender.terminate()
        # queue_pc.join()
        graceful_shutdown() 