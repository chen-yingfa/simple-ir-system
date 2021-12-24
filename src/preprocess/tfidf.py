from math import log
from pathlib import Path
import json
import pickle as pkl
from tqdm import tqdm

import numpy as np
from scipy.sparse import csr_matrix, lil_matrix
from scipy import sparse

from file_utils import jsonl_loader, save_jsonl, load_txt_line, save_txt_line


class TfIdf:
    '''Class for building a matrix of TF-IDF values.'''
    def __init__(self, vocab: [str]):
        self.vocab = vocab
        self.vocab_set = set(vocab)
        self.df = {t: 0 for t in vocab}
        self.corpus_size = 0

    def add_docs(self, docs):
        '''Process list of docs'''
        for doc in docs:
            self.add_doc(doc)
            self.corpus_size += 1

    def add_doc(self, doc: list):
        '''Add a new document to the corpus'''

        # Get set of all terms in this doc
        terms_set = set()
        for i, para in enumerate(doc['content']):
            for sent in para:
                for term in sent:
                    if term in self.vocab_set:
                        terms_set.add(term)
        for term in terms_set:
            if term not in self.df:
                self.df[term] = 0
            self.df[term] += 1

    def doc_to_tf_dict(self, doc: list) -> dict:
        '''
        Get the term frequency dict for a document.

        `doc` should be the same as the doc that was added to this TD-IDF by
        calling `add_docs` or `add_doc`.
        '''
        tf_dict = {}
        doc_size = 0
        for para in doc:
            for sent in para:
                doc_size += len(sent)
                for term in sent:
                    if term in self.vocab_set:
                        if term not in tf_dict:
                            tf_dict[term] = 0
                        tf_dict[term] += 1
        for t in tf_dict:
            tf_dict[t] /= doc_size
        return tf_dict

    def docs_to_tf_dicts(self, docs: list) -> list:
        '''Turn documents into list of term frequency dicts'''
        tf_dicts = []
        for doc in docs:
            tf_dicts.append(self.doc_to_tf_dict(doc))
        return tf_dicts

    def get_idf(self, term: str) -> float:
        '''Get the inverse document frequency of a term'''
        # Smoothing to avoid zero division
        return log(self.corpus_size / (1 + self.df[term]))

    def get_tf(self, term: str, doc: list) -> float:
        '''
        Get the term frequency.
        '''
        term_cnt = 0
        doc_size = 0
        for para in doc:
            for sent in para:
                doc_size += len(sent)
                if term in sent:
                    term_cnt += 1
        return term_cnt / doc_size

    def get_mat(self, docs: list) -> np.array:
        '''
        Get the TF-IDF matrix, return numpy array of float32.

        `docs` should be the same as the docs that was added to this TD-IDF by
        calling `add_docs` or `add_doc`.
        '''
        docs = [doc['content'] for doc in docs]
        print('Turning docs into tf-dicts')
        tf_dicts = self.docs_to_tf_dicts(docs)
        del docs
        print('Building matrix')
        print('Size of matrix:', len(self.vocab), self.corpus_size)
        import gc
        gc.collect()
        # Use int16 to save space, this matrix easily causes memory error.
        mat = np.zeros((len(self.vocab), self.corpus_size), dtype=np.float32)
        for i, term in tqdm(enumerate(self.vocab), total=len(self.vocab)):
            for j, tf_dict in enumerate(tf_dicts):
                mat[i][j] = tf_dict.get(term, 0)
            mat[i] *= np.float32(self.get_idf(term))
        return mat


def get_docs_by_column(column: str, doc_loader) -> [dict]:
    docs = []
    for i, doc in tqdm(enumerate(doc_loader)):
        if doc['column'].strip() == column:
            docs.append(doc)
    return docs


def get_docs_loader_by_column(column: str, doc_loader):
    for doc in doc_loader:
        if doc['column'] == column:
            yield doc


def build_vocab(docs, min_term_freq=4) -> [str]:
    '''Build and return a vocab, remove stopwords, infrequent words etc.'''
    # Get vocab from docs
    term_freq = {}  # NOTE: This is different from TF in TF-IDF
    for doc in docs:
        for para in doc['content']:
            for sent in para:
                for term in sent:
                    term_freq[term] = term_freq.get(term, 0) + 1
    vocab = sorted(term_freq.keys(), key=lambda x: term_freq[x], reverse=True)
    print('Original vocab size:', len(vocab))

    vocab = [w for w in vocab if w.strip()]

    # Remove stopwords
    print('Removing stopwords...')
    stopwords = load_txt_line('../../data/stopwords_all.txt')
    stopwords = set(stopwords)
    vocab = [w for w in vocab if w not in stopwords]
    print('Vocab size after removing stopwords:', len(vocab))

    # Remove infrequent words
    print(f'Removing infrequent words (frequency < {min_term_freq})...')
    vocab = [t for t in vocab if term_freq[t] >= min_term_freq]
    print('Vocab size after removing infrequent words:', len(vocab))

    # Remove expressions
    print('Removing expressions...')
    new_vocab = []

    for t in vocab:
        for s in ['.', '%', '&', ',', '^', '+', '-', '—', '*', '/', '$', '(', 
                  ':', ')', '￥', '@', '号', '第', 'st', 'nd', 'th', 's']:
            normed = t.replace(s, '')
        if not normed.isdecimal():
            new_vocab.append(t)
    vocab = new_vocab
    print('Vocab size after removing expressions:', len(vocab))

    # # Remove punctuations
    # print('Removing punctuations...')
    # punctuations = '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~《》，。、！@#￥%……&（）-_·~[]；‘：“'
    # vocab = [t for t in vocab if t not in punctuations]
    # print('Vocab size after removing punctuations:', len(vocab))

    return vocab


def main():
    COLUMN = '文化'

    data_dir = Path('../../data')

    # Extract a small portion of docs to construct TF-IDF from (to save time).
    file_docs = data_dir / 'docs_small.jsonl'
    file_docs_small = data_dir / 'docs_small.jsonl'
    if file_docs_small.exists():
        print(f'Loading {file_docs_small}')
        docs = jsonl_loader(file_docs_small)
    else:
        doc_loader = jsonl_loader(data_dir / 'docs.jsonl')
        docs = get_docs_loader_by_column(COLUMN, doc_loader)
        print(f'Saving {len(docs)} docs to "{file_docs_small}"')
        save_jsonl(docs, file_docs_small)

    # Contruct a smaller vocab
    small_vocab_file = Path('..', '..', 'data', 'vocab_small.txt')
    if False and small_vocab_file.exists():
        print('Loading smaller vocab...')
        small_vocab = load_txt_line(small_vocab_file)
    else:
        print('Building smaller vocab...')
        small_vocab = build_vocab(docs)
        save_txt_line(small_vocab, small_vocab_file)

    # Build TF-IDF
    tfidf = TfIdf(small_vocab)
    tfidf.add_docs(jsonl_loader(file_docs_small))
    v = sorted(tfidf.df.items(), key=lambda x: x[1], reverse=True)
    print('Building TF-IDF matrix...')
    tfidf_mat = tfidf.get_mat(jsonl_loader(file_docs_small))
    print('Saving TF-IDF matrix...')
    np.save(data_dir / 'tfidf_mat.npy', tfidf_mat)    
    print('Save sparse version')
    sparse_tfidf_mat = csr_matrix(tfidf_mat)
    sparse.save_npz(data_dir / 'tfidf_sparse.npz', sparse_tfidf_mat)


if __name__ == '__main__':
    main()