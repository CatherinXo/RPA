from RPA.Browser.Selenium import Selenium
import time
import re
import requests
import os
import csv
import configparser

browser_lib = Selenium(page_load_timeout=10, implicit_wait=10)

def open_the_website(url):
    browser_lib.open_available_browser(url)

def accept_cookies():
	browser_lib.click_button_when_visible('class:css-1fzhd9j')
	browser_lib.click_button_when_visible('class:css-1qw5f1g')
	#browser_lib.click_button_when_visible('data-testid:GDPR-accept')


def search_for(term, news_section, months='0'):
	#x = browser_lib.find_element('class:css-tkwi90')
	browser_lib.click_button_when_visible("class:e1iflr850")
	browser_lib.input_text('class:css-1j26cud', term)
	browser_lib.press_keys('class:css-1j26cud', "ENTER")

	browser_lib.click_button_when_visible('class:css-1qw5f1g')


	# Section
	browser_lib.click_button_when_visible('class:css-4d08fs')
	ul = browser_lib.find_elements('xpath://ul[@class="css-64f9ga"]//li//label//input')
	for x in ul:
		for section in news_section:
			if section.lower() in x.get_attribute('value').lower():
				x.click()

	# Sort by newest
	browser_lib.click_element_when_clickable('xpath://select[@class="css-v7it2b"]//option[@value="newest"]', 5)

	# show more till all news # queries only 2 times for now
	i = 1
	while i < 3:
		time.sleep(2)

		z = browser_lib.find_element('data:testid:search-show-more-button')
		i+=1
		browser_lib.wait_and_click_button('data:testid:search-show-more-button')

	# date, title, description
	result_news = []
	y = browser_lib.find_elements('xpath://ol[@data-testid="search-results"]//li[@class="css-1l4w6pd"]')
	for news in y:
		print(news.text.splitlines())

		details = news.text.splitlines()
		date = details[0]
		section = details[1]
		title = details[2]
		description = ''
		if not details[3].startswith('By') or details[3].startswith('PRINT EDITION'):
			description = details[3]

		count_phrase = title.lower().count(term.lower()) + description.lower().count(term.lower())

		# $11.1 | $111,111.11 | 11 dollars | 11 USD
		pattern = r'\$[0-9,]+\.{0,1}[0-9]+|[0-9,]+\.{0,1}[0-9]+ (dollars|USD)'
		match = re.search(pattern, title)
		if match:
			contains_money = True
		else:
			contains_money = False

		# image
		try:
			image = browser_lib.find_element('class:css-rq4mmj', parent=news)
		except:
			imgpath = ''
		else:
			imgurl = image.get_attribute('src')

			imgname = ''
			pattern = r'[\w-]+\.jpg'
			x = re.search(pattern, imgurl)
			if x:
				imgname = x.group()

			imgpath = ''
			pattern = r'images/.*[\w-]+\.jpg'
			x = re.search(pattern, imgurl)
			if x:
				imgpath = x.group()

				# download image
				response = requests.get(imgurl)
				os.makedirs(os.path.dirname(imgpath), exist_ok=True)
				with open(imgpath, 'wb') as fp:
					fp.write(response.content)

		record = {"date": date, "title": title, "description": description, "img": imgpath, "count_phrase": count_phrase, "contains_money": contains_money}
		result_news.append(record)

	keys = result_news[0].keys()
	filename = term + ''.join(news_section) + months + '.csv'
	with open(filename, 'w', newline='') as fp:
		dict_writer = csv.DictWriter(fp, keys)
		dict_writer.writeheader()
		dict_writer.writerows(result_news)



	
def store_screenshot(filename):
    browser_lib.screenshot(filename=filename)


# Define a main() function that calls the other functions in order:
def main():

    '''
    search_phrase = 'USD'
    news_section=[]
    #news_section = []
    months = 2
    '''

    section='case1'
    config = configparser.ConfigParser()
    config.read('configfile')
    search_phrase = config[section]['phrase']
    news_section = [x for x in config[section]['sections'].split(',') if x]
    months = config[section]['months']

    print(search_phrase, news_section, months)

    try:
        open_the_website("https://www.nytimes.com/")
        accept_cookies()
        search_for(search_phrase, news_section)
        store_screenshot("output/screenshot.png")
    finally:
        browser_lib.close_all_browsers()


# Call the main() function, checking that we are running as a stand-alone script:
if __name__ == "__main__":
    main()