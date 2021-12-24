from elasticsearch import Elasticsearch
from pyroaring import BitMap


es_index = 'rmrb_00-15'
es_index_date = 'rmrb_00-15-date'  # An index for dates for faster date lookup


def get_docs_iter(ids: [int], min_index: int, max_index: int, min_date: str, 
             max_date: str, sort_order: str='desc') -> [dict]:
    '''
    Load a list of docs from Elasticsearch database iteratively.
    Fetch a chunk of documents from database every iteration, and check if the
    total number of documents satisfying the filter conditions are enough for a page.
    '''
    assert ids is not None
    if len(ids) == 0:
        return []
    es = Elasticsearch()
    req_body = {
        'query': {
            'range': {
                'date': {
                    'gte': min_date,
                    'lte': max_date
                }
            }
        },
        'sort': [
            {
                'date': {
                    'order': sort_order
                }
            }
        ],
        'from': min_index,
        'size': max_index - min_index,
    }
    res = es.search(index=es_index, body=req_body)
    docs = []
    for doc in res['hits']['hits']:
        docs.append(doc['_source'])
    return docs


def get_docs(ids: [int]) -> [dict]:
    '''
    Load a list of docs from Elasticsearch database.
    
    ids: doc ids'''
    assert ids is not None
    if len(ids) == 0:
        return []
    es = Elasticsearch()
    res = es.mget(index=es_index, body={'ids': ids})
    docs = res['docs']
    found_docs = []
    # TODO: Warn about unfound docs?
    for doc in docs:
        if doc['found']:
            found_docs.append(doc['_source'])
    return found_docs


def get_dates(ids: [int]) -> [str]:
    '''Given a list of doc ids, return a list of corresponding dates.'''
    assert ids is not None
    if len(ids) == 0:
        return []
    es = Elasticsearch()
    res = es.mget(index=es_index_date, body={'ids': ids})
    dates = res['docs']
    found_dates = []
    for date in dates:
        if date['found']:
            found_dates.append(date['_source']['date'])
    return found_dates


def process_boolean_query(bool_expr: str, postings_lists: {str: BitMap}, 
                          num_docs: int) -> BitMap:
    '''Given a string of boolean query, compute the resulting postings list'''

    # 用两个栈来实现表达式计算
    op_stack = []
    set_stack = []

    # 预处理表达式：转成大写，全角转半角，操作符两端加空格
    bool_expr = bool_expr.upper()
    bool_expr = bool_expr.replace('（', '(')
    bool_expr = bool_expr.replace('）', ')')
    bool_expr = bool_expr.replace('AND', '&')
    bool_expr = bool_expr.replace('OR', '|')
    bool_expr = bool_expr.replace('NOT', '!')
    for op in ['&', '|', '!', '(', ')']:
        bool_expr = bool_expr.replace(op, ' ' + op + ' ')

    print('Processed:', bool_expr)

    tokens = bool_expr.split()

    print('Tokens:', tokens)

    def collapse_once():
        '''Pop an operator from operator stack, pop operand sets, then execute 
        and push the result'''
        op = op_stack.pop()
        res = None
        if op == '&':
            a = set_stack.pop()
            b = set_stack.pop()
            res = a & b
        elif op == '|':
            a = set_stack.pop()
            b = set_stack.pop()
            res = a | b
        elif op == '!':
            a = set_stack.pop()
            res = a.flip(0, num_docs)
        else:
            raise ValueError('Invalid operator:', op)
        set_stack.append(res)

    # 高优先级会被先处理
    OP_PRIORITY = {'(': -1, '|': 0, '&': 1, '!': 2}

    for token in tokens:
        if token == '(':
            op_stack.append(token)
        elif token == ')':
            # Pop all operators until '('
            while op_stack[-1] != '(':
                collapse_once()
            op_stack.pop()
        elif token in OP_PRIORITY:
            # Pop operators with higher priority
            while op_stack and OP_PRIORITY[op_stack[-1]] >= OP_PRIORITY[token]:
                collapse_once()
            op_stack.append(token)
        else:
            # token is a term
            if token in postings_lists:
                set_stack.append(postings_lists[token])
            else:
                set_stack.append(BitMap())
    while op_stack:
        collapse_once()
    if len(set_stack) != 1:
        raise ValueError('Invalid boolean query:', bool_expr)
    return set_stack[-1]
