import os
import glob
import nltk
import string
import numpy as np
from preprocessing import preprocess
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def doc_to_dict(path: str, len_lim: int = 100_000):
    '''
    Returns dictionary with: Doc_name -> Content_String
    '''
    name_content = {}

    file_names = glob.glob(path)

    for file in file_names:
        name = os.path.basename(file)  # Extracts the file name with dots intact
        print(f"Now Loading: \'{name}\', into memory")

        with open(file, 'r') as f:
            if len_lim:
                data = f.read(len_lim)
            else:
                data = f.read()
        name_content[name] = data

    return name_content

def doc_processor(docs: dict[str, str]):
    '''
    Preprocesses documents into the specified standard
    '''
    preprocessed_docs = {}

    for doc_title, doc_content in docs.items():
        preprocessed_docs[doc_title] = " ".join(preprocess(doc_content))

    return preprocessed_docs

def sklearn_tfidf(docs: dict[str, str]):
    tfidic_vectorizer = TfidfVectorizer()
    processed_docs = doc_processor(docs)
    return tfidic_vectorizer.fit_transform(processed_docs.values()), tfidic_vectorizer

def sklearn_tfidif_query(query: str, cust_vectorizer: TfidfVectorizer):
    return cust_vectorizer.transform([' '.join(preprocess(query))])

def sklearn_cos_sim(q_vec, tfidf_mat, docs):
    similarities = cosine_similarity(q_vec, tfidf_mat)

    results = [(key, similarities[0][i]) for i, key in enumerate(docs)]
    results.sort(key = lambda x: x[1], reverse = True)
    print(f"results: {results[0]}")
    return results

def build_vocab(docs: dict[str, str]):
    '''
    Vocabulary Builder
    '''
    vocab = []

    for doc in docs.values():
        for word in doc:
            if word not in vocab:
                vocab.append(word)

    return vocab

def term_freq(doc_vocab: list[str], docs: dict[str, str]):
    '''
    Returns the Term Frequency in every document
    `doc_id`, `word`: `count(word, doc)`
    '''
    tf_docs = {}

    for doc_id in docs.keys():
        tf_docs[doc_id] = {}

    for word in doc_vocab:
        for doc_id, doc in docs.items():
            tf_docs[doc_id][word] = doc.count(word)

    return tf_docs

def word_freq(vocab: list[str], docs: dict[str, str]):
    '''
    Returning the word frequency in a given set of documents
    '''
    document_freq = {}

    for word in vocab:
        freq = 0

        for doc in docs.values():
            if word in doc:
                freq += doc.count(word)

        document_freq[word] = freq

    return document_freq

def inverse_doc_freq(vocab: list[str], doc_freq: dict[str, int],  n_docs: int):
    '''
    Calculates the inverse document frequency
    '''
    idf = {}

    for word in vocab:
        idf[word] = np.log2(n_docs / (doc_freq[word] + 1)) + 1

    return idf

def tfidf(docs: dict[str, str]):
    '''
    Calculates the TF-IDF for a given set of documents
    '''
    preprocessed_docs = doc_processor(docs)

    vocab = build_vocab(preprocessed_docs)

    t_freq = term_freq(vocab, preprocessed_docs)
    d_freq = word_freq(vocab, preprocessed_docs)
    idf_scr = inverse_doc_freq(vocab, d_freq, len(preprocessed_docs.keys()))

    tf_idf_score = {}

    for doc_id in docs.keys():
        tf_idf_score[doc_id] = {}

    for word in vocab:
        for doc_id, _ in docs.items():
            tf_idf_score[doc_id][word] = t_freq[doc_id][word] * idf_scr[word]

    return tf_idf_score
