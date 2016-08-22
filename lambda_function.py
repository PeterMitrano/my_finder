import logging

from my_finder.skill import main
from my_finder.util import core

_skill = {}


def handle_event(event, context):
    logging.getLogger(core.LOGGER).warn(event)

    global _skill
    _skill = main.Skill()
    return _skill.handle_event(event, context)
