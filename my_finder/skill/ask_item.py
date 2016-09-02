from my_finder.util import responder
from my_finder.util import core
from my_finder.skill import asking_response
from my_finder.skill import telling_response


def handle(intent, slots, session_attributes, db_result):
    if intent == 'ItemOrLocationIntent':
        item = slots['ItemOrLocation'].get('value', None)

        if item:
            if 'asking' in session_attributes:
                asking_response._handle(item, db_result)
            elif 'telling' in session_attributes:
                session_attributes['current_item'] = item
                if 'current_location' in session_attributes:
                    # we've got all we need
                    session_attributes['STATE'] = core.STATES.TELLING_RESPONSE
                    location = session_attributes['current_location']
                    return telling_response.add_item_location(item, location, db_result)
                else:
                    return responder.ask("What's the location?", session_attributes)
        else:
            return responder.ask("Sorry, what's the item?", session_attributes)

    responder.tell(
        "Something went wrong, and I couldn't understand your intent. Try again later")
