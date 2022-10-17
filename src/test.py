import os
import pickle

import pandas as pd

from classify import bow
from keras.models import load_model, Model

load_path = os.path.join('models', 'yesno')

model: Model = load_model(load_path)
with open('misc/yesno/words.pkl', 'rb') as f:
    words = pickle.load(f)
with open('misc/yesno/classes.pkl', 'rb') as f:
    classes = pickle.load(f)
    
def classify_local(sentence):
    ERROR_THRESHOLD = 0.50
    
    input_data = pd.DataFrame([bow(sentence, words)], dtype=float, index=['input'])
    results = model.predict([input_data])[0]
    results = [[i, r] for i, r in enumerate(results) if r > ERROR_THRESHOLD]
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    
    for r in results:
        return_list.append((classes[r[0]], str(r[1])))
        
    return return_list

print(classify_local('Yes, no, maybe'))