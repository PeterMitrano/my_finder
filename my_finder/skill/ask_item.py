from my_finder.util import responder
from my_finder.util import core
from my_finder.skill import asking_response
from my_finder.skill import telling_response


def handle(intent, slots, session_attributes, db):
    if intent == 'ItemOrLocationIntent':
        item = slots['ItemOrLocation'].get('value', None)

        if item:
            if 'asking' in session_attributes:
                return asking_response._handle(item, db)
            elif 'telling' in session_attributes:
                session_attributes['current_item'] = item
                if 'current_location' in session_attributes:
                    # we've got all we need
                    session_attributes['STATE'] = core.STATES.TELLING_RESPONSE
                    location = session_attributes['current_location']
                    return telling_response.add_item_location(item, location,
                                                              db)
                else:
                    session_attributes['STATE'] = core.STATES.ASK_LOCATION
                    return responder.ask("What's the location?",
                                         session_attributes)
        else:
            return responder.ask("Sorry, what's the item?", session_attributes)

    return responder.tell(
        "Something went wrong. I expected you to tell me which item you'e asking about.")
