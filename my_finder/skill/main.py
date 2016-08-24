import logging

from my_finder import stage
from my_finder.util import core
from my_finder.util import responder
from my_finder.util import dbhelper


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

    def handle_intent(self, event, session_attributes):
        # handle simple launch request
        request_type = event['request']['type']
        if request_type == 'LaunchRequest':
            session_attributes['expecting_item'] = True
            return responder.ask("What's the item?", session_attributes)

        elif request_type == 'IntentRequest':
            intent = event['request']['intent']['name']
            slots = event['request']['intent']['slots']

            if intent == 'ItemLocationIntent':
                if 'value' in slots['ItemLocation']:
                    item_or_location = slots['ItemLocation']['value']

                    if session_attributes['expecting_item']:
                        item = slots['ItemLocation']['value']
                        session_attributes['current_item'] = item
                        session_attributes['expecting_item'] = False
                        session_attributes['expecting_location'] = True
                        return responder.ask("What's the location?", session_attributes)

                    elif session_attributes['expecting_location']:
                        location = slots['ItemLocation']['value']
                        session_attributes['current_location'] = location
                        item = session_attributes['current_item']
                        self.add_item_location(item, location)
                        return responder.tell("item is %s and location is %s. Got it" % (item, location))

                    else:
                        raise RuntimeError('neither item not location expected')
                else:
                    if session_attributes['expecting_item']:
                        return responder.ask("Sorry, what's the item?", session_attributes)

                    elif session_attributes['expecting_location']:
                        return responder.ask("Sorry, what's the location?", session_attributes)

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
                    return responder.ask("I didn't get an item or a location. What's the item?", session_attributes)
                if not item and location:
                    session_attributes['current_location'] = location
                    return responder.ask("Sorry, what's the item?", session_attributes)
                if not location and item:
                    session_attributes['current_item'] = item
                    return responder.ask("Sorry, what's the location?", session_attributes)

                self.add_item_location(item, location)
                return responder.tell('Item is %s. Location is %s. Got it.' % (item, location))

            elif intent == 'GetLocationIntent':
                item = event['request']['intent']['slots']['Item']['value']

                # make sure we replace spaces with underscores
                item_key = item.replace(' ', '_')

                if self.result.value is None or item_key not in self.result.value:
                    return responder.tell(
                        "Sorry, you need to tell me where that item is first.")


                # check what we pulled from db
                location = self.result.value[item_key]

                return responder.tell("The Item is %s, and the location is %s"
                                      % (item, location))

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
