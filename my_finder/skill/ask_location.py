import logging
import sys
import pickle
from fuzzywuzzy import process
from fuzzywuzzy import fuzz
from nltk.corpus import wordnet

from my_finder.util import responder
from my_finder.util import core
from my_finder.skill import telling_response

filename = sys.path[0] + '/my_finder/util/location_words.pkl'
f = open(filename, 'rb')
all_location_words = pickle.load(f)
f.close()

FUZZY_SIMILARITY_THRESHOLD = 50.0 # scale from 0 to 100

def ask_to_modify_location(location):
    new_location_words = []
    for location_word in location.split(' '):

        fuzzy_location_word, fuzzy_similarity = process.extractOne(location_word, all_location_words, scorer=fuzz.ratio)
        logging.getLogger(core.LOGGER).info("%s %s %f", location_word, fuzzy_location_word, fuzzy_similarity)

        # get part of speech
        is_adjective = len(wordnet.synsets(location_word, wordnet.ADJ)) > 0

        #ignore adjectives, or small words like of, or, an, ect...
        if is_adjective or len(location_word) <= 2:
           new_location_words.append(location_word)
        elif fuzzy_similarity < FUZZY_SIMILARITY_THRESHOLD:
           new_location_words.append(location_word)
        else:
           # suggest this as a replacement
           new_location_words.append(fuzzy_location_word)

    new_location = ' '.join(new_location_words)

    if new_location != location:
        return "Did you mean %s?" % new_location, new_location

    return None, None

def handle(intent, slots, session_attributes, db):
    if intent == 'ItemOrLocationIntent':
        location = slots['ItemOrLocation'].get('value', None)

        if location:
            speech, new_location = ask_to_modify_location(location)

            if speech:
                # ask the user if they want to accept our suggestion for location
                session_attributes['STATE'] = core.STATES.CONFIRM_LOCATION
                session_attributes['raw_current_location'] = location
                session_attributes['guessing_current_location'] = new_location
                return responder.ask(speech, session_attributes)


            if 'telling' in session_attributes:
                if 'current_item' in session_attributes:
                    item = session_attributes['current_item']
                    return telling_response.add_item_location(item, location,
                                                              db)
                else:
                    session_attributes['STATE'] = core.STATES.ASK_ITEM
                    return responder.ask("what's the item again?",
                                         session_attributes)
        else:
            return responder.ask("Sorry, what's the location?",
                                 session_attributes)

    # fall through
    return responder.ask(
        "Hmm. I expected you to tell me a location. Say the location now, or say quit to start over.",
        session_attributes)
