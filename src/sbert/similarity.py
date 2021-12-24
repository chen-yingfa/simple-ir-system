import pickle as pkl


class Similarity:
    def __init__(self, corpus_embeds_file):
        self.corpus_embeds = load_corpus_embeds(corpus_embeds_file)

    def load_corpus_embeds(self, corpus_embeds_file):
        return pkl.load(open(corpus_embeds_file, 'rb'))