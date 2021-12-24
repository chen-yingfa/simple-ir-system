# coding: utf8
import time
import json
import pickle as pkl
from pathlib import Path

from tqdm import tqdm
from elasticsearch import Elasticsearch
from pyroaring import BitMap

from preprocess.file_utils import jsonl_loader, load_txt_line
from preprocess.utils import split_tokens, format_doc
from preprocess.vocab_building import build_vocab


NUM_DOCS = 612031


def build_inv_idx(data_dir: Path, es_index: str) -> {str: [int]}:
    '''Loop through all docs and build an inverted index
    
    inverted_index: {str: [int]}, key is term, value is a list of doc ids
    '''

    def build_token_to_id(vocab: [str]) -> {str: int}:
        '''Create a mapping from token to ID for simpler token lookup, which is
        useful for looking up inverted index that is stored in a database such as
        Elastic search'''
        token_to_id = {}
        for i, token in enumerate(vocab):
            token_to_id[token] = i
        return token_to_id


    file = data_dir / 'docs.jsonl'
    file_token_to_id = data_dir / 'token_to_id.json'
    file_inv_idx_roaring = data_dir / 'inv_idx_roaring.pkl'
    file_inv_idx = data_dir / 'inv_idx.pkl'
    
    loader = jsonl_loader(file)

    # Load vocab
    vocab = build_vocab(data_dir)

    if file_token_to_id.exists():
        token_to_id = json.load(open(file_token_to_id, 'r', encoding='utf8'))
    else:
        token_to_id = build_token_to_id(vocab)
        with open(file_token_to_id, 'w', encoding='utf8') as f:
            json.dump(token_to_id, f, ensure_ascii=False)

    if file_inv_idx.exists():
        print(f"Loading inverted index from \"{file_inv_idx}\"...")
        inv_idx = pkl.load(open(file_inv_idx, 'rb'))
    else:
        # Building inverted index dictionary
        print('Building inverted index')
        inv_idx = {token_to_id[t]: [] for t in vocab}
        for doc_id, doc in tqdm(enumerate(loader), total=NUM_DOCS):
            content = doc['content']
            for para in content:
                for sent in para:
                    for t in sent:
                        if t in inv_idx:
                            if len(inv_idx[t]) == 0 or inv_idx[t][-1] != doc_id:
                                inv_idx[t].append(doc_id)
        print(f'Saving to {file_inv_idx}...')
        pkl.dump(inv_idx, open(file_inv_idx, 'wb'))
        # Save a smaller inverted index containing 10k most frequent tokens
        print('Saving a small inverted index...')
        small = {t: inv_idx for t in vocab[:1000]}
        pkl.dump(small, open(data_dir / 'inv_idx_1000.pkl', 'wb'))

    # Turn postings lists into roaring bitmaps
    print('Converting postings lists to roaring bitmaps...')
    roaring_inv_idx = {}
    for t in tqdm(inv_idx):
        roaring_inv_idx[t] = BitMap(inv_idx[t])
    pkl.dump(roaring_inv_idx, open(file_inv_idx_roaring, 'wb'))

    return inv_idx


def gen_formatted_docs(data_file: Path, target_file: Path) -> None:
    '''
    Format each doc in `data_file` and save to target_file in jsonl format,
    where each line is a json in following format: 
    {
        "file_name": "1234770.dat",
        "title": "xxx",
        "date": "2003-12-23",
        "column": "",
        "content": [[["token_1", ], ], ]
        "pos_tags": [[["np", ], ], ]
        "id": 4,
    }

    Explanation: 
        content is a list of paragraphs, each paragraph is a list of sentences,
        each sentence is a list of tokens. and each token is a `str`. 
        
        pos_tag is of the same shape and type, and each corresponding element is
        the POS tag of the corresponding token. 
    '''
    doc_loader = jsonl_loader(data_file)
    writer = open(target_file, 'w', encoding='utf8')
    for doc_id, doc in tqdm(enumerate(doc_loader), total=NUM_DOCS):
        formatted = format_doc(doc)
        formatted['id'] = doc_id

        # Save to file
        writer.write(json.dumps(formatted, ensure_ascii=False) + '\n')


def add_all_docs_to_es(data_file: Path, es_index: str) -> None:
    '''Add all docs to Elasticsearch database.'''
    from concurrent.futures import ThreadPoolExecutor

    es = Elasticsearch()
    doc_loader = jsonl_loader(data_file)

    def _add_doc(doc: dict):
        es.index(index=es_index, id=doc['id'], document=doc)

    def _add_doc_date(doc: dict):
        date_index = es_index + '-date'
        es.index(index=date_index, id=doc['id'], document={'date': doc['date']})
    

    # Add each doc using thread pool to speed up
    # Load documents in chunks sequentially, then the thread pool processes each
    # chunk in parallel.
    i = 0
    num_threads = 64
    max_chunk_size = 8196   # A multiple of threads count for better optimization
    prev = i
    start_time = time.time()
    while i < NUM_DOCS:
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            chunk_size = min(NUM_DOCS - i, max_chunk_size)
            docs = [next(doc_loader) for _ in range(chunk_size)]
            i += chunk_size
            executor.map(_add_doc, docs)
            # executor.map(_add_doc_date, docs)
        if i - prev > 1000:
            # Log
            prev += 1000
            elapsed = time.time() - start_time
            eta = elapsed * (NUM_DOCS / i - 1)
            print(f'[{i}/{NUM_DOCS}] elapsed: {elapsed:.2f}, eta: {eta:.2f}')


def build_id_to_date(data_file: Path, target_file: Path) -> None:
    '''
    Build a dictionary of date to doc ids.
    '''
    doc_loader = jsonl_loader(data_file)
    with open(target_file, 'w') as f:
        for doc in tqdm(doc_loader):
            f.write(f'{doc["id"]}\t{doc["date"]}\n')


def main():
    data_dir = Path('..', 'data')
    data_file = data_dir / 'rmrb_2000-2015.jsonl'
    docs_file = data_dir / 'docs.jsonl'
    id_to_date_file = data_dir / 'id_to_date.txt'
    ES_INDEX = 'rmrb_00-15'
    ES_INDEX_INV_IDX = 'test_inv_idx'

    if not docs_file.exists():
        print("Formatting docs to " + str(docs_file))
        gen_formatted_docs(data_file, docs_file)

    print("Building inverted index...")
    build_inv_idx(data_dir, ES_INDEX_INV_IDX)     # Takes about 2.5 min
    
    print("Adding documents to Elasticsearch...")
    add_all_docs_to_es(docs_file, ES_INDEX)       # Takes about an hour

    print("Building id to date dict...")
    build_id_to_date(docs_file, id_to_date_file)  # Takes about 1 min

    print("Done preprocessing")


if __name__ == '__main__':
    main()