import csv
import gensim
from nltk import word_tokenize
import numpy as np
from sklearn.feature_extraction import text
import time
import datetime

class Restaurant:
    def __init__(self, rest_id):
        self.rest_id = rest_id
        self.f_dates = []
        self.f_stars = []
        self.y_star = []
        self.reviews = []
        self.rev_dates = []

def read_r_id_to_y_id(filename):
    yelp_rest = {}
    tr = {}
    with open("yelp/data/restaurant_ids_to_yelp_ids.csv") as f:
        reader = csv.reader(f)
        header = reader.next()
        for row in reader:
            yelp_rest[row[1]] = Restaurant(row[0])
            tr[row[0]] = row[1]
    return tr, yelp_rest

def get_yelp_id(filename="yelp/data/train_labels.csv"):
    '''returns dict of yelp_id -> Restaurant class'''
    tr, yelp_rest = read_r_id_to_y_id(filename)
    with open(filename) as f:
        reader = csv.reader(f)
        header = reader.next()
        for row in reader:
            yelp_rest[tr[row[2]]].f_stars.append([int(row[3]), int(row[4]), int(row[5])])
            yelp_rest[tr[row[2]]].f_dates.append(row[1])
    with open("yelp/data/yelp_academic_dataset_review.csv") as f:
        reader = csv.reader(f)
        header = reader.next()
        for row in reader:
            if row[4] in yelp_rest:
                yelp_rest[row[4]].reviews.append(row[2])
                yelp_rest[row[4]].rev_dates.append(row[7])
                yelp_rest[row[4]].y_star.append(int(row[6]))

    return yelp_rest

def get_data(filename = "yelp/data/train_labels.csv",embedding = False):
    "Build a list of tuples of the form (features, tag) for the Yelp data."

    # Possible features:
    # Average yelp rating, concatenation of all reviews, average of previous inspection grades
    # Count of "dirty" and/or "clean" words in reviews and/or tags,
    # Restaurant ID, Date of inspection

    # Tag: result of inspection on above date
    tr, _ = read_r_id_to_y_id(filename)

    restaurants = get_yelp_id(filename)
    result = []
    corpus = []
    if embedding == "doc2vec":
        model = gensim.models.Word2Vec.load("yelp/doc2vecmodel")
    if embedding == "word2vec":
        model = gensim.models.Word2Vec.load("yelp/word2vecmodel")
    with open(filename) as f:
        reader = csv.reader(f)
        headers = reader.next()
        for row in reader:
            rest_id = row[2]
            r = restaurants[tr[rest_id]]
            date = row[1]
            unix_date = (int(time.mktime(time.strptime(date,"%Y-%m-%d"))) - 10**9)/10**5
            tag = r.f_stars[r.f_dates.index(date)]

            avg_rating = sum(r.y_star) / float(len(r.y_star))
            yelp_reviews = "\n".join(r.reviews)
            if embedding:
                if embedding == "tfidf":
                    corpus.append(yelp_reviews)
                elif embedding == "word2vec":
                    yelp_embeddings = []
                    yelp_tokens = word_tokenize(yelp_reviews.decode('utf-8'))
                    for token in yelp_tokens:
                        try:
                            yelp_embeddings.append(model[token])
                        except: Exception
                    yelp_reviews = np.asarray(yelp_embeddings)
                elif embedding == "doc2vec":
                    rev_vector = embedding_dict(model[r.rest_id])
                    #made empty to make cleaner code, I don't think it should impact results
                    yelp_reviews = "a"

            grades = [map(lambda x: x[i], r.f_stars) for i in range(3)]  # list of lists of number of stars
            if len(grades[0]) == 0 and len(grades[1]) == 0 and len(grades[2]) == 0:
                avg_grades = [0, 0, 0]
            else:
                avg_grades = [sum(l)/float(len(l)) for l in grades]            

            features = {
                "avg_rating": avg_rating,
                "reviews": yelp_reviews,
                "avg_one_star_grades": avg_grades[0],
                "avg_two_star_grades": avg_grades[1],
                "avg_three_star_grades": avg_grades[2],
                #"rest_id": rest_id,
                "date": date
            }
            if embedding == "doc2vec":
                features = merge(features,rev_vector)
            result.append((features, tag))
    if embedding == "tfidf":
        tfidf_transformer = text.TfidfTransformer()
        count_vect = text.CountVectorizer()
        corpus_counts = count_vect.fit_transform(corpus)
        corpus_tfidf = tfidf_transformer.fit_transform(corpus)
        for entry in result:
            features = merge(features,tfidf_transformer.transform(count_vect(entry["reviews"])))

    return result

def merge(x,y):
    '''Given two dicts, merge them into a new dict as a shallow copy.'''
    z = x.copy()
    z.update(y)
    return z

def embedding_dict(vector):
    features = {}
    for index,value in enumerate(vector):
        index = str(index)
        features[index] = value
    return features

def get_test_data():
    return get_data(filename = "yelp/data/SubmissionFormat.csv")

def print_results(results):
    with open("yelp/data/SubmissionFormat.csv") as f:
        with open("out.csv", "w") as o:
            reader = csv.reader(f)
            out = csv.writer(o)
            header = reader.next()
            out.writerow(header)
            for result, row in zip(results, reader):
                row[3], row[4], row[5] = int(result[0]), int(result[1]), int(result[2])
                out.writerow(row)

if __name__ == "__main__":
    yelp_to_b = read_yelp_to_b()
    targets = read_targets()
    objects = get_yelp_id()
    print objects["NOxXooahnQvpHoYKYTdh8g"].reviews
