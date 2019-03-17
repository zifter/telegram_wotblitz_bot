#coding=utf8
import utils

import relevant_search
import hashlib
import random
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
    'other': u'BLITZ',
    'none': u'',
}

TYPE = {
    'lightTank' : u'ЛТ',
    'mediumTank' : u'CT',
    'heavyTank' : u'TT',
    'AT-SPG' : u'ПТ-САУ',
    'SPG' : u'ПТ',
}

class VehicleData(object):
    def __init__(self, json_data, json_loc_data):
        self.name = json_data['name']
        self.image_preview = json_data['images']['preview']
        self.image_normal = json_data['images']['normal']
        self.localized_names = [json_data['name'], json_loc_data['name']]
        self.uuid = hashlib.md5(self.name.encode('utf-8')).hexdigest(),
        self.nation = json_data['nation']
        self.is_premium = json_data['is_premium']
        self.tier = json_data['tier']
        self.type = json_data['type']
        cost = json_data['cost']
        self.cost_gold = cost['price_gold'] if cost  else None
        self.cost_credit = cost['price_credit'] if cost else None
        self.description = json_loc_data['description']
        self.tankopedia_url = 'http://wiki.wargaming.net/ru/Blitz:{}'.format('MS-1')

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


@utils.cached_value
def get_all_data():
    responseAll = requests.get(GET_ALL_VEHICLE_URL)
    assert responseAll.ok == True
    contentAll = json.loads(responseAll.content)

    responseLoc = requests.get(GET_LOC_VEHICLE_URL)
    assert responseLoc.ok == True
    contentLoc = json.loads(responseLoc.content)

    data = dict()
    for k, v in contentAll['data'].items():
        print(v['name'])
        d = VehicleData(v, contentLoc['data'][k])
        loc_name = contentLoc['data'][k]['name']
        data[v['name']] = d
        data[loc_name] = d

    return data


@utils.cached_value
def get_vehicle_names():
    return get_all_data().keys()


def get_vehicle_data(name):
    return get_all_data()[name]


def get_nearest_vehicle_names(name):
    names = get_vehicle_names()
    if name in names:
        return [name]

    return relevant_search.search(name, get_vehicle_names())


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