from my_finder.util import responder
from my_finder.util import core
from my_finder.skill import telling_response

def handle(intent, slots, session_attributes, db):
    if "AMAZON" in intent:
        if intent == 'AMAZON.YesIntent':
            location = session_attributes['guessing_current_location']
        elif intent == 'AMAZON.NoIntent':
            location = session_attributes['raw_current_location']

        session_attributes['current_location'] = location
        if 'current_item' in session_attributes:
            item = session_attributes['current_item']
            return telling_response.add_item_location(item, location,
                                                      db)
        else:
            session_attributes['STATE'] = core.STATES.ASK_ITEM
            return responder.ask("Location is %s. what's the item?" % location,
                                 session_attributes)

    return responder.ask("That was a yes or no question. Say yes or no, or say quit and try again", session_attributes)

