'''Preprocess data and create document embeddings using SentenceBERT.'''
import sys
from pathlib import Path
import json
import pickle as pkl

from tqdm import tqdm

from modeling import get_model

sys.path.append('../preprocess')
from file_utils import jsonl_loader, save_jsonl, load_jsonl


def preprocess_data(docs):
    '''
    Preprocess original jsonl into format that is convenient for SentenceBERT.

    This executes in in a generator manner.
    
    - Discard all fields except for ID and content.
    - Concatenate each token (result of THULAC) into sentences, and concatenate
      all sentences.
    '''
    processed = []
    for doc in tqdm(docs):
        content = ''
        for para in doc['content']:
            for sent in para:
                content += ''.join(sent)
        content = content.strip()
        processed.append({
            'id': doc['id'],
            'content': content})
    return processed


def embed_sentences(sentences) -> list:
    '''Get embeddings for each sentence using SentenceBERT'''
    print('Loading model...')
    model = get_model()


    print(f'Embedding {len(sentences)} sentences...')

    # Encoding it in chunks is faster, I don't know why.
    all_embeds = []
    chunk_size = 5000
    start = 0
    while start < len(sentences):
        print(f'Encoding [{start}, {start + chunk_size})')
        sents = sentences[start:start + chunk_size]
        embeds = model.encode(sents, show_progress_bar=True)
        all_embeds += embeds
        start += chunk_size
    return all_embeds


def main():
    data_dir = Path('../../data')
    docs_file = data_dir / 'docs.jsonl'
    text_docs_file = data_dir / 'text_docs.jsonl'
    embeddings_file = data_dir / 'embeddings.pkl'

    # Preprocess tokens to natural text for SentenceBERT
    if text_docs_file.exists():
        print(f'Loading preprocessed data from {text_docs_file}')
        text_docs = jsonl_loader(text_docs_file)
    else:
        doc_loader = jsonl_loader(docs_file)
        # Turn into text docs, takes ~1 min.
        text_docs = preprocess_data(doc_loader)
        print(f'Saving preprocessed {len(text_docs)} documents to {text_docs_file}')
        save_jsonl(text_docs, text_docs_file)
    
    # Embed documents, takes ~4h on GPU.
    # SentenceTransformer accepts a list of sentences (strings).
    # We just pass the document text as sentences.
    text_docs = [d['content'] for d in text_docs]
    embeds = embed_sentences(text_docs)
    with open(embeddings_file, 'wb') as f:
        pkl.dump(embeds, f)
    print(f'Saved embeddings to {embeddings_file}')


if __name__ == '__main__':
    main()
