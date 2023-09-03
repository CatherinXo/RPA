from RPA.Browser.Selenium import Selenium

import calendar
import configparser
import csv
from datetime import date, timedelta, datetime
import os
import re
import requests
import time


class general_operations:
    def __init__(self, configfile='configfile', section='default'):
        '''
        Arguments:
        str: configfile: configuration file which contains values
        str: section: section from config file
        '''

        self.configfile = configfile
        self.section = section

    def read_config(self):
        '''
        Reads values for search phrase, sections, months from config file

        Returns:
        str: search_phrase: search phrase, text that needs to searched
        str: news_sections: news category or section
        str: months: number of months for which you need to receive news
        '''

        config = configparser.ConfigParser()
        config.read(self.configfile)

        self.search_phrase = config[self.section]['phrase']
        self.news_section = [x for x in config[self.section]['sections'].split(',') if x]
        self.months = config[self.section]['months']

        return self.search_phrase, self.news_section, self.months

    def extract_values(self, allnews):
        '''
        Arguments:
        list: allnews: list of text from webelement

        Extracts date, title, description, image name,
        count phrase, contains money.
        Downloads the image.
        Appends extracted values to the list all_records.
        '''

        self.all_records = []

        for details in allnews:
            date = details[0].encode('utf8')
            title = details[2].encode('utf8')

            description = ''
            if not details[3].startswith('By') or details[3].startswith('PRINT EDITION'):
                description = details[3].encode('utf8')

            
            imgurl = details[-1]

            imgname = ''
            pattern = r'[\w-]+\.jpg'
            x = re.search(pattern, imgurl)
            if x:
                imgname = x.group().encode('utf8')

            imgpath = ''
            pattern = r'images/.*[\w-]+\.jpg'
            x = re.search(pattern, imgurl)
            if x:
                imgpath = x.group().encode('utf8')

                # download image
                response = requests.get(imgurl)
                os.makedirs(os.path.dirname(imgpath), exist_ok=True)
                with open(imgpath, 'wb') as fp:
                    fp.write(response.content)

            phrase = self.search_phrase.encode('utf8').lower()
            count_phrase = title.lower().count(phrase) + description.lower().count(phrase)


            # $11.1 | $111,111.11 | 11 dollars | 11 USD
            pattern = r'\$[0-9,]+\.{0,1}[0-9]+|[0-9,]+\.{0,1}[0-9]+ (dollars|USD)'
            match = re.search(pattern, title.decode('utf8'))
            if match:
                contains_money = True
            else:
                contains_money = False

            record = {"title": title, "date": date, "description": description, "img": imgpath, "count_phrase": count_phrase, "contains_money": contains_money}
            self.all_records.append(record)

    def store_excel(self):
        '''
        Stores extracted values to excel file in csv format
        '''

        keys = self.all_records[0].keys()
        filename = self.search_phrase + ''.join(self.news_section) + self.months + '.csv'

        print(self.all_records)
        with open(filename, 'w', newline='') as fp:
            dict_writer = csv.DictWriter(fp, keys)
            dict_writer.writeheader()
            dict_writer.writerows(self.all_records)


