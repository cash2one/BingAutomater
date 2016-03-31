import unittest
import os
import sys
import time
import random


from selenium import webdriver
from selenium.common.exceptions import (TimeoutException,
                                        NoSuchElementException)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

import BingAutomater
from BingAutomater import BingSearcher, MobileSearcher, PCSearcher

# this is used for the custom selenium wait function
test_html = """
               <!DOCTYPE html>
               <html>
                <body>

                    <script>
                    (function main() {
                      var newNode = document.createElement('p');
                      document.body.appendChild(newNode); 
                      
                      window.setTimeout(function() {
                        newNode.innerHTML = "not null"; 
                      }, %s);
                    }());
                    </script>
                
                </body>
               </html>
"""


class TestUtilities(unittest.TestCase):
    
    def test_make_profile(self):
        profile = BingAutomater.make_profile()

        profile_type = type(profile)
        is_it_equal = profile_type == type(webdriver.FirefoxProfile())

        javascript_enabled = profile.default_preferences.get('javascript.enabled', None)
        max_script_run_time = profile.default_preferences.get('dom.max_script_run_time', None) 
        

        self.assertTrue(is_it_equal)
        self.assertFalse(javascript_enabled)
        self.assertEqual(max_script_run_time, 0)


    def test_get_adblock(self):
        xpi_name = 'adblock.xpi'

        adblock_xpi = BingAutomater.get_adblock()
        
        adblock_exists = os.path.exists('./adblock.xpi')
        xpi_set= xpi_name == adblock_xpi

        self.assertTrue(adblock_exists)
        self.assertTrue(xpi_set)


    def test_get_keyword_files(self):
        data_directory = BingAutomater.AUXILARY_DATA_DIRECTORY
        dummy_keyword_file = os.path.join(data_directory, 'dummy_keywords.txt')


        with open(dummy_keyword_file, 'w') as fp:
            fp.write('')
        
        BingAutomater.get_keyword_files()
        
        keywords_files_list = BingAutomater.KEYWORD_FILES

        self.assertIn(os.path.split(dummy_keyword_file)[-1], keywords_files_list)

        os.remove(dummy_keyword_file)

    def test_get_auth_info_from_file(self):
        dummy_user = 'Monty'
        dummy_password = 'Python'
        fName = 'test_auth.txt'

        with open(fName, 'w') as fp:
            fp.write("user={}\n".format(dummy_user))
            fp.write("pass={}\n".format(dummy_password))

        user, passInfo = BingAutomater.get_user_info(fName)
        
        self.assertEqual(dummy_user, user)
        self.assertEqual(dummy_password, passInfo) 

        os.remove(fName)


        
    
         
        
        
