#! /usr/bin/env python

from selenium import webdriver
from selenium.common.exceptions import (TimeoutException, 
                NoSuchElementException, UnexpectedAlertPresentException)
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from bs4 import BeautifulSoup as bsoup
import requests

from zipfile import ZipFile
import time
import string
import os
import shutil

import random


FILE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
AUXILARY_DATA_DIRECTORY = os.path.join(FILE_DIRECTORY, 'auxilary_data')
PREPEND_AUX             = lambda f: os.path.join(AUXILARY_DATA_DIRECTORY, f)
ENTRY_URL = "http://www.outlook.com"
BING_URL = "http://www.bing.com"
MOBILE_UA = 'Mozilla/5.0 (Linux; Android 4.4.4; en-us; Nexus 5 Build/JOP40D)'

keyword_files = ['interests.txt']

AVOID_LINKS = ['youtube', 'pdf', 'ppt', 'doc', 'video']

adblock_xpi = None


STOP_WORDS = PREPEND_AUX("stop-word-list.txt")

XPATHS = {
    'search_result_count': r'//*[@class="sb_count"]',
    'offer_box'          : r'//*[@class="offers"]/div[1]',
    'search_box'         : r'//*[@name="q"]',
    'pop_search_format'  : r'//*[@id="sa_{}"]',
    'bottom_pane_link'   : r'//*[@id="crs_itemLink_{}"]',
    'pc_progress'        : r'//*[@id="srch1-2-15-Control-Exist"]/div[2]',
    'mobile_progress'    : r'//*[@id="mobsrch1-2-10-Control-Exist"]/div[2]',
    'mobile_pop_link'    : r'//*[@id="pop_link{}"]',
    'sidebar_related'    : r'//*[@id="b_context"]/li/ul/li[{}]/a',
    'mobile_related'     : r'//*[@class="b_rs"]/div/div/ul[{}]/li[{}]/a',
    'related_searches'   : r'//*[@id="b_results"]/li[7]/div/div/' \
                                        'div/ul[{}]/li[{}]/a',
}
    


def get_adblock():

    global adblock_xpi
    adblock_file_name = 'adblock.xpi'
    dest_dir = 'adblockplus'
    adblock_git_url = 'https://github.com/adblockplus/adblockplus.git'
    ##adblock_git_url = 'https://github.com/adblockplus/adblockplus/archive/master.zip'
    
    #check to see if adblock.xpi doesn't already exist
    if not os.path.exists(os.path.join(FILE_DIRECTORY, adblock_file_name)):
        # download the repo
        adp_zip_name = adblock_file_name.split('.')[0] + '.zip'
        adp_zip = requests.get(adblock_git_url)
        # write to zip
        with open(adp_zip_name, 'wb') as fh:
            fh.write(adp_zip.content)
        # make directory
        os.makedirs(dest_dir)
        with ZipFile(adp_zip_name, 'r') as zf:
            zf.extractall(dest_dir)
        # execute the build
        os.system("python {0}/adblockplus-master/build.py build {1}".format(
                                                    dest_dir, adblock_file_name))
        assert os.path.exists(os.path.join(FILE_DIRECTORY, adblock_file_name))
        
        #clean up
        os.remove(adp_zip_name)
        shutil.rmtree(dest_dir)

    adblock_xpi = adblock_file_name
    

def get_keyword_files(directory = FILE_DIRECTORY):
    global keyword_files
    for filename in os.listdir(AUXILARY_DATA_DIRECTORY):
        if filename.endswith('_keywords.txt'):
            keyword_files.append(filename)

def get_user_info(fileName = PREPEND_AUX("userInfo.txt")):
    with open(fileName, 'r') as fh:
        user = fh.readline().split("=")[-1].strip()
        pass_= fh.readline().split("=")[-1].strip()

    return (user, pass_)

def get_stop_words(fileName = STOP_WORDS):
    stopwords = []
    with open(fileName, 'r') as fh:
        stopwords = filter(lambda x: x != "", 
                        map(lambda line: line.strip(), fh.readlines()))
    return stopwords


