import pickle as pkl
import scipy as sp
import numpy as np
from lsi.lsi import lsi
from sklearn.manifold import TSNE
# from yellowbrick.text import TSNEVisualizer

from preprocess.file_utils import load_txt_line, jsonl_loader

import matplotlib.pyplot as plt

terms = ['学习', '读书', '学校', '音乐']
orig_doc_indices = [
    [447066, 428133, 408933, 426832],
    [338269, 419670, 602555, 575475],
    [413791, 512145, 555488, 563406],
    [484847, 370552, 428259, 446284],
]


def tsne(vecs: list, verbose=False, perplexity=None, lr=None) -> list:
    '''
    Perform t-SNE on a list of vectors and return the projected vectors.
    '''
    tsne = TSNE(n_components=2, verbose=verbose, random_state=0,
                perplexity=perplexity, learning_rate=lr)
    tsne_vecs = tsne.fit_transform(vecs)
    return tsne_vecs


def plot_2d(points: list, label: str=None):
    '''Plot the points in 2D'''
    x = [p[0] for p in points]
    y = [p[1] for p in points]
    plt.scatter(x, y, label=label)


def plot_term_tsne(term_vecs: list) -> None:
    '''
    Plot the t-SNE of terms.
    '''
    tsne_vecs = tsne(term_vecs, perplexity=1, lr=10)
    for i, term in enumerate(terms):
        plot_2d([tsne_vecs[i]], f'term {i}')
    plt.title('Term vectors')
    plt.legend()
    plt.show()


def tsne_on_term_and_doc_vecs(term_vecs: list, doc_vecs: list, perplexity=None,
                              lr=None) -> list:
    '''
    Perform t-SNE on term and doc vectors and return
    '''
    doc_vecs_flat = np.concatenate(doc_vecs)
    vecs = np.concatenate((term_vecs, doc_vecs_flat))
    print('Run t-SNE')
    vecs = tsne(vecs, 2, perplexity=perplexity, lr=lr)
    print('Done t-SNE')


    # Restore the lists of feature vectors
    doc_vecs = np.zeros(doc_vecs.shape[:-1] + (2, ))
    term_vecs = vecs[:len(term_vecs)]
    for i in range(len(doc_vecs)):
        for j in range(len(doc_vecs[i])):
            doc_vecs[i][j] = vecs[len(term_vecs) + i * len(doc_vecs[i]) + j]
    return term_vecs, doc_vecs


def plot_term_and_doc_tsne(term_vecs: list, doc_vecs: list) -> None:
    '''
    Plot the t-SNE of terms and documents.
    `docs_vecs` has shape (4, 4, 100)
    '''
    print('Running t-SNE on term and doc vectors...')
    # NOTE: Change perplexity here!
    term_vecs, doc_vecs = tsne_on_term_and_doc_vecs(term_vecs, doc_vecs,
                                                    perplexity=2, lr=1000)
    for i, term_vec in enumerate(term_vecs):
        plot_2d([term_vec], f'term {i+1}')
    for i in range(len(doc_vecs)):
        plot_2d(doc_vecs[i], f'doc with {i} terms')
    plt.title('Term and doc vectors')
    plt.legend()
    plt.show()


def cos_similarity(vec1: list, vec2: list) -> float:
    '''
    Calculate the cosine similarity between two vectors.
    '''
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


def plot_similarity_map_of_vecs(vecs: list, labels: list, title: str) -> None:
    '''
    Plot the similarity map of vectors.
    '''
    fig, ax = plt.subplots(1, 1)
    ax.set_xticks(list(range(len(vecs))))
    ax.set_yticks(list(range(len(vecs))))
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)

    similarity_mat = np.zeros((len(vecs), len(vecs)))
    for i in range(len(vecs)):
        for j in range(i, len(vecs)):
            a = vecs[i]
            b = vecs[j]
            similarity_mat[i][j] = similarity_mat[j][i] = cos_similarity(a, b)
    plt.imshow(similarity_mat, cmap='hot', interpolation='nearest')
    plt.colorbar()
    plt.title(title)
    plt.show()


def plot_similarity_of_terms(terms: list, vocab: list, term_topic: np.array) -> None:
    '''
    Plot the similarity of terms in the term-topic matrix.
    term_topic: The term-topic matrix, U in LSI result.
    '''
    # Get the feature vector for each term
    term_indices = [vocab.index(term) for term in terms]
    term_vecs = [term_topic[i] for i in term_indices]
    labels = ['term ' + str(i) for i in range(1, 1 + len(terms))]
    title = f'Similarity of terms (k = {len(term_vecs[0])})'
    plot_similarity_map_of_vecs(term_vecs, labels, title)


def plot_similarity_of_docs(doc_indices: list, doc_topic: np.array) -> None:
    '''
    Plot the similarity of documents in the doc-topic matrix.
    doc_topic: The doc-topic matrix, V in LSI result.
    '''
    # Get the feature vector for each doc
    doc_vecs = np.array([doc_topic[i] for i in doc_indices])
    labels = [str(i) for i in range(1, 1 + len(doc_indices))]
    title = f'Similarity of documents (k = {len(doc_vecs[0])})'
    plot_similarity_map_of_vecs(doc_vecs, labels, title)


def plot_similarity_matrices(vocab: list, terms: list, docs: list, 
                             tfidf: np.array) -> None:
    '''
    Plot the similarity matrices of terms and documents.
    '''
    
    for n_components in [10, 20, 50, 100, 200, 300, 400, 500, 600]:
        U, sigma, V = lsi(tfidf, n_components) 
        plot_similarity_of_terms(terms, vocab, U)
        plot_similarity_of_docs(docs, V)


def main():
    vocab = load_txt_line('../data/vocab_small.txt')
    doc_loader = jsonl_loader('../data/docs_small.jsonl')
    term_indices = [vocab.index(term) for term in terms]

    # Get the selected docs and their indices in the smaller corpus.
    orig_indices = sum(orig_doc_indices, [])
    selected_docs = {}
    orig_to_small_indices = {}
    for i, doc in enumerate(doc_loader):
        if doc['id'] in orig_indices:
            orig_to_small_indices[doc['id']] = i
            selected_docs[i] = doc
    doc_indices = [[orig_to_small_indices[x] for x in row] \
        for row in orig_doc_indices]

    # Perform LSI
    tfidf = sp.sparse.load_npz('../data/tfidf_sparse.npz')
    
    # Plot similarity matrix of terms and documents
    plot_similarity_matrices(vocab, terms, docs, tfidf)

    def plot_tsne(n_components):
        U, sigma, V = lsi(tfidf, n_components)
        # Get the feature vector for each term and selected doc
        term_vecs = U[term_indices]
        doc_vecs = []
        for d in doc_indices:
            doc_vecs.append(V[d])
        doc_vecs = np.array(doc_vecs)
        print('Term vec shape:', term_vecs.shape)
        print('Doc vecs shape:', doc_vecs.shape)

        print('Plot feature vectors using t-SNE...')
        plot_term_tsne(term_vecs)
        plot_term_and_doc_tsne(term_vecs, doc_vecs)
    n_components = 200
    plot_tsne(n_components)

if __name__ == '__main__':
    main()