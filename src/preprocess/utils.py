def split_tokens(raw_tokens: [str]) -> ([str], [str]):
    '''Return (tokens, pos_tags)'''
    tokens, pos_tags = [], []
    for t in raw_tokens:
        sep = t.rindex('_')
        token, pos_tag = t[:sep], t[sep + 1:]
        tokens.append(token)
        pos_tags.append(pos_tag)
    return tokens, pos_tags 


def format_doc(doc: dict) -> dict:
    content = doc['content']
    formatted_content = []
    formatted_pos_tags = []
    for para in content:
        formatted_content.append([]) # New paragraph
        formatted_pos_tags.append([])
        for sent in para:
            raw_tokens = sent.split()
            tokens, pos_tags = split_tokens(raw_tokens)
            formatted_content[-1].append(tokens)       # new sentence
            formatted_pos_tags[-1].append(pos_tags)
    formatted_doc = {}
    copy_keys = ['title', 'author', 'date', 'column', 'file_name']
    for key in copy_keys:
        formatted_doc[key] = doc[key]
    formatted_doc['content'] = formatted_content
    formatted_doc['pos_tags'] = formatted_pos_tags
    return formatted_doc