def initialize_driver(url, userInfo, passInfo, prof = None ):
    """ signs into outlook and returns driver
        Optional argument of prof can change UA of driver
    """

    default_prof = webdriver.FirefoxProfile()
    default_prof.set_preference("dom.max_chrome_script_run_time", 0)
    default_prof.set_preference("dom.max_script_run_time", 0)
    default_prof.set_preference('dom.ipc.plugins.enabled.libflashplayer.so',
                                      'false')
    default_prof.set_preference("javascript.enabled", False);

    profile_to_use = prof if prof is not None else default_prof
    profile_to_use.add_extension(extension=adblock_xpi)


    driver = webdriver.Firefox(profile_to_use)

    time.sleep(10)
    driver.get("http://www.outlook.com")

    try:
        user = driver.find_element_by_name("loginfmt")
        pass_ = driver.find_element_by_name("passwd")
        user.send_keys(userInfo)
        pass_.send_keys(passInfo)
        time.sleep(5)
        user.submit()
    except (NoSuchElementException, TimeoutException) as err:
        print("Couldn't initialize browser: %s", err)

    time.sleep(10)
    return driver

def get_driver_ua(driver):
    return driver.execute_script("return navigator.userAgent")

#def search_email_for(driver, text="Bing"):
#    if "Outlook" not in driver.title:
#        print ("not on email page")
#    q = driver.find_element_by_name("query")
#    q.send_keys(text) 
#    q.submit()
#    time.sleep(5)

def get_bing_page(driver, url = BING_URL):
    driver.get(url)
    assert "Bing" in driver.title
    time.sleep(5)

def query_bing(driver, search = "Sub-optimal traceroute implementation"):
    assert "Bing" in driver.title, "Not on correct page"
    in_ = driver.find_element_by_id("sb_form_q")
    in_.clear() # clear existing
    in_.send_keys(search)
    time.sleep(5)
    in_.submit()

def click_link(driver, link_element):
    if not hasattr(link_element, 'click'):
        return
    if not any(map(lambda x: x in link_element.text.lower(), AVOID_LINKS)):
        link_element.click()
        


def populate_search_terms(textfile = PREPEND_AUX('interests.txt')):
    'assume a clean file with lines of keywords'
    terms = []
    with open(PREPEND_AUX(textfile), 'r') as fh:
        terms = map(lambda l: l.strip(), fh.readlines())
    return list(terms)

def get_random_search(keywords = populate_search_terms()):
    query = None

    while not query:
        query = random.choice(keywords)
    return unicode(query, errors = 'replace')

def is_offer_already_claimed(link_element):
    """ takes a link element and sees if it has class ="progress"
        returns true if 'of' not in the progress or if there is an error
    """
    try:
        text = link_element.find_element_by_class_name("progress").text
        if 'of' in text:
            return False
    except (NoSuchElementException, AttributeError):
        pass

    return True
        

def get_bing_special_offers(driver):
    
    if get_driver_ua(driver) == MOBILE_UA:
        return

    driver.get('https://www.bing.com/rewards/dashboard')
    assert "Bing Rewards" in driver.title

    
    get_offer_box = lambda : driver.find_element_by_xpath(XPATHS['offer_box'])

    #get current window name for later use
    main_window = driver.current_window_handle

    offers_list = get_offer_box().find_elements_by_tag_name('li')
    number_of_offers = len(offers_list) 
    #cycle through the offers and avoid the trivia offer and Status ones
    for i in range(number_of_offers):
        # after clicking a link, the link shifts down.  So it is appropriate to keep on clicking link 1
        list_item = offers_list[1]
        list_item_text = list_item.text
        
        if ("Trivia" in list_item_text or "Status" in list_item_text or
                 is_offer_already_claimed(list_item)):
            continue
        else:
            #click on link usually opens in new window
            list_item.find_element_by_tag_name('a').click()
            try:
                new_window_handle = driver.window_handles[1]
                driver.switch_to_window(new_window_handle)
                driver.close()
                driver.switch_to_window(main_window)
                # at this point offers_list may have changed
                offers_list = get_offer_box().find_elements_by_tag_name('li')
            except IndexError:
                #new window did not open maybe just go back?
                driver.back()
    

def get_bing_popular_search(driver, n=-1):     #default behavior is random
    """ get popular search
    params: driver: driver to use
            n: nth popular item
    """
    popular_n = 7                               #number of popular links
    if not driver.title.strip() == 'Bing':
        driver.get(BING_URL)
    
    if n < 0 or n > popular_n:
        n = random.randint(0, popular_n)

    search_box = driver.find_element_by_xpath(XPATHS['search_box'])
    search_box.click()                          #bring up the popular now box
    time.sleep(3)  #let box show
    xpath_fmt = XPATHS['pop_search_format']
    li = driver.find_element_by_xpath(xpath_fmt.format(n))
    click_link(driver, li)                                   #now you can click on the hidden element

