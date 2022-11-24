import nltk
import khmernltk
import pandas as pd
import numpy as np

from time import time
from polyglot.detect import Detector

from nltk.stem.lancaster import LancasterStemmer
stemmer = LancasterStemmer()

from keras.models import Model

def clean_up_sentences(sentence):
    try:
        lang = Detector(sentence).language.code
    except Exception as e:
        lang = 'en'
        
    if lang == 'km':
        sentence_words = khmernltk.word_tokenize(sentence)
    else:
        sentence_words = nltk.word_tokenize(sentence)
    
    sentence_words = [stemmer.stem(word.lower()) for word in sentence_words]
    return sentence_words


def bow(sentence, words, show_details=True):
    sentence_words = clean_up_sentences(sentence)
    try:
        lang = Detector(sentence).language.code
    except Exception as e: 
        lang = 'en'
    
    bag = [0] * len(words)
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s:
                bag[i] = 1
                if show_details:
                    print("found in bag: %s" % w)
                    
    return np.array(bag), lang


def classify(model: Model, sentence: str, words: list[str], classes: list[str], threshold: float = 0.25) -> tuple[list[tuple[str, str]], str]:
    """Classify the sentence using the model and return the intent and the primary language of the sentence.
    Falls back to English if failed to detect the language.

    Args:
        model (Model): The model to use for classification.
        sentence (str): The sentence to predict the intent.
        words (list[str]): The list of words.
        classes (list[str]): The list of classes.
        threshold (float, optional): The confidence threshold of intents to accept. Defaults to 0.25.

    Returns:
        tuple[list[tuple[str, str]], str]: The list of (intent, confidence) and the primary language of the sentence.
    """
    bag_of_words, lang = bow(sentence, words)

    input_data = pd.DataFrame([bag_of_words], dtype=float, index=['input'])
    # results = model.predict([input_data])[0]
    results = model.__call__(np.array(input_data))[0]
    
    results = [[i, r] for i, r in enumerate(results) if r > threshold]
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    
    for r in results:
        return_list.append((classes[r[0]], str(r[1])))
        
    return return_list, lang