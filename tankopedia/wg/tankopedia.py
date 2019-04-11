# coding=utf8
import logging
import utils

import hashlib
import json
import requests

from Levenshtein import ratio as levenshtein_ratio

from config import WG_APP_ID
from wg.constants import NATION, TYPE, HOST

GET_ALL_VEHICLE_URL = '{host}/wotb/encyclopedia/vehicles/' \
                      '?application_id={app_id}' \
                      '&fields=name,images,nation,is_premium,tier,type,cost' \
                      '&language=en'.format(host=HOST, app_id=WG_APP_ID)
GET_LOC_VEHICLE_URL = '{host}/wotb/encyclopedia/vehicles/' \
                      '?application_id={app_id}' \
                      '&fields=name,description' \
                      '&language=ru'.format(host=HOST, app_id=WG_APP_ID)


def _prepare_for_search(value):
    return value.replace('.', '').replace('-', '').lower()


class VehicleData(object):
    def __init__(self, json_data, localized_data):
        self.name = json_data['name']
        self.localized_names = [data['name'] for data in localized_data.values()]
        self.search_names = set([_prepare_for_search(name) for name in self.localized_names])
        self.image_preview = json_data['images']['preview']
        self.image_normal = json_data['images']['normal']
        self.uuid = hashlib.md5(self.name.encode('utf-8')).hexdigest(),
        self.nation = json_data['nation']
        self.is_premium = json_data['is_premium']
        self.tier = json_data['tier']
        self.type = json_data['type']
        cost = json_data['cost']
        self.cost_gold = cost['price_gold'] if cost else None
        self.cost_credit = cost['price_credit'] if cost else None
        self.description = localized_data['ru']['description']  # TODO
        self.tankopedia_url = None # TODO

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
        self.vehicles = self.load_data()

    @staticmethod
    def load_data():
        response_all = requests.get(GET_ALL_VEHICLE_URL)
        assert response_all.ok is True
        content_all = json.loads(response_all.content)

        response_loc = requests.get(GET_LOC_VEHICLE_URL)
        assert response_loc.ok is True
        content_loc = json.loads(response_loc.content)

        data = []
        for k, v in content_all['data'].items():
            loc_data = content_loc['data'][k]
            localized_data = {
                'en': v,
                'ru': loc_data,  # TODO Other localizations
            }
            data.append(VehicleData(v, localized_data))

        return data

    def find_by_localized_name(self, name):
        for vehicle in self.vehicles:
            if name in vehicle.localized_names:
                return vehicle

        return None

    def fuzzy_search_vehicle(self, query):
        vehicle_data = self.find_by_localized_name(query)
        if vehicle_data:
            return [vehicle_data]

        relevant_result = []
        search_query = _prepare_for_search(query)
        for data in self.vehicles:
            for name in data.search_names:
                ratio = levenshtein_ratio(search_query, name)

                if ratio > 0:
                    relevant_result.append((ratio, data))

        result = sorted(relevant_result, key=lambda v: v[0], reverse=True)
        result = [value[1] for value in result[0:5] if value[0] > 0.5]
        logging.info(result)
        return result
