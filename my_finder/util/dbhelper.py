import boto3
from collections import namedtuple
import logging

from my_finder.util import core

logging.getLogger('boto3').setLevel(logging.WARNING)
logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('nose').setLevel(logging.WARNING)


class DBHelper:
    def __init__(self, user, endpoint_url):
        self.endpoint_url = endpoint_url
        self.user = user
        if endpoint_url:
            self.local = True
            self.dynamodb = boto3.resource(
                "dynamodb",
                endpoint_url=endpoint_url,
                region_name="fake_region",
                aws_access_key_id="fake_id",
                aws_secret_access_key="fake_key")
        else:
            self.local = False
            self.dynamodb = boto3.resource("dynamodb")

    def init_table(self):
        # check if table exists, and if it doesn't then create it
        # and wait for it to be ready

        tables = [table.name for table in self.dynamodb.tables.all()]
        if core.DB_TABLE not in tables:
            if self.local:
                self.table = self.dynamodb.create_table(
                    TableName=core.DB_TABLE,
                    KeySchema=[
                        {
                            'AttributeName': 'userId',
                            'KeyType': 'HASH'
                        },
                    ],
                    AttributeDefinitions=[
                        {
                            'AttributeName': 'userId',
                            'AttributeType': 'S'
                        },
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 1,
                        'WriteCapacityUnits': 1
                    })
                self.table.wait_until_exists()
            else:
                raise Exception(
                    "Table doesn't exist in production. Skipping create.")

        # at this point we know the table is there
        self.table = self.dynamodb.Table(core.DB_TABLE)

    def getAll(self):
        """get all values of attribute, return tuple of (truthy error, value dict, error speech"""
        result = namedtuple('result', ['err', 'value', 'error_speech'])
        key = {'userId': self.user}

        if not self.table:
            logging.getLogger(core.LOGGER).warn("Did you call init_table?")
            return result(
                True, None,
                'I cannot reach my database right now. I would try again later.')

        response = self.table.get_item(Key=key)

        try:
            if response['ResponseMetadata']['HTTPStatusCode'] != 200:
                return result(
                    True, None,
                    'I cannot reach my database right now. I would try again later.')

            if "Item" not in response:
                # this is fine, it just means we don't have this user yet
                # so we mark that they've used the skill and put them in the db
                logging.getLogger(core.LOGGER).info("Adding new user: %s" %
                                                    self.user)
                item = { 'userId': self.user, }
                self.table.put_item(Item=item)

                # this is an not error, so you better check for None as value
                return result(False, None,
                              'This must be your first time. Welcome!')

            return result(False, response['Item'], None)
        except KeyError:
            return result(True, None,
                          "I've forgotten where we were. Please start over")

    def setAll(self, attributes):
        """ Set many attributes of an item return tuple of (truthy error, error speech)

        This will also create the user if they don't exist
        """
        result = namedtuple('result', ['err', 'error_speech'])
        item_key = {'userId': self.user}

        # ok so this badass python formats the update expression
        # don't fight it--the tests show it works. Just learn to love it
        updateExpr = 'SET '
        exprAttributeValues = {}
        exprAttributeNames = {}
        for key in attributes:
            expr_val_key = ':%s' % key
            exprAttributeValues[expr_val_key] = attributes[key]
            expr_name_key = '#_%s' % key
            exprAttributeNames[expr_name_key] = key
            updateExpr += '%s = :%s,' % (expr_name_key, key)

        updateExpr = updateExpr[:-1]  #strip trailing comma

        if not self.table:
            logging.getLogger(core.LOGGER).warn("Did you call init_table?")
            return result(
                True,
                'I cannot reach my database right now. I would try again later.')

        response = self.table.update_item(
            Key=item_key,
            UpdateExpression=updateExpr,
            ExpressionAttributeNames=exprAttributeNames,
            ExpressionAttributeValues=exprAttributeValues)

        try:
            if response['ResponseMetadata']['HTTPStatusCode'] != 200:
                return result(
                    True,
                    'I cannot reach my database right now. I would try again later.')

            if "Item" not in response:
                # this isn't actually an error
                return result(False, 'This must be your first time. Welcome!')

            return result(False, None)
        except KeyError:
            return result(True, 'Keyerror')
