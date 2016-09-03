from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

LOGGER = 'my_finder'
LOCAL_DB_URI = 'http://localhost:8000/'
APP_ID = 'amzn1.ask.skill.4c1c3cfe-a0fd-4dbd-8b6e-29c29d9ae755'
DB_TABLE = 'my_finder'


class STATES:
    ASK_ITEM = '_ASK_ITEM'
    ASK_LOCATION = '_ASK_LOCATION'
    ASK_OR_TELL = '_ASK_OR_TELL'
    TELLING_RESPONSE = '_TELLING_RESPONSE'
    ASKING_RESPONSE = '_ASKING_RESPOSNE'
    CONFIRM_LOCATION = '_CONFIRM_LOCATION'
