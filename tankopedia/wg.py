# coding=utf8
from functools import lru_cache
import logging
import utils

import search
import hashlib
import json
import requests
import decimal

from config import WG_APP_ID

HOST = 'https://api.wotblitz.ru'

GET_ALL_VEHICLE_URL = '{host}/wotb/encyclopedia/vehicles/' \
                      '?application_id={app_id}' \
                      '&fields=name,images,nation,is_premium,tier,type,cost' \
                      '&language=en'.format(host=HOST, app_id=WG_APP_ID)
GET_LOC_VEHICLE_URL = '{host}/wotb/encyclopedia/vehicles/' \
                      '?application_id={app_id}' \
                      '&fields=name,description' \
                      '&language=ru'.format(host=HOST, app_id=WG_APP_ID)

NATION = {
    'ussr': u'СССР',
    'germany': u'Германия',
    'usa': u'США',
    'china': u'Китай',
    'france': u'Франция',
    'uk': u'Великобритания',
    'japan': u'Япония',
    'european': u'Сборная Европы',
    'other': u'BLITZ',
    'none': u'',
}

TYPE = {
    'lightTank': u'ЛТ',
    'mediumTank': u'CT',
    'heavyTank': u'TT',
    'AT-SPG': u'ПТ-САУ',
    'SPG': u'ПТ',
}


def prepare_for_search(value):
    return value.replace('.', '').replace('-', '').lower()


class VehicleData(object):
    def __init__(self, json_data, localized_data):
        self.name = json_data['name']
        self.localized_names = [data['name'] for data in localized_data.values()]
        self.search_names = [prepare_for_search(name) for name in self.localized_names]
        self.image_preview = json_data['images']['preview']
        self.image_normal = json_data['images']['normal']
        self.uuid = hashlib.md5(self.name.encode('utf-8')).hexdigest(),
        self.nation = json_data['nation']
        self.is_premium = json_data['is_premium']
        self.tier = json_data['tier']
        self.type = json_data['type']
        cost = json_data['cost']
        self.cost_gold = cost['price_gold'] if cost  else None
        self.cost_credit = cost['price_credit'] if cost else None
        self.description = localized_data['ru']['description']  # TODO
        self.tankopedia_url = 'http://wiki.wargaming.net/ru/Blitz:{}'.format('MS-1')

    def __repr__(self):
        return self.name

    def get_loc_name(self):
        return self.localized_names[1]

    def get_loc_nation(self):
        return NATION.get(self.nation, self.nation)

    def get_loc_type(self):
        return TYPE.get(self.type, self.type)

    def get_loc_cost(self):
        if self.cost_gold:
            return u'{} голды'.format(utils.moneyfmt(self.cost_gold, sep=' '))
        elif self.cost_credit:
            return u'{} серебра'.format(utils.moneyfmt(self.cost_credit, sep=' '))
        return u'0'


class WOTBTankopedia(object):
    def __init__(self):
        self.vehicles = get_all_data()

    def search(self, query):
        result = []
        search_query = prepare_for_search(query)
        for data in self.vehicles.values():
            for name in data.search_names:
                ratio = search.ratio(search_query, name)

                if ratio > 0:
                    result.append((ratio, data))

        result = sorted(result, key=lambda v: v[0], reverse=True)
        result = [value[1] for value in result[0:5] if value[0] > 0.5]
        logging.info(result)
        return result


def get_all_data():
    response_all = requests.get(GET_ALL_VEHICLE_URL)
    assert response_all.ok == True
    content_all = json.loads(response_all.content)

    response_loc = requests.get(GET_LOC_VEHICLE_URL)
    assert response_loc.ok == True
    content_loc = json.loads(response_loc.content)

    data = dict()
    for k, v in content_all['data'].items():
        loc_data = content_loc['data'][k]
        localized_data = {
            'en': v,
            'ru': loc_data,  # TODO Other localizations
        }
        d = VehicleData(v, localized_data)
        data[d.name] = d

    return data


@lru_cache(maxsize=1)
def get_vehicle_names():
    return get_all_data().keys()


def get_vehicle_data(name):
    return get_all_data()[name]


def get_choices_for_request(name):
    names = get_nearest_vehicle_names(name)
    return list(set([get_vehicle_data(n) for n in names]))


def tests():
    t = get_choices_for_request('T34')[0]
    assert get_choices_for_request(u'T34')[0].name == 'T34'
    # assert get_choices_for_vehicle_name('Т-34')[0]['name'] == 'Т-34'
    # TODO Расстояние махаланобиса, выгрузить все локализации, полные имена и короткие и составлять список подходящих танков


if __name__ == '__main__':
    tests()