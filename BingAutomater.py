import os
import shutil
from zipfile import ZipFile
import time
import random

import requests


from selenium import webdriver 
from selenium.common.exceptions import (TimeoutException,  
               NoSuchElementException, 
                ElementNotVisibleException,
               UnexpectedAlertPresentException,
               StaleElementReferenceException) 
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0 
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys

# globals
ENTRY_URL = "https://www.outlook.com"
HOME_URL  = "https://bing.com"
REWARDS_URL = "https://bing.com/rewards/dashboard"
FILE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
AUXILARY_DATA_DIRECTORY = os.path.join(FILE_DIRECTORY, 'auxilary_data')
KEYWORD_FILES  = []
PREPEND_AUX             = lambda f: os.path.join(AUXILARY_DATA_DIRECTORY, f)
STOP_WORDS = PREPEND_AUX("stop-word-list.txt")

# xpaths

XPATHS = {
    'pc_progress'        : r'//*[@id="srch1-2-15-NOT_T1T3_Control-Exist"]/div[2]',
    'mobile_progress'    : r'//*[@id="credit-progress"]/div[5]',
    'offer_box'          : r'//*[@class="offers"]/div[1]',
    'quiz'               : r'//*[@class="progress" and contains(text(), "3")]',
    'quiz_link'          : r'//a[contains(@id, "BingRewardsQuiz")]',
    'start_quiz'         : r'',
}

# Mobile UA string, can change this to another mobile UA string
# Run Tests afterwards to see if the change doesn't break the script
MOBILE_UA = 'Mozilla/5.0 (Linux; Android 4.4.4; en-us; Nexus 5 Build/JOP40D)'

def make_profile():
    """ Set up a profile and return it """

    profile = webdriver.FirefoxProfile()
    profile.set_preference("dom.max_chrome_script_run_time", 0)
    profile.set_preference("dom.max_script_run_time", 0)
    profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so',
                                      'false')
    profile.set_preference("javascript.enabled", False)
    

    #profile_to_use.add_extension(extension=adblock_xpi)
    return profile



def get_adblock():

    adblock_file_name = 'adblock.xpi'
    dest_dir = 'adblockplus'
    ##adblock_git_url = 'https://github.com/adblockplus/adblockplus.git'
    adblock_git_url = 'https://github.com/adblockplus/adblockplus/archive/master.zip'
    buildtools_url = 'https://github.com/adblockplus/buildtools/archive/master.zip'
    
    #check to see if adblock.xpi doesn't already exist
    if not os.path.exists(os.path.join(FILE_DIRECTORY, adblock_file_name)):
        # download the repo
        adp_zip_name = adblock_file_name.split('.')[0] + '.zip'
        adp_zip = requests.get(adblock_git_url)
        buildtools_zip = requests.get(buildtools_url)
        # write to zip
        with open(adp_zip_name, 'wb') as fh:
            fh.write(adp_zip.content)
        with open('buildtools.zip', 'wb') as fh:
            fh.write(buildtools_zip.content)

        # make directory
        os.makedirs(dest_dir)
        with ZipFile(adp_zip_name, 'r') as zf:
            zf.extractall(dest_dir)

        with ZipFile('buildtools.zip') as zf:
            zf.extractall(dest_dir+'/adblockplus-master')
        # execute the build
        os.system("python {0}/adblockplus-master/build.py build {1}".format(
                                                    dest_dir, adblock_file_name))
        assert os.path.exists(os.path.join(FILE_DIRECTORY, adblock_file_name))
        
        #clean up
        os.remove(adp_zip_name)
        shutil.rmtree(dest_dir)
        os.remove('buildtools.zip')

    return adblock_file_name

def get_keyword_files():
    global KEYWORD_FILES
    for filename in os.listdir(AUXILARY_DATA_DIRECTORY):
        if filename.endswith('_keywords.txt'):
            KEYWORD_FILES.append(filename)


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


############
# Classes #
###########
class text_to_be_present_not_empty(object):
    """ An expectation for checking if the given elements text is not empty."""

    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        try:
            element = EC._find_element(driver, self.locator)
            return element if element.text != "" else False

        except StaleElementReferenceException:
            return False

