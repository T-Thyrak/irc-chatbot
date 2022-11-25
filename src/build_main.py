from src.helper import stemmer


import nltk
import numpy as np
import khmernltk

from polyglot.detect import Detector

from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.optimizers import SGD
from keras.utils import plot_model

import pickle
import random
import json
import os


TARGET = 'chatbot'


def main():
    words = []
    classes = []
    documents = []
    ignore_words = ['?', ' ', '!', ',', '.', '​']
    
    with open('misc/intents.json') as json_data:
        intents = json.load(json_data)
        
        for intent in intents['intents']:
            for pattern in intent['patterns']:
                lang = Detector(pattern).language.code
                
                if lang == 'km':
                    word = khmernltk.word_tokenize(pattern)
                else:
                    word = nltk.word_tokenize(pattern)
                    
                words.extend(word)
                documents.append((word, intent['tag']))
                if intent['tag'] not in classes:
                    classes.append(intent['tag'])
                    
    words = [stemmer.stem(w.lower()) for w in words if w not in ignore_words]
    words = sorted(list(set(words)))
    
    classes = sorted(list(set(classes)))
    
    print(len(documents), "documents")
    print(len(classes), "classes", classes)
    print(len(words), "uniquely stemmed words", words)
    
    training = []
    output_empty = [0] * len(classes)
    
    for doc in documents:
        bag = []
        pattern_words = doc[0]
        pattern_words = [stemmer.stem(word.lower()) for word in pattern_words]
        
        for w in words:
            bag.append(1) if w in pattern_words else bag.append(0)
            
        output_row = list(output_empty)
        output_row[classes.index(doc[1])] = 1
        
        training.append([bag, output_row])
        
    random.shuffle(training)
    training = np.array(training)
    
    train_x = list(training[:, 0])
    train_y = list(training[:, 1])
    
    model = Sequential([
        Dense(256, input_shape=(len(train_x[0]),), activation='relu'),
        Dropout(0.5),
        Dense(128, activation='relu'),
        Dropout(0.5),
        Dense(len(train_y[0]), activation='softmax')
    ])
    
    sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
    model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])
    
    model.fit(np.array(train_x), np.array(train_y), epochs=200, batch_size=5, verbose=1)
    
    save_path = os.path.join(os.getcwd(), 'models', TARGET)
    
    model.save(save_path, overwrite=True)
    
    plot_model(model, to_file='model.png', show_shapes=True, show_dtype=False, rankdir="LR", show_layer_names=False) # remove this line if you don't want to generate the model image
    return (words, classes)

if __name__ == "__main__":
    words, classes = main()
    
    if not os.path.exists("misc/chatbot"):
        os.mkdir("misc/chatbot")
    
    with open('misc/chatbot/words.pkl', 'wb') as f:
        pickle.dump(words, f)
        
    with open('misc/chatbot/classes.pkl', 'wb') as f:
        pickle.dump(classes, f)