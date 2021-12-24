# coding: utf8
import json


def load_jsonl(fname: str, count=None) -> list:
    '''Load `count` instances from jsonl file'''
    data = []
    with open(fname, 'r', encoding='utf8') as f:
        if count is None:
            for line in f:
                data.append(json.loads(line))
        else:
            for i in range(count):
                line = next(f)
                data.append(json.loads(line))
    return data


def save_jsonl(data: list, fname: str) -> None:
    with open(fname, 'w', encoding='utf8') as f:
        for d in data:
            f.write(json.dumps(d, ensure_ascii=False))
            f.write('\n')


def jsonl_loader(fname: str):
    '''Return the generator that yields lines one by one from jsonl'''
    f = open(fname, 'r', encoding='utf8')
    for line in f:
        data = json.loads(line)
        yield data


def save_txt_line(lines: [str], fname: str) -> None:
    '''Save list of str to file as ascii where each element is one line'''
    with open(fname, 'w', encoding='utf8') as f:
        for s in lines:
            f.write(s)
            f.write('\n')
    

def load_txt_line(fname: str) -> [str]:
    '''Load ascii file, and return each line as element in list'''
    lines = []
    with open(fname, 'r', encoding='utf8') as f:
        for line in f:
            lines.append(line.strip())
    return lines
