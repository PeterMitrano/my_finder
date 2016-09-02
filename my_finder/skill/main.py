import logging

from my_finder import stage
from my_finder.util import core
from my_finder.util import responder
from my_finder.util import dbhelper
from my_finder.skill import ask_or_tell
from my_finder.skill import ask_item
from my_finder.skill import ask_location
from my_finder.skill import asking_response
from my_finder.skill import telling_response

states = {
    core.STATES.ASK_OR_TELL: ask_or_tell,
    core.STATES.ASK_ITEM: ask_item,
    core.STATES.ASK_LOCATION: ask_location,
    core.STATES.TELLING_RESPONSE: telling_response,
    core.STATES.ASKING_RESPONSE: asking_response
}


class Skill:
    def handle_intent(self, event, session_attributes):
        # handle simple launch request
        request_type = event['request']['type']
        if request_type == 'LaunchRequest':
            session_attributes['STATE'] = core.STATES.ASK_OR_TELL
            return responder.ask("Are you asking about an item or telling?",
                                 session_attributes)

        elif request_type == 'IntentRequest':
            intent = event['request']['intent']['name']
            slots = event['request']['intent'].get('slots', {})
            new = event['session']['new']

            if new:
                if intent == 'SetLocationIntent':
                    # collect item and or location
                    # hopefully both...
                    if 'value' in slots['Item']:
                        item = slots['Item']['value']
                    else:
                        item = None

                    if 'value' in slots['Location']:
                        location = slots['Location']['value']
                    else:
                        location = None

                    if not item and not location:
                        session_attributes['STATE'] = core.STATES.ASK_ITEM
                        return responder.ask(
                            "I didn't get an item or a location. What's the item?",
                            session_attributes)
                    if not item and location:
                        session_attributes['STATE'] = core.STATES.ASK_ITEM
                        return responder.ask("Sorry, what's the item?",
                                             session_attributes)
                    if not location and item:
                        session_attributes['STATE'] = core.STATES.ASK_LOCATION
                        return responder.ask("Sorry, what's the location?",
                                             session_attributes)

                    telling_response.add_item_location(item, location, self.db_result)
                    return responder.tell('Item is %s. Location is %s. Got it.'
                                          % (item, location))

                if intent == 'GetLocationIntent':
                    asking_response.handle(intent, slots, session_attributes, self.db_result)

            else:
                state = session_attributes['STATE']

                states['state'].handle(intent, slots, session_attributes,
                                       self.db_result)

    def handle_event(self, event, context):
        # check if we're debugging locally
        if stage.PROD:
            debug = False
            endpoint_url = None
            logging.getLogger(core.LOGGER).setLevel(logging.INFO)
        else:
            debug = True
            logging.getLogger(core.LOGGER).setLevel(logging.DEBUG)
            endpoint_url = core.LOCAL_DB_URI

        # check application id and user
        user = event['session']['user']['userId']
        request_appId = event['session']['application']['applicationId']
        if core.APP_ID != request_appId:
            raise Exception('application id %s does not match.' %
                            request_appId)

        self.db_helper = dbhelper.DBHelper(user, endpoint_url)
        self.db_helper.init_table()
        self.db_result = self.db_helper.getAll()

        if 'attributes' in event['session']:
            session_attributes = event['session']['attributes']
        else:
            session_attributes = {}

        response = self.handle_intent(event, session_attributes)

        logging.getLogger(core.LOGGER).warn(response)
        return response
