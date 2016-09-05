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

def contains_known_location_word(location):
    for location_word in location.split(' '):
        if location_word in all_location_words:
            return True
    return False

def handle(intent, slots, session_attributes, db):
    if intent == 'ItemOrLocationIntent':
        location = slots['ItemOrLocation'].get('value', None)

        if location:
            session_attributes['current_location'] = location
            if not contains_known_location_word(location):
                # ask the user to confirm location
                session_attributes['STATE'] = core.STATES.CONFIRM_LOCATION
                return responder.ask("I heard %s. is that the right location?" % location, session_attributes)


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
