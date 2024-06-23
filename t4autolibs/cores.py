import datetime
import logging
import random
import time
from dataclasses import dataclass
from enum import IntEnum
from threading import Event

import requests
from apscheduler.schedulers.qt import QtScheduler


@dataclass
class URL:
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
class ActionRowV2:
    keyword: str
    action_time: datetime.datetime
    action_type: ActionType
    reason: str
    store_id: int


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
                return LoginStatus(success=False, message='Login failed:'
                                                          + response['additional_info']['validation_errors'][0]['msg'])
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


def random_sleep(min_sec=1, max_sec=60):
    time.sleep(random.randint(min_sec, max_sec))


class AgentV2:

    def __init__(self):
        self.stores = []
        self._initialize_class_logger()
        self._start_new_session()
        self._scheduler = QtScheduler()

    def _initialize_class_logger(self):
        self.class_logger = logging.getLogger('t4auto')

        formatter = logging.Formatter('[%(asctime)s] %(name)s (%(levelname)s): %(message)s',
                                      '%Y-%m-%d %H:%M:%S')
        fh = logging.FileHandler('t4auto log.txt')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        self.class_logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        self.class_logger.addHandler(ch)

    def _start_new_session(self):
        self.session = requests.session()
        self.session.headers['User-Agent'] = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                                              'Chrome/124.0.0.0 Safari/537.36')
        self.class_logger.debug('_start_new_session()')

    def login(self, user_info: UserInfo) -> LoginStatus:
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
                self._get_store_ids()
                success = True
                message = 'Login successfully'
            else:
                success = False
                message = f'Login failed: {response['additional_info']['validation_errors'][0]['msg']}'
        else:
            success = False
            message = f'Login failed with HTTP error: HTTP status code is {response.status_code}'

        self.class_logger.info(f'{message}')
        return LoginStatus(success, message)

    def _get_store_ids(self):
        response = self.session.get(URL.GET_STORES_API, params={'restricted': 'true'}).json()
        if not response['success']:
            raise ValueError('Response["success"] is false.\n' + str(response))

        for data in response['data']:
            store_name = data['name']
            store_id = data['value']
            self.stores.append(Store(store_id, store_name))
        self.class_logger.debug(f'_get_store_ids() -> {self.stores}')

    def logout(self) -> LoginStatus:
        response = self.session.get(URL.LOGOUT_API)
        if response.status_code == 200:
            self.session.close()
            self._start_new_session()
            success = True
            message = 'Logout successfully'
        else:
            success = False
            message = f'Logout failed with HTTP error: HTTP status code is {response.status_code}'
        self.class_logger.info(f'{message}')
        return LoginStatus(success, message)

    def _search_items_from_api(self, keyword, api):
        random_sleep()
        n_items_per_page = 100
        params = {
            'qv': keyword,
            'start': 0,
            'limit': n_items_per_page,
        }
        response = self.session.get(api, params=params).json()
        if not response['success']:
            self.class_logger.error(f'Searching items was failed.')
            self.class_logger.debug(f'GET {api} with params {params} -> {response}')
            return None

        items = response['data']
        start_idx = 0
        while start_idx + response['count'] < response['total']:
            start_idx += n_items_per_page
            params['start'] = start_idx
            response = self.session.get(api, params=params).json()
            if not response['success']:
                self.class_logger.error(f'Searching items was failed.')
                self.class_logger.debug(f'GET {api} with params {params} -> {response}')
                return None
            items += response['data']
        return items

    def _take_items_offline_by_search(self, action_row: ActionRowV2):
        items = self._search_items_from_api(action_row.keyword, URL.GET_ITEMS_API)
        random_sleep()
        self.class_logger.info(f'Taking items offline with the keyword: {action_row.keyword}.')
        if items:
            self.class_logger.info('The following items were searched:')
            for item in items:
                self.class_logger.debug(f'\tPLUCode: {item["PLUCode"]}')
                self.class_logger.info(f'\t{item["LongName"]}')
        else:
            self.class_logger.info('No items were searched. Skipped.')
            return

        plu_codes = [item['PLUCode'] for item in items]
        payload = {
            'PLUCode': plu_codes,
            'CustomReason': action_row.reason if action_row.reason else 'Deleted by t4auto',
            'Reason': 'Custom',
            'StoreID': [action_row.store_id],
        }
        response = self.session.post(URL.UPDATE_ITEMS_API, data=payload).json()
        if response['success']:
            self.class_logger.info(f'The items were offline, total {len(items)} items.')
        else:
            self.class_logger.error(f'Taking items offline was failed: the items were not offline.')
            self.class_logger.debug(f'Failed: response["success"] was false.\n{response}')

    def _take_items_online_by_search(self, action_row: ActionRowV2):
        items = self._search_items_from_api(action_row.keyword, URL.UPDATE_ITEMS_API)
        random_sleep()
        self.class_logger.info(f'Restoring items online with the keyword: {action_row.keyword}.')
        if items:
            self.class_logger.info('The following items were searched:')
            for item in items:
                self.class_logger.debug(f'\tID: {item["ID"]}')
                self.class_logger.info(f'\t{item["LongName"]}')
        else:
            self.class_logger.info('No items were searched. Skipped.')
            return

        item_ids = [item['ID'] for item in items]
        payload = {
            'IDs': item_ids,
        }
        response = self.session.delete(URL.UPDATE_ITEMS_API, data=payload).json()
        if response['success']:
            self.class_logger.info(f'The items were online, total {len(items)} items.')
        else:
            self.class_logger.error(f'Restoring items online was failed: the items were not online.')
            self.class_logger.debug(f'Failed: response["success"] was false.\n{response}')

    def start_scheduler(self, actions: list[ActionRowV2]):
        time_set = set()
        for action in actions:
            if action.action_type == ActionType.START:
                func = self._take_items_offline_by_search
            else:
                func = self._take_items_online_by_search

            action_time = action.action_time
            while action_time in time_set:
                action_time += datetime.timedelta(seconds=30)
            time_set.add(action_time)

            self._scheduler.add_job(
                func,
                'interval',
                args=(action,),
                days=1,
                start_date=action_time,
            )
            self.class_logger.info(f'Add in the scheduler:')
            if action.action_type == ActionType.START:
                self.class_logger.info(f'\taction: taking items offline')
            else:
                self.class_logger.info(f'\taction: restoring items online')
            self.class_logger.info(f'\tkeyword: {action.keyword}')
            self.class_logger.info(f'\tstart time: {action_time.strftime('%Y-%m-%d %H:%M:%S')}')

        self._scheduler.start()

    def stop_scheduler(self):
        self._scheduler.pause()
        self._scheduler.remove_all_jobs()
