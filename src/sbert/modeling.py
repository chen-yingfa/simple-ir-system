'''For manipulating SentenceBERT'''

MODEL_NAME = 'imxly/sentence_rtb3'

def get_model():
    '''Return SentenceBERT'''
    from sentence_transformers import models, SentenceTransformer, util
    import torch
    word_embedding_model = models.Transformer(MODEL_NAME, cache_dir='../.cache')
    pooling_model = models.Pooling(word_embedding_model.get_word_embedding_dimension(),
                                pooling_mode_mean_tokens=True,
                                pooling_mode_cls_token=False,
                                pooling_mode_max_tokens=False)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f'Runinng on {device}')
    model = SentenceTransformer(modules=[word_embedding_model, pooling_model], device=device)
    return model