def get_bing_bottom_pane_link(driver, n=-1):
    """ On the bing page, there are a bunch of links on the bottom
        let's get em
    """
    max_links = 24      
    print get_driver_ua(driver), get_driver_ua(driver) == MOBILE_UA
    if get_driver_ua(driver) == MOBILE_UA:
        get_bing_mobile_popular_link(driver, n)
        return

    if not driver.title.strip() == 'Bing':
        driver.get(BING_URL)
        time.sleep(random.randint(5, 10))      # wait for page to load
    if n < 0 or n > max_links:
        n = random.randint(0, max_links)


    xpath_fmt = XPATHS['bottom_pane_link']

    li = driver.find_element_by_xpath(xpath_fmt.format(n))
    click_link(driver, li)
    

def close_driver(driver, sleepTime=30):
    time.sleep(sleepTime)
    driver.close()

def setup_mobile_profile():
    """ Sets up a profile to use with driver, returns profile"""
    prof = webdriver.FirefoxProfile()
    ua_string = MOBILE_UA
    prof.set_preference("general.useragent.override", ua_string)
    prof.set_preference("dom.max_chrome_script_run_time", 0)
    prof.set_preference("dom.max_script_run_time", 0)
    prof.set_preference('dom.ipc.plugins.enabled.libflashplayer.so',
                                      'false')
    return prof

def click(driver, link):
    """ controls the behavior of clicking with driver """
    try:
        pass
    except (TimeoutException, Exception) as e:
        pass
    pass

def getDailySearchesLeft(driver):
    """ returns true if exceeded daily search usage, false otherwise"""
    url = 'https://www.bing.com/rewards/dashboard'
    driver.get(url)

    try:
        progress_pc_xpath = XPATHS['pc_progress']
        progress_mobile_xpath = XPATHS['mobile_progress']
        pc_points_earned = driver.find_element_by_xpath(progress_pc_xpath)
        mobile_points_earned = driver.find_element_by_xpath(progress_mobile_xpath)
    except NoSuchElementException:
        return (30, 15)
    # click on the dropdown

    
    exceed_daily_limits = lambda x: 'of' not in x
    get_remaining_searches = lambda x: 15 - int(x.split('of')[0].strip())

    pc_exceeded = exceed_daily_limits(pc_points_earned.text)
    mobile_exceeded = exceed_daily_limits(mobile_points_earned.text)
    print (pc_exceeded, mobile_exceeded)
    
    # how many searches are left?
    mobile_searches_left = 0
    pc_searches_left = 0
    if not pc_exceeded:
        pc_searches_left = get_remaining_searches(pc_points_earned.text) 
    if not mobile_exceeded:
        mobile_searches_left = get_remaining_searches(mobile_points_earned.text)
    
    # client checks to see if these are 0, else that means we got some to go
    return (pc_searches_left, mobile_searches_left)

def get_bing_mobile_popular_link(driver, n=-1):
    """ on mobile pages the links have pop_link instead of crs_itemLink"""
    max_links = 5

    if not driver.title.strip() == 'Bing':
        driver.get(BING_URL)
        time.sleep(random.randint(5, 10))
    if n < 0 or n > max_links:
        n = random.randint(0, max_links)

    xpath_fmt = XPATHS['mobile_pop_link']
    li = driver.find_element_by_xpath(xpath_fmt.format(n))
    click_link(driver, li)

def behavior_search_sequence(driver, st, cycles = 30):
    for i in range(30):
        time.sleep(random.randint(0,30))
        get_bing_bottom_pane_link(driver)
        time.sleep(random.randint(5,30))
        
        if random.randint(0,5):
            get_bing_page(driver)
            query_bing(driver, get_random_search(st))

def behavior_researching(driver,stop_words, st, cycles = 30):
    for i in range(cycles):
        get_bing_page(driver)
        query_bing(driver, get_random_search(st))
        if not random.randint(0,4):
            behavior_get_related_search(driver)
         #research
        kw = behavior_search_click_on_links(driver, stop_words, st, .25)
         # should i search more?
        if not random.randint(0,4):
            behavior_use_keywords_for_searches(driver, kw, st, stop_words)
            if not random.randint(0,10):
                behavior_get_related_search(driver)
         #oh no got distracted
        get_bing_page(driver)
        get_bing_bottom_pane_link(driver)
        time.sleep(random.randint(0,30))
        if not random.randint(0,10):
            behavior_get_related_search(driver)
            if not random.randint(0,10):
                behavior_search_click_on_links(driver, stop_words, st, .10)

