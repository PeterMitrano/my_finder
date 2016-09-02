from fuzzywuzzy import process
from nltk.corpus import wordnet

FUZZY_SIMILARITY_THRESHOLD = 65  # handles transcriptions errors

from my_finder.util import responder
from my_finder.util import core
import logging

def compare_to_known_items(item_query, known_items):
    fuzzy_item, fuzzy_similarity = process.extractOne(item_query, known_items)

    if fuzzy_similarity > FUZZY_SIMILARITY_THRESHOLD:
        # good enough, probably transcription error
        return fuzzy_item

    # go through each word and compare to another item
    most_similar = 0
    most_similar_item = None
    for known_item in known_items:
        # compare to the item we're given word-by-word
        known_item_similarity = 0

        # need to fix this... it doesn't do what I think it does.
        item_query_words = item_query.split('_')
        for word_query in item_query_words:
            best_known_word_for_query_word = None
            s = 0

            for word_known in known_item.split('_'):
                w1 = wordnet.synsets(word_query)
                w2 = wordnet.synsets(word_known)

                if len(w1) > 0 and len(w2) > 0:
                    word_similarity = w1[0].wup_similarity(w2[0])

                    if word_similarity > s:
                        s = word_similarity
                        best_known_word_for_query_word = word_known

            # now we know which word in a give known_item best matches a word in our query item
            # add this up to score the similarity of everything
            known_item_similarity += s

        avg_similarity = known_item_similarity / len(item_query_words)
        logging.getLogger(core.LOGGER).warn("%f %s %s" % (
            avg_similarity, known_item, item_query))
        if avg_similarity > most_similar:
            most_similar = avg_similarity
            most_similar_item = known_item

    if most_similar > 0.8:
        # probably refers to the same item semantically
        return most_similar_item

    return None


def get_item_location(db, item_query):
    """ item_query must have all spaces replaced with underscores"""

    if db.result.value is None:
        return None, None

    known_items = db.result.value.keys()

    known_items.remove('userId')

    if known_items is None or len(known_items) == 0:
        return None, None

    true_item = compare_to_known_items(item_query, known_items)

    if not true_item:
        # ok definitely not an item we know the location of
        # we even tried fuzzy and nltk matching.
        return None, None

    return true_item, db.result.value[true_item]


def _handle(db, item):
    # make sure we replace spaces with underscores
    item_key = item.replace(' ', '_')

    # check what we pulled from db
    true_item_key, location = get_item_location(db, item_key)

    if location is None:
        return responder.tell(
            "Sorry, you need to tell me where the item %s is." % item)

    true_item = true_item_key.replace('_', ' ')
    if true_item == item:
        return responder.tell("The Item is %s, and the location is %s" %
                              (true_item, location))
    else:
        return responder.tell(
            "Not sure where %s is. But I know %s has the location %s" %
            (item, true_item, location))


def handle(intent, slots, session_attributes, db):
    item = slots['Item']['value']
    _handle(item,db)
