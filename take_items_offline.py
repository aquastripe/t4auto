import datetime
import logging
from dataclasses import dataclass
from enum import IntEnum
from threading import Event

import requests
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

TIMEOUT = 120


@dataclass
class XPath:
    LOGIN_BUTTON = '/html/body/div/div[2]/div/div/div/div/div/div[2]/form/button'
    LOGIN_MESSAGE = '/html/body/div[2]/div[1]/span'

    ITEM_AVAIL_RULES = '/html/body/div[1]/div[1]/div/ul/li[3]/div/ul/li[3]/a'
    PLU_FILTER = ('/html/body/div[1]/div/div[2]/div[2]/div/div/form/div[1]/div[1]/div[2]/div/div/div/'
                  'table/tbody/tr[1]/td[2]/div/div/input')
    CHECK_BOX = ('/html/body/div[1]/div/div[2]/div[2]/div/div/form/div[1]/div[1]/div[2]/div/div/div/'
                 'table/tbody/tr[3]/td[1]/span/span[1]/input')
    CHECK_BOX_ALL = ('/html/body/div[1]/div/div[2]/div[2]/div/div/form/div[1]/div[1]/div[2]/div/div/div/'
                     'table/thead/tr/th[1]/span/span[1]/input')

    PLU_TEXT = ('/html/body/div[1]/div/div[2]/div[2]/div/div/form/div[1]/div[1]/div[2]/div/div/div/'
                'table/tbody/tr[3]/td[2]')
    SEARCH_BAR = '/html/body/div[1]/div/div[2]/div[2]/div/div/form/div[1]/div[1]/div[1]/div/div[3]/div/input'

    LOCATION = '/html/body/div[1]/div/div[2]/div[2]/div/div/form/div[2]/div/div'
    LOCATION_FIRST_OPTION = '/html/body/div[4]/div[3]/ul/li[2]'

    END_DATE = '/html/body/div[1]/div/div[2]/div[2]/div/div/form/div[3]/div/input'

    REASON_BUTTON = '/html/body/div[1]/div/div[2]/div[2]/div/div/form/div[4]/div/div'
    OPTION_CUSTOM_BUTTON = '/html/body/div[4]/div[3]/ul/li'
    REASON_TEXT = '/html/body/div[1]/div/div[2]/div[2]/div/div/form/div[5]/div/textarea[1]'

    SAVE_BUTTON = '/html/body/div[1]/div/div[2]/div[2]/div/div/form/div[7]/div[2]/div/button'

    NEXT_PAGE_BUTTON = ('/html/body/div[1]/div/div[2]/div[2]/div/div/form/div[1]/div[1]/'
                        'table/tfoot/tr/td/div/div[3]/span[4]/button')


@dataclass
class Selector:
    CHECKBOXES = ('#root > div > div.Screen > div.InnerContainer > div > div > form > div:nth-child(1) '
                  '> div.MuiPaper-root.MuiPaper-elevation2.MuiPaper-rounded > div.jss34 > div > div > '
                  'div > table > tbody input[type="checkbox"]')


@dataclass
class URL:
    LOGIN_PAGE = 'https://t4australia.redcatcloud.com.au/auth/login'
    GET_ITEMS_API = 'https://t4australia.redcatcloud.com.au/api/v1/plus-active/'
    UPDATE_ITEMS_API = 'https://t4australia.redcatcloud.com.au/api/v1/pluavailabilityrules'
    GET_STORES_API = 'https://t4australia.redcatcloud.com.au/api/v1/config/lookup/stores/'


class ActionType(IntEnum):
    START = 0
    END = 1


@dataclass
class ActionRow:
    action_idx: int
    location: str
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


def time_difference_seconds(time1: datetime.datetime, time2: datetime.datetime):
    """
    Returns seconds of (time1 - time2).
    """
    return (time1 - time2).total_seconds()


class Agent:

    def __init__(self):
        self.session_is_started = False
        self.store_name_to_id = {}
        self.store_id_to_name = {}
        self.session = requests.session()
        self.stop_event = Event()

    def create_browser_session(self):
        self.session_is_started = True

    def destroy_browser_session(self):
        self.session_is_started = False

    def login(self, user_info: UserInfo):
        driver = webdriver.Chrome()
        self._login_by_driver(driver, user_info)
        self._update_session(driver)
        self._get_store_ids()
        driver.quit()

    def _login_by_driver(self, driver, user_info):
        driver.get(URL.LOGIN_PAGE)
        is_login = False
        while not is_login:
            username = user_info.username
            password = user_info.password

            username_box = driver.find_element(By.ID, 'username')
            username_box.clear()
            username_box.send_keys(username)

            password_box = driver.find_element(By.ID, 'password')
            password_box.clear()
            password_box.send_keys(password)

            login_button = driver.find_element(By.XPATH, XPath.LOGIN_BUTTON)
            login_button.click()

            try:
                WebDriverWait(driver, 2).until(
                    EC.url_changes(URL.LOGIN_PAGE)
                )
                is_login = True
            except TimeoutException:
                logging.info('Login failed.')
                print('Login failed.')

    def _update_session(self, driver):
        user_agent = driver.execute_script('return navigator.userAgent;')
        self.session.headers['user-agent'] = user_agent
        for cookie in driver.get_cookies():
            self.session.cookies.set(name=cookie['name'], value=cookie['value'], domain=cookie['domain'])

    def logout(self):
        self.session.close()
        self.session = requests.session()

    def take_items_offline_by_search(self, item: ActionRow):
        # select all items by the keyword
        n_items_per_page = 100
        params = {
            'qv': item.keyword,
            'start': 0,
            'limit': n_items_per_page,
        }
        response = self.session.get(URL.GET_ITEMS_API, params=params).json()
        if not response['success']:
            raise ValueError('Response["success"] is false.\n' + str(response))

        items = response['data']
        start_idx = 0
        while start_idx + response['count'] < response['total']:
            start_idx += n_items_per_page
            params['start'] = start_idx
            response = self.session.get(URL.GET_ITEMS_API, params=params).json()
            if not response['success']:
                raise ValueError('Response["success"] is false.\n' + str(response))

            items += response['data']

        plu_codes = [item['PLUCode'] for item in items]
        payload = {
            'PLUCode': plu_codes,
            'CustomReason': item.reason if item.reason else 'Deleted by t4auto',
            'Reason': 'Custom',
            'StoreID': [item.store_id],
        }
        response = self.session.post(URL.UPDATE_ITEMS_API, data=payload).json()
        if not response['success']:
            raise ValueError('Response["success"] is false.\n' + str(response))
        logging.info(f'{item.keyword} was checked and saved.')

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
                    print('Take items online.')

            actions[i].action_time += datetime.timedelta(days=1)

            i += 1
            i %= len(actions)

    def stop(self):
        self.stop_event.set()

    def _get_store_ids(self):
        response = self.session.get(URL.GET_STORES_API, params={'restricted': 'true'}).json()
        if not response['success']:
            raise ValueError('Response["success"] is false.\n' + str(response))

        for data in response['data']:
            store_name = data['name']
            store_id = data['value']
            self.store_name_to_id[store_name] = store_id
            self.store_id_to_name[store_id] = store_name
