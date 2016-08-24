import boto3
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
                "name": "ItemLocationIntent",
                "slots": {
                    "ItemLocation": {
                        "name": "ItemLocation",
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


class MyFinderTest(unittest.TestCase):

    items = ["keys", "wallet", "yellow folder", "work shoes"]
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

        for item, location in zip(self.items, self.locations):
            request = make_get_request(item)
            response_dict = lambda_function.handle_event(request, None)

            self.assertTrue(responder.is_valid(response_dict))
            self.assertIn(item,
                          response_dict['response']['outputSpeech']['ssml'])

    def test_missing_location(self):
            request = make_set_request('blue notebook', 'first pocket of my backpack')
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

        request = make_launch_request()
        response_dict = lambda_function.handle_event(request, None)
        self.assertTrue(responder.is_valid(response_dict))
        self.assertFalse(response_dict['response']['shouldEndSession'])

        # give item
        request = make_item_or_location_request('pencil case')
        request['session']['attributes'] = response_dict['sessionAttributes']
        response_dict = lambda_function.handle_event(request, None)
        self.assertTrue(responder.is_valid(response_dict))
        self.assertFalse(response_dict['response']['shouldEndSession'])

        # give location
        request = make_item_or_location_request('bean bag chair')
        request['session']['attributes'] = response_dict['sessionAttributes']
        response_dict = lambda_function.handle_event(request, None)
        self.assertTrue(responder.is_valid(response_dict))
        self.assertTrue(response_dict['response']['shouldEndSession'])