class myrpa:
    def __init__(self, search_phrase, news_section, months):
        '''
        Arguments:
        str: search_phrase: search phrase, text that needs to searched
        str: news_sections: news category or section
        str: months: number of months for which you need to receive news
        list: allnews: contains text from each news
        RPA.Browser.Selenium.Selenium: browser_lib: to interact with browser
        '''

        self.search_phrase = search_phrase
        self.news_section = news_section
        self.months = months
        self.allnews = []

        self.browser_lib = Selenium(page_load_timeout=10, implicit_wait=10)

    def open_browser(self, url):
        # opens browser
        self.browser_lib.open_available_browser(url)

    def accept_cookies(self):
        # clicks on continue and close buttons
        self.browser_lib.click_button_when_visible('class:css-1fzhd9j')
        self.browser_lib.wait_and_click_button('data:testid:GDPR-accept')

    def click_search(self):
        # clicks on search, inputs search phrase and hits ENTER
        self.browser_lib.click_button_when_visible("class:e1iflr850")
        self.browser_lib.input_text('class:css-1j26cud', self.search_phrase)
        self.browser_lib.press_keys('class:css-1j26cud', "ENTER")

    def select_sections(self):
        # given a list of news_sections, selects them in section/category
        self.browser_lib.click_button_when_visible('class:css-4d08fs')
        ul = self.browser_lib.find_elements('xpath://ul[@class="css-64f9ga"]//li//label//input')
        for x in ul:
            for section in self.news_section:
                if section.lower() in x.get_attribute('value').lower():
                    x.click()
    def monthdelta(self, date, delta):
        m, y = (date.month+delta) % 12, date.year + ((date.month)+delta-1) // 12
        if not m: m = 12
        d = min(date.day, calendar.monthrange(y, m)[1])
        return date.replace(day=d,month=m, year=y)

    def month_range(self):
        enddate = date.today()
        if int(self.months) <= 1:
            startdate = enddate - timedelta(days=enddate.day-1)
        else:
            startdate = self.monthdelta(enddate, -int(self.months))
        enddate = enddate.strftime('%m/%d/%Y')
        startdate = startdate.strftime('%m/%d/%Y')

        self.browser_lib.click_button_when_visible('class:css-p5555t')
        ul = self.browser_lib.find_elements('xpath://ul[@class="css-vh8n2n"]//li//button')
        for x in ul:
            if x.get_attribute('value') == 'Specific Dates':
                x.click()
                self.browser_lib.input_text('data:testid:DateRange-startDate', startdate)
                self.browser_lib.press_keys('data:testid:DateRange-startDate', "ENTER")
                self.browser_lib.input_text('data:testid:DateRange-endDate', enddate)
                self.browser_lib.press_keys('data:testid:DateRange-endDate', "ENTER")

    def sortby_newest(self):
        # clicks on sort by newest
        self.browser_lib.click_element_when_clickable('xpath://select[@class="css-v7it2b"]//option[@value="newest"]', 5)

    def show_more(self):
        # click show more until all news are fetched
        # scripted as specific date filter not working in UI prod
        
        loop = True
        while loop:
            time.sleep(2)
            self.browser_lib.wait_and_click_button('data:testid:search-show-more-button')

            res = self.browser_lib.find_elements('xpath://ol[@data-testid="search-results"]//li[@class="css-1l4w6pd"]//div//div//div//a')
            lastdate = res[-1].get_attribute('href').split('/')[3:6]
            print(lastdate)
            print(res[-1].get_attribute('href'))

            try:
                lastdate = datetime.strptime('/'.join(lastdate), '%Y/%m/%d')
            except ValueError:
                continue

            newdate = datetime.today()
            if int(self.months) <= 1:
                olddate = newdate - timedelta(days=newdate.day-1)
            else:
                olddate = self.monthdelta(newdate, -int(self.months))

            if (lastdate - olddate).days < 0:
                loop = False
        
    def get_all_news(self):
        # gets all the news in the specified search phrase, news section and months
        res = self.browser_lib.find_elements('xpath://ol[@data-testid="search-results"]//li[@class="css-1l4w6pd"]')
        for news in res:
            try:
                image = self.browser_lib.find_element('class:css-rq4mmj', parent=news)
            except Exception as e:
                pass
            else:
                imgurl = image.get_attribute('src')

            record = news.text.splitlines()
            record.append(imgurl)
            self.allnews.append(record)


        return self.allnews


def main():
    go = general_operations(section='case2')
    search_phrase, news_section, months = go.read_config()

    myrpao = myrpa(search_phrase, news_section, months)
    myrpao.open_browser('https://www.nytimes.com/')
    myrpao.accept_cookies()
    myrpao.click_search()
    myrpao.select_sections()
    myrpao.month_range()
    myrpao.sortby_newest()
    myrpao.show_more()
    all_news = myrpao.get_all_news()

    go.extract_values(all_news)
    go.store_excel()


if __name__ == "__main__":
    main()
    '''
    try:
        main()
    except Exception as e:
        print(f'Error occurred: {e}')
    '''

'''
hardening:

- add logs
- for various inputs, check errors
- can implement csv chunk write
- can implement processing in chunks


NOTE:
cant chose none news section
date range not working in prod UI itself, need to script out
'''
