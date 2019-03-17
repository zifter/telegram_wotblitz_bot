from functools import lru_cache
from os.path import realpath, join, dirname
import json


PROJECT_PATH = realpath(join(dirname(__file__), './../'))


@lru_cache(maxsize=1)
def get_config():
    with open(join(PROJECT_PATH, 'config.json'), 'r') as f:
        return json.load(f)


def _value(key):
    return get_config()[key]


TELEGRAM_TOKEN = _value('TELEGRAM_TOKEN')
WG_APP_ID = _value('WG_APP_ID')