def behavior_get_related_search(driver):
    related_searches_xpath = XPATHS['related_searches'] 
    sidebar_related_xpath= XPATHS['sidebar_related']
    mobile_related_xpath = XPATHS['mobile_related']
    # this is for the in text related searches for...
    col, row = range(1,3), range(1,4)
    link = None

    if get_driver_ua(driver) != MOBILE_UA:
        #desktop
        try:
            #first click on the intext related searches
            link = driver.find_element_by_xpath(related_searches_xpath.format(
                                        random.choice(col), random.choice(row)))
            click_link(driver, link)
        except NoSuchElementException:
            try:
                link = driver.find_element_by_xpath(
                             sidebar_related_xpath.format(random.choice(row)))
                click_link(driver, link)
            except NoSuchElementException:
                print "ERROR in finding relating search" 
    else:
        try:
            link = driver.find_element_by_xpath(mobile_related_xpath.format(
                                        random.choice(col), random.choice(row)))
            click_link(driver, link)
        except NoSuchElementException:
            print "Error in mobile related search" 
        

def get_search_result(driver, low, high):
    """ Get a webdriver element from results page, checks two variations """
    if "- Bing" not in driver.title.strip():
        return
    result_xpath_var_1 = r'//*[@id="b_results"]/li[{}]/h2/a' 
    result_xpath_var_2 = r'//*[@id="b_results"]/li[{}]/div[1]/h2/a'
    
    n = low if low == high else random.randint(low, high)

    link = None
    trys = 0
    found = False
    while trys < 3 and not found:
        try:
            link = driver.find_element_by_xpath(result_xpath_var_1.format(n))
            found = True
        except NoSuchElementException:
            print "trying again"
            try:
                link = (driver.
                        find_element_by_xpath(result_xpath_var_2.format(n)))
                found = True
            except NoSuchElementException:
                # try next link or better yet return not found object
                trys += 1
                n += 1
                print "trys: {} n: {}".format(trys, n)

    return link

def behavior_search_click_on_links(driver, stop_words, st, click_prob = .10):
    """ Goes through a search result and randomly clicks 
    driver: driver being used for search
    stop_words: a list of common used words in the language of results
    click_prob: chance of clicking through

    returns a list of keywords to try to search later
    """
    # It is possible that there may be more results than these but for now lets make it work
    beginningResult = 1 
    endingResult = 11
    keywords_to_try = []
        
    # After getting a page of results
    if  get_driver_ua(driver) != MOBILE_UA:
        if (driver.title.strip() == 'Bing' or not 
            driver.find_element_by_xpath(XPATHS['search_result_count'])):
            get_bing_page(driver)
            query_bing(driver, get_random_search(st))
    else:
        if (driver.title.strip() == 'Bing'  or not
            driver.find_element_by_xpath('//*[@id="b_results"]')):
            get_bing_page(driver)
            query_bing(driver, get_random_search(st))
    # try one of the first five links
    link = get_search_result(driver, 1,5)
    if not link:
        get_bing_page(driver)
        query_bing(driver, get_random_search(st))
        link = get_search_result(driver, 1,5)
    click_link(driver, link)
    # stay on those links for a random amount of time
    time.sleep(random.randint(1,60))

    #add some keywords to the bucket
    #if can't find p, then find another thing
    try:
        text = driver.find_element_by_tag_name('p').text
    except NoSuchElementException:
        text = driver.title.strip() 

    
    keywords_to_try.extend(filter_text(text, stop_words))

    # try going to another link on the page try with bs4
    # go back to the search results, while title of page doesn't indicate anything about search results
    get_back_to_search_results(driver)
    # go on the next two pages, and with a click prob, click on any links along the way
    search_depth = 0
    next_xpath = r'//*[@class="sb_pagN"]' 
    while search_depth < 3:
        # with probability of 10 percent, break out of search
        if not random.randint(0, 10):
            break 
        current_link = None
        for i in range(beginningResult+5 ,endingResult+1):
            current_link = get_search_result(driver, i,i)

            if random.random() <= click_prob and current_link:
                click_link(driver, current_link)
                time.sleep(4) #random.randint(20,60))
                #get some keywords from each page
                if not random.randint(0,5):  # make this unlikely
                    text = scrape_text_from_page(driver)
                    text = filter_text(text, stop_words)
                    keywords_to_try.extend(text)
            get_back_to_search_results(driver)
            #time.sleep(5)
        try:
            driver.find_element_by_xpath(next_xpath).click()
        except NoSuchElementException:
            break
            
        search_depth += 1
       
    return keywords_to_try 
            
