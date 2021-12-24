import time
import pickle as pkl
from pyroaring import BitMap
from flask import Flask, render_template, g, request, url_for, jsonify
from flask_cors import CORS, cross_origin
from elasticsearch import Elasticsearch

import utils

app = Flask(__name__)
CORS(app, support_credentials=True)

es_index = 'rmrb_00-15'
es_index_date = 'rmrb_00-15-date'
file_inv_idx = '../../data/inv_idx_roaring.pkl'
id_to_date: [int] = []   # Store a map from doc id to date for faster date lookup
NUM_DOCS = None


def get_inv_idx():
    '''Load inverted index, add it to g if not added'''
    if 'inv_idx' not in g:
        print('Loading inverted index...')
        with open(file_inv_idx, 'rb') as f:
            g.inv_idx = pkl.load(f)
    return g.inv_idx


def get_id_to_date():
    '''Get all dates in the index'''
    if 'dates' not in g:
        print('Loading dates...')
        FILE_ID_TO_DATE = '../../data/id_to_date.txt'
        id_to_date = {}
        with open(FILE_ID_TO_DATE, 'r') as f:
            for line in f:
                line = line.strip().split('\t')
                id_to_date[int(line[0])] = line[1]
        g.id_to_date = id_to_date
        print(f'Got {len(g.id_to_date)} dates')
    return g.id_to_date


# Initialize global variables
start_time = time.time()
print('Initializing global variables...')
with app.app_context():
    # 将全局变量加到`g`中。
    NUM_DOCS = 612031
    inv_idx = get_inv_idx()
    id_to_date = get_id_to_date()

elapsed_time = time.time() - start_time
print('Done initializing global variables.')
print(f'Elapsed time: {elapsed_time}')


@app.route('/search')
@cross_origin(supports_credentials=True)
def search_bool_expr():
    '''Parse boolean query expression and merge postings lists'''

    # Parse query
    expr = request.args.get('query', None)
    sort_by = request.args.get('sort_by', 'date')
    sort_order = request.args.get('sort_order', 'desc')
    min_index = request.args.get('min_index', 0)
    max_index = request.args.get('max_index', None)
    min_date = request.args.get('min_date', None)
    max_date = request.args.get('max_date', None)
    if min_index is not None:
        min_index = int(min_index)
    if max_index is not None:
        max_index = int(max_index)

    # 解析并处理布尔表达式
    print(f'Searching for {expr}')
    try:
        # NOTE: `process_boolean_query` returns a pyroaring `BitMap`
        postings_list = utils.process_boolean_query(expr, inv_idx, NUM_DOCS)
    except:
        # 表达式有问题，返回 error status
        result = {
            'status': 'error',
            'message': 'invalid query'
        }
        return jsonify(result)

    # 过滤和排序
    filtered = postings_list
    if sort_by == 'date':
        # 从数据库获取所有 date
        if min_date is not None:
            filtered = [x for x in filtered if id_to_date[x] >= min_date]
        if max_date is not None:
            filtered = [x for x in filtered if id_to_date[x] <= max_date]
        filtered = sorted(filtered, key=lambda x: id_to_date[x],
                          reverse=sort_order == 'desc')
    else:
        raise ValueError(f'Invalid sort_by: {sort_by}')


    filtered = list(filtered)  # Convert to list to make it JSON serializable
    total_count = len(filtered)
    print('Length of final postings list:', total_count)
    
    # 只从数据库获取指定范围的文档
    print(f'Fetching first documents in range [{min_index}, {max_index})')
    filtered = filtered[min_index:max_index]
    try:
        docs = utils.get_docs(filtered)
    except:
        # 无法从数据库获取文档，返回 error status
        result = {
            'status': 'error',
            'message': 'datebase error'
        }
        return jsonify(result)
        

    # 返回结果
    result = {
        'status': 'success',
        'docs': docs,
        'total': total_count
    }
    return jsonify(result)


if __name__ == '__main__':
    app.run()