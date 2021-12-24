from pathlib import Path
import sys
import pickle as pkl

import torch 

from modeling import get_model
from sentence_transformers import util

sys.path.append('../preprocess')
from file_utils import load_jsonl


def main():
    print('Loading model... (takes ~30s)')
    model = get_model()

    print('Loading data...')
    data_dir = Path('../../data')
    corpus_file = data_dir / 'text_docs_1000.jsonl'
    corpus_embeds_file = data_dir / 'embeddings_1000.pkl'
    corpus = load_jsonl(corpus_file)
    corpus_embeds = pkl.load(open(corpus_embeds_file, 'rb'))

    # Test data
    queries = [
        '太原地铁',
        '清华大学',
        '姚期智，图灵奖',
        '诺贝尔奖',
        '计算机',
    ]

    print('Getting result...')
    for i in range(3):
        query = corpus[i]['content']
        query_embed = corpus_embeds[i]
        cos_scores = util.cos_sim(query_embed, corpus_embeds)[0]
        top_results = torch.topk(cos_scores, k=5)

        print("\n\n======================\n\n")
        print("Query:", query)
        print("\nTop 5 most similar sentences in corpus:")

        for score, idx in zip(top_results[0], top_results[1]):
            print(corpus[idx], "(Score: {:.4f})".format(score))


if __name__ == '__main__':
    main()
