import tfidf_fn
from preprocessing import preprocess
from collections import Counter, OrderedDict

class VectorSpaceModel():
    def __init__(self, documents: dict[str, str]):
        self.docs = documents
        self.tf_idf_scores = tfidf_fn.tfidf(self.docs)

    def return_top_n(self, query: str, n: int):
        q_wc = Counter(preprocess(query))

        relevance_scores = {}

        for doc_id in self.docs.keys():
            score = 0

            for word in q_wc:
                score += q_wc[word] * self.tf_idf_scores[doc_id][word]

            relevance_scores[doc_id] = score

        sorted_values = OrderedDict(sorted(relevance_scores.items(),
                                           key = lambda x: x[1],
                                           reverse = True))

        return {k: sorted_values[k] for k in list(sorted_values)[:n]}

