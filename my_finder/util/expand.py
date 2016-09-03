from nltk.corpus import wordnet

def combined_hyponyms(words):
    h = set()
    for word in words:
        h = h.union(all_hyponyms(word))

    return h

def all_hyponyms(word):
    synset = wordnet.synsets(word)[0]
    hyponyms = set(synset.lemma_names())
    hyponyms = expand_synset(hyponyms, synset)
    return hyponyms

def expand_synset(h, synset):
    """takes a synset, adds all synonyms, then does so recursively for all hyponyms"""
    for hyponym in synset.hyponyms():
        h = h.union(set(hyponym.lemma_names()))
        h = expand_synset(h, hyponym)

    return h

if __name__ == "__main__":
    all_hyponyms('dog')


