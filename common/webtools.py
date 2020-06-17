# python 3.6
# webtools.py : Helper functions related to Selenium, Web Driver, lxml and requests used in 500px_APIless.py

import common.config as config
import common.apiless as apiless
import common.utils as utils
from common.config import LOG as logger
from common.utils import print_and_log, printB, printC, printG, printR, printY

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains  
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import NoSuchElementException   
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import TimeoutException

from lxml import html
import random, glob, random

import time
from time import sleep

#---------------------------------------------------------------
def get_element_text_by_xpath(page, xpath_string):
    """Return the text of element, specified by the element xpath. Return '' if element not found. """
    if page is None or not xpath_string:
        return ''
    ele = page.xpath(xpath_string)
    if ele is not None and len(ele) > 0 : 
        return ele[0].text
    return ''

#---------------------------------------------------------------
def get_element_attribute_by_ele_xpath(page, xpath, attribute_name):
    """Get the value of the given attribute name, at the element of the given xpath. Return '' if element not found."""
    if page is None or not xpath or not attribute_name:
        return ''
    ele = page.xpath(xpath)
    time.sleep(1)
    if ele and len(ele) > 0:
        try:
            return ele[0].attrib[attribute_name] 
        except:
            printR(f'   Error getting attribute {attribute_name}')
    return ''

#---------------------------------------------------------------
def get_web_ele_text_by_xpath(element_or_driver, xpath):
    """ Use WebDriver function to find text from a given xpath, return empty string if not found.
    
    Use absolute xpath if the driver is passed
    Use relative xpath if an web element is passed
     """
    if element_or_driver is None or not xpath:
        return ''
    try:
        ele = element_or_driver.find_element_by_xpath(xpath)
        if ele is not None:
            return ele.text       
    except NoSuchElementException:
        return ''

#---------------------------------------------------------------
def get_upload_date(driver, photo_link):
    """Given a photo link, returns the photo upload date or time. """

    driver.get(photo_link)
    last_photo_page_HTML = driver.execute_script("return document.body.innerHTML") 
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    page = html.document_fromstring(last_photo_page_HTML)
    p = page.xpath('//*[@id="root"]/div[4]/div/div[2]/div[3]/div[1]/div[2]/p/span')
                    
    if len(p) > 0:
        return p[0].text_content() 
    else: 
       return "not found" 

#---------------------------------------------------------------
def open_user_home_page(driver, user_name):
    """Open the home page of a given user and wait for the page to load. If the user page is not found or timed out (30s),
       return False and the error message. If not, return True and a blank message """ 
    if driver is None or not user_name:
        return False, f"    - Open {user_name}'s home page ..."

    driver.get('https://500px.com/' + user_name)
    # waiting until the page is opened
    main_window_handle = None
    time_out = 30
    count_down = time_out
    while not main_window_handle and count_down > 0:
        main_window_handle = driver.current_window_handle
        count_down -= 1
    if count_down <=0:
        return False, f"Timed out ({time_out}s) while opening {user_name}'s home page. Please retry"

    if check_and_get_ele_by_class_name(driver, 'not_found'):
        return False, f'User {user_name} does not exit'
    elif check_and_get_ele_by_class_name(driver, 'missing') is None:
        return True, ''
    else:
        return False, f'Error reading {user_name}\'s page. Please make sure a valid user name is used'

#---------------------------------------------------------------
def check_and_get_ele_by_xpath(element, xpath):
    """ Find the web element from a given xpath, return none if not found.
    
    The search can be limited within a given web element, or the whole document if the browser driver is passed instead of the web element
    """
    if element is None or not xpath:
        return  None
    try:
        return element.find_element_by_xpath(xpath)
    except NoSuchElementException:
        return None

#---------------------------------------------------------------
def check_and_get_all_elements_by_xpath(element, xpath):
    """ Find the web elements from a given xpath, return none if not found.
    
    The search can be limited within a given web element, or the whole document if the browser driver is passed instead of the web element
    """
    if element is None or not xpath:
        return  []
    try:
        return element.find_elements_by_xpath(xpath)
    except NoSuchElementException:
        return []

