import pandas as pd
import numpy as np
import math
import datetime
import time
import requests
import json
from selenium.common.exceptions import WebDriverException
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import os
import geckodriver_autoinstaller


class TinyEarn():
    '''
    This class scrapes Zacks.com to get earnings data from a companies earnings reports.
    '''
    def __init__(self):
        geckodriver_autoinstaller.install()

    def get_earnings(self, ticker:str, start, end = datetime.date.today(), pandas = True, delay = 1):

        if isinstance(start,str): start = pd.to_datetime(start)
        if isinstance(end,str): end = pd.to_datetime(end)

        if not isinstance(start, datetime.date) or not isinstance(end, datetime.date):
            raise ValueError('Type error occured with start or end parameters. Please enter valid date string or datetime object.')

        browser = self.__get_browser()

        url = "https://www.zacks.com/stock/research/" + ticker + "/earnings-announcements"
        browser.get(url)

        eps = self.__get_eps(browser, start,end,ticker,delay)
        bv = self.__get_book_value(browser, start,end,ticker,delay)

        revenue = self.__get_revenue(browser, start,end,url,delay)

        browser.close()

        #results = self.__merge_dicts(eps,revenue)
        results = self.__merge_dicts(eps,bv)

        if pandas == True:
            return pd.DataFrame.from_dict(results, orient='index')
        else:
            return results


    def __merge_dicts(self, first:dict, second:dict):

        first = pd.DataFrame(first)
        second = pd.DataFrame(second)
        r = pd.concat([first, second], axis=0)
        return r.to_dict()

    def __clean_vals(self, value:str):
        if value == '--':
            return np.nan
        else:
            return float(value.replace('$',"").replace('%',"").replace(',',''))

    def __get_table(self, browser, start, end, url, prefix, index, delay = 1):

        stats_list = {}
        return_list = {}
        done = False
        date = None

        dfs = []
        while done == False:
            html = browser.page_source
            soup = BeautifulSoup(html, 'html.parser')

            stats_list = pd.read_html(str(html))
            stats_list = stats_list[index]
            stats_list["Date"] = pd.to_datetime(stats_list["Date"])
            dfs.append(stats_list)
            #if date is not None and date == stats_list["Date"].iloc[-1]:
            #    done = True
            #else:
            #    date = stats_list["Date"].iloc[-1]
            date = stats_list["Date"].iloc[-1]
            if date < start:
                done = True

            next_btn = browser.find_element_by_xpath('//*[@id="'+prefix+'_next"]')
            location = next_btn.location

            y = location['y'] - 100
            browser.execute_script("window.scrollTo(0, " + str(y) + ")")
            time.sleep(delay)

            actions = ActionChains(browser)
            actions.move_to_element(next_btn)
            actions.click(next_btn)
            actions.perform()

        r = pd.concat(dfs, ignore_index=True)
        r = r.set_index("Date")
        r = r.transpose()
        return r.to_dict()

    def __get_book_value(self, browser, start, end, ticker, delay = 1):
        url = "https://www.zacks.com/stock/chart/" + ticker + "/fundamental/book-value"
        browser.get(url)
        return self.__get_table(browser, start, end, url, "DataTables_Table_0", 2, delay)



    def __get_eps(self, browser, start, end, ticker, delay = 1):
        url = "https://www.zacks.com/stock/research/" + ticker + "/earnings-announcements"
        browser.get(url)
        return self.__get_table(browser, start, end, url, "earnings_announcements_earnings_table", 3, delay)

    def __get_browser(self):
        opts = Options()
        path = os.getcwd()
        opts.headless = True
        try:
            browser = Firefox(executable_path=r'{}/geckodriver.exe'.format(path), options=opts)
        except WebDriverException:
            try:
                browser = Firefox(executable_path=r'{}/geckodriver'.format(path), options=opts)
            except WebDriverException:
                browser = Firefox(executable_path=r'geckodriver', options=opts)
        return browser
