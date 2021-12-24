'''
A file a random sampling documents for analysis of LSI result.
'''

import pickle as pkl

from preprocess.file_utils import load_jsonl
from backend.utils import process_boolean_query
import random


print('Loading inverted index...')
inv_idx = pkl.load(open('../data/inv_idx_roaring.pkl', 'rb'))
print('Loading docs...')
docs = load_jsonl('../data/docs_small.jsonl')
doc_ids_small = {doc['id']: doc['file_name'] for doc in docs}

a, b, c, d = '学习', '读书', '学校', '音乐'

queries = [
    f'not（{a} or {b} or {c} or {d}）',
    f'{a} and not({b} or {c} or {d}）',
    f'{a} and {b} and not({c} or {d}）',
    f'{a} and {b} and {c} and not {d}']

final_doc_ids = []

for query in queries:
    print('Processing query:', query)
    doc_ids = process_boolean_query(query, inv_idx, len(docs))
    doc_ids = [doc_id for doc_id in doc_ids if doc_id in doc_ids_small]
    print('Found {} docs'.format(len(doc_ids)))
    sampled_doc_ids = random.sample(doc_ids, 4)
    print('Randomly select 2 docs:', sampled_doc_ids)
    final_doc_ids.append(sampled_doc_ids)
    # print([doc_ids_small[doc_id] for doc_id in doc_ids])

print(final_doc_ids)
