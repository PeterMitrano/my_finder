import boto3
import unittest
from nose.plugins.attrib import attr

from my_finder.util import core
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


def make_request(item, location):
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


class MyFinderTest(unittest.TestCase):
    @wip
    def test_set_and_get(self):
        delete_table(core.LOCAL_DB_URI)
        request = make_request("keys", "drawer")
        lambda_function.handle_event(request, None)

        result = lambda_function._skill.db_helper.getAll()
        self.assertEqual(result.value["keys"], "drawer")
