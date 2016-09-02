from my_finder.util import responder
from my_finder.util import core


def handle(intent, slots, session_attributes, db):
    if intent == 'AskOrTellIntent':
        ask_or_tell = slots['AskOrTell']['value']
        if ask_or_tell == 'asking':
            session_attributes['STATE'] = core.STATES.ASK_ITEM
            session_attributes['asking'] = True
            return responder.ask("What's the item?", session_attributes)
        elif ask_or_tell == 'telling':
            session_attributes['STATE'] = core.STATES.ASK_ITEM
            session_attributes['telling'] = True
            return responder.ask("What's the item?", session_attributes)

    return responder.ask("Say asking or telling", session_attributes)