#---------------------------------------------------------------
def check_and_get_ele_by_class_name(element, class_name):
    """Find the web element of a given class name, return none if not found.
    
    The search can be limited within a given web element, or the whole document if the browser driver is passed instead of the web element
    """
    if element is None or not class_name:
        return None 
    try:
        return element.find_element_by_class_name(class_name) 
    except NoSuchElementException:
        return None

#---------------------------------------------------------------
def check_and_get_ele_by_id(element, id_name):
    """Find the web element of a given id, return none if not found.

    The search can be limited within a given web element, or the whole document if the browser driver is passed instead of the web element
    """
    if element is None or not id_name:
        return  None 
    try:
        return element.find_element_by_id(id_name) 
    except NoSuchElementException:
        return None

#---------------------------------------------------------------
def check_and_get_ele_by_tag_name(element, tag_name):
    """Find the web element of a given tag name, return none if not found.

    THE SEARCH CAN BE LIMITED WITHIN A GIVEN WEB ELEMENT, OR THE WHOLE DOCUMENT, BY PASSING THE BROWSER DRIVER
    """
    if element is None or not tag_name:
        return None   
    try:
        return element.find_element_by_tag_name(tag_name) 
    except NoSuchElementException:
        return None
 
#---------------------------------------------------------------
def check_and_get_all_elements_by_tag_name(element, tag_name):
    """Find all the web elements of a given tag name, return empty list if tag_name not found.

    The search can be limited within a given web element, or the whole document if the browser driver is passed instead of the web element
    """
    if element is None or not tag_name:
        return []
    try:
        return element.find_elements_by_tag_name(tag_name) 
    except NoSuchElementException:
        return []

#---------------------------------------------------------------
def check_and_get_all_elements_by_class_name(element, class_name):
    """Find all the web elements of a given class name, return empty list if class_name not found.

    The search can be limited within a given web element, or the whole document if the browser driver is passed instead of the web element
    """
    if element is None or not class_name:
        return []
    try:
        return element.find_elements_by_class_name(class_name) 
    except NoSuchElementException:
        return []

#---------------------------------------------------------------
def check_and_get_ele_by_css_selector(element, selector):
    """Find the web element of a given css selector, return none if not found.

    The search can be limited within a given web element, or the whole document if the browser driver is passed instead of the web element
    """
    if element is None or not selector:
        return None  
    try:
        return element.find_element_by_css_selector(selector)
    except NoSuchElementException:
        return None

#---------------------------------------------------------------
def check_and_get_all_elements_by_css_selector(element, selector):
    """Find the web elements of a given css selector, return none if not found.

    The search can be limited within a given web element, or the whole document if the browser driver is passed instead of the web element
    """
    if element is None or not selector:
        return  [] 
    try:
        return element.find_elements_by_css_selector(selector)
    except NoSuchElementException:
        return []

#---------------------------------------------------------------
def check_and_get_ele_by_its_text(element, text):
    """
    """
    if element is None or not text:
        return None
    try:
        return element.find_elements_by_xpath("//*[contains(text(), text)]")
    except NoSuchElementException:
        return None

#---------------------------------------------------------------
def close_popup_windows(chrome_driver, close_ele_class_names):
    """  Close the popup windows, specified by the given class names, ignoring exceptions, if any"""

    for class_name in close_ele_class_names:
        close_ele = check_and_get_ele_by_class_name(chrome_driver, class_name) 
        if close_ele:
            try:
                close_ele.click()
                time.sleep(1)
            except:
                pass

#--------------------------------------------------------------- 
def get_IMG_element_from_homefeed_page(driver):
    """Get all <img> elements on page then remove elmenents that are not from user's friends.

    We want to get the list of loaded photos on the user home feed page, the ones from the photographers that you are following.
    Since all the class names in the user homefeed page are now postfixed with randomized texts, we will use the img tag as identifier for a photo, 
    from there, we remove non-interested img items such as avatars, thumbnails or recommended photos
    """
    # we are interested in items with the tag <img>
    img_eles = check_and_get_all_elements_by_tag_name(driver, 'img') 
    time.sleep(4)
    # img_eles list contains other img elements that we don't want, such as thumbnails, recommended photos..., we will remove them from the list
    for ele in reversed(img_eles):
        parent_4 = check_and_get_ele_by_xpath(ele, '../../../..') 
        if parent_4 is not None and parent_4.get_attribute('class').find('Elements__HomefeedPhotoBox') == -1:
            img_eles.remove(ele)
    return img_eles

