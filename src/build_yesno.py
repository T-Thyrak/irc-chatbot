import nltk
import numpy as np

from keras.models import Sequential
from keras.layers import Dense, Dropout
from csv import reader

import pickle
import random
import os



stemmer = nltk.LancasterStemmer()

TARGET = 'yesno'


def main():
    with open('misc/yesno.csv', 'r') as f:
        csv_reader = reader(f)
        _header = next(csv_reader)
        
        data = np.array(list(csv_reader))
        
    answers = data[:, 0]
    sentences = data[:, 1]
    
    words = []
    classes = []
    documents = []
    ignore_words = ['?']
    
    for i, sentence in enumerate(sentences):
        word = nltk.word_tokenize(sentence)
        words.extend(word)
        documents.append((word, answers[i]))
        if answers[i] not in classes:
            classes.append(answers[i])
            
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
 
    print("Training data created")
    
    model = Sequential([
        Dense(128, input_shape=(len(train_x[0]),), activation='relu'),
        Dropout(0.5),
        Dense(64, activation='relu'),
        Dropout(0.5),
        Dense(len(train_y[0]), activation='softmax')
    ])
    
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
    
    hist = model.fit(np.array(train_x), np.array(train_y), epochs=100, batch_size=5, verbose=1)
    
    save_path = os.path.join(os.getcwd(), 'models', TARGET)
    
    model.save(save_path, overwrite=True)
    return (words, classes)

if __name__ == "__main__":
    words, classes = main()
    
    if not os.path.exists("misc/yesno"):
        os.mkdir("misc/yesno")
    
    with open('misc/yesno/words.pkl', 'wb') as f:
        pickle.dump(words, f)
        
    with open('misc/yesno/classes.pkl', 'wb') as f:
        pickle.dump(classes, f)