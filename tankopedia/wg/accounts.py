from collections import namedtuple
import json

import requests

from config import WG_APP_ID
from wg.constants import HOST

SEARCH_ACCOUNT = '{host}/wotb/account/list/?application_id={app_id}'.format(host=HOST, app_id=WG_APP_ID)
GET_ACCOUNT = '{host}/wotb/account/info/?application_id={app_id}'.format(host=HOST, app_id=WG_APP_ID)


Account = namedtuple('Account', ['nickname', 'account_id'])
AccountData = namedtuple('AccountData', [
    'nickname',
    'last_battle_time',
    'private',
    'updated_at',
    'created_at',
    'account_id',
    'statistics'])


class Player(object):
    def __init__(self, data):
        self.raw = AccountData(**data)

    def win_rate(self):
        battles = self.raw.statistics['all']['battles']
        if battles:
            return self.raw.statistics['all']['wins']/battles

        return 0

    def win_rate_str(self):
        win_rate = round(100*self.win_rate(), 2)
        return '{:.2f}%'.format(win_rate)


class WOTBAccounts(object):
    def __init__(self):
        pass

    def fuzzy_search(self, name, accurate=False):
        if len(name) <= 3:
            return []

        response = requests.get(SEARCH_ACCOUNT + '&search={}'.format(name))
        if not response.ok:
            return []

        data = json.loads(response.content)
        if 'data' not in data:
            return []

        accounts = [Account(**acc) for acc in data['data']]
        if accurate:
            accurate_list = [acc for acc in accounts if acc.nickname.lower() == name.lower()]
            if accurate_list:
                accounts = accurate_list

        return accounts

    def fuzzy_search_and_get_info(self, name):
        return self.get_player_info_for([acc.account_id for acc in self.fuzzy_search(name)])

    def get_player_info_by_name(self, name, accurate=False):
        accounts = self.fuzzy_search(name, accurate=accurate)
        if len(accounts) > 0:
            return self.get_player_info_for([acc.account_id for acc in accounts])

        return None

    def get_player_info_for(self, account_ids):
        if not account_ids:
            return None

        ids = account_ids
        if isinstance(account_ids, list):
            ids = ','.join(str(i) for i in account_ids)

        response = requests.get(GET_ACCOUNT + '&account_id={}'.format(ids))
        if response.ok:
            data = json.loads(response.content)['data']

            if isinstance(account_ids, list):
                return [Player(data[str(account_id)]) for account_id in account_ids]
            else:
                return Player(data[str(account_ids)])

        return None