class elements_to_be_present(object):
    """ An expectation for checking if elements should be present """
    
    def __init__(self, locator):
        self.locator = locator
    
    def __call__(self, driver):
        try:
            elements = EC._find_elements(driver, self.locator)
            return elements if len(elements) > 0 else False

        except StaleElementReferenceException:
            return False
    

class BingSearcher(object):

    def __init__(self,  auth_info=None, 
                 entry_url=ENTRY_URL, ua=None, 
                 profile=None):
        self.profile = profile if profile else make_profile()
        self.user, self.pw = auth_info if auth_info else get_user_info()
        self.authToken     = None
        self.remainingSearches = None
        self.mainWindowHandle  = None

       # self.initializeDriver()
        self.restrictedPaths = []

    def initializeDriver(self):
        """ Sets driver and loads outlook Page """
        self.getStopWords()
        self._install_adblock()        
        self.driver = webdriver.Firefox(self.profile)
        self.mainWindowHandle = self.driver.current_window_handle
        

    def authenticate(self):
        self.driver.get(ENTRY_URL)
        try:
            user = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'loginfmt'))
            )


        except (NoSuchElementException, TimeoutException) as err:
            print("Couldn't initialize browser: %s", err)

        else:
            pass_ = self.driver.find_element_by_name("passwd")
            user.send_keys(self.user)
            pass_.send_keys(self.pw)
            user.submit()
            time.sleep(5)

            self.authToken = self.driver.get_cookie('MSPAuth') 

    def isAuthenticated(self):
        return self.authToken != None

        

    def getStopWords(self):
        self.stopWords = get_stop_words()     

    def _install_adblock(self):
        xpi_name = get_adblock()
        self.profile.add_extension(xpi_name)


    def gotoHome(self):
        self.driver.get(HOME_URL)

    def updateRemainingSearches(self):
        return NotImplemented

    def getSpecialOffers(self):
        return NotImplemented

    def click(self, element):
        # control what is clicked and click
        if (hasattr(element, 'text') 
            and any([blocked in element.text for blocked  in self.restrictedPaths])):
            # break from here if the link has restricted text

            return
            
        if hasattr(element, 'click'):
            # process link
            element.click()

            
        

    def query(self, q='Bing Wikipedia'):
        if not "Bing" in self.driver.title:
            self.gotoHome()
        in_ = self.driver.find_element_by_id("sb_form_q")
        in_.clear()
        in_.send_keys(q)
        in_.submit()

    def randomQuery(self):
        q = None
        trys = 0
        MAX = 10

        if not hasattr(self, 'searchTerms'):
            self.populateSearchTerms()
            

        # in the previous version, an empty string could 
        # have resulted. stay safe here
        while not q and trys < MAX:
            q = random.choice(self.searchTerms) 
            trys += 1
        return unicode(q, errors = 'replace')
        
    def populateSearchTerms(self, f=None):
        if f is None:
            if len(KEYWORD_FILES) == 0:
                get_keyword_files()
            f = PREPEND_AUX(random.choice(KEYWORD_FILES))
            
        with open(f, 'r') as fh:
            self.searchTerms = map(lambda l: l.strip(), fh.readlines())


    def closeExtraWindows(self):
        otherWindows = self.driver.window_handles[1:] 

        if (self.driver.window_handles) > 1:
            for w in otherWindows:
                self.driver.switch_to_window(w)
                self.driver.close()

            self.switchToMainWindow() 


    def switchToMainWindow(self): 
        self.driver.switch_to_window(self.mainWindowHandle)
        
    