#@unittest.skip('skipping base class tests')    
class TestBingSearcher(unittest.TestCase):
    def setUp(self):
        self.auth_info = "user", "pass"
        self.bs = BingSearcher(self.auth_info) 
    
    def test_check_initial_attributes(self):
        s = self.bs

        # test if the preferences are the same
        self.assertEqual(s.profile.default_preferences, BingAutomater.make_profile().default_preferences)
        self.assertEqual(self.auth_info, (s.user, s.pw))

    def test_searcher_can_get_stop_words(self):
        # not sure what kind of stopwords we will have
        # just check to see if length of stopwords is larger than one as a
        # smoke screen

        s = self.bs

        s.getStopWords()
        
        sw = s.stopWords

        self.assertGreater(len(sw), 0)

    def test_install_adblock(self):
        s = self.bs
        s._install_adblock()

        # to see whether or not an extensions are installed
        # check the profile directory
        directory = s.profile.extensionsDir
        subdirectory = os.listdir(directory)[0]
        extension_path = os.path.join(directory, subdirectory)

        # adblock has a file called lib/antiadblockInit.js, test for it
        file_path = os.path.join(extension_path, 'lib/antiadblockInit.js')
        file_exists = os.path.exists(file_path)

        self.assertTrue(file_exists)

    def test_initialize_driver_and_test_that_it_is_working(self):
        self.bs.initializeDriver()
        d = self.bs.driver
        # test to see if it can get to the entry page
        time.sleep(3)
        url = 'login.live.com' 
        d.get(url)

        self.assertIn(url, d.current_url)


    def test_initializeDriver_setsMainWindow(self):
        self.bs.initializeDriver()
        mainHandle = self.bs.mainWindowHandle

        self.assertIsNotNone(mainHandle)

    
    def test_authenticate_a_user_into_outlook(self):
        self.bs.initializeDriver()
        self.bs.user, self.bs.pw = BingAutomater.get_user_info()
        d = self.bs.driver


        self.bs.authenticate()

        # if everything worked go to bing page
        d.get('http://bing.com')
        time.sleep(10)
        try:
            # here you should see your name inside the contents of id_n
            e = WebDriverWait(d, 5).until(
                EC.presence_of_element_located((By.ID, 'id_n')),
            ) 
            self.assertNotEqual(e.text, '') 
            
        except NoSuchElementException:
            self.fail("Couldn't authenticate")

    def test_isAuthenticated_returnsFalseWhenNotLoggedIn(self):
        self.bs.initializeDriver()
        self.bs.authenticate()

        authToken = self.bs.authToken
        is_authenticated = self.bs.isAuthenticated()

        self.assertIsNone(authToken) 

        self.assertFalse(is_authenticated)

    def test_isAuthenticated_returnsTrueWhenLoggedIn(self):
        self.bs.initializeDriver()
        self.bs.user, self.bs.pw = BingAutomater.get_user_info()
        self.bs.authenticate()

        authToken = self.bs.authToken
        is_authenticated = self.bs.isAuthenticated()

        self.assertIsNotNone(authToken)
        self.assertTrue(is_authenticated)

    def test_gotoHome_takes_you_to_the_bing_page(self):
        self.bs.initializeDriver()
        self.bs.user, self.bs.pw = BingAutomater.get_user_info()
        self.bs.authenticate()

        self.bs.gotoHome()

        title = self.bs.driver.title

        self.assertEqual(title.strip(), 'Bing')


    def test_populateKeywords_setsKeywordAttribute(self):
        kw = ['python', 'is', 'cool']

        with open('dummy.txt', 'w') as fp:
            for i in kw:
                fp.write(i)
                fp.write('\n')

        self.bs.populateSearchTerms('dummy.txt')
        
         
        self.assertEqual(kw, self.bs.searchTerms)

    def test_getRandomQuery(self):
        self.bs.initializeDriver()

        q = self.bs.randomQuery()

        self.assertIsNotNone(q)

    def test_getRandomQueryDoesNotSetSearchTerms(self):
        self.bs.initializeDriver()
        searchTerms = ['python', 'is', 'cool']
        self.bs.searchTerms = searchTerms

        q = self.bs.randomQuery()
        
        self.assertEqual(self.bs.searchTerms, searchTerms)  
        self.assertIn(q, searchTerms)
        
    def test_queryIsAbleToQuery(self):
        self.bs.initializeDriver()
        d = self.bs.driver
        
        query_string = random.choice('Linux Windows.10 Guitar Chairs Popular-Music'.split(' '))
        self.bs.query(query_string)
        time.sleep(2)

        self.assertIn(query_string, d.title)


    def test_click_clicksOnElement(self):
        self.bs.initializeDriver()
        self.bs.gotoHome()

        # this is the images button on the bing home page
        click_on = '//*[@id="scpl0"]'
        self.bs.restrictedPaths = []

        e = self.bs.driver.find_element_by_xpath(click_on)
        current_url = self.bs.driver.current_url
        self.bs.click(e)
        new_url = self.bs.driver.current_url

        self.assertNotEqual(current_url, new_url)
        
         

        

        
    
    def test_click_doesNotClickOnAForbiddenElement(self):

        self.bs.initializeDriver()
        self.bs.gotoHome()

        # this is the images button on the bing home page
        click_on = '//*[@id="scpl0"]'


        self.bs.restrictedPaths = ['Images',]
        e = self.bs.driver.find_element_by_xpath(click_on)
        current_url = self.bs.driver.current_url
        self.bs.click(e)
        new_url = self.bs.driver.current_url

        self.assertEqual(current_url, new_url)


    def test_multipleWindowsGetClosed(self):
        self.bs.initializeDriver()
        mainWindowHandle = self.bs.mainWindowHandle
        d = self.bs.driver

        # open up several windows
        body = d.find_element_by_tag_name('body')
        for i in range(3): 
            d.execute_script("window.open('')")

        self.assertEqual(len(d.window_handles), 4)

        self.bs.closeExtraWindows()

        # Close all windows and make sure your back on the main window
        self.assertEqual(len(d.window_handles), 1)
        self.assertEqual(d.current_window_handle, mainWindowHandle)

    def test_element_text_is_not_empty(self):
        # wait 5 seconds
        delay_time = 5000
        file_name = 'test_html.html'

        self.bs.initializeDriver()

        with open(file_name, 'w') as fh:
            # test with specified delaytime
            fh.write(test_html % (delay_time))

        # now you can navigate to the file
        self.bs.driver.get('file://'+os.getcwd() + '/'+ file_name)

        e = WebDriverWait(self.bs.driver, 10).until(
            BingAutomater.text_to_be_present_not_empty((By.XPATH, r'//p')),
        )
        

        os.remove(file_name)
        # if it all worked, then text should not be empty
        self.assertNotEqual('', e.text) 


    def test_element_text_is_empty(self):
        delay_time = 5000
        file_name = 'test_html.html'

        self.bs.initializeDriver()
        
        with open(file_name, 'w') as fh:
            fh.write(test_html % (delay_time))
        
        self.bs.driver.get('file://'+os.getcwd()+ '/' + file_name)

        with self.assertRaises(TimeoutException):
            e = WebDriverWait(self.bs.driver, 3).until(
                BingAutomater.text_to_be_present_not_empty((By.XPATH, r'//p')),
            )

        os.remove(file_name)




    def tearDown(self):
        try:
            self.bs.driver.close()

            if os.path.exists('dummy.txt'): 
                os.remove('dummy.txt')
        except AttributeError:
            pass

