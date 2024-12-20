import tfidf_fn
from preprocessing import preprocess
from collections import Counter, OrderedDict

class VectorSpaceModel():
    def __init__(self, documents: dict[str, str]):
        self.docs = documents
        self.tf_idf_scores, self.custom_vectorizer = tfidf_fn.sklearn_tfidf(documents)

    def return_top_n(self, query: str, n: int):
        tfidf_query = tfidf_fn.sklearn_tfidif_query(query, self.custom_vectorizer)
        results = tfidf_fn.sklearn_cos_sim(tfidf_query, self.tf_idf_scores, self.docs)

        return results[:n]

