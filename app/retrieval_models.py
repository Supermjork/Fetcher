import re
import os
import glob
import math
import tfidf_fn as idf_fns
from typing import List, Dict
from preprocessing import preprocess
from collections import Counter, OrderedDict, defaultdict

class VectorSpaceModel():
    def __init__(self, folder_path: str):
        self.path = folder_path
        self.docs = self._doc_to_dict(folder_path)
        self.tf_idf_scores, self.custom_vectorizer = idf_fns.sklearn_tfidf(self.docs)

    def return_top_n(self, query: str, n: int):
        tfidf_query = idf_fns.sklearn_tfidif_query(query, self.custom_vectorizer)
        results = idf_fns.sklearn_cos_sim(tfidf_query, self.tf_idf_scores, self.docs)

        return results[:n]

    def _doc_to_dict(self, path: str, len_lim: int = 100_000):
        '''
        Returns dictionary with: Doc_name -> Content_String
        '''
        name_content = {}

        file_names = glob.glob(path)

        for file in file_names:
            name = os.path.basename(file)  # Extracts the file name with dots intact
            print(f"[VSM] Now Loading: \'{name}\', into memory")

            with open(file, 'r') as f:
                if len_lim:
                    data = f.read(len_lim)
                else:
                    data = f.read()
            name_content[name] = data

        return name_content

class BooleanIR:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.documents = self._load_documents()
        self.processed_docs = self._doc_processor(self.documents)
        self.inverted_index = self._create_inverted_index()

    def _load_documents(self, len_lim: int = 100_000):
        '''
        Returns dictionary with: Doc_name -> Content_String
        '''
        name_content = {}

        file_names = glob.glob(self.folder_path)

        for file in file_names:
            name = os.path.basename(file)
            print(f"[BOOL] Now Loading: \'{name}\', into memory")

            with open(file, 'r') as f:
                if len_lim:
                    data = f.read(len_lim)
                else:
                    data = f.read()
            name_content[name] = data

        return name_content

    def _doc_processor(self, docs: dict[str, str]):
        '''
        Preprocesses documents into the specified standard
        '''
        preprocessed_docs = {}

        for doc_title, doc_content in docs.items():
            preprocessed_docs[doc_title] = " ".join(preprocess(doc_content))

        return preprocessed_docs

    def _create_inverted_index(self):
        """Creates an inverted index from the documents."""
        inverted_index = defaultdict(set)
        for doc_name, content in self.processed_docs.items():
            for token in content.split():
                inverted_index[token].add(doc_name)
        return inverted_index

    def query(self, boolean_query):
        """Processes a Boolean query and returns matching document names."""
        tokens = re.findall(r'NOT|AND|OR|\(|\)|\w+', boolean_query.upper())
        postfix = self._to_postfix(tokens)
        print(f"Postfix query: {postfix}")  # Debugging output
        return self._evaluate_postfix(postfix)

    def _to_postfix(self, tokens):
        """Converts infix Boolean query to postfix notation using the Shunting-yard algorithm."""
        precedence = {'NOT': 3, 'AND': 2, 'OR': 1, '(': 0, ')': 0}
        output = []
        stack = []

        for token in tokens:
            if token.isalnum():
                output.append(token)
            elif token == '(':
                stack.append(token)
            elif token == ')':
                while stack and stack[-1] != '(':
                    output.append(stack.pop())
                stack.pop()
            else:  # Operator
                while stack and precedence[token] <= precedence[stack[-1]]:
                    output.append(stack.pop())
                stack.append(token)

        while stack:
            output.append(stack.pop())

        return output

    def _evaluate_postfix(self, postfix):
        """Evaluates a postfix Boolean query and returns matching document names."""
        stack = []

        for token in postfix:
            if token.isalnum():
                matching_docs = self.inverted_index.get(token.lower())
                stack.append(matching_docs)
            elif token == 'NOT':
                operand = stack.pop()
                all_docs = set(self.documents.keys())
                result = all_docs - operand
                stack.append(result)
            else:  # AND or OR
                right = stack.pop()
                left = stack.pop()
                if token == 'AND':
                    result = left & right
                    stack.append(result)
                elif token == 'OR':
                    result = left | right
                    stack.append(result)

        final_result = stack.pop() if stack else set()
        return final_result

class BM25:
    def __init__(self, folder_path: str, len_lim: int = 100_000):
        self.folder_path = folder_path
        self.len_lim = len_lim

        # Load and preprocess documents
        self.documents = self._load_documents(len_lim)
        self.preprocessed_docs = self._doc_processor(self.documents)

        # Compute document statistics
        self.doc_lengths = {doc: len(content.split()) for doc, content in self.preprocessed_docs.items()}
        self.avg_doc_length = sum(self.doc_lengths.values()) / len(self.doc_lengths)
        self.inverted_index = self._build_inverted_index(self.preprocessed_docs)
        self.doc_count = len(self.preprocessed_docs)

    def _load_documents(self, len_lim: int = 100_000) -> dict[str, str]:
        """
        Load `.txt` files and return a dictionary mapping file names to their content.
        """
        name_content = {}
        file_names = glob.glob(self.folder_path)

        for file in file_names:
            name = os.path.basename(file)
            print(f"[BM25] Loading: '{name}' into memory")

            with open(file, 'r') as f:
                if len_lim:
                    data = f.read(len_lim)
                else:
                    data = f.read()
            name_content[name] = data

        return name_content

    def _doc_processor(self, docs: Dict[str, str]) -> dict[str, str]:
        """
        Preprocess documents to lowercase and tokenize them by splitting on whitespace.
        """
        def preprocess(text: str) -> list[str]:
            return text.lower().split()

        preprocessed_docs = {}

        for doc_title, doc_content in docs.items():
            preprocessed_docs[doc_title] = " ".join(preprocess(doc_content))

        return preprocessed_docs

    def _build_inverted_index(self, docs: dict[str, str]) -> dict[str, dict[str, int]]:
        """
        Build an inverted index mapping terms to document frequencies.
        """
        inverted_index = {}
        for doc, content in docs.items():
            term_freq = Counter(content.split())
            for term, freq in term_freq.items():
                if term not in inverted_index:
                    inverted_index[term] = {}
                inverted_index[term][doc] = freq
        return inverted_index

    def compute_bm25(self, query: str, k1: float = 1.5, b: float = 0.75):
        """
        Compute BM25 scores for the query across all documents.
        """
        query_terms = query.lower().split()
        scores = {doc: 0 for doc in self.preprocessed_docs}

        for term in query_terms:
            if term in self.inverted_index:
                doc_freq = len(self.inverted_index[term])
                idf = math.log((self.doc_count - doc_freq + 0.5) / (doc_freq + 0.5) + 1)

                for doc, freq in self.inverted_index[term].items():
                    term_freq = freq
                    doc_length = self.doc_lengths[doc]

                    numerator = term_freq * (k1 + 1)
                    denominator = term_freq + k1 * (1 - b + b * doc_length / self.avg_doc_length)

                    scores[doc] += idf * (numerator / denominator)

        return sorted(scores.items(), key=lambda item: item[1], reverse=True)