#@unittest.skip('Skipping pc tests')
class TestPCBingSearcher(unittest.TestCase):
    """ Not inheriting from base test class since that one replicates most of the functionallity in this class """
    
    def setUp(self):
        self.auth_info = "user", "pass"
        self.bs = PCSearcher(self.auth_info)     

    def test_updateRemainingSearches_setsAttribute(self):
        self.bs.initializeDriver()
        self.bs.user, self.bs.pw = BingAutomater.get_user_info()
    
        d = self.bs.driver

        self.bs.authenticate()

        self.bs.updateRemainingSearches()

        self.assertIsNotNone(self.bs.remainingSearches)  

        # check if it is the correct result by manually doing it here
        ns = PCSearcher()
        ns.initializeDriver()
        ns.authenticate()
        ns.driver.get(BingAutomater.REWARDS_URL) 

        try:
            e = WebDriverWait(ns.driver, 30).until (
                EC.presence_of_element_located((By.XPATH, '//*[@id="srch1-2-15-NOT_T1T3_Control-Exist"]/div[2]'))
            )

            if 'of' in e.text:
                done, _, out_of, _ = e.text.split()
                remaining = int(out_of) - int(done)

                self.assertEqual(remaining, self.bs.remainingSearches)
            
            
        except (NoSuchElementException, TimeoutException):
            self.fail("Couldn't Find the pc progress element")
        finally:
            ns.driver.close()

    def test_updateRemainingSearches_catchesAllPointsClaimedCondition(self):
        self.bs.initializeDriver()
        self.bs.user, self.bs.pw = BingAutomater.get_user_info()
        d = self.bs.driver
        self.bs.authenticate()
        self.bs.updateRemainingSearches()

        ns = PCSearcher()
        ns.initializeDriver()
        ns.authenticate()
        ns.driver.get(BingAutomater.REWARDS_URL)

        try:
            e = WebDriverWait(ns.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, BingAutomater.XPATHS['pc_progress']))
            )

            if 'of' not in e.text:
                remaining = 0

                self.assertEqual(remaining, self.bs.remainingSearches)                

        except (NoSuchElementException, TimeoutException):
            self.fail("Couldn't find the pc progress element")

        finally:
            ns.driver.close()


    def test_getSpecialOffers(self):
        self.bs.initializeDriver()
        self.bs.user, self.bs.pw = BingAutomater.get_user_info()
        self.bs.authenticate
        d = self.bs.driver

        ns = PCSearcher()
        ns.initializeDriver()
        ns.authenticate()
        ns.driver.get(BingAutomater.REWARDS_URL)

        offer_box = ns.driver.find_element_by_xpath(BingAutomater.XPATHS['offer_box'])
        offers = [offer for offer in offer_box.find_elements_by_tag_name('li') if 'of 1' in offer.text]

        if len(offers) > 0:
            self.bs.getSpecialOffers()
            
            ns.driver.refresh()
            offer_box = ns.driver.find_element_by_xpath(BingAutomater.XPATHS['offer_box'])
            offers = [offer for offer in offer_box.find_elements_by_tag_name('li') if 'of 1' in offer.text]

            ns.driver.close()
            self.assertEqual(0, len(offers))

        else:
            ns.driver.close()
            self.assertTrue(True)


    def test_playTriviaGame(self):
        self.bs.initializeDriver()
        self.bs.user, self.bs.pw = BingAutomater.get_user_info()
        d = self.bs.driver
        self.bs.authenticate()

        ns = PCSearcher()
        ns.initializeDriver()
        ns.authenticate()
        time.sleep(3)
        ns.driver.get(BingAutomater.REWARDS_URL)

        try:
            e = ns.driver.find_element_by_xpath('//*[@class="progress" and contains(text(), "3")]')
            

            credits_received = int(e.text.split(" ")[0])
            

            self.bs.playTriviaGame()
        
            ns.driver.refresh()
            e = ns.driver.find_element_by_xpath('//*[@class="progress" and contains(text(), "3")]')

            # should get 3 credits
            self.assertEqual(int(e.text.split()[0]), 3)


        except NoSuchElementException as e:
            self.fail("Couldn't find the quiz element: {}".format(e))

        finally:
            ns.driver.close()
            

    def tearDown(self):
        if hasattr(self.bs, 'driver'):
            self.bs.driver.close()


         
