from my_finder.util import responder
from my_finder.util import core
from my_finder.skill import telling_response


def handle(intent, slots, session_attributes, db_result):
    if intent == 'ItemOrLocationIntent':
        location = slots['ItemOrLocation'].get('value', None)

        if location:
            if 'telling' in session_attributes:
                if 'current_item' in session_attributes:
                    item = session_attributes['current_item']
                    return telling_response.add_item_location(item, location, db_result)
                else:
                    session_attributes['STATE'] = core.STATES.ASK_ITEM
                    return responder.ask("what's the item again?",
                                         session_attributes)

        else:
            return responder.ask("Sorry, what's the location?",
                                 session_attributes)

    # fall through
    return responder.tell(
        "Something went wrong, and I couldn't understand your intent. Try again later")
