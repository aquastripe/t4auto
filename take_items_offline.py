import argparse
import getpass
import logging
from dataclasses import dataclass

import pandas as pd
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


class Agent:

    def __init__(self):
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.driver.get(URL.LOGIN_PAGE)

    def login(self):
        is_login = False

        while not is_login:
            username = input('Username: ')
            password = getpass.getpass()

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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('offline_items', nargs='?', default='offline_items.csv', type=str,
                        help='The file name of a CSV file contains the items to be taken offline.')
    args = parser.parse_args()

    logging.basicConfig(filename='take_items_offline_log.txt', level=logging.INFO, format='[%(asctime)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    agent = Agent()
    agent.login()

    df = pd.read_csv(args.offline_items)
    for plu in df['PLU']:
        agent.update_rules(plu)

    agent.driver.quit()
    logging.info('Done.')


if __name__ == '__main__':
    main()