#---------------------------------------------------------------
def close_chrome_browser(chrome_driver):
    """ Close the chrome browser, care-free of exceptions. """
    if chrome_driver is None:
        return
    try:
        chrome_driver.close()
    except WebDriverException:
        pass
#---------------------------------------------------------------
def start_chrome_browser(options_list, headless_mode, desired_capab= None, my_queue = None):
    """ Start Chrome Web driver with given options.
        Suppress the default log messages. 
        Put the result chrome driver in the queue, if given, so that it can be retrieved in an multithread/multiprocessing environments"""

    driver = None
    chrome_options = Options()
    for option in options_list:
        chrome_options.add_argument(option)   
    
    # suppress chrome log info
    chrome_options.add_argument('--log-level=3')   
    chrome_options.add_argument('--disable-dev-shm-usage')    
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--enable-automation")

    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

    if headless_mode:
        print('Starting Chrome browser without the graphical user interface ...')
        chrome_options.add_argument("--headless") 
    else:
        printY('DO NOT INTERACT WITH THE CHROME BROWSER. IT IS CONTROLLED BY THE SCRIPT AND  WILL BE CLOSED WHEN THE TASK FINISHES')
        #chrome_options.add_argument("--window-size=900,1200")

    if desired_capab:
        driver = webdriver.Chrome(options=chrome_options, desired_capabilities= desired_capab)
    else:
        driver = webdriver.Chrome(options=chrome_options)

    if my_queue:
        my_queue.put(driver)

    return driver

#---------------------------------------------------------------
def has_server_connection(driver, server_url):
    """ Check the internet connection and check whether a given server is down or not.
        We use the text on the chrome page when it detects no internet connection (this may change)
        For 500px it it https://500px.com
        Print error message on negative result """

    OK = True
    try:
        driver.get(server_url)
        # we aim at this element on the chrome default page on 'No internet connection' error
        ele = driver.find_element_by_xpath('//*[@id="main-message"]/h1/span')
        if ele is not None and ele.text == 'No internet':
            printR('   No internet connection')
            return not OK
        
        if requests.get(server_url).status_code != 200:
            printR(f'   Error connecting to {server_url}')
            return not OK
    except: 
        return OK
#---------------------------------------------------------------
def hover_element_by_its_xpath(driver, xpath):
    """ hover the mouse on an element specified by the given xpath. """
    element = check_and_get_ele_by_xpath(driver, xpath)
    if element is not None:
        hov = ActionChains(driver).move_to_element(element)
        hov.perform()

#---------------------------------------------------------------
def hover_by_element(driver, element):
    """ Hover the mouse over a given element. """               
    #element.location_once_scrolled_into_view
    hov = ActionChains(driver).move_to_element (element)
    hov.perform()

