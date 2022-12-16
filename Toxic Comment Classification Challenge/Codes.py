import re
import json

import pandas as pd
import numpy as np

from string import punctuation
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer


class ToxicCommentClassification:

    def __init__(self):

        self.classes_ = ['toxic', 'severe_toxic', 'obscene', 'threat', 'insult', 'identity_hate']
        self.new_features = ['count_sent', 'count_word', 'count_unique_word', 'count_letters', 'count_punctuations', 'count_words_upper', 'count_words_title', 'count_stopwords', 'mean_word_len']
        self.stop_words = set(stopwords.words('english'))
        self.contraction_dict = json.load(open('inputs/contraction_dict.json', 'r'))

    def export_data(self):

        self.train = pd.read_csv('./inputs/train.csv')
        self.test = pd.read_csv('inputs/test.csv')
        self.submission = pd.read_csv('inputs/sample_submission.csv')

    def tokenizer(self, sentences):
        lemmatizer = WordNetLemmatizer()
        tokens = sentences.lower().split()
        sentences = ' '.join([self.contraction_dict[token] if token in self.contraction_dict else token for token in tokens])
        sentences = re.sub(f'[{punctuation}“”¨«»®´·º½¾¿¡§£₤‘’]', ' ', sentences)
        sentences = re.sub('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', ' ', sentences)
        sentences = re.sub('\[\[.*\]', ' ', sentences)
        sentences = re.sub(r'[0-9+]', ' ', sentences)
        tokens = word_tokenize(sentences.lower())
        tokens = [token for token in tokens if token not in self.stop_words]
        tokens = [lemmatizer.lemmatize(token) for token in tokens]

        return tokens

    def nbsvm_model(self):

        def _log_count_ratio(X, y):

            epsilon = 1.0
            p = np.log((epsilon + X[y == 1].sum(axis=0)) / (epsilon + (y == 1).sum(axis=0)))
            q = np.log((epsilon + X[y == 0].sum(axis=0)) / (epsilon + (y == 0).sum(axis=0)))
            r = p - q

            return r

        vectorizer = TfidfVectorizer(ngram_range=(1, 2), tokenizer=self.tokenizer)
        vectorizer.fit(self.train['comment_text'])

        X_train = vectorizer.transform(self.train['comment_text'])
        X_test = vectorizer.transform(self.test['comment_text'])

        preds = np.zeros((len(self.test), len(self.classes_)))

        for i, label in enumerate(self.classes_):
            print(f'----------{label}----------')
            r = _log_count_ratio(X_train, self.train[label])
            X = X_train.multiply(r)
            model = LogisticRegression(dual=False, max_iter=1000, random_state=42)
            model.fit(X, self.train[label])
            preds[:, i] = model.predict_proba(X_test.multiply(r))[:, 1]

        submission_id = pd.DataFrame({'id': self.submission['id']})
        submission = pd.concat([submission_id, pd.DataFrame(preds, columns=self.classes_)], axis=1)
        submission.to_csv('./outputs/3.csv', index=False)


if __name__ == '__main__':

    tcc = ToxicCommentClassification()
    tcc.export_data()
    tcc.nbsvm_model()