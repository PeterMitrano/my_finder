import boto3
import os
import unittest
from nose.plugins.attrib import attr

from my_finder.util import core
from my_finder.util import responder
from my_finder.util import dbhelper
import lambda_function


def wip(f):
    return attr('wip')(f)


def delete_table(endpoint_url):
    """deletes the table if it already exists"""
    client = boto3.client(
        "dynamodb",
        endpoint_url=endpoint_url,
        region_name="fake_region",
        aws_access_key_id="fake_id",
        aws_secret_access_key="fake_key")
    tables = client.list_tables()['TableNames']
    if core.DB_TABLE in tables:
        client.delete_table(TableName=core.DB_TABLE)


def make_set_request(item, location):
    return {
        "version": 1.0,
        "session": {
            "new": True,
            "sessionId": "0",
            "application": {
                "applicationId": core.APP_ID
            },
            "user": {
                "userId": "test_user"
            }
        },
        "request": {
            "type": "IntentRequest",
            "intent": {
                "name": "SetLocationIntent",
                "slots": {
                    "Item": {
                        "name": "Item",
                        "value": item
                    },
                    "Location": {
                        "name": "Location",
                        "value": location
                    }
                }
            }
        }
    }


def make_item_or_location_request(item_or_location):
    return {
        "version": 1.0,
        "session": {
            "new": True,
            "sessionId": "0",
            "application": {
                "applicationId": core.APP_ID
            },
            "user": {
                "userId": "test_user"
            }
        },
        "request": {
            "type": "IntentRequest",
            "intent": {
                "name": "ItemOrLocationIntent",
                "slots": {
                    "ItemOrLocation": {
                        "name": "ItemOrLocation",
                        "value": item_or_location
                    }
                }
            }
        }
    }


def make_get_request(item):
    return {
        "version": 1.0,
        "session": {
            "new": True,
            "sessionId": "0",
            "application": {
                "applicationId": core.APP_ID
            },
            "user": {
                "userId": "test_user"
            }
        },
        "request": {
            "type": "IntentRequest",
            "intent": {
                "name": "GetLocationIntent",
                "slots": {
                    "Item": {
                        "name": "Item",
                        "value": item
                    }
                }
            }
        }
    }


def make_launch_request():
    return {
        "version": 1.0,
        "session": {
            "new": True,
            "sessionId": "0",
            "application": {
                "applicationId": core.APP_ID
            },
            "user": {
                "userId": "test_user"
            }
        },
        "request": {
            "type": "LaunchRequest"
        }
    }

class EnvTest(unittest.TestCase):
    def test_env(self):
        self.assertIn('NLTK_DATA', os.environ)

class MyFinderTest(unittest.TestCase):

    items = ["left sandal", "keys", "blue chair", "wallet", "yellow folder",
             "work shoes"]
    semantically_similar_items = ["left shoe", "remote", "blue stool", "purse",
                     "yellow notebook", "work loafers"]
    similar_items = ["love sandel", "key", "chair", "my wallet",
                     "yellow folders", "my worm shoe"]
    locations = ["dresser drawer", "bottom of closet", "backpack",
                 "under my desk"]

    def test_set_and_get(self):
        delete_table(core.LOCAL_DB_URI)

        for item, location in zip(self.items, self.locations):
            request = make_set_request(item, location)
            response_dict = lambda_function.handle_event(request, None)

            result = lambda_function._skill.db_helper.getAll()
            item_key = item.replace(' ', '_')
            self.assertEqual(result.value[item_key], location)
            self.assertIn('response', response_dict)
            self.assertTrue(response_dict['response']['shouldEndSession'])

        for item, location in zip(self.items, self.locations):
            request = make_get_request(item)
            response_dict = lambda_function.handle_event(request, None)

            self.assertTrue(responder.is_valid(response_dict))
            self.assertIn(item,
                          response_dict['response']['outputSpeech']['ssml'])
            self.assertIn(location,
                          response_dict['response']['outputSpeech']['ssml'])
            self.assertTrue(response_dict['response']['shouldEndSession'])

    def test_semantic_similarity(self):
        delete_table(core.LOCAL_DB_URI)

        for item, location in zip(self.items, self.locations):
            request = make_set_request(item, location)
            response_dict = lambda_function.handle_event(request, None)

            result = lambda_function._skill.db_helper.getAll()
            item_key = item.replace(' ', '_')
            self.assertEqual(result.value[item_key], location)
            self.assertIn('response', response_dict)
            self.assertTrue(response_dict['response']['shouldEndSession'])

        for item, location in zip(self.semantically_similar_items, self.locations):
            request = make_get_request(item)
            response_dict = lambda_function.handle_event(request, None)

            self.assertTrue(responder.is_valid(response_dict))
            self.assertIn(item,
                          response_dict['response']['outputSpeech']['ssml'])
            self.assertIn(location,
                          response_dict['response']['outputSpeech']['ssml'])
            self.assertIn('Not sure',
                          response_dict['response']['outputSpeech']['ssml'])
            self.assertTrue(response_dict['response']['shouldEndSession'])

    def test_fuzzy(self):
        delete_table(core.LOCAL_DB_URI)

        for item, location in zip(self.items, self.locations):
            request = make_set_request(item, location)
            response_dict = lambda_function.handle_event(request, None)

            result = lambda_function._skill.db_helper.getAll()
            item_key = item.replace(' ', '_')
            self.assertEqual(result.value[item_key], location)
            self.assertIn('response', response_dict)
            self.assertTrue(response_dict['response']['shouldEndSession'])

        for item, location in zip(self.similar_items, self.locations):
            request = make_get_request(item)
            response_dict = lambda_function.handle_event(request, None)

            self.assertTrue(responder.is_valid(response_dict))
            self.assertIn(item,
                          response_dict['response']['outputSpeech']['ssml'])
            self.assertIn(location,
                          response_dict['response']['outputSpeech']['ssml'])
            self.assertIn('Not sure',
                          response_dict['response']['outputSpeech']['ssml'])
            self.assertTrue(response_dict['response']['shouldEndSession'])

    def test_nonextistant_item_amongst_other_items(self):
        delete_table(core.LOCAL_DB_URI)

        for item, location in zip(self.items, self.locations):
            request = make_set_request(item, location)
            response_dict = lambda_function.handle_event(request, None)

        request = make_get_request('fake item')
        response_dict = lambda_function.handle_event(request, None)

        self.assertTrue(response_dict['response']['shouldEndSession'])
        self.assertTrue(responder.is_valid(response_dict))
        self.assertIn("you need to tell me where the item",
                      response_dict['response']['outputSpeech']['ssml'])

    def test_nonextistant_item(self):
        delete_table(core.LOCAL_DB_URI)
        request = make_get_request('fake item')
        response_dict = lambda_function.handle_event(request, None)

        self.assertTrue(response_dict['response']['shouldEndSession'])
        self.assertTrue(responder.is_valid(response_dict))
        self.assertIn("you need to tell me where the item",
                      response_dict['response']['outputSpeech']['ssml'])

    def test_missing_location(self):
        request = make_set_request('blue notebook',
                                   'first pocket of my backpack')
        request['request']['intent']['slots']['Location'].pop('value')
        response_dict = lambda_function.handle_event(request, None)

        self.assertTrue(responder.is_valid(response_dict))
        self.assertFalse(response_dict['response']['shouldEndSession'])
        self.assertIn('current_item', response_dict['sessionAttributes'])

    def test_missing_item(self):
        request = make_set_request('giant pan', 'leftmost cupboard')
        request['request']['intent']['slots']['Item'].pop('value')
        response_dict = lambda_function.handle_event(request, None)

        self.assertTrue(responder.is_valid(response_dict))
        self.assertFalse(response_dict['response']['shouldEndSession'])
        self.assertIn('current_location', response_dict['sessionAttributes'])

    def test_missing_item_and_location(self):
        request = make_set_request('giant pan', 'leftmost cupboard')
        request['request']['intent']['slots']['Item'].pop('value')
        request['request']['intent']['slots']['Location'].pop('value')
        response_dict = lambda_function.handle_event(request, None)

        self.assertTrue(responder.is_valid(response_dict))
        self.assertFalse(response_dict['response']['shouldEndSession'])

    def test_launch(self):
        delete_table(core.LOCAL_DB_URI)

        item = 'pencil case'
        location = 'bean bag chair'

        request = make_launch_request()
        response_dict = lambda_function.handle_event(request, None)
        self.assertTrue(responder.is_valid(response_dict))
        self.assertFalse(response_dict['response']['shouldEndSession'])

        # give item
        request = make_item_or_location_request(item)
        request['session']['attributes'] = response_dict['sessionAttributes']
        request['session']['new'] = False
        response_dict = lambda_function.handle_event(request, None)
        self.assertTrue(responder.is_valid(response_dict))
        self.assertFalse(response_dict['response']['shouldEndSession'])

        # give location
        request = make_item_or_location_request(location)
        request['session']['attributes'] = response_dict['sessionAttributes']
        request['session']['new'] = False
        response_dict = lambda_function.handle_event(request, None)
        self.assertTrue(responder.is_valid(response_dict))
        self.assertTrue(response_dict['response']['shouldEndSession'])

        result = lambda_function._skill.db_helper.getAll()
        item_key = item.replace(' ', '_')
        self.assertEqual(result.value[item_key], location)
        self.assertIn('response', response_dict)

    def test_accidental_item_or_location_intent_on_start(self):
        delete_table(core.LOCAL_DB_URI)
        request = make_item_or_location_request('some jibberish message')
        response_dict = lambda_function.handle_event(request, None)

        self.assertTrue(responder.is_valid(response_dict))
        self.assertFalse(response_dict['response']['shouldEndSession'])
        # this should respond gracefully so we can finish the interaction
        # successfully

        item = 'febreze bottle'
        location = 'kitchen sink'

        # give item
        request = make_item_or_location_request(item)
        request['session']['new'] = False
        request['session']['attributes'] = response_dict['sessionAttributes']
        response_dict = lambda_function.handle_event(request, None)
        self.assertTrue(responder.is_valid(response_dict))
        self.assertFalse(response_dict['response']['shouldEndSession'])

        # give location
        request = make_item_or_location_request(location)
        request['session']['attributes'] = response_dict['sessionAttributes']
        request['session']['new'] = False
        response_dict = lambda_function.handle_event(request, None)
        self.assertTrue(responder.is_valid(response_dict))
        self.assertTrue(response_dict['response']['shouldEndSession'])

        result = lambda_function._skill.db_helper.getAll()
        item_key = item.replace(' ', '_')
        self.assertEqual(result.value[item_key], location)
        self.assertIn('response', response_dict)

    def test_launch_then_get(self):
        delete_table(core.LOCAL_DB_URI)

        request = make_launch_request()
        response_dict = lambda_function.handle_event(request, None)
        self.assertTrue(responder.is_valid(response_dict))
        self.assertFalse(response_dict['response']['shouldEndSession'])

        request = make_get_request('fake item')
        request['session']['new'] = False
        response_dict = lambda_function.handle_event(request, None)

        self.assertTrue(response_dict['response']['shouldEndSession'])
        self.assertTrue(responder.is_valid(response_dict))
        self.assertIn("you need to tell me where the item",
                      response_dict['response']['outputSpeech']['ssml'])

    def test_invalid_intent(self):
        request = {
            "session": {
                "sessionId": "SessionId.414a743a-9e9e-49b7-8364-0cf5a3657a5e",
                "application": {
                    "applicationId":
                    "amzn1.ask.skill.4c1c3cfe-a0fd-4dbd-8b6e-29c29d9ae755"
                },
                "attributes": {},
                "user": {
                    "userId":
                    "amzn1.ask.account.AFP3ZWPOS2BGJR7OWJZ3DHPKMOMH5D5WJ3SSUDI6AF4AAQWYGDYL62FAK3YBDNSPFXMPWZEJGHJHH5D6WYZSSKHYXI7GCJC2YIMCLC6WPFI2JAI2OBGZGNY4NGU6MPLDHOAIY2UOJZLMYNWAPGYORHRPJUGW65FF4KFDFAHATDTI4AT5G2BYECZI6NEJX62FET7HU476KCAPDEQ"
                },
                "new": True
            },
            "request": {
                "type": "IntentRequest",
                "requestId":
                "EdwRequestId.d5f43e0f-d0e3-4db9-81bf-744a5ecc9c11",
                "locale": "en-US",
                "timestamp": "2016-08-28T17:08:12Z",
                "intent": {
                    "name": "NotAnIntent"
                }
            },
            "version": "1.0"
        }

        response_dict = lambda_function.handle_event(request, None)
        self.assertTrue(responder.is_valid(response_dict))
