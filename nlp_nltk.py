import argparse
import numpy
import nltk.classify

from nltk import compat
from nltk.classify import SklearnClassifier
from sklearn import svm
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import SGDClassifier, Ridge
from sklearn.naive_bayes import MultinomialNB

import yelp.start
import slate
import blog
import amazon

def train(classif, vectorizer, train_set, sparse):
    X, y = list(compat.izip(*train_set))
    X = vectorizer.fit_transform(X)
    return classif.fit(X, y)

# See http://www.nltk.org/_modules/nltk/classify/scikitlearn.html
def classify_many(classif, vectorizer, featuresets, round = True):
    X, _ = list(compat.izip(*featuresets))
    X = vectorizer.transform(X)
    results = classif.predict(X)
    results = [numpy.round_(x) for x in results]
    return results

# See http://www.nltk.org/_modules/nltk/classify/util.html
def accuracy(results, test_set):
    correct = [l == r for ((fs, l), r) in zip(test_set, results)]
    correct = [x[0] and x[1] and x[2] for x in correct]
    if correct:
        return float(sum(correct))/len(correct)
    else:
        return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source",    choices=["slate", "amazon", "blog", "yelp"],
        required=True, help="Source to use for training")
    parser.add_argument("-a", "--algorithm", choices=["bayes", "svm", "lsvc", "gboost", "ridge"],
        required=True, help="Machine learning algorithm")
    args = parser.parse_args()

    sparse = True

    if args.source == "slate":
        data = slate.get_data()
    elif args.source == "yelp":
        data = yelp.start.get_data()
    elif args.source == "amazon":
        data = amazon.get_data()
    elif args.source == "blog":
        data = blog.get_data()

    if args.algorithm == "bayes":
        classif = MultinomialNB()
    elif args.algorithm == "svm":
        classif = SGDClassifier(loss='hinge', penalty='l2', alpha=1e-3, n_iter=5, random_state=42)
    elif args.algorithm == "lsvc":
        classif = svm.LinearSVC()
    elif args.algorithm == "gboost":
        classif = GradientBoostingClassifier()
        sparse = False
    elif args.algorithm == "ridge":
        classif = Ridge()

    pct_train = .7
    num_train = int(len(data) * pct_train)
    train_set, test_set = data[:num_train], data[num_train:]

    vectorizer = DictVectorizer(dtype=float, sparse=sparse)

    classif = train(classif, vectorizer, train_set, sparse)
    results = classify_many(classif, vectorizer, test_set)

    print "Perfect Accuracy:", accuracy(results, test_set)