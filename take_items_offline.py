import heapq
import logging
from dataclasses import dataclass
from datetime import datetime
from threading import Event
from typing import List

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


@dataclass
class XPath:
    LOGIN_BUTTON = '/html/body/div/div[2]/div/div/div/div/div/div[2]/form/button'
    LOGIN_MESSAGE = '/html/body/div[2]/div[1]/span'

    ITEM_AVAIL_RULES = '/html/body/div[1]/div[1]/div/ul/li[3]/div/ul/li[3]/a'
    PLU_FILTER = ('/html/body/div[1]/div/div[2]/div[2]/div/div/form/div[1]/div[1]/div[2]/div/div/div/'
                  'table/tbody/tr[1]/td[2]/div/div/input')
    CHECK_BOX = ('/html/body/div[1]/div/div[2]/div[2]/div/div/form/div[1]/div[1]/div[2]/div/div/div/'
                 'table/tbody/tr[3]/td[1]/span/span[1]/input')
    PLU_TEXT = ('/html/body/div[1]/div/div[2]/div[2]/div/div/form/div[1]/div[1]/div[2]/div/div/div/'
                'table/tbody/tr[3]/td[2]')
    SEARCH_BAR = '/html/body/div[1]/div/div[2]/div[2]/div/div/form/div[1]/div[1]/div[1]/div/div[3]/div/input'

    LOCATION = '/html/body/div[1]/div/div[2]/div[2]/div/div/form/div[2]/div/div'
    OPTION_T4_MORLEY = '/html/body/div[4]/div[3]/ul/li[2]'

    END_DATE = '/html/body/div[1]/div/div[2]/div[2]/div/div/form/div[3]/div/input'

    REASON_BUTTON = '/html/body/div[1]/div/div[2]/div[2]/div/div/form/div[4]/div/div'
    OPTION_CUSTOM_BUTTON = '/html/body/div[4]/div[3]/ul/li'
    REASON_TEXT = '/html/body/div[1]/div/div[2]/div[2]/div/div/form/div[5]/div/textarea[1]'

    SAVE_BUTTON = '/html/body/div[1]/div/div[2]/div[2]/div/div/form/div[7]/div[2]/div/button'


@dataclass
class URL:
    LOGIN_PAGE = 'https://t4australia.redcatcloud.com.au/auth/login'
    ADMIN_PAGE = 'https://t4australia.redcatcloud.com.au/admin'
    RULES_PAGE = 'https://t4australia.redcatcloud.com.au/admin2/item-availability-rules/rule'


@dataclass
class ItemRow:
    location: str
    keyword: str
    start_time: datetime
    end_time: datetime
    reason: str


@dataclass
class UserInfo:
    username: str
    password: str


class Agent:

    def __init__(self, item_row_list: List[ItemRow]):
        self.item_row_list = item_row_list

    def __enter__(self):
        self.create_browser_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.destroy_browser_session()

    def create_browser_session(self):
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()

    def destroy_browser_session(self):
        self.driver.quit()

    def login(self, user_info: UserInfo):
        self.driver.get(URL.LOGIN_PAGE)

        is_login = False
        while not is_login:
            username = user_info.username
            password = user_info.password

            username_box = self.driver.find_element(By.ID, 'username')
            username_box.clear()
            username_box.send_keys(username)

            password_box = self.driver.find_element(By.ID, 'password')
            password_box.clear()
            password_box.send_keys(password)

            login_button = self.driver.find_element(By.XPATH, XPath.LOGIN_BUTTON)
            login_button.click()

            try:
                WebDriverWait(self.driver, 2).until(
                    EC.url_changes(URL.LOGIN_PAGE)
                )
                is_login = True
            except TimeoutException:
                logging.info('Login failed.')
                print('Login failed.')

    def update_rules(self, plu):
        self.driver.get(URL.RULES_PAGE)

        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.XPATH, XPath.PLU_FILTER))
        )
        plu_filter = self.driver.find_element(By.XPATH, XPath.PLU_FILTER)
        plu_filter.clear()
        plu_filter.send_keys(plu)

        WebDriverWait(self.driver, 5).until(
            EC.text_to_be_present_in_element((By.XPATH, XPath.PLU_TEXT), f'{plu}')
        )
        check_box = self.driver.find_element(By.XPATH, XPath.CHECK_BOX)
        check_box.click()

        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.XPATH, XPath.LOCATION))
        )
        location = self.driver.find_element(By.XPATH, XPath.LOCATION)
        location.click()

        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.XPATH, XPath.OPTION_T4_MORLEY))
        )
        option = self.driver.find_element(By.XPATH, XPath.OPTION_T4_MORLEY)
        option.click()
        option.send_keys(Keys.TAB)

        actions = ActionChains(self.driver).send_keys(Keys.TAB * 4)
        actions.perform()

        WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, XPath.REASON_BUTTON))
        )
        reason_button = self.driver.find_element(By.XPATH, XPath.REASON_BUTTON)
        reason_button.click()

        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.XPATH, XPath.OPTION_CUSTOM_BUTTON))
        )
        reason_option = self.driver.find_element(By.XPATH, XPath.OPTION_CUSTOM_BUTTON)
        reason_option.click()
        reason_text = self.driver.find_element(By.XPATH, XPath.REASON_TEXT)
        reason_text.send_keys('Delete by take_items_offline.py')

        save_button = self.driver.find_element(By.XPATH, XPath.SAVE_BUTTON)
        save_button.click()

        logging.info(f'PLU: {plu} was checked and saved.')

    def update_rules_by_search(self, item: ItemRow):
        self.driver.get(URL.RULES_PAGE)

        # Select the search bar
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.XPATH, XPath.SEARCH_BAR))
        )
        search_bar = self.driver.find_element(By.XPATH, XPath.SEARCH_BAR)
        search_bar.send_keys(item.keyword)

        # TODO: Check all items

        # Click the location
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.XPATH, XPath.LOCATION))
        )
        location = self.driver.find_element(By.XPATH, XPath.LOCATION)
        location.click()

        # TODO: Select by the location
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.XPATH, XPath.OPTION_T4_MORLEY))
        )
        option = self.driver.find_element(By.XPATH, XPath.OPTION_T4_MORLEY)
        option.click()
        option.send_keys(Keys.TAB)

        actions = ActionChains(self.driver).send_keys(Keys.TAB * 4)
        actions.perform()

        # Enter the reason
        WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, XPath.REASON_BUTTON))
        )
        reason_button = self.driver.find_element(By.XPATH, XPath.REASON_BUTTON)
        reason_button.click()
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.XPATH, XPath.OPTION_CUSTOM_BUTTON))
        )
        reason_option = self.driver.find_element(By.XPATH, XPath.OPTION_CUSTOM_BUTTON)
        reason_option.click()
        reason_text = self.driver.find_element(By.XPATH, XPath.REASON_TEXT)
        reason = item.reason if item.reason else 'Deleted by t4auto'
        reason_text.send_keys(reason)

        save_button = self.driver.find_element(By.XPATH, XPath.SAVE_BUTTON)
        save_button.click()

        logging.info(f'{item.keyword} was checked and saved.')

    def update_rules_loop(self):
        now = datetime.now()
        event_queue = [((item_row.start_time - now).seconds, item_row) for item_row in self.item_row_list]
        heapq.heapify(event_queue)
        stop = Event()
        while not stop.is_set():
            now = datetime.now()
            _, item_row = heapq.heappop(event_queue)
            if now < item_row.start_time:
                stop.wait((item_row.start_time - now).seconds)

            self.update_rules_by_search(item_row)