#---------------------------------------------------------------
def scroll_down(driver, scroll_pause_time = 0.5, number_of_scrolls = 10, estimate_scrolls_needed = 3, message = ''):
    """Scrolling down the active window in a controllable fashion.

    Passing the scroll_pause_time according to the content of the page, to make sure all items are loaded before the next scroll. default is 0.5s
    The page could have a very long list, or almost infinity, so by default we limit it to 10 times.
    If number_of_scrolls =  0, return without scrolling
    If number_of_scrolls = -1, keep scrolling until the end is reached ...
    for this case, in order to have a realistic progress bar, we will use estimate_scrolls_needed  ( total request items / load items per scroll )
    Message is a string described the title of the progress bar. if empty is passed, the progress bar will not be stimulated
    """
    if number_of_scrolls == 0 :
        return

    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")
    iteration_count = 0
    scrolls_count_for_stimulated_progressbar = 0
    while True:
        if number_of_scrolls == -1:
            # if we were able to give an estimate of number of scrolls needed (ex. number of photos, followers, friends are known)
            if estimate_scrolls_needed != -1: 
                utils.update_progress(scrolls_count_for_stimulated_progressbar / estimate_scrolls_needed, message)
            # here, we dont know when it ends (for example, we ask for all notifications, but we don't know how many the 500px server will provide) 
            else:
                notifications_loaded_so_far = scrolls_count_for_stimulated_progressbar * config.NOTIFICATION_PER_LOAD
                text = f'\r{message} {str(notifications_loaded_so_far)}'
                sys.stdout.write(text)
                sys.stdout.flush()
        elif iteration_count > 0:
            utils.update_progress(iteration_count / number_of_scrolls, message)

        scrolls_count_for_stimulated_progressbar += 1

        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait for page to load
        time.sleep(scroll_pause_time)
        innerHTML = driver.execute_script("return document.body.innerHTML") #make sure document javascript is executed

        # exit point #1 : when number of scrolls requested has been reached
        if number_of_scrolls != -1:
            iteration_count = iteration_count + 1
            if iteration_count >= number_of_scrolls:
               break

        #  exit point #2: when all items are loaded (by calculating new scroll height and compare with last scroll height)
        #                 or when the server stop responding after the given sleep time (scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # mark the end of the progress bar update    
    if number_of_scrolls == -1 and estimate_scrolls_needed == -1:   # indeterminate number of scrolls
        sys.stdout.write('\r\n')                                    # end the progress update with a line-feed
        sys.stdout.flush()
    else:
        utils.update_progress(1, message)                                 # force the display of "100% Done" 
  
    time.sleep(scroll_pause_time)

#---------------------------------------------------------------
def scroll_to_end_by_class_name(driver, class_name, likes_count):
    """Scroll the active window to the end, where the last element of the given class name become visible.

    Argument 'likes_count' is used for creating a realistic progress bar
    """
    eles = driver.find_elements_by_class_name(class_name)
    count = 0
    new_count = len(eles)

    while new_count != count:
        try:
            utils.update_progress(new_count / likes_count, f'    - Scrolling to load more items {new_count}/{likes_count}:')
            the_last_in_list = eles[-1]
            the_last_in_list.location_once_scrolled_into_view 
            time.sleep(random.randint(15, 20) / 10)  
            try:
                WebDriverWait(driver, timeout = 60).until(EC.visibility_of(the_last_in_list))
            except TimeoutException:
                pass 
            count = new_count
            eles = driver.find_elements_by_class_name(class_name)
            new_count = len(eles)
        except TimeoutException :
            printR(f'   Time out while scrolling down. Please retry.')
        except NoSuchElementException:
            pass
    if new_count < likes_count:
        utils.update_progress(1, f'    - Scrolling to load more items:{new_count}/{likes_count}')

#---------------------------------------------------------------
def scroll_to_end_by_class_or_tag_name(driver, expected_items_count, class_name= '', tag_name=''):
    """Scroll the active window to the end, where the last element of the given class name become visible.

    Argument 'expected_items_count' is used for creating a realistic progress bar
    """
    if class_name:
        eles = driver.find_elements_by_class_name(class_name)
    elif tag_name:
        eles = driver.find_elements_by_tag_name(tag_name)

    count = 0
    new_count = len(eles)

    while new_count != count:
        try:
            utils.update_progress(new_count / expected_items_count, f'    - Scrolling to load more items {new_count}/{expected_items_count}:')
            the_last_in_list = eles[-1]
            the_last_in_list.location_once_scrolled_into_view 
            time.sleep(random.randint(15, 20) / 10)  
            try:
                WebDriverWait(driver, timeout = 60).until(EC.visibility_of(the_last_in_list))
            except TimeoutException:
                pass 

            count = new_count
            if class_name:
                eles = driver.find_elements_by_class_name(class_name)
            elif tag_name:
                eles = driver.find_elements_by_tag_name(tag_name)
            new_count = len(eles)
        except TimeoutException :
            printR(f'   Time out while scrolling down. Please retry.')
        except NoSuchElementException:
            pass
    if new_count >= expected_items_count:
        utils.update_progress(1, f'    - Scrolling to load more items:{expected_items_count}/{expected_items_count}')
    else:
        print(f'     - Available items: {new_count}')
    return eles

