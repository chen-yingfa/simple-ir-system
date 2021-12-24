import numpy as np
import scipy as sp
from sklearn.utils.extmath import randomized_svd


def frobenius(a, b) -> float:
    '''
    Frobenius norm of the difference of two matrices.
    '''
    s = 0
    for i in range(a.shape[0]):
        d = a[i] - b[i]
        d = np.array(d).squeeze()
        s += d.dot(d)
    return s ** 0.5


def lsi(mat, n_components: int) -> (np.ndarray, np.ndarray, np.ndarray):
    '''
    Perform LSI on a matrix, return (U, Sigma, V)
    mat: scipy.sparse.csr_matrix
    '''
    U, Sigma, VT = randomized_svd(
        mat, 
        n_components=n_components,
        n_iter=5,
        random_state=0)
    return U, Sigma, VT.T


def main():
    # Plot the approximation error of LSI for different number of components.
    file_tfidf = '../../data/tfidf_sparse.npz'

    print('Loading tfidf...')
    tfidf = sp.sparse.load_npz(file_tfidf)
    import matplotlib.pyplot as plt
    diffs = []
    list_k = [1, 5, 10, 20, 50, 100, 200, 500]
    for n_components in list_k:
        print(f'Fitting LSI with {n_components} components...')
        U, sigma, V = lsi(tfidf, n_components)

        # print(U.shape, sigma.shape, V.shape)
        restored = U @ np.diag(sigma) @ V.T
        diff = frobenius(tfidf, restored)
        print('Difference with original:', diff)
        diffs.append(diff)

    plt.plot(list_k, diffs)
    plt.xlabel('k')
    plt.ylabel('Frobenius norm of difference')
    plt.title('Frobenius norm of difference of LSI approximation')
    plt.show()


if __name__ == '__main__':
    main()