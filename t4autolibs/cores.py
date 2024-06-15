import datetime
import logging
from dataclasses import dataclass
from enum import IntEnum
from threading import Event

import requests


@dataclass
class URL:
    LOGIN_PAGE = 'https://t4australia.redcatcloud.com.au/auth/login'
    LOGIN_API = 'https://t4australia.redcatcloud.com.au/api/v1/login'
    LOGOUT_API = 'https://t4australia.redcatcloud.com.au/auth/logout'
    GET_ITEMS_API = 'https://t4australia.redcatcloud.com.au/api/v1/plus-active/'
    UPDATE_ITEMS_API = 'https://t4australia.redcatcloud.com.au/api/v1/pluavailabilityrules'
    GET_STORES_API = 'https://t4australia.redcatcloud.com.au/api/v1/config/lookup/stores/'


class ActionType(IntEnum):
    START = 0
    END = 1


@dataclass
class ActionRow:
    action_idx: int
    keyword: str
    action_time: datetime.datetime
    action_type: ActionType
    reason: str
    store_id: int

    def __lt__(self, other):
        return (self.action_time, self.action_idx) < (other.action_time, other.action_idx)

    def __eq__(self, other):
        return (self.action_time, self.action_idx) == (other.action_time, other.action_idx)


@dataclass
class UserInfo:
    username: str
    password: str


@dataclass
class Store:
    id: int
    name: str


@dataclass
class LoginStatus:
    success: bool
    message: str


def time_difference_seconds(time1: datetime.datetime, time2: datetime.datetime):
    """
    Returns seconds of (time1 - time2).
    """
    return (time1 - time2).total_seconds()


class Agent:

    def __init__(self):
        self.stores = []
        self._reset_session()
        self.stop_event = Event()

    def _reset_session(self):
        self.session = requests.session()
        self.session.headers['User-Agent'] = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                                              'Chrome/124.0.0.0 Safari/537.36')

    def login(self, user_info: UserInfo):
        data = {
            'username': user_info.username,
            'psw': user_info.password,
            'auth_type': 'U',
            'next': '/admin',
            'save_session': True,
        }
        response = self.session.post(URL.LOGIN_API, data=data)
        if response.status_code == 200:
            response = response.json()
            if response['success']:
                self.get_store_ids()
                return LoginStatus(success=True, message='Login successfully')
            else:
                return LoginStatus(success=False, message=response['additional_info']['validation_errors'][0]['msg'])
        else:
            raise ValueError('')

    def logout(self):
        response = self.session.get(URL.LOGOUT_API)
        if response.status_code == 200:
            self.session.close()
            self._reset_session()
        else:
            raise ValueError('Response.status_code is not 200.\n' + str(response))

    def search_items_from_api(self, keyword, api):
        n_items_per_page = 100
        params = {
            'qv': keyword,
            'start': 0,
            'limit': n_items_per_page,
        }
        response = self.session.get(api, params=params).json()
        if not response['success']:
            raise ValueError('Response["success"] is false.\n' + str(response))
        items = response['data']
        start_idx = 0
        while start_idx + response['count'] < response['total']:
            start_idx += n_items_per_page
            params['start'] = start_idx
            response = self.session.get(api, params=params).json()
            if not response['success']:
                raise ValueError('Response["success"] is false.\n' + str(response))

            items += response['data']
        return items

    def take_items_offline_by_search(self, action_row: ActionRow):
        items = self.search_items_from_api(action_row.keyword, URL.GET_ITEMS_API)

        plu_codes = [item['PLUCode'] for item in items]
        payload = {
            'PLUCode': plu_codes,
            'CustomReason': action_row.reason if action_row.reason else 'Deleted by t4auto',
            'Reason': 'Custom',
            'StoreID': [action_row.store_id],
        }
        response = self.session.post(URL.UPDATE_ITEMS_API, data=payload).json()
        if not response['success']:
            raise ValueError('Response["success"] is false.\n' + str(response))
        logging.info(f'{action_row.keyword} is offline, total {len(items)} items.')

    def take_items_online_by_search(self, action_row: ActionRow):
        items = self.search_items_from_api(action_row.keyword, URL.UPDATE_ITEMS_API)

        item_ids = [item['ID'] for item in items]
        payload = {
            'IDs': item_ids,
        }
        response = self.session.delete(URL.UPDATE_ITEMS_API, data=payload).json()
        if not response['success']:
            raise ValueError('Response["success"] is false.\n' + str(response))
        logging.info(f'{action_row.keyword} is online, total {len(items)} items.')

    def update_rules_loop(self, actions: list[ActionRow]):
        actions.sort()

        i = 0
        while not self.stop_event.is_set():
            now_time = datetime.datetime.now()
            if now_time < actions[i].action_time:
                seconds = time_difference_seconds(actions[i].action_time, now_time)
                self.stop_event.wait(seconds)

            if not self.stop_event.is_set():
                if actions[i].action_type == ActionType.START:
                    self.take_items_offline_by_search(actions[i])
                else:
                    self.take_items_online_by_search(actions[i])

            actions[i].action_time += datetime.timedelta(days=1)

            i += 1
            i %= len(actions)

    def stop(self):
        self.stop_event.set()

    def get_store_ids(self):
        response = self.session.get(URL.GET_STORES_API, params={'restricted': 'true'}).json()
        if not response['success']:
            raise ValueError('Response["success"] is false.\n' + str(response))

        for data in response['data']:
            store_name = data['name']
            store_id = data['value']
            self.stores.append(Store(store_id, store_name))
