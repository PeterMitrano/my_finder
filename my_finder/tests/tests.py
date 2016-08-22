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


class MyFinderTest(unittest.TestCase):

    items = ["keys", "wallet", "yellow folder", "work shoes"]
    locations = ["dresser drawer", "bottom of closet", "backpack",
                 "under my desk"]

    def test_set_and_get(self):
        delete_table(core.LOCAL_DB_URI)

        for item, location in zip(self.items, self.locations):
            request = make_set_request(item, location)
            lambda_function.handle_event(request, None)

            result = lambda_function._skill.db_helper.getAll()
            item_key = item.replace(' ', '_')
            self.assertEqual(result.value[item_key], location)

        for item, location in zip(self.items, self.locations):
            request = make_get_request(item)
            response_dict = lambda_function.handle_event(request, None)

            self.assertTrue(responder.is_valid(response_dict))
            self.assertIn(item,
                          response_dict['response']['outputSpeech']['ssml'])