class PCSearcher(BingSearcher):

    def updateRemainingSearches(self):
        self.driver.get(REWARDS_URL)
        try:
            # add in a check to make sure not all credits are already claimed
            e = WebDriverWait(self.driver, 10).until (
                EC.presence_of_element_located((By.XPATH, XPATHS['pc_progress']))
            )

        except (NoSuchElementException, TimeoutException):
            self.remainingSearches = 16

        else:
            if 'of' in e.text:

                done, _, out_of, _ = e.text.split()
                remaining = int(out_of) - int(done)

                self.remainingSearches = remaining

            else:
                self.remainingSearches = 0

    def getSpecialOffers(self):
        self.driver.get(REWARDS_URL)
        

        main_window = self.driver.current_window_handle
        offerBox = self.driver.find_element_by_xpath(XPATHS['offer_box'])
        offers = filter(lambda offer: 'of 1' in offer.text,
                    offerBox.find_elements_by_tag_name('li')
        )

        while len(offers) > 0:
            offers[0].click()
                
            if len(self.driver.window_handles) > 1:
                #a new window opens up 
                new_window_handle = self.driver.window_handles[1]
                self.driver.switch_to_window(new_window_handle)
                self.driver.close()
                self.driver.switch_to_window(main_window)

            else:# new window doesn't open up
                self.driver.back()

                
            self.driver.refresh()
            offerBox = self.driver.find_element_by_xpath(XPATHS['offer_box'])
            offers = filter(lambda offer: 'of 1' in offer.text,
                        offerBox.find_elements_by_tag_name('li')
            )


    def playTriviaGame(self):
        self.driver.get(REWARDS_URL)
        l = self.driver.find_element_by_xpath(XPATHS['quiz_link'])
        self.click(l)

        trivia_window = self.driver.window_handles[-1]
        # switch to window
        self.driver.switch_to_window(trivia_window)
        start_game = self.driver.find_elements_by_id('rqStartQuiz')
        
        # start the trivia game
        self.click(start_game)

        def quizIsDone():
            try:
                e = (self
                    .driver
                    .find_element_by_xpath(r'//*[@id="quizCompleteContainer" '
                                             'and not('
                                              'contains(@class, "b_hide"))]')
                )
            except NoSuchElementException:
                return False
            else:
                return True

        time.sleep(10)

        while not quizIsDone():
            # blacked out answers have optionDisable class; thats why the 
            # space is left in the xpath below
            options = (self
                       .driver
                       .find_elements_by_xpath('//*[@class="option "]')
            )

            try:
                self.click(random.choice(options))
                time.sleep(5)
            except ElementNotVisibleException:
                time.sleep(5)

        self.closeExtraWindows()

    def getBottomPaneSearch(self):
        if self.driver.title != 'Bing':
            self.gotoHome()
        
        try:
            links = WebDriverWait(self.driver, 10).until (
                elements_to_be_present((By.XPATH, '//*[@id="crs_pane"]/li'))
            )

        except (NoSuchElementException, TimeoutException):
            return

        else:
            e = random.choice(links)
            self.click(e)
    

class MobileSearcher(BingSearcher):
    
    def __init__(self, *args, **kwargs):
        super(MobileSearcher, self).__init__(*args, **kwargs)
        self.setUA()
    
    def setUA(self):
        self.profile.set_preference('general.useragent.override', 
                                     MOBILE_UA)

    def updateRemainingSearches(self):
        self.driver.get(REWARDS_URL)

        try:
            e = WebDriverWait(self.driver, 10).until(
                text_to_be_present_not_empty((By.XPATH, 
                                              XPATHS['mobile_progress'])
                                            ),
            )

            done = int(e.find_element_by_class_name("primary").text)
            total = int(
                e.find_element_by_class_name("secondary").text.strip("/")
            )
            self.remainingSearches = total - done

        except TimeoutException:
            self.remainingSearches = 11

    def getSpecialOffers(self):
        showRewardsQuery = '?showOffers=1'
        self.driver.get(REWARDS_URL+showRewardsQuery)

        offers = filter(lambda offer: 'Tap' in offer.text,
                        self.driver.find_elements_by_class_name('cta')
        ) 


        while len(offers) > 0:
            offers[0].click()
            time.sleep(5)
            self.driver.get(REWARDS_URL+showRewardsQuery)
            
            
            offers = filter(lambda offer: 'Tap' in offer.text,
                        self.driver.find_elements_by_class_name('cta')
            
            )

    def getBottomPaneSearch(self):
        if self.driver.title != 'Bing':
            self.gotoHome()

        try:
            links = WebDriverWait(self.driver, 10).until (
                elements_to_be_present((By.XPATH, '//*[@id="hc_popnow"]//ul'))
            )

        except (NoSuchElementException, TimeoutException):
            return

        else:
            e = random.choice(link)
            self.click(e)
    
            
        
            
            
