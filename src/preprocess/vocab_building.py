# coding: utf8
from pathlib import Path
import pickle as pkl
from tqdm import tqdm

from .file_utils import jsonl_loader, load_txt_line, save_txt_line


def get_token_freq(docs_file: Path, num_docs=None) -> {str: int}:
    '''Loop through data and count freq. of every token'''
    doc_loader = jsonl_loader(docs_file)
    token_freq = {}
    cnt = 0
    for doc in tqdm(doc_loader):
        content = doc['content']
        for para in content:
            for sent in para:
                for token in sent:
                    if token in token_freq:
                        token_freq[token] += 1
                    else:
                        token_freq[token] = 1
        cnt += 1
        if num_docs is not None and cnt == num_docs:
            break
    return token_freq


def process_token_freq(token_freq: {str: int}) -> {str: int}:
    '''
    Process a dict of token freq. by following steps:
        - Remove whitespaces
        - Remove stopwords
        - Remove punctuations
        - Remove tokens whose freq. = 1
    '''
    # All the following functions are executed in-place on `token_freq`
    def remove_stopwords(token_freq: dict):
        def get_stopwords() -> [str]:
            STOPWORD_FILES = ['stopwords_all.txt']
            words = []
            for file in STOPWORD_FILES:
                with open('../data/' + file, 'r', encoding='utf8') as f:
                    for line in f:
                        words.append(line.strip())
            return words
        stopwords = get_stopwords()
        for word in stopwords:
            if word in token_freq:
                del token_freq[word]
    def remove_punc(token_freq: dict):
        zh_punc = """　∶’．￥％……＆×＃＼～！？｡。，·＂＃＄％＆＇（）＊＋－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘'‛“”„‟…‧﹏"""
        en_punc = """!\"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ """
        for punc in zh_punc:
            if punc in token_freq:
                del token_freq[punc]
        for punc in en_punc:
            if punc in token_freq:
                del token_freq[punc]
    def remove_rare_tokens(token_freq: dict):
        rare_tokens = []
        for t in token_freq:
            if token_freq[t] == 1:
                rare_tokens.append(t)
        for t in rare_tokens:
            del token_freq[t]
    
    print('\nOriginal vocab')
    print(sum(token_freq.values()), len(token_freq))

    # Rmove whitespace and empty token
    ws = [' ', '　', '\n', '\f', '\r', '\t', '\v', '\u00a0', '\u1680', '\u2000',
          '\u2001', '\u2002', '\u2003', '\u2004', '\u2005', '\u2006', '\u2007', 
          '\u2008', '\u2009', '\u200a', '\u202f', '\u205f', '\u3000']
    for c in ws:
        if c in token_freq:
            del token_freq[c]
    print('Removed whitespaces')
    print('  total cnt, # tokens =', sum(token_freq.values()), len(token_freq))

    # Remove stop words
    remove_stopwords(token_freq)
    print('Removed stopwords')
    print('  total cnt, # tokens =', sum(token_freq.values()), len(token_freq))

    # Remove punctuation (if they persist after stopwords removal)
    remove_punc(token_freq)
    print('Removed punctuations marks')
    print('  total cnt, # tokens =', sum(token_freq.values()), len(token_freq))

    # Remove tokens that happen only once
    remove_rare_tokens(token_freq)
    print('Removed rare tokens (freq = 1)')
    print('  total cnt, # tokens =', sum(token_freq.values()), len(token_freq))
    return token_freq


def build_vocab(data_dir: Path, doc_cnt: int=None) -> [str]:
    '''Count all token freq, then based on that, build and return a vocab'''
    # Filenames
    data_dir = Path(data_dir)
    if doc_cnt == None:
        file_token_freq = data_dir / 'token_freq_raw.pkl'
    else:
        file_token_freq = data_dir / f'token_freq_raw_{doc_cnt/1000}k.pkl'
    file_processed = data_dir / 'token_freq.pkl'
    file_vocab = data_dir / 'vocab.txt'

    # Raw token freq
    if file_token_freq.exists():
        print('Loading raw token frequencies')
        token_freq = pkl.load(open(file_token_freq, 'rb'))
        is_new_freq = False
    else:
        print('*** Count all tokens frequencies ***')
        token_freq = get_token_freq(data_dir / 'docs.jsonl', doc_cnt)
        print('Saving to ' + str(file_token_freq))
        pkl.dump(token_freq, open(file_token_freq, 'wb'))
        is_new_freq = True
    
    # Token freq
    if not is_new_freq and file_processed.exists():
        print('Loading token frequencies from ' + str(file_processed))
        token_freq = pkl.load(open(file_processed, 'rb'))
        is_processed_new = False
    else:
        print('*** Processing tokens ***')
        token_freq = process_token_freq(token_freq)
        print('Saving to ' + str(file_processed))
        pkl.dump(token_freq, open(file_processed, 'wb'))
        is_processed_new = True

    # Vocab
    if not is_processed_new and file_vocab.exists():
        print('Loading vocab from ' + str(file_vocab))
        vocab = load_txt_line(file_vocab)
    else:
        # Sorted by descending freq
        vocab = sorted(token_freq.keys(), key=lambda x: token_freq[x], reverse=True)
        print('Saving to ' + str(file_vocab))
        save_txt_line(vocab, file_vocab)
    return vocab


if __name__ == '__main__':
    
    build_vocab('../../data')
    token_freq = pkl.load(open('../../data/token_freq.pkl', 'rb'))

    # Log result
    freq_sorted = sorted(token_freq.items(), key=lambda x: x[1], reverse=True)
    print('*** Result ***')
    print('Vocab size:', len(vocab))
    print('Sum of token freq.:', sum(token_freq.values()))
    print('Most frequent 10 tokens:')
    print(freq_sorted[:10])
    print('Least frequent 10 tokens:')
    print(freq_sorted[-10:])