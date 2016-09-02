import logging

from my_finder import stage
from my_finder.util import core
from my_finder.util import responder
from my_finder.util import dbhelper

from fuzzywuzzy import process
from nltk.corpus import wordnet

FUZZY_SIMILARITY_THRESHOLD = 65  # handles transcriptions errors


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

    def compare_to_known_items(self, item_query, known_items):
        fuzzy_item, fuzzy_similarity = process.extractOne(item_query,
                                                          known_items)

        if fuzzy_similarity > FUZZY_SIMILARITY_THRESHOLD:
            # good enough, probably transcription error
            return fuzzy_item

        # go through each word and compare to another item
        most_similar = 0
        most_similar_item = None
        for known_item in known_items:
            # compare to the item we're given word-by-word
            known_item_similarity = 0

            # need to fix this... it doesn't do what I think it does.
            item_query_words = item_query.split('_')
            for word_query in item_query_words:
                best_known_word_for_query_word = None
                s = 0

                for word_known in known_item.split('_'):
                    w1 = wordnet.synsets(word_query)
                    w2 = wordnet.synsets(word_known)

                    if len(w1) > 0 and len(w2) > 0:
                        word_similarity = w1[0].wup_similarity(w2[0])

                        if word_similarity > s:
                            s = word_similarity
                            best_known_word_for_query_word = word_known

                # now we know which word in a give known_item best matches a word in our query item
                # add this up to score the similarity of everything
                known_item_similarity += s

            avg_similarity = known_item_similarity / len(item_query_words)
            logging.getLogger(core.LOGGER).warn("%f %s %s" % (
                avg_similarity, known_item, item_query))
            if avg_similarity > most_similar:
                most_similar = avg_similarity
                most_similar_item = known_item

        if most_similar > 0.8:
            # probably refers to the same item semantically
            return most_similar_item

        return None

    def get_item_location(self, item_query):
        """ item_query must have all spaces replaced with underscores"""

        if self.result.value is None:
            return None, None

        known_items = self.result.value.keys()

        known_items.remove('userId')

        if known_items is None or len(known_items) == 0:
            return None, None

        true_item = self.compare_to_known_items(item_query, known_items)

        if not true_item:
            # ok definitely not an item we know the location of
            # we even tried fuzzy and nltk matching.
            return None, None

        return true_item, self.result.value[true_item]

    def get_intent(self, item):
        # make sure we replace s_aces with underscores
        item_key = item.replace(' ', '_')

        # check what we pulled from db
        true_item_key, location = self.get_item_location(item_key)

        if location is None:
            return responder.tell(
                "Sorry, you need to tell me where the item %s is." % item)

        true_item = true_item_key.replace('_', ' ')
        if true_item == item:
            return responder.tell("The Item is %s, and the location is %s" %
                                  (true_item, location))
        else:
            return responder.tell(
                "Not sure where %s is. But I know %s has the location %s" %
                (item, true_item, location))

    def handle_intent(self, event, session_attributes):
        # handle simple launch request
        request_type = event['request']['type']
        if request_type == 'LaunchRequest':
            session_attributes['expecting_item'] = True
            session_attributes['telling'] = True
            return responder.ask("What's the item?", session_attributes)

        elif request_type == 'IntentRequest':
            intent = event['request']['intent']['name']
            slots = event['request']['intent'].get('slots', {})

            new = event['session']['new']

            if intent == 'ItemOrLocationIntent' and new:
                return responder.ask(
                    "I couldn't figure out what you meant. Are you asking about an item or telling?",
                    session_attributes)

            elif intent == 'ItemOrLocationIntent':
                if 'value' in slots['ItemOrLocation']:
                    item_or_location = slots['ItemOrLocation']['value']

                    if session_attributes.get('expecting_item', False):
                        item = item_or_location
                        if 'telling' in session_attributes:
                            session_attributes['current_item'] = item
                            session_attributes['expecting_item'] = False
                            session_attributes['expecting_location'] = True

                            if 'current_location' in session_attributes:
                                location = session_attributes[
                                    'current_location']
                                return responder.tell(
                                    "item is %s and location is %s. Got it" %
                                    (item, location))
                            else:
                                return responder.ask("What's the location?",
                                                     session_attributes)
                        elif 'asking' in session_attributes:
                            return self.get_intent(item)
                        else:
                            return responder.ask(
                                "Sorry, please say either, asking, or, telling",
                                session_attributes)

                    elif session_attributes.get('expecting_location', False):
                        location = item_or_location
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
                    session_attributes['expecting_item'] = True
                    session_attributes['telling'] = True
                    return responder.ask(
                        "I didn't get an item or a location. What's the item?",
                        session_attributes)
                if not item and location:
                    session_attributes['expecting_item'] = True
                    session_attributes['current_location'] = location
                    session_attributes['telling'] = True
                    return responder.ask("Sorry, what's the item?",
                                         session_attributes)
                if not location and item:
                    session_attributes['expecting_location'] = True
                    session_attributes['current_item'] = item
                    return responder.ask("Sorry, what's the location?",
                                         session_attributes)

                self.add_item_location(item, location)
                return responder.tell('Item is %s. Location is %s. Got it.' %
                                      (item, location))

            elif intent == 'GetLocationIntent':
                item = event['request']['intent']['slots']['Item']['value']
                return self.get_intent(item)

            elif intent == 'AskOrTellIntent':
                ask_or_tell = slots['AskOrTell']['value']
                if ask_or_tell == 'asking':
                    session_attributes['expecting_item'] = True
                    session_attributes['asking'] = True
                    return responder.ask("What's the item?",
                                         session_attributes)
                elif ask_or_tell == 'telling':
                    session_attributes['expecting_item'] = True
                    session_attributes['telling'] = True
                    return responder.ask("What's the item?",
                                         session_attributes)
                else:
                    return responder.ask(
                        "Sorry, please say either, asking, or, telling",
                        session_attributes)

            # fall through
            return responder.tell(
                "Something went wrong, and I couldn't understand your intent. Try again later")

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