#@unittest.skip('skipping mobile searcher tests')
class TestMobileBingSearcher(TestBingSearcher):

    def setUp(self):
        self.auth_info = "user", "pass"
        self.bs = MobileSearcher(self.auth_info) 

    def test_check_initial_attributes(self):
        ua = self.bs.profile.default_preferences['general.useragent.override']

        # UA string must be the mobile ua string
        self.assertEqual(BingAutomater.MOBILE_UA, ua)

    def test_authenticate_a_user_into_outlook(self):
        self.bs.initializeDriver()
        self.bs.user, self.bs.pw = BingAutomater.get_user_info()
        d = self.bs.driver


        self.bs.authenticate()

        # if everything worked you would see a signout link at the bottom of the page
        try:
            # here you should see your name inside the contents of id_n
            e = WebDriverWait(d, 10).until(
                EC.presence_of_element_located((By.XPATH, r'//*[@id="c_f_ul1"]/li[2]/span[1]')),
            ) 
            self.assertEqual(e.text.lower().strip(), 'sign out') 
            
        except NoSuchElementException:
            self.fail("Couldn't authenticate")

    def test_getRemainingSearches_setsAttribute(self):

        self.bs.initializeDriver()
        self.bs.user, self.bs.pw = BingAutomater.get_user_info()
        d = self.bs.driver
        self.bs.authenticate()

        self.bs.updateRemainingSearches() 

        remainingSearches = self.bs.remainingSearches

        self.assertIsNotNone(remainingSearches)

        # is it the correct result?
        ns = MobileSearcher()
        ns.initializeDriver()
        ns.authenticate()
        ns.driver.get(BingAutomater.REWARDS_URL)

        try:
            e = WebDriverWait(ns.driver, 10).until(
                BingAutomater.text_to_be_present_not_empty(
                    (By.XPATH, r'//*[@id="credit-progress"]/div[5]')
                ),
            )

            done = int(e.find_element_by_class_name("primary").text)
            outof = int(e.find_element_by_class_name("secondary").text.strip("/"))
            remaining = outof - done 
            
            self.assertEqual(remaining, self.bs.remainingSearches)

        except (NoSuchElementException, TimeoutException):
            self.fail("The layout of bing rewards may have been changed")
        finally:
            ns.driver.close()

    def test_getSpecialOffers(self):
        # get to the rewards page
        self.bs.initializeDriver()
        self.bs.user, self.bs.pw = BingAutomater.get_user_info()
        d = self.bs.driver
        self.bs.authenticate()

        ns = MobileSearcher()
        ns.initializeDriver()
        ns.authenticate()
        ns.driver.get(BingAutomater.REWARDS_URL+'?showOffers=1')

        offers = filter(lambda offer: 'Tap' in offer.text, ns.driver.find_elements_by_class_name('cta'))
        # see if there are is anything to tap
        if len(offers):
            # if there is perform the operation
            self.bs.getSpecialOffers() 
            # after the action has been performed
            # check to see if there are any remaining offers
            ns.driver.refresh()
            offers = filter(
                        lambda offer: 'Tap' in offer.text, 
                        ns.driver.find_elements_by_class_name('cta')
            )
            
            ns.driver.close()
            # if there are, then the test failed. otherwise operation is a success
            self.assertEqual(0, len(offers))
            
        
        else: 
            # if not I guess the test passed
            self.assertTrue(True)

        ns.driver.close()


    def tearDown(self):
        if hasattr(self.bs, 'driver'):
            self.bs.driver.close()
