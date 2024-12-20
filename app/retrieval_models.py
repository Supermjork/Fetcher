import re
import tfidf_fn as idf_fns
from preprocessing import preprocess
from collections import Counter, OrderedDict

class VectorSpaceModel():
    def __init__(self, documents: dict[str, str]):
        self.docs = documents
        self.tf_idf_scores, self.custom_vectorizer = idf_fns.sklearn_tfidf(documents)

    def return_top_n(self, query: str, n: int):
        tfidf_query = idf_fns.sklearn_tfidif_query(query, self.custom_vectorizer)
        results = idf_fns.sklearn_cos_sim(tfidf_query, self.tf_idf_scores, self.docs)

        return results[:n]

class BooleanIR:
    def __init__(self, documents: dict[str, list[str]]):
        self.documents: dict[str, list[str]] = documents
        self.inverted_index = self._build_inverted_index()

    def _build_inverted_index(self):
        inverted_index = {}
        for doc_name, tokens in self.documents.items():
            for token in tokens:
                if token not in inverted_index:
                    inverted_index[token] = set()
                inverted_index[token].add(doc_name)
        return inverted_index

    def _preprocess_query(self, query: str):
        query = " ".join(preprocess(query, remove_stopwords = False))
        query = re.sub(r'\b(and|or|not)\b', lambda x: x.group(0).upper(), query)  # Normalize operators
        return query

    def _resolve(self, term):
        return self.inverted_index.get(term, set())

    def _evaluate_boolean_query(self, query):
        tokens = re.findall(r'\w+|AND|OR|NOT|\(|\)', query)
        stack = []
        operators = {"AND", "OR", "NOT"}

        print(query)

        for token in tokens:
            if token not in operators:
                stack.append(self._resolve(token))  # Push resolved term set
            elif token == "NOT":
                if stack:
                    set_to_negate = stack.pop()
                    stack.append(set(self.documents.keys()) - set_to_negate)
                else:
                    raise ValueError(f"Malformed query: 'NOT' operator with no operand.")
            elif token in {"AND", "OR"}:
                if len(stack) < 2:
                    raise ValueError(f"Malformed query: '{token}' operator with insufficient operands.")
                set2 = stack.pop()
                set1 = stack.pop()
                if token == "AND":
                    stack.append(set1 & set2)
                elif token == "OR":
                    stack.append(set1 | set2)
        if len(stack) != 1:
            raise ValueError("Malformed query: Remaining terms or operators after evaluation.")
        return stack.pop()

    def search(self, query):
        processed_query = self._preprocess_query(query)
        return self._evaluate_boolean_query(processed_query)

