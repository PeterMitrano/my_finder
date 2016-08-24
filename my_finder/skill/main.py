import logging

from my_finder import stage
from my_finder.util import core
from my_finder.util import responder
from my_finder.util import dbhelper

from fuzzywuzzy import process

DEFINITELY_NOT_A_MATCH = 50


class Skill:
    def add_item_location(self, item, location):
        # make sure we replace spaces with underscores
        item = item.replace(' ', '_')

        # save this to our database!
        # first grab whatever was there previously so we don't lose it
        if self.result.value is not None:
            data = self.result.value
            data.pop('userId')
        else:
            data = {}
        data[item] = location

        self.db_helper.setAll(data)

    def get_item_location(self, item_key):
        """ item_key must have all spaces replaced with underscores"""

        if self.result.value is None:
            return None, None

        choices = self.result.value.keys()

        choices.remove('userId')
        true_item_key, confidence = process.extractOne(item_key, choices)

        if confidence < DEFINITELY_NOT_A_MATCH:
            return None, None

        return true_item_key, self.result.value[true_item_key]

    def handle_intent(self, event, session_attributes):
        # handle simple launch request
        request_type = event['request']['type']
        if request_type == 'LaunchRequest':
            session_attributes['expecting_item'] = True
            return responder.ask("What's the item?", session_attributes)

        elif request_type == 'IntentRequest':
            intent = event['request']['intent']['name']
            slots = event['request']['intent']['slots']

            new = event['session']['new']

            if intent == 'ItemLocationItent' and new:
                session_attributes['expecting_item'] = True
                return responder.ask("I couldn't figure out what was the item and what was location. What's the item?")

            if intent == 'ItemLocationIntent':
                if 'value' in slots['ItemLocation']:
                    item_or_location = slots['ItemLocation']['value']

                    if session_attributes['expecting_item']:
                        item = slots['ItemLocation']['value']
                        session_attributes['current_item'] = item
                        session_attributes['expecting_item'] = False
                        session_attributes['expecting_location'] = True
                        return responder.ask("What's the location?",
                                             session_attributes)

                    elif session_attributes['expecting_location']:
                        location = slots['ItemLocation']['value']
                        session_attributes['current_location'] = location
                        item = session_attributes['current_item']
                        self.add_item_location(item, location)
                        return responder.tell(
                            "item is %s and location is %s. Got it" %
                            (item, location))

                    else:
                        raise RuntimeError(
                            'neither item not location expected')
                else:
                    if session_attributes['expecting_item']:
                        return responder.ask("Sorry, what's the item?",
                                             session_attributes)

                    elif session_attributes['expecting_location']:
                        return responder.ask("Sorry, what's the location?",
                                             session_attributes)

            elif intent == 'SetLocationIntent':
                if 'value' in slots['Item']:
                    item = slots['Item']['value']
                else:
                    item = None

                if 'value' in slots['Location']:
                    location = slots['Location']['value']
                else:
                    location = None

                if not item and not location:
                    return responder.ask(
                        "I didn't get an item or a location. What's the item?",
                        session_attributes)
                if not item and location:
                    session_attributes['current_location'] = location
                    return responder.ask("Sorry, what's the item?",
                                         session_attributes)
                if not location and item:
                    session_attributes['current_item'] = item
                    return responder.ask("Sorry, what's the location?",
                                         session_attributes)

                self.add_item_location(item, location)
                return responder.tell('Item is %s. Location is %s. Got it.' %
                                      (item, location))

            elif intent == 'GetLocationIntent':
                item = event['request']['intent']['slots']['Item']['value']

                # make sure we replace s_aces with underscores
                item_key = item.replace(' ', '_')

                # check what we pulled from db
                true_item_key, location = self.get_item_location(item_key)

                if location is None:
                    return responder.tell(
                        "Sorry, you need to tell me where the item %s is." % item)

                true_item = true_item_key.replace('_', ' ')
                if true_item == item:
                    return responder.tell("The Item is %s, and the location is %s"
                                          % (true_item, location))
                else:
                    return responder.tell("Not sure where %s is. But I know %s has the location %s"
                                      % (item, true_item, location))

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
        self.result = self.db_helper.getAll()

        if 'attributes' in event['session']:
            session_attributes = event['session']['attributes']
        else:
            session_attributes = {}

        response = self.handle_intent(event, session_attributes)

        logging.getLogger(core.LOGGER).warn(response)
        return response
