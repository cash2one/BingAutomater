import unittest
import os
import sys
import time


from selenium import webdriver
from selenium.common.exceptions import (TimeoutException,
                                        NoSuchElementException)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

import BingAutomater
from BingAutomater import BingSearcher



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
        
    
class TestDriver(unittest.TestCase):
    def setUp(self):
        self.auth_info = "user", "pass"
        self.bs = BingSearcher(self.auth_info) 
    
    def test_BingSearcher_initial_attributes(self):
        s = self.bs

        # test if the preferences are the same
        self.assertEqual(s.profile.default_preferences, BingAutomater.make_profile().default_preferences)
        self.assertEqual(self.auth_info, (s.user, s.pw))

    def test_BingSearcher_can_get_stop_words(self):
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
        url = 'login.live.com' 
        d.get(url)

        self.assertIn(url, d.current_url)

    
    def test_authenticate_a_user_into_outlook(self):
        self.bs.initializeDriver()
        self.bs.user, self.bs.pw = BingAutomater.get_user_info()
        d = self.bs.driver


        self.bs.authenticate()

        # if everything worked go to bing page
        d.get('http://bing.com')
        time.sleep(3)
        try:
            # here you should see your name inside the contents of id_n
            e = WebDriverWait(d, 5).until(
                EC.presence_of_element_located((By.ID, 'id_n')),
            ) 
            self.assertNotEqual(e.text, '') 
            
        except NoSuchElementException:
            self.fail("Couldn't authenticate")
        

    def tearDown(self):
        try:
            self.bs.driver.close()
        except AttributeError:
            pass

        
         