def behavior_use_keywords_for_searches(driver, key_words, stop_words, st):        

    # shuffle keywords
    random.shuffle(key_words)
    
    while key_words:
        search_phrase = ""
        for i in range(3):
            if key_words:
                search_phrase += key_words.pop() + " "
        query_bing(driver, search_phrase)
        
        # pick up some new words?
        behavior_search_click_on_links(driver, stop_words, st, .25)

        if random.random() < .05:
            break

    return    
         
         
def get_back_to_search_results(driver):
    count = 0

    while True and count < 5:
        try:
            if get_driver_ua(driver) == MOBILE_UA:
                driver.find_element_by_xpath('//*[@id="b_results"]')
            else:
                driver.find_element_by_xpath('//*[@id="b_tween"]')
                
            return
        except UnexpectedAlertPresentException:
            Alert(driver).dismiss() 
            driver.back()
            count += 1
        except NoSuchElementException:
            # attempt to go back until 5 attempts then just exit
            print "count = {}".format(count)
            driver.back()
            count += 1
    get_bing_page(driver)
    get_bing_bottom_pane_link(driver)  
    return


def scrape_text_from_page(driver):
    text = ""
    tags = ['h2', 'h1', 'h4', 'h3', 'strong', 'p']
    random.shuffle(tags)
    for tag in tags:
        if text:
            break
        try:
            text = driver.find_element_by_tag_name(tag).text
        except NoSuchElementException:
            continue
    return text


def filter_text(text, stop_words, p = string.punctuation):

    wo_stopwords = filter(lambda x: x.strip().lower() not in stop_words, 
                           text.split())
    filtered_text = map(lambda x: filter(lambda c: c not in p, x), wo_stopwords)
    return filtered_text

def debug():
    """
        Just for testing
    """
    driver = webdriver.Firefox()
    stop_words = get_stop_words()
    user_info, pass_info = get_user_info()
    get_bing_page(driver)
    return (driver, stop_words, user_info, pass_info)
    
   
def behavior_search_2(driver, stop_words, search_terms):
    print "getting bing page"
    get_bing_page(driver)
    print "querying.."
    query_bing(driver, get_random_search(search_terms))
    print "getting keywords.."
    kw = behavior_search_click_on_links(driver, stop_words, search_terms)
    time.sleep(5)
    print "behavior use keywords for searches"
    behavior_use_keywords_for_searches(driver, kw, stop_words, search_terms)

    if not random.randint(0,10):
        get_bing_bottom_pane_link(driver)
        kw = behavior_search_click_on_links(driver, stop_words, search_terms)
        behavior_use_keywords_for_searches(driver, kw, stop_words, search_terms)

def closeExtraWindows(driver, main_window, other_windows):

    for window_handle in other_windows:
        if window_handle != main_window:
            new_window_handle = window_handle
            driver.switch_to_window(new_window_handle)
            driver.close()
    if driver.current_window_handle != main_window:
        driver.switch_to_window(main_window)
    
def stopSearchAtThreshold(driver):
    exceeded = False
    pc_searches_left, mobile_searches_left = getDailySearchesLeft(driver)
    return (pc_searches_left == 0, mobile_searches_left == 0)
         
    
def main():
    stop_words = get_stop_words()

    get_keyword_files() 
    search_terms = populate_search_terms(random.choice(keyword_files))
    userInfo, passInfo = get_user_info()
    #adblock
    get_adblock()

    driver = initialize_driver(ENTRY_URL, userInfo, passInfo)
    driver_mobile = initialize_driver(ENTRY_URL, userInfo, passInfo,
                                      prof = setup_mobile_profile())
    get_bing_page(driver)
    

    time.sleep(10)
    pc_searches_left, mobile_searches_left = getDailySearchesLeft(driver)
    get_bing_page(driver)

   
    # Here you can mix and match what sort of behavior you want
    # if there are no searches left to perform, the loop exits
    for d,n in [(driver, pc_searches_left*2), 
                (driver_mobile, mobile_searches_left*2)]: 
        ## check offers
        print "getting bing offers"
        get_bing_special_offers(d) 

        main_window = d.current_window_handle
        for _ in range(n):
            behavior_search_2(d, stop_words, search_terms)
            closeExtraWindows(d, main_window, d.window_handles)
            if  d == driver and stopSearchAtThreshold(driver)[0]:
                break
            elif d == driver_mobile and stopSearchAtThreshold(driver)[1]:
                break

    map(close_driver, [driver, driver_mobile]) 

if __name__ == "__main__":
    main()    
