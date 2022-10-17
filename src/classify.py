import nltk
from nltk.stem.lancaster import LancasterStemmer
stemmer = LancasterStemmer()

import pandas as pd
import numpy as np

from keras.models import Model

def clean_up_sentences(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [stemmer.stem(word.lower()) for word in sentence_words]
    return sentence_words


def bow(sentence, words, show_details=True):
    sentence_words = clean_up_sentences(sentence)
    bag = [0] * len(words)
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s:
                bag[i] = 1
                if show_details:
                    print("found in bag: %s" % w)
                    
    return np.array(bag)


def classify(model: Model, sentence: str, words: list[str], classes: list[str], threshold: float = 0.25):
    input_data = pd.DataFrame([bow(sentence, words)], dtype=float, index=['input'])
    results = model.predict([input_data])[0]
    results = [[i, r] for i, r in enumerate(results) if r > threshold]
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    
    for r in results:
        return_list.append((classes[r[0]], str(r[1])))
        
    return return_list