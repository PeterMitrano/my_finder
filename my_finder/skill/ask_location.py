import sys
import pickle

from my_finder.util import responder
from my_finder.util import core
from my_finder.skill import telling_response

filename = sys.path[0] + '/my_finder/util/location_words.pkl'
f = open(filename, 'rb')
location_words = pickle.load(f)
f.close()

def handle(intent, slots, session_attributes, db):
    if intent == 'ItemOrLocationIntent':
        location = slots['ItemOrLocation'].get('value', None)

        if location:
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
