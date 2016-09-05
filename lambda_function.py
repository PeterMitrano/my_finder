import json
import logging

from my_finder.skill import main
from my_finder.util import core

_skill = None


def handle_event(event, context):
    logging.getLogger(core.LOGGER).warn("==============REQUEST==============")
    logging.getLogger(core.LOGGER).warn(json.dumps(event, indent=2))

    global _skill
    _skill = main.Skill()

    response = _skill.handle_event(event, context)

    logging.getLogger(core.LOGGER).warn("==============RESPONSE==============")
    try:
        logging.getLogger(core.LOGGER).warn(json.dumps(response, indent=2))
    except TypeError:
        logging.getLogger(core.LOGGER).warn(response)

    return response
