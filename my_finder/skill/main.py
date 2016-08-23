import logging

from my_finder import stage
from my_finder.util import core
from my_finder.util import responder
from my_finder.util import dbhelper


class Skill:
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
        result = self.db_helper.getAll()

        # handle simple launch request
        request_type = event['request']['type']
        if request_type == 'LaunchRequest':
            return responder.ask('Try saying, tell my finder I put my frisbee is in the suitecase under my bed')

        elif request_type == 'IntentRequest':

            intent = event['request']['intent']['name']

            if intent == 'SetLocationIntent':
                item = event['request']['intent']['slots']['Item']['value']
                location = event['request']['intent']['slots']['Location'][
                    'value']

                # make sure we replace spaces with underscores
                item = item.replace(' ', '_')

                # save this to our database!
                # first grab whatever was there previously so we don't lose it
                if result.value is not None:
                    data = result.value
                    data.pop('userId')
                else:
                    data = {}
                data[item] = location

                self.db_helper.setAll(data)

                return responder.tell('%s is %s. Got it.' % (item, location))

            if intent == 'GetLocationIntent':
                if result.value is None:
                    return responder.tell(
                        "Sorry, you need to tell me where that item is first.")

                item = event['request']['intent']['slots']['Item']['value']

                # make sure we replace spaces with underscores
                item_key = item.replace(' ', '_')

                # check what we pulled from db
                location = result.value[item_key]

                return responder.tell("The Item is %s, and the location is %s"
                                      % (item, location))