#---------------------------------------------------------------
def scroll_to_end_by_tag_name_within_element(driver, element, tag_name, likes_count):
    """Scroll the active window to the end, where the last element of the given tag name is loaded and visible.

    Argument 'likes_count' is used for creating a realistic progress bar
    """
    eles = check_and_get_all_elements_by_tag_name(element, tag_name)
    count = 0
    new_count = len(eles)
    time_out = 60
    count_down_timer = time_out
    while new_count != count:
        try:
            utils.update_progress(new_count / likes_count, f'    - Scrolling to load more items {new_count}/{likes_count}:')
            the_last_in_list = eles[-1]
            the_last_in_list.location_once_scrolled_into_view 
            time.sleep(1)
            try:
                WebDriverWait(driver, time_out).until(EC.visibility_of(the_last_in_list))
            except TimeoutException:
                pass 

            count = new_count
            eles = check_and_get_all_elements_by_tag_name(element, tag_name)
            new_count = len(eles)

            # give the slow server a chance to load the new items 
            while new_count == count and count_down_timer >= 0 and new_count < likes_count:
                count_down_timer -= 1
                the_last_in_list.location_once_scrolled_into_view 
                time.sleep(1)

        except TimeoutException :
            printR(f'   Time out ({time_out}s) while scrolling down. Please retry.')
        except NoSuchElementException:
            pass
    if new_count >= likes_count:
        utils.update_progress(1, f'    - Scrolling to load more items:{likes_count}/{likes_count}')
    return eles

#---------------------------------------------------------------
def scroll_down_active_page(driver, web_element, class_name_to_check, tag_name_to_check, number_of_items_requested = 100, message = '', time_out= 60):
    """Scrolling down the active window until all the request items of a given class name or a tag name, are loaded.

    - The process monitors the change of the page height to decide if another scroll down is needed
      After a scroll down, if the server fails to load new items within a given time out (default is 60s), the process will stop 
    - If both class name and tag name are given, class name take priority. if none is given, no action is taken
    - Message is the text shown on the progress bar

"""
    if web_element is None:
        web_element = driver    
    if class_name_to_check: 
        items = web_element.find_elements_by_class_name(class_name_to_check) 
    elif tag_name_to_check: 
        items = web_element.find_elements_by_tag_name(tag_name_to_check) 
    else:
        printR('   Items were not specified. The process stopped.')
        return
    if items is None or len(items) == 0:
        printR('   No items found.')
        return
      
    if len(items) >= number_of_items_requested:
        return    
     
    # get the current height of the page
    last_scroll_height = driver.execute_script("return document.body.scrollHeight")

    time_out_count_down = time_out
    count_sofar = 0
    if number_of_items_requested == -1:
        number_of_items_requested  = config.MAX_NOTIFICATION_REQUEST

    while count_sofar < number_of_items_requested :   
        utils.update_progress(count_sofar / number_of_items_requested, f'    - Scrolling down {count_sofar}/{number_of_items_requested}')
        # scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        new_scroll_height = driver.execute_script("return document.body.scrollHeight")

        # give the slow server a chance to load the new items
        while new_scroll_height == last_scroll_height and time_out_count_down >= 0:
            time_out_count_down -= 1
            new_scroll_height = driver.execute_script("return document.body.scrollHeight") 
            time.sleep(1)
 
        last_scroll_height = new_scroll_height

        if class_name_to_check : 
            items = web_element.find_elements_by_class_name(class_name_to_check)         
        elif tag_name_to_check: 
            items = web_element.find_elements_by_tag_name(tag_name_to_check) 

        count_sofar = len(items)    

        if count_sofar < number_of_items_requested and time_out_count_down <= 0:
            printR(f'\n   Time out ({time_out}s)! {count_sofar}/{number_of_items_requested} items obtained. You may try again at another time')
            break
 
    # normal termination of while loop: show completed progress bar
    else:
        utils.update_progress(1, f'    - Scrolling down {number_of_items_requested}/{number_of_items_requested}')


