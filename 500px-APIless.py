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

#not use yet
#from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
#from selenium.webdriver.chrome import service
#import pychromecast
#import logging
#import getpass 

from lxml import html
import os, sys, time, datetime, re, math, csv, json, codecs, argparse
from time import sleep
from enum import Enum

PHOTOS_PER_PAGE = 50             # 500px currently loads 50 photos per page
LOADED_ITEM_PER_PAGE = 50        # it also loads 50 followers, or friends, at a time in the popup window
NOTIFICATION_PER_LOAD = 20       # currently notifications are requested to display ( by scrolling the window) 20 items at a time
MAX_NOTIFICATION_REQUEST = 5000  # self limitation to avoid abusing
MAX_AUTO_LIKE_REQUEST = 100      # self limitation to avoid abusing
MAX_FOLLOWINGS_STATUSES = 100    # max number of users you want to find the following statuses with you
DEBUG = False

class photo:
    """ Represent a photo with id number, what page it is on in the user photo list, the title and the href."""
    def __init__(self, order, id, on_page, desc, link):
        self.order = order
        self.id = id
        self.on_page = on_page
        self.desc = str(desc)
        self.link = link

class notification:
    """ Represent a notification object."""
    def __init__(self, order, display_name, username, content, photo_link, photo_title, timestamp, status):
        self.order = order
        self.display_name = display_name
        self.username = username
        self.content = content
        self.photo_link = photo_link
        self.photo_title = photo_title
        self.timestamp = timestamp
        self.status = status
    def print_screen(self):
        print(self.order + "\n" + self.display_name + "\n" + self.username + "\n" + self.content + "\n" + self.photo_link + "\n" + self.photo_title + "\n" + self.timestamp +  "\n" + self.status )   
    def write_to_textfile(self):
        print(self.order + "\n" + self.display_name + "\n" + self.username + "\n" + self.content + "\n" + self.photo_link + "\n" + self.photo_title + "\n" + self.timestamp +  "\n" + self.status )

class notificator:
    """ Represent a user, with display name and user name, who generated a notification. """
    def __init__(self, display_name, username):
        self.display_name = display_name
        self.username = username   
    def print_screen(self):
        print(self.display_name + "\n" + self.username + "\n" )   
    def write_to_textfile(self):
        print(self.display_name + "\n" + self.username + "\n")

class user_stats:
    """ Represent basic statistics of a user. Object of the class is considered mutabble and therefore can be passed as reference"""
    def __init__(self, display_name='', user_name='', id='', location='', affection_note='', following_note='', affections_count='', views_count='', 
                 followers_count='', followings_count='', photos_count='', galleries_count='', registration_date='', last_upload_date='', user_status=''):
        self.display_name = display_name
        self.user_name = user_name
        self.id = id
        self.location = location
        self.affection_note = affection_note
        self.following_note = following_note
        self.affections_count = affections_count
        self.views_count = views_count
        self.followers_count = followers_count
        self.followings_count = followings_count
        self.photos_count = photos_count
        self.galleries_count = galleries_count
        self.registration_date = registration_date
        self.last_upload_date = last_upload_date
        self.user_status = user_status
class user:
    """ Represent a user with display name, user name and number of followers."""
    def __init__(self, order, display_name, user_name, number_of_followers, following_status = ''):
        self.order = order
        self.display_name = display_name
        self.user_name = user_name
        self.number_of_followers = number_of_followers
        self.following_status = following_status
    
    def to_dict(self):
        return {
            'order': self.order,
            'display_name': self.display_name,
            'user_name': self.user_name,
            'number_of_followers': self.number_of_followers,
            'following_status': self.following_status
        }


#class Output_file_type(Enum):
#   """ Enum representing 4 types of output list"""
#   USERS_LIST = 0
#   PHOTOS_LIST = 1
#   NOTIFICATIONS_LIST = 2
#   STATISTICS_HTML_FILE = 3

class User_inputs():
    """ Represent the input entered by the user. 
    
    Choice is an character string representing available options: [1-13] or 'r','q' . The default value is zero which means commnand line arguments will not be used 
    """

    def __init__(self, use_command_line_args = False, choice='0', user_name='', password='', target_user_name='', photo_href='', gallery_href='', gallery_name='',
                 number_of_photos_to_be_liked=2 , index_of_start_photo=1, number_of_notifications=200, time_interval=3, index_of_start_user=1, number_of_users=100):
        self.use_command_line_args          = use_command_line_args
        self.choice                         = choice
        self.user_name                      = user_name
        self.password                       = password
        self.target_user_name               = target_user_name
        self.photo_href                     = photo_href
        self.gallery_href                   = gallery_href
        self.gallery_name                   = gallery_name
        self.number_of_photos_to_be_liked   =  number_of_photos_to_be_liked
        self.index_of_start_photo           = index_of_start_photo
        self.number_of_notifications        = number_of_notifications
        self.time_interval                  = time_interval
        self.index_of_start_user            = index_of_start_user
        self.number_of_users                = number_of_users

    def Reset(self):
        self.use_command_line_args = False
        self.choice                         = '0'
        self.user_name                      = ''
        self.password                       = ''
        self.target_user_name               = ''
        self.photo_href                     = ''
        self.gallery_href                   = ''
        self.gallery_name                   = ''
        self.number_of_photos_to_be_liked   =  2
        self.index_of_start_photo           = 1
        self.number_of_notifications        = 200
        self.time_interval                  = 3
        self.index_of_start_user            = 1
        self.number_of_users                = 100
class Output_data():
    """ Represent all the output lists and data"""
    def __init__(self, output_dir = '', json_data = [], photos = [],notifications = [], unique_notificators = [], followers_list = [], followings_list = [], like_actioners_list= []):
        self.json_data = json_data      
        self.photos = photos         
        self.notifications = notifications  
        self.unique_notificators = unique_notificators
        self.followers_list = followers_list  
        self.followings_list = followings_list 
        self.like_actioners_list= like_actioners_list
        self.stats = user_stats()  
        
        # Set default output folder :  %PROGRAMDATA%\500px_APIless\Output (C:\ProgramData\500px_Apiless\Output)
        output_dir = os.path.join(os.getenv('ProgramData'), r'500px_Apiless\Output')
        os.makedirs(output_dir, exist_ok = True)
        self.output_dir = output_dir
 
    def Reset(self):
        self.json_data = []       
        self.photos = []          
        self.notifications = []   
        self.unique_notificators = []
        self.followers_list = []  
        self.followings_list = [] 
        self.like_actioners_list= []
        self.stats = user_stats() 

# print colors text on console
def printR(text): print(f"\033[91m {text}\033[00m") #; logging.info(text)
def printG(text): print(f"\033[92m {text}\033[00m") #; logging.info(text)
def printY(text): print(f"\033[93m {text}\033[00m") #; logging.info(text)
def printC(text): print(f"\033[96m {text}\033[00m") #; logging.info(text) 
def printB(text): print(f"\033[94m {text}\033[00m") #; logging.info(text) 

#---------------------------------------------------------------
def Start_chrome_browser(options_list = []):
    """ use selenium webdriver to start chrome, with various options. Ex ["--start-maximized", "--log-level=3"] """

    chrome_options = Options()
 
    for option in options_list:
        chrome_options.add_argument(option)
    
    chrome_options.add_argument('--log-level=3')   
    chrome_options.add_argument("--window-size=800,1080")
    driver = webdriver.Chrome(options=chrome_options)
    printY('DO NOT INTERACT WITH THE CHROME BROWSER. IT IS CONTROLLED BY THE SCRIPT AND  WILL BE CLOSED WHEN THE TASK FINISHES')
    return driver

#---------------------------------------------------------------
def Close_chrome_browser(chrome_driver):
    """ Close the chrome browser, care-free of exceptions. """
    if chrome_driver is None:
        return
    try:
        chrome_driver.close()
    except WebDriverException:
        pass

#---------------------------------------------------------------
def Create_user_statistics_html(stats):
    """ write user statistic object stats to an html file. """

    time_stamp = datetime.datetime.now().replace(microsecond=0).strftime("%Y-%m-%d, %H:%M:%S")

    output = f'''
<html>\n\t<body>
        <h2>User statistics</h2>
        <h3>{time_stamp}</h3>
        <table>
            <tr>                <td><b>User name</b></td>           <td>{stats.user_name}</td>\n</tr>
            <tr>                <td><b>Display name</b></td>        <td>{stats.display_name}</td>\n</tr>
            <tr>                <td><b>Id</b></td>                  <td>{stats.id}</td>\n</tr>
            <tr>                <td><b>Location</b></td>            <td>{stats.location}</td>\n</tr>
            <tr>                <td><b>Activities</b></td>          <td>{stats.affection_note}</td>\n</tr>
            <tr>                <td> </td>                          <td>{stats.following_note}</td>\n</tr>
            <tr>                <td><b>Affections</b></td>          <td>{stats.affections_count}</td>\n</tr>
            <tr>                <td><b>Views</b></td>               <td>{stats.views_count}</td>\n</tr>
            <tr>                <td><b>Followers</b></td>           <td>{stats.followers_count}</td>\n</tr>
            <tr>                <td><b>Followings</b></td>          <td>{stats.followings_count}</td>\n</tr>
            <tr>                <td><b>Photos count</b></td>        <td> {stats.photos_count}</td>\n</tr>
            <tr>                <td><b>Galleries count</b></td>     <td>{stats.galleries_count}</td>\n</tr>
            <tr>                <td><b>Registration date</b></td>   <td>{stats.registration_date}</td>\n</tr>
            <tr>                <td><b>Last upload date</b></td>    <td>{stats.last_upload_date}</td>\n</tr>
            <tr>                <td><b>User status</b></td>         <td>{stats.user_status}</td>\n</tr>
        <table>\n\t<body>\n<html>
'''
    return output

#---------------------------------------------------------------
def Write_photos_list_to_csv(user_name, list_of_photos, csv_file_name):
    """ Write photos list to a csv file with the given  name. Return True if success.
    
    IF THE FILE IS CURRENTLY OPEN, GIVE THE USER A CHANCE TO CLOSE IT AND RE-SAVE   
    """
    try:
        with open(csv_file_name, 'w', encoding = 'utf-16', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer = csv.DictWriter(csv_file, fieldnames = ['Order', 'Page', 'ID', 'Title', 'Link'])  
            writer.writeheader()
            for i, a_photo in enumerate(list_of_photos):
                writer.writerow({'Order' : str(a_photo.order), 'Page': str(a_photo.on_page), 'ID': str(a_photo.id), 'Title' : str(a_photo.desc), 'Link' :a_photo.link}) 
            printG(f"- List of {user_name}\'s {len(list_of_photos)} photo is saved at:\n  {os.path.abspath(csv_file_name)}")
        return True

    except PermissionError:
        printR(f'Error writing file {os.path.abspath(csv_file_name)}.\nMake sure the file is not in use. Then type r for retry >')
        retry = input()
        if retry == 'r': 
            Write_photos_list_to_csv(user_name, list_of_photos, csv_file_name)
        else:
            printR('Error witing file' + os.path.abspath(csv_file_name))
            return False

#---------------------------------------------------------------
def Write_users_list_to_csv(users_list, csv_file_name):
    """ Write the users list to a csv file with the given  name. Return True if success.
    
    THE USERS LIST COULD BE A FOLLOWERS LIST, FRIENDS LIST 
    IF THE FILE IS CURRENTLY OPEN, GIVE THE USER A CHANCE TO CLOSE IT AND RE-SAVE
    """
    try:
        with open(csv_file_name, 'w', encoding = 'utf-16', newline='') as csv_file:  # could user utf-16be
            writer = csv.writer(csv_file)
            writer = csv.DictWriter(csv_file, fieldnames = ['Order', 'Display Name', 'User Name', 'Followers', 'Status'])  
            writer.writeheader()
            for a_user in users_list:
                writer.writerow({'Order' : a_user.order, 'Display Name' : a_user.display_name, 'User Name': a_user.user_name, 'Followers': a_user.number_of_followers, 'Status': a_user.following_status}) 
        printG('The users list is saved at:\n ' + os.path.abspath(csv_file_name) )
        return True
    except PermissionError:
        retry = input(f'Error writing to file {csv_file_name}. Make sure the file is not in use. Then type r for retry >')
        if retry == 'r': 
            Write_users_list_to_csv(users_list, csv_file_name)
        else:
            printG('Error writing file\n' + os.path.abspath(csv_file_name))
            return False 

#---------------------------------------------------------------
def Write_notifications_to_csvfile(notifications_list, csv_file_name):
    """ Write the  notifications list to a csv file with the given  name. Return True if success.

    IF THE FILE IS CURRENTLY OPEN, GIVE THE USER A CHANCE TO CLOSE IT AND RE-SAVE
    """
    try:
        with open(csv_file_name, 'w', encoding = 'utf-16', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer = csv.DictWriter(csv_file, fieldnames = ['Order', 'Display Name', 'User Name', 'Content', 'Photo Title', 'Time Stamp', 'Status'])    
            writer.writeheader()
            for notif in notifications_list:
                writer.writerow({'Order': notif.order, 'Display Name': notif.display_name, 'User Name': notif.username, 'Content': notif.content, 'Photo Title': notif.photo_title, 'Time Stamp': notif.timestamp, 'Status': notif.status}) 
        printG('Notifications list is saved at:\n ' + os.path.abspath(csv_file_name))
        return True 
    except PermissionError:
        retry = input(f'Error writing to file {csv_file_name}.\n Make sure the file is not in use, then type r for retry >')
        if retry == 'r':  
            Write_notifications_to_csvfile(notifications, csv_file_name)
        else: 
            printR(f'Error writing file {csv_file_name}')
            return False

#---------------------------------------------------------------
def Write_unique_notificators_list_to_csv(unique_notifications_list, csv_file_name):
    """ Write the unique notifications list to a csv file with the given  name. Return True if success.
    
    IF THE FILE IS CURRENTLY OPEN, GIVE THE USER A CHANCE TO CLOSE IT AND RE-SAVE
    """
    try:
        with open(csv_file_name, 'w', encoding = 'utf-16', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer = csv.DictWriter(csv_file, fieldnames = ['Order', 'Display Name', 'User Name', 'Count'])  
            writer.writeheader()

            for actor in unique_notifications_list:
                items = actor.split(',')
                if len(items) == 4:
                    writer.writerow({'Order': items[0], 'Display Name': items[1], 'User Name': items[2], 'Count': items[3]}) 
            printG('Unique notificators is saved at:\n' + os.path.abspath(csv_file_name))
            return True 

    except PermissionError:
        retry = input(f'Error writing to file {csv_file_name}. Make sure the file is not in use. Then type r for retry >')
        if retry == 'r': 
            Write_unique_notificators_list_to_csv(unique_notificators, csv_file_name)
        else: 
            printR(f'Error writing file {csv_file_name}')
            return False

#---------------------------------------------------------------
def Hover_element_by_its_xpath(driver, xpath):
    """ hover the mouse on an element specified by the given xpath. """
    element = check_and_get_ele_by_xpath(driver, xpath)
    if element is not None:
        hov = ActionChains(driver).move_to_element(element)
        hov.perform()

#---------------------------------------------------------------
def Hover_by_element(driver, element):
    """ Hover the mouse over a given element. """               
    #element.location_once_scrolled_into_view
    hov = ActionChains(driver).move_to_element (element)
    hov.perform()

#---------------------------------------------------------------
def Get_element_text_by_xpath(page, xpath_string):
    """Return the text of element, specified by the element xpath. Return '' if element not found. """
    ele = page.xpath(xpath_string)
    if len(ele) > 0 : 
        return ele[0].text
    return ''

#---------------------------------------------------------------
def Get_element_attribute_by_ele_xpath(page, xpath, attribute_name):
    """Get the value of the given attribute name, at the element of the given xpath. Return '' if element not found."""
    ele = page.xpath(xpath)
    if len(ele) > 0:
        return ele[0].attrib[attribute_name] 
    return ''

#---------------------------------------------------------------
def check_and_get_ele_by_xpath(element, xpath):
    """ Find the web element from a given xpath, return none if not found.
    
    THE SEARCH CAN BE LIMITED WITHIN A GIVEN WEB ELEMENT, OR THE WHOLE DOCUMENT, BY PASSING THE BROWSER DRIVER
    """
    try:
        return element.find_element_by_xpath(xpath)
    except NoSuchElementException:
        return None

#---------------------------------------------------------------
def check_and_get_all_elements_by_xpath(element, xpath):
    """ Find the web elements from a given xpath, return none if not found.
    
    THE SEARCH CAN BE LIMITED WITHIN A GIVEN WEB ELEMENT, OR THE WHOLE DOCUMENT, BY PASSING THE BROWSER DRIVER
    """
    try:
        return element.find_elements_by_xpath(xpath)
    except NoSuchElementException:
        return []
#---------------------------------------------------------------
def check_and_get_ele_by_class_name(element, class_name):
    """Find the web element of a given class name, return none if not found.
    
    THE SEARCH CAN BE LIMITED WITHIN A GIVEN WEB ELEMENT, OR THE WHOLE DOCUMENT, BY PASSING THE BROWSER DRIVER
    """
    try:
        return element.find_element_by_class_name(class_name) 
    except NoSuchElementException:
        return None

#---------------------------------------------------------------
def check_and_get_ele_by_id(element, id_name):
    """Find the web element of a given id, return none if not found.

    THE SEARCH CAN BE LIMITED WITHIN A GIVEN WEB ELEMENT, OR THE WHOLE DOCUMENT, BY PASSING THE BROWSER DRIVER
    """
    try:
        return element.find_element_by_id(id_name) 
    except NoSuchElementException:
        return None

#---------------------------------------------------------------
def check_and_get_ele_by_tag_name(element, tag_name):
    """Find the web element of a given tag name, return none if not found.

    THE SEARCH CAN BE LIMITED WITHIN A GIVEN WEB ELEMENT, OR THE WHOLE DOCUMENT, BY PASSING THE BROWSER DRIVER
    """
    try:
        return element.find_element_by_tag_name(tag_name) 
    except NoSuchElementException:
        return None


#---------------------------------------------------------------
def check_and_get_all_elements_by_tag_name(element, tag_name):
    """Find all the web elements of a given tag name, return empty list if tag_name not found.

    THE SEARCH CAN BE LIMITED WITHIN A GIVEN WEB ELEMENT,  OR ON THE WHOLE DOCUMENT IF THE BROWSER DRIVER IS PASSED
    """
    try:
        return element.find_elements_by_tag_name(tag_name) 
    except NoSuchElementException:
        return []

#---------------------------------------------------------------
def check_and_get_all_elements_by_class_name(element, class_name):
    """Find all the web elements of a given class name, return empty list if class_name not found.

    THE SEARCH CAN BE LIMITED WITHIN A GIVEN WEB ELEMENT, OR ON THE WHOLE DOCUMENT IF THE BROWSER DRIVER IS PASSED
    """
    try:
        return element.find_elements_by_class_name(class_name) 
    except NoSuchElementException:
        return []

#---------------------------------------------------------------
def check_and_get_ele_by_css_selector(element, selector):
    """Find the web element of a given css selector, return none if not found.

    THE SEARCH CAN BE LIMITED WITHIN A GIVEN WEB ELEMENT,  OR ON THE WHOLE DOCUMENT IF THE BROWSER DRIVER IS PASSED
    """
    try:
        return element.find_element_by_css_selector(selector)
    except NoSuchElementException:
        return None

#---------------------------------------------------------------
def check_and_get_all_elements_by_css_selector(element, selector):
    """Find the web elements of a given css selector, return none if not found.

    THE SEARCH CAN BE LIMITED WITHIN A GIVEN WEB ELEMENT,  OR ON THE WHOLE DOCUMENT IF THE BROWSER DRIVER IS PASSED
    """
    try:
        return element.find_elements_by_css_selector(selector)
    except NoSuchElementException:
        return []

#---------------------------------------------------------------
def GetUploadDate(photo_link):
    """Given a photo link, returns the photo upload date or time. """

    driver.get(photo_link)
    last_photo_page_HTML = driver.execute_script("return document.body.innerHTML") 
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    page = html.document_fromstring(last_photo_page_HTML)
    p = page.xpath('//*[@id="content"]/div/div/div[2]/div/div[1]/div[3]/div[1]/div/p/span')  
                    
    if len(p) > 0:
        return p[0].text_content() 
    else: 
       return "not found" 

#---------------------------------------------------------------
def Open_user_home_page(driver, user_name):
    """Open the home page of a given user. If the user page is not found, print error and return false. """ 

    driver.get('https://500px.com/' + user_name)
    # waiting until the page is opened
    main_window_handle = None
    while not main_window_handle:
        main_window_handle = driver.current_window_handle

    if check_and_get_ele_by_class_name(driver, 'not_found') is not None:
        printR(f'Error reading {user_name}\'s page. Please make sure a valid user name is used')
        return False
    elif check_and_get_ele_by_class_name(driver, 'missing') is None:
        return True
    else:
        printR(f'Error reading {user_name}\'s page. Please make sure a valid user name is used')
        return False

def Finish_Javascript_rendered_body_content(driver, time_out=10, class_name_to_check='', css_selector_to_check='', xpath_to_check=''):
    """ Run the Javascript to render the body content. Log error if it happened. Return the fail/success status and the page content text.
    
    THE COMPLETION OF THE JS SCRIPT, WITHIN THE GIVEN TIMEOUT, IS DETERMINED BY CHECKING THE EXISTANCE OF A GIVEN ELEMENT, 
    IDENTIFIED EITHER BY A GIVEN CLASS_NAME, OR A CSS_SELECTOR
    """

    innerHtml = driver.execute_script("return document.body.innerHTML")  
    
    try:
        if class_name_to_check != '' and css_selector_to_check == '':
            element = WebDriverWait(driver, time_out).until(EC.presence_of_element_located((By.CLASS_NAME, class_name_to_check)))
        elif class_name_to_check == '' and css_selector_to_check != '':
            element = WebDriverWait(driver, time_out).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector_to_check)))

    except TimeoutException :
        printR(f'Time out {time_out}s while loading. Please retry.')
        return False, ''
    except:
        printR('Error loading. Please retry.')
        return False, ''   
    
    return True, innerHtml
#---------------------------------------------------------------
def Wait_for_element_visibility(driver, web_element, time_out=10 ):
    """ Wait for an element to be visible within a given timeout. Log error if it occurs."""
   
    try:
        element = WebDriverWait(driver, time_out).until(EC.visibility_of_element_located(web_element))

    except TimeoutException :
        printR(f'Time out {time_out}s while loading. Please retry.')
        return False
    except: # NoSuchElementException:
        printR('No such Element error. Please retry.')
        return False  

    return (element is not None)

#---------------------------------------------------------------

def Get_stats(driver, user_inputs, output_lists):
    """Get statistics of a given user: number of likes, views, followers, following, photos, last upload date...

    OPEN USER HOME PAGE https://500px.com/[user_name]
    RUN THE DOCUMENT JAVASCRIPT TO RENDER THE PAGE CONTENT
    USE LXML TO EXTRACT INTERESTED DATA
    USE REGULAR EXPRESSION TO EXTRACT THE JSON PART IN THE BODY, AND OBTAIN MORE DATA FROM IT.
    """

    if Open_user_home_page(driver, user_inputs.user_name) == False:
        user_inputs.user_name = ''
        Show_menu(user_inputs)
        return None, None
        
    Hide_banners(driver)
  
    # abort the action if the target objects failed to load within a timeout of 15s
    success, innerHtml = Finish_Javascript_rendered_body_content(driver, time_out=15, class_name_to_check='finished')
    if not success:
        return None, None
    # using lxml for html handling
    page = html.document_fromstring(innerHtml)

    # Affection note
    affection_note = Get_element_attribute_by_ele_xpath(page, "//li[@class='affection']", 'title' )
    # Following note
    following_note = Get_element_attribute_by_ele_xpath(page, "//li[@class='following']", 'title' )
    # Views count
    views_count =  Get_element_text_by_xpath(page,'//*[@id="content"]/div[2]/div[4]/ul/li[2]/span')

    #using regex to extract from the javascript-rendered html the json part that holds user data 
    userdata = re.findall('"userdata":(.*),"viewer":', innerHtml)
    if len(userdata) == 0:
        return
    json_data = json.loads(userdata[0])
    location = ''
    city = json_data['city']
    if json_data['state'] != None: 
        state = json_data['state']  
    else: 
        state = ''
    country = json_data['country'] 
    if  city == '' and state == '' and country == '':
        location = 'not specified'
    else:
        if city    != '':  location  =  json_data['city']
        if state   != '':  location += ', ' +  json_data['state']
        if country != '':  location += ', ' +  json_data['country']
    user_id = json_data['id']
    photos = json_data['photos']
    photosCount = len(photos)
    #first_upload_date = json_data['photos'][photosCount -1]['created_at'][:10]
    if photosCount > 0:
        last_upload_date = photos[0]['created_at'][:10]
    else:
        last_upload_date = 'Has no photo'

    active_int = json_data['active'] 
    if   active_int == 0 : user_status = 'Not Active'
    elif active_int == 1 : user_status = 'Active'
    elif active_int == 2 : user_status = 'Deleted by user'
    elif active_int == 3 : user_status = 'Banned'

    # write to file the userdata in json for debugging
    if DEBUG:
        jason_string = json.dumps(json_data, indent=2, sort_keys=True) 
        time_stamp = datetime.datetime.now().replace(microsecond=0).strftime("%Y_%m_%d__%H_%M_%S")
        Write_string_to_text_file(jason_string, os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_stats_json_{time_stamp}.txt'))

    stats = user_stats(json_data['fullname'], user_inputs.user_name,  user_id, location, 
                       affection_note, following_note, json_data['affection'], views_count, json_data['followers_count'], json_data['friends_count'], 
                       json_data['photos_count'], json_data['galleries_count'], json_data['registration_date'][:10], last_upload_date, user_status)
    return json_data, stats
      
#---------------------------------------------------------------
def Get_photos_list(driver, user_inputs):
    """Return the list of photos from a given user.

    PROCESS: 
    - OPEN USER HOME PAGE, SCROLL DOWN UNTIL ALL PHOTOS ARE LOADED
    - MAKE SURE THE DOCUMENT JAVASCRIPT IS CALLED TO GET THE FULL CONTENT OF THE PAGE
    - EXTRACT THE user_data, the json section that contains all the photos data
    """

    photos_list = []

    if Open_user_home_page(driver, user_inputs.user_name) == False:
        Show_menu(user_inputs)
        return []
    Hide_banners(driver)

    # We intend to scroll down an indeterminate number of times until the end is reached
    # In order to have a realistic progress bar, we need give an estimate of the number of scrolls needed
    estimate_scrolls_needed = 3  #default value, just in case error occurs
    photos_count  = 1
    photos_count_ele = check_and_get_ele_by_css_selector(driver, '#content > div.profile_nav_wrapper > div > ul > li.photos.active > a > span')
    if photos_count_ele is not None:
        photos_count = int(photos_count_ele.text.replace('.', '').replace(',', ''))
        estimate_scrolls_needed =  math.floor( photos_count / PHOTOS_PER_PAGE) +1

    Scroll_down(driver, 1.5, -1, estimate_scrolls_needed, ' - Scrolling down for more photos:') # scroll down until end, pause 1.5s between scrolls, 

    # abort the action if the target objects failed to load within a timeout of 15s
    success, innerHtml = Finish_Javascript_rendered_body_content(driver, time_out=15, class_name_to_check='finished')
    if not success:
        return []
    
    update_progress(0, ' - Extracting data:')
    #if DEBUG:
    #     Write_string_to_text_file(str(innerHtml.encode('utf-8')), user_inputs.user_name + '_innerHTML.txt')
    page = html.document_fromstring(innerHtml)

    userdata = re.findall('"userdata":(.*),"viewer":', innerHtml)
    if len(userdata) == 0:
        return None
    json_data = json.loads(userdata[0]) 
    user_id = json_data['id']

    # TODO: by some unknown reason the json.loads() method just loads the first 50 photos, 
    # for now we have to use the traditional way (parsing the xml by using lxml) 

    #extract photo title and href (alt tag) using lxml and regex
    els = page.xpath("//a[@class='photo_link ']")
    titles = page.xpath("//img[@data-src='']")
    num_item = len(els)
    if num_item == 0:
        printR(f'User {user_name} does not upload any photo')
        return None

    # Create list of photos
    for i in range(num_item): 
        update_progress(i / (num_item -1), ' - Extracting data:')
        reg = "/photo/([0-9]*)/"  
        photoId = re.findall(reg, els[i].attrib["href"])
        if len(photoId) != 0:
            pId = photoId[0] 
        else:
            pId = 0
        on_page = math.floor(i / PHOTOS_PER_PAGE ) + 1
        link = f"https://500px.com{els[i].attrib['href']}?ctx_page={on_page}&from=user&user_id={user_id}"

        new_photo = photo(i+1, pId, on_page, str(titles[i].attrib["alt"]), link)
        photos_list.append(new_photo)
 
    return photos_list

#---------------------------------------------------------------
def Get_followers_list(driver, user_inputs):
    """Given a user name, return the list of followers, the link to theis pages and the number of followers of each of them.

    PROCESS:
    - OPEN THE USER HOME PAGE, LOCATE THE TEXT followers AND CLICK ON IT TO OPEN THE MODAL WINDONW CONTAINING FOLLOWERS LIST
    - SCROLL TO THE END FOR ALL ITEMS TO BE LOADED
    - MAKE SURE THE DOCUMENT JS IS RUNNING FOR ALL THE DATA TO LOAD IN THE PAGE BODY
    - EXTRACT INFO AND PUT IN A LIST. RETURN THE LIST
    """

    followers_list = []
    if Open_user_home_page(driver, user_inputs.user_name) == False:
        user_inputs.user_name = ''
        Show_menu(user_inputs)
        return []
    Hide_banners(driver)
    # click on the Followers text to open the modal window
    ele = check_and_get_ele_by_class_name(driver, "followers")    
    if ele is not None:
       ele.click()

    # abort the action if the target objects failed to load within a timeout of 15s
    if not Finish_Javascript_rendered_body_content(driver, time_out=15, class_name_to_check='actors')[0]:
        return []

    # extract number of followers                 
    followers_ele = check_and_get_ele_by_xpath(driver, '//*[@id="modal_content"]/div/div/div/div/div[1]/span')
    if followers_ele is None:
        return []
    # remode thousand-separator character, if existed
    followers_count = int(followers_ele.text.replace(",", "").replace(".", ""))

    # keep scrolling the modal window (LOADED_ITEM_PER_PAGE items are loaded at a time), until the end, where the followers count is reached 
    iteration_num = math.floor(followers_count / LOADED_ITEM_PER_PAGE) + 1 
    printG(f'User {user_inputs.user_name} has {str(followers_count)} follower(s)')
           
    for i in range(1, iteration_num):
        update_progress(i / (iteration_num -1), ' - Scrolling down to load all followers:')
        index_of_last_item_on_page = i * LOADED_ITEM_PER_PAGE
        last_ele = check_and_get_ele_by_xpath(driver, '//*[@id="modal_content"]/div/div/div/div/div[2]/ul/li[' + str(index_of_last_item_on_page) + ']')
            
        if last_ele is not None:
            last_ele.location_once_scrolled_into_view
            time.sleep(2)
        else:
            pass
    # now that we have all followers loaded, start extracting the info
    update_progress(0, f' - Extracting data 0/{followers_count}:')

    # abort the action if the target objects failed to load within a timeout of 15s
    if not Finish_Javascript_rendered_body_content(driver, time_out=15, class_name_to_check='finished')[0]:
        return None, None

    actor_infos = driver.find_elements_by_class_name('actor_info')
    actors_following =  driver.find_elements_by_css_selector('.actor.following')
    len_following = len(actors_following)

    lenght = len(actor_infos)

    follower_user_name = ''
    follower_page_link = ''
    count = ' '
    following_status = ''

    for i, actor in enumerate(actor_infos):
        if i > 0:
            update_progress( i / (len(actor_infos) - 1), f' - Extracting data {i + 1}/{followers_count}:')
  
        try:
            name_ele = check_and_get_ele_by_class_name(actor, 'name')  
            if name_ele is not None:
                follower_page_link = name_ele.get_attribute('href')
                follower_user_name = follower_page_link.replace('https://500px.com/', '')
        except NoSuchElementException:
            continue  #ignore if follower name not found

        # if logged-in, we can determine if this user has been followed or not
        if user_inputs.password != '':
            try:          
                class_name_ele = check_and_get_ele_by_xpath(actor, '../..')  #class_name = actor.find_element_by_xpath('../..').get_attribute('class')
                if class_name_ele is not None:
                    class_name = class_name_ele.get_attribute('class')
                    following_status = 'Following' if class_name.find('following') != -1  else 'Not yet follow'
            except NoSuchElementException:
                pass

        number_of_followers = ''
        texts = actor.text.split('\n')
        if len(texts) > 1: 
            follower_name = texts[0] 
            count = texts[1]
            number_of_followers =  count.replace(' followers', '').replace(' follower', '') 
        followers_list.append(user(str(i+1), follower_name, follower_user_name, number_of_followers, following_status))
    return  followers_list 

#---------------------------------------------------------------
def Does_this_user_follow_me(driver, user_inputs):
    """Check if a target_user follows a given user

    PROCESS:
    GET THE LIST OF USERS THAT THE TARGET USER IS FOLLOWING, THEN CHECK IF THE LIST CONTAINT THE GIVEN USER NAME
    FOR BETTER PERFORMANCE, WE DO NOT LOAD THE FULL LIST BUT RATHER 50 USERS AT A TIME (LOADED_ITEM_PER_PAGE IS 50). WE LOAD MORE (SCROLLING DOWN)
    ONLY IF NEEDED:
    - OPEN THE TARGER USER HOME PAGE, LOCATE THE TEXT Following AND CLICK ON IT TO OPEN THE MODAL WINDONW CONTAINING FOLLOWING USERS LIST
    - SCROLL TO THE LAST LOADED ITEM TO MAKE ALL DATA AVAILABLE
    - MAKE SURE THE DOCUMENT JS IS RUNNING FOR ALL THE DATA TO LOAD IN THE PAGE BODY
    - COMPARE THE USER NAME OF EACH LOAD ITEM TO THE GIVEN my_user_name. STOP IF A MATCH IS FOUND, OR CONTINUE TO THE NEXT ITEM UNTIL ALL THE LOADED ITEMS...
      ARE PROCESSED. SCROLLING DOWN TO LOAD MORE ITEMS AND REPEAT THE PROCESS.
    """
 
    if Open_user_home_page(driver, user_inputs.target_user_name) == False:
        user_inputs.target_user_name = ''
        #Show_menu(user_inputs)
        return False, f"User name {user_inputs.target_user_name} not found"
  
    Hide_banners(driver)     
    # click on the Following text to open the modal window
    ele = check_and_get_ele_by_xpath(driver, '//*[@id="content"]/div[1]/div[4]/ul/li[4]')     
    if ele is not None:
        ele.click()

    # abort the action if the target objects failed to load within a timeout of 15s
    if not Finish_Javascript_rendered_body_content(driver, time_out=15, class_name_to_check='actors')[0]:
        return  False, ""

    # extract number of following                      
    following_ele = check_and_get_ele_by_xpath(driver, '//*[@id="modal_content"]/div/div/div/div/div[1]/span') 
    if following_ele is None:
        return  False, ""

    # remode thousand separator character, if existed
    following_count = int(following_ele.text.replace(",", "").replace(".", ""))
    printG(f'User {user_inputs.target_user_name} is following {str(following_count)} user(s)')
    if following_count == 0:
        return  False, ""
  
    # start the progress bar
    update_progress(0, ' - Processing loaded data:')
    iteration_num = math.floor(following_count / LOADED_ITEM_PER_PAGE) + 1    

    users_done = 0
    current_index = 0   # the index of the photo in the loaded photos list. We dynamically scroll down the page to load more photos as we go, so ...
                        # ... more photos are appended at the end of the list. We use this current_index to keep track where we were after a list update 
    
    # abort the action if the target objects failed to load within a timeout of 15s    
    if not Finish_Javascript_rendered_body_content(driver, time_out=15, class_name_to_check='finished')[0]:
        return  False, ""

    actor_infos = driver.find_elements_by_class_name('actor_info')
    loaded_users_count = len(actor_infos)

    while users_done < following_count: 
        # check if we have processed all loaded users, then we have to load more  
        if current_index >= loaded_users_count: 
            prev_loaded_users = loaded_users_count
            # loading more users by scrolling into view the last loaded item
            last_item_on_page =  current_index -1  #i * LOADED_ITEM_PER_PAGE - 1
            try:
                loaded_elements = check_and_get_all_elements_by_xpath(driver, '//*[@id="modal_content"]/div/div/div/div/div[2]/ul/li[' + str(last_item_on_page) + ']')                                                                   
                if len(loaded_elements) > 0:
                    loaded_elements[-1].location_once_scrolled_into_view
                    time.sleep(2)
            except NoSuchElementException:
                pass

            # abort the action if the target objects failed to load within a timeout of 15s    
            if not Finish_Javascript_rendered_body_content(driver, time_out=15, class_name_to_check='finished')[0]:
                return  False, ""

            # update list with more users
            actor_infos = driver.find_elements_by_class_name('actor_info')
            loaded_users_count = len(actor_infos)
 
            # stop when all photos are loaded
            if loaded_users_count == prev_loaded_users:
                break;

        following_user_name = ''
        following_user_page_link = ''
        for i in range(current_index, loaded_users_count):
            current_index += 1
            actor = actor_infos[i]
            update_progress(current_index / following_count, f' - Processing loaded data {current_index}/{following_count}:')  
            try:
                ele = check_and_get_ele_by_class_name(actor, 'name')   #following_user_page_link = actor.find_element_by_class_name('name').get_attribute('href')
                if ele is not None:
                    following_user_page_link = ele.get_attribute('href')
                    following_user_name = following_user_page_link.replace('https://500px.com/', '')

                if following_user_name is not None and following_user_name == user_inputs.user_name:
                    update_progress(1, f' - Processing loaded data {current_index}/{following_count}:')
                    detail_message = f'({current_index}/{following_count})'
                    return True, detail_message

            except NoSuchElementException:
                continue  #ignore if follower name not found

    return False, ''

#---------------------------------------------------------------
# Time-consuming process, in need for a better solution to improve or to limit the request number ( in-progress)
def Get_following_statuses(driver, user_inputs, start_index, number_of_users, following_list):
    """ Get the follow statuses of the users that you are following, with the option to specify the range of user in the following list.
   
    start_user_index IS 1-BASED AND WILL BE CONVERTED TO 0-BASED
    number_of_users : THIS IS A LENGTHY PROCESS, SO WE PROVIDE THIS OPTION TO LIMIT THE NUMBER OF USERS WE WILL PROCESS. PASSING -1 TO IGNORE THIS LIMIT
    """
    import pandas as pd

    csv_file = os.path.join(output_lists.output_dir, user_inputs.user_name + '_followings.csv')
    result_file = os.path.join(output_lists.output_dir, user_inputs.user_name + '_following_statuses.csv')

    # the end user will use 1-base index, so we will convert the input to 0-base index
    if start_index > 0: start_index -= 1

    # use the following list if it exists
    if following_list is not None and len(following_list) > 0:
        # convert list of users to dataframe
        # ERROR HERE, WRONG COLUMN ORDER
        df = pd.DataFrame.from_records([s.to_dict() for s in following_list])
        df.columns = ["Order", "Display Name", "User Name", "Followers", "Status"]
        #size = str(len(following_list))
        printY(f'Using the existing list in memory (str(len({following_list})) users)')
        print(df)

    # use the csv data file on disk if it exists 
    elif os.path.isfile(csv_file):
        df = pd.read_csv(csv_file, encoding='utf-16') #, usecols=["User Name"])     
        # a trick to force column Status content as string instead of the default float      
        df.Status = df.Status.fillna(value="")      
        
        # make sure the user's inputs stay in range with the size of the following list
        followings_count = df.shape[0]
        start_index = min(start_index, followings_count -1)

        printY(f'Using the existing csv file on disk {csv_file} ({followings_count} users)')
    # get the list of followings users
    # else:
      
   
    # process each user in dataframe
    for index, row in df.iterrows():
        if index < start_index:
            continue
        if number_of_users != -1 and index > start_index + number_of_users - 1:
            break
        user_inputs.target_user_name = row["User Name"]
        result, message = Does_this_user_follow_me(driver, user_inputs)
        status = ''
        if result == True:
            status = 'Following you ' + message
            printG(status)
        elif message == 'User name not found':
            printR(message)
        else:
            status = 'Not following you'
            printR(status)
        df.at[index, 'Status'] = status
        
    print(df) 
    try:
        df.to_csv(result_file, encoding='utf-16', index = False)
    except: # pd.Errors.PermissionDenied:
        printR(f'Error writing file {os.path.abspath(result_file)}.\nMake sure the file is not in use. Then type r for retry >')
        retry = input()
        if retry == 'r': 
            df.to_csv(result_file, encoding='utf-16', index = False)
        else:
            printR('Error witing file' + os.path.abspath(result_file))
            return 
    Show_html_result_file(CSV_to_HTML(result_file))

#---------------------------------------------------------------
def Get_followings_list(driver, user_inputs):
    """Get the list of followings, the link to theis pages and the number of followers of each of them.

    PROCESS:
    - OPEN THE USER HOME PAGE, LOCATE THE TEXT followers AND CLICK ON IT TO OPEN THE MODAL WINDONW CONTAINING FOLLOWERS LIST
    - SCROLL TO THE END FOR ALL ITEMS TO BE LOADED
    - MAKE SURE THE DOCUMENT JS IS RUNNING FOR ALL THE DATA TO LOAD IN THE PAGE BODY
    - EXTRACT INFO AND PUT IN A LIST. RETURN THE LIST
    """

    followings_list = []
    if Open_user_home_page(driver, user_inputs.user_name) == False:
        user_inputs.user_name = ''
        Show_menu(user_inputs)
        return []
    Hide_banners(driver)                  
                                          
    # click on the Following text to open the modal window
    ele = check_and_get_ele_by_xpath(driver, '//*[@id="content"]/div[1]/div[4]/ul/li[4]')     
    if ele is not None:
        ele.click()
    
    # abort the action if the target objects failed to load within a timeout of 15s    
    if not Finish_Javascript_rendered_body_content(driver, time_out=15, class_name_to_check='actors')[0]:
        return []
            
    # extract number of following                      
    following_ele = check_and_get_ele_by_xpath(driver, '//*[@id="modal_content"]/div/div/div/div/div[1]/span') 
    if following_ele is None:
        return []

    # remove thousand separator character, if existed
    following_count = int(following_ele.text.replace(",", "").replace(".", ""))
    printG(f'User {user_inputs.user_name} is following { str(following_count)} user(s)')
    

    # keep scrolling the modal window, 50 followers at a time, until the end, where the followers count is reached 
    iteration_num = math.floor(following_count / LOADED_ITEM_PER_PAGE) + 1 
    for i in range(1, iteration_num):
        update_progress(i / (iteration_num -1 ), ' - Scrolling down to load all following users')
        last_item_on_page = i * LOADED_ITEM_PER_PAGE - 1
        try:
            the_last_in_list = driver.find_elements_by_xpath('//*[@id="modal_content"]/div/div/div/div/div[2]/ul/li[' + str(last_item_on_page) + ']')[-1]                                                             
            the_last_in_list.location_once_scrolled_into_view
            time.sleep(2)
        except NoSuchElementException:
            pass
 
    # now that we have all followers loaded, start extracting info
    update_progress(0, ' - Extracting data:')
    actor_infos = driver.find_elements_by_class_name('actor_info')
    lenght = len(actor_infos)
    following_name = ''
    followings_page_link = ''
    count = '' 

    for i, actor in enumerate(actor_infos):
        if i > 0:
            update_progress( i / (len(actor_infos) - 1), f' - Extracting data {i + 1}/{following_count}:')

        try:
            #following_page_link = actor.find_element_by_class_name('name').get_attribute('href')
            ele = check_and_get_ele_by_class_name(actor, 'name')
            if ele is not None:
                following_page_link = ele.get_attribute('href')
                following_user_name = following_page_link.replace('https://500px.com/', '')
        except NoSuchElementException:
            continue  #ignore if follower name not found

        texts = actor.text.split('\n')
        if len(texts) > 0: following_name = texts[0] 
        if len(texts) > 1: count = texts[1]; number_of_followings =  count.replace(' followers', '').replace(' follower', '')  
        followings_list.append(user(str(i+1), following_name, following_user_name, number_of_followings))
    return followings_list 

#---------------------------------------------------------------
def Get_notification_list(driver, user_inputs, get_full_detail = True ):
    """Get n last notification items. Return 2 lists, notifications list and a list of unique users from it, along with the count of appearances of each user
    
    A DETAILED NOTIFICATION ITEM CONTAINS FULL_NAME, USER NAME, THE CONTENT OF THE NOTIFICATION, TITLE OF THE PHOTO IN QUESTION, THE TIME STAMP AND A STATUS
    A SHORT NOTIFICATION ITEM CONTAINS JUST FULL NAME AND USER NAME
    A UNIQUE NOTIFICATION LIST IS A SHORT NOTIFICATION LIST WHERE ALL THE DUPLICATION ARE REMOVED.
    IF THE GIVEN get_full_detail IS TRUE, RETURN THE DETAILED LIST, IF FALSE, RETURN THE UNIQUE LIST
    PROCESS:
    - EXPECTING THE USER WAS LOGGED IN, AND THE NOTIFICATION PAGE IS THE ACTIVE PAGE
    - SCROLL DOWN  N TIMES FOR ALL REQUIRED ITEMS TO BE LOADED . N IS CALCULATED BY THE GIVEN number_of_notifications AND THE CONSTANT 'NOTIFICATION_PER_LOAD'
    - EXTRACT INFO, RETURN THE FULL LIST OF A UNIQUE LIST DEPENTING ON THE REQUEST
    """

    unique_notificators = []
    notifications_list = []
    short_list = []

    if user_inputs.number_of_notifications == -1: # secret switch: -1 to bypass the limit on number of notifications (could be time-consuming process)
        scrolls_needed = -1
    else:                                         # Notifications are loaded 20 items at a time. Ex. to get 80 items we need to scroll 4 times 
        scrolls_needed =  math.floor(user_inputs.number_of_notifications / NOTIFICATION_PER_LOAD) +1

    pause_between_scrolls = 1.5
    estimate_scrolls_needed = scrolls_needed
    # estimate_scrolls_needed is used only when we want unlimited scrolls times (scrolls_needed = -1). We pass irrelevant value here to Scroll_down() just to fill the function signature 
    Scroll_down(driver, pause_between_scrolls, scrolls_needed, estimate_scrolls_needed, ' - Scrolling down for more notifications:' ) 

    # get the info now that all the needed notifications are loaded
    items = driver.find_elements_by_class_name('notification_item')  
    count = len(items) 
    # number of loaded items may exceed the required items: adjust to count accordingly for the correct progresstion
    if count > user_inputs.number_of_notifications:
       count = user_inputs.number_of_notifications 
    for i, item in enumerate(items):
        if user_inputs.number_of_notifications != -1 and i >=  user_inputs.number_of_notifications:
            update_progress(1, f' - Extracting data {user_inputs.number_of_notifications}/{user_inputs.number_of_notifications}:')
            break
        if i > 0:
            update_progress( i / (count), f' - Extracting data {i}/{count}:')

        actor = check_and_get_ele_by_class_name(item, 'notification_item__actor') 
        if actor is None:
            continue
        display_name = actor.text
        user_name = actor.get_attribute('href').replace('https://500px.com/', '')
        
        item_text = check_and_get_ele_by_class_name(item, 'notification_item__text')  #item.find_element_by_class_name('notification_item__text')
        if item_text is not  None:
            if item_text.text.find('liked') != -1: 
                content = 'liked'
            elif item_text.text.find('followed') != -1: 
                content = 'followed'
            elif item_text.text.find('added') != -1: 
                content = 'added to gallery'
            elif item_text.text.find('commented') != -1: 
                content = 'commented'
            else: 
                content = item_text.text
            # ignore Quest notification
            if content.find('Quest') != -1:
                continue

        photo_ele = check_and_get_ele_by_class_name(item_text, 'notification_item__photo_link')
        photo_title = ''
        photo_link = ''        
        status = ''
        # in case of a new follow, instead of a photo element, there will be 2 overlapping boxex, Follow and Following. We will determine if whether or not this actor has been followered  
        if photo_ele is None:  
            following_box = check_and_get_ele_by_class_name(item, 'following')
            if following_box is not None and following_box.is_displayed():        
                status = 'Following'
            else:  
                status = 'Not yet follow' 

        else: 
            photo_title = photo_ele.text
            photo_link = photo_ele.get_attribute('href') 
        
        ele = check_and_get_ele_by_class_name(item, 'notification_item__timestamp')  #timestamp = item.find_element_by_class_name('notification_item__timestamp').text
        timestamp  = ele.text if ele is not None else ""
        notifications_list.append(notification(str(i+1), display_name, user_name, content, photo_link, photo_title, timestamp, status))
        # in some rare cases, the user_name may contain coma. We replace it with space
        short_list.append(f'{display_name.replace(",", " ")},{user_name}')

    unique_notificators = Count_And_Remove_Duplications(short_list)

    # add order number at the begining of each row
    for j in range(len(unique_notificators)):
        unique_notificators[j] = f'{str(j+1)},{unique_notificators[j]}'

    if len(notifications_list) == 0 and len(unique_notificators) == 0: 
        printG(f'User {user_name} has no notification')
   
    return notifications_list, unique_notificators

#---------------------------------------------------------------
def Get_like_actioners_list(driver, output_lists):
    """Get the list of users who liked a given photo. Return the list a suggested file name that includes owner name, photo title and the like count

    PROCESS:
    - EXPECTING THE ACTIVE PAGE IN THE BROWSER IS THE GIVEN PHOTO PAGE
    - RUN THE DOCUMENT JS TO RENDER THE PAGE BODY
    - EXTRACT PHOTO TITLE AND PHOTOGRAPHER NAME
    - LOCATE THE LIKE COUNT NUMBER THEN CLICK ON IT TO OPEN THE MODAL WINDOW HOSTING THE LIST OF ACTIONER USER
    - SCROLL DOWN TO THE END AND EXTRACT RELEVANT INFO, PUT ALL TO THE LIST AND RETURN IT
    """

    actioners_list = []
    date_string = datetime.datetime.now().replace(microsecond=0).strftime("%Y_%m_%d")

    # abort the action if the target objects failed to load within a timeout of 15s    
    if not Finish_Javascript_rendered_body_content(driver, time_out=15, class_name_to_check='react_photos_index_container')[0]:
        return None, None
 
    # find an ancestor element that cover all needed elements
    react_photos_index_container = check_and_get_ele_by_class_name(driver, 'react_photos_index_container')
    if react_photos_index_container is None:
        printR('Error getting like_actioners list')
        return [], ''
    print(' - Getting photo details ...')
    styled_link =  check_and_get_ele_by_xpath(react_photos_index_container, '//div/div/div[2]/div/div[2]/div[2]/div[1]/p[1]/span/a') 
                                                                             
    if styled_link is not None: 
        styled_link.location_once_scrolled_into_view
        photographer_name = styled_link.text
    else:                       
        photographer_name = 'Photographer name not found'
    printG(f'   Photogapher: {photographer_name}')

    styled_layout_box = check_and_get_ele_by_xpath(react_photos_index_container, '//div/div/div[2]/div/div[2]/div[2]/div[1]/h3')
    if styled_layout_box is None: 
        printR('Error getting like_actioners list')
        return [], ''
    photo_title = styled_layout_box.text
    printG(f'   Photo title: {photo_title}')

    # make sure the  photo title is visible
    styled_layout_box.location_once_scrolled_into_view

    # find the affection count number element, get the affection count 
    count_number_button = check_and_get_ele_by_xpath(react_photos_index_container, '//div/div/div[2]/div/div[2]/div[1]/div[1]/a')
    if count_number_button is None:                           
        printG('   Photo has 0 like')
        return [], ''
    likes_count_string = count_number_button.text
    likes_count = int(likes_count_string.replace('.','').replace(',',''))
    printG(f"   This photo has {likes_count}'s likes")
    
    # click on affection count number element to open the modal window, wait for page loading
    driver.execute_script("arguments[0].click();", count_number_button)
    
    # abort the action if the target objects failed to load within a timeout of 15s    
    #if not Finish_Javascript_rendered_body_content(driver, time_out=15, class_name_to_check = 'ant-modal-body')[0]:
    #    return []	
    time.sleep(2)
        
    # make a meaningful output file name
    like_actioners_file_name = os.path.join(output_lists.output_dir, \
        f"{photographer_name.replace(' ', '-')}_{photo_title.replace(' ', '-')}_{likes_count}_ like_actioners_{date_string}.csv")

    # scroll to the end for all elements of the given class name to load all actioners
    Scroll_to_end_by_class_name(driver, 'ifsGet', likes_count)
    
    # create actionners list
    actioners = driver.find_elements_by_class_name('ifsGet')
    actioners_count = len(actioners)
    display_name = ''
    followers_count = ''
    for i, actioner in enumerate(actioners):
        update_progress(i / (actioners_count - 1), f' - Extracting data {i+1}/{actioners_count}:')
        try:    
            texts = actioner.text.split('\n')
            if len(texts) > 0: 
                display_name = texts[0] 
            if len(texts) > 1:
                followers_count  = re.sub('[^\d]+', '', texts[1]) 
            # extract actioner's user name
            ele = check_and_get_ele_by_tag_name(actioner, 'a') 
            if ele is not None:
                name = ele.get_attribute('href').replace('https://500px.com/','')

            actioners_list.append(user(str(i+1), display_name, name, str(followers_count)) )
        except NoSuchElementException:
            continue
    return actioners_list, like_actioners_file_name 

#---------------------------------------------------------------
def Like_n_photos_from_user(driver, target_user_name, number_of_photos_to_be_liked, include_already_liked_photo_in_count = True, close_browser_on_error = True):
    """Like n photo of a given user, starting from the top. Return False if error occurs

    IF THE include_already_liked_photo IS TRUE (DEFAULT), THE ALREADY-LIKED PHOTO WILL BE COUNTED AS DONE BY THE AUTO-LIKE PROCESS
    FOR EXAMPLE, IF YOU NEED TO AUTO-LIKE 3 PHOTOS FROM A USER, BUT THE FIRST TWO ARE ALREADY LIKED, THEN YOU ONLY NEED TO DO ONE
    IF THE include_already_liked_photo_in_count IS FALSE, THE PROCESS WILL AUTO-LIKE THE EXACT NUMBER REQUESTED
    THE ARGUMENT close_browser_on_error NEEDS TO BE FALSE IF THIS FUNCTION IS CALLED IN A LOOP: IF ERRORS OCCUR, WE WANT TO PROCESS THE NEXT ITEM
    PROCESS:
    - OPEN THE USER HOME PAGE
    - FORCE DOCUMENT JS TO RUN TO FILL THE VISIBLE BODY
    - LOCATE THE FIRST PHOTO, CHECK IF IT IS ALREADY-LIKED OR NOT, IF YES, GO THE NEXT PHOTO, IT NO, CLICK ON IT TO LIKE THE PHOTO
    - CONTINUE UNTIL THE ASKING NUMBER OF PHOTOS IS REACHED. 
    - WHEN WE HAVE PROCESSED ALL THE LOADED PHOTOS BUT THE REQUIRED NUMBER IS NOT REACHED YET, 
      ... SCROLL DOWN ONCE TO LOAD MORE PHOTOS ( CURRENTLY 500PX LOADS 50 PHOTOS AT A TIME) AND REPEAT THE STEPS UNTIL DONE
      """
    if Open_user_home_page(driver, target_user_name) == False:
        #user_inputs.user_name = ''
        if close_browser_on_error == True:
            Close_chrome_browser(driver)
        return False
                    
    # abort the action if the target objects failed to load within a timeout of 15s    
    if not Finish_Javascript_rendered_body_content(driver, time_out=15, class_name_to_check='finished')[0]:
        return None, None

    Hide_banners(driver)        
    
    new_fav_icons =  check_and_get_all_elements_by_css_selector(driver, '.button.new_fav.only_icon') 
    if len(new_fav_icons) == 0:
        printY('  - user has no photos')
    done_count = 0

    for i, icon in enumerate(new_fav_icons):
       # skip already-liked photo. Count it as done if requested so
        if done_count < number_of_photos_to_be_liked and 'heart' in icon.get_attribute('class'): 
            if include_already_liked_photo_in_count == True:
                done_count = done_count + 1          
            printY(f'  - liked #{str(done_count):3} Photo { str(i+1):2} - already liked')

            continue        

        # check limit
        if done_count >= number_of_photos_to_be_liked:  
            break
        
        Hover_by_element(driver, icon) # not neccessary, but good for visual demonstration
        try:
            title =  icon.find_element_by_xpath('../../../../..').find_element_by_class_name('photo_link').find_element_by_tag_name('img').get_attribute('alt')
            driver.execute_script("arguments[0].click();", icon) 
            done_count = done_count + 1
            printG(f'  - liked #{str(done_count):3} Photo {str(i + 1):2} - {title:.50}')
            # intentional slowing  down a bit to make it look more like human
            time.sleep(1)

        except Exception as e:
            printR(f'Error after {str(done_count)}, at index {str(i)}, title {title}:\nException: {e}')
            return False
    return True

#---------------------------------------------------------------
def Like_n_photos_on_current_page(driver, number_of_photos_to_be_liked, index_of_start_photo):
    """Like n photos on the active photo page. It could be either popular, popular-undiscovered, upcoming, fresh or editor's choice page.

    THIS WILL AUTOMATICALLY SCROLL DOWN IF MORE PHOTOS ARE NEEDED
    PROCESS:
    - SIMILAR TO THE PREVIOUS METHOD ( Autolike_photos() )
    """
    photos_done = 0
    current_index = 0   # the index of the photo in the loaded photos list. We dynamically scroll down the page to load more photos as we go, so ...
                        # ... more photos are appended at the end of the list. We use this current_index to keep track where we were after a list update 
            
    # debug info: without scrolling, it would load (PHOTOS_PER_PAGE = 50) photos
    new_fav_icons = check_and_get_all_elements_by_css_selector(driver, '.button.new_fav.only_icon')  #driver.find_elements_by_css_selector('.button.new_fav.only_icon')
    loaded_photos_count = len(new_fav_icons)

    #optimization: at the begining, scrolling down to the desired index instead of repeatedly scrolling & checking 
    if index_of_start_photo > PHOTOS_PER_PAGE:
        estimate_scrolls_needed =  math.floor( index_of_start_photo / PHOTOS_PER_PAGE) +1
        Scroll_down(driver, 1, estimate_scrolls_needed, estimate_scrolls_needed, f' - Scrolling down to photos #{index_of_start_photo}:') 
        
        # instead of a fixed waiting time, we wait until the desired photo to be loaded  
        while loaded_photos_count < index_of_start_photo:
            new_fav_icons = check_and_get_all_elements_by_css_selector(driver, '.button.new_fav.only_icon')
            loaded_photos_count = len(new_fav_icons)
          
    while photos_done < number_of_photos_to_be_liked: 
        # if all loaded photos have been processed, scroll down 1 time to load more
        if current_index >= loaded_photos_count: 
            prev_loaded_photos = loaded_photos_count
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # instead of a fixed waiting time, we wait until the desired photo to be loaded  
            while loaded_photos_count <= current_index:
                new_fav_icons =  check_and_get_all_elements_by_css_selector(driver, '.button.new_fav.only_icon')  
                loaded_photos_count = len(new_fav_icons)

            # stop when all photos are loaded
            if loaded_photos_count == prev_loaded_photos:
                break;

        for i in range(current_index, loaded_photos_count):
            current_index += 1
            icon = new_fav_icons[i]

            # stop when limit reaches
            if photos_done >= number_of_photos_to_be_liked: break     
            # skip un-interested items  
            if i < index_of_start_photo - 1 : continue                   
            # skip already liked photo: 'liked' class is a subclass of 'new_fav_only_icon', so these elements are also included in the list
            if 'heart' in icon.get_attribute('class'): continue
            
            Hover_by_element(driver, icon) # not needed, but good to have a visual demonstration
            try:
                #intentional slowing down a bit to make it look more like human
                time.sleep(1.5)
                title =  icon.find_element_by_xpath('../../../../..').find_element_by_class_name('photo_link').find_element_by_tag_name('img').get_attribute('alt')
                photographer_ele = icon.find_element_by_xpath('../../../..').find_element_by_class_name('photographer')
                photographer_ele.location_once_scrolled_into_view
                Hover_by_element(driver, photographer_ele)
                #driver.execute_script("arguments[0].scrollIntoView();", photographer_ele)
                photographer = photographer_ele.text
                driver.execute_script("arguments[0].click();", icon) 
                photos_done = photos_done + 1
                printG(f'Liked {str(photos_done):>3}/{number_of_photos_to_be_liked:<3}, {photographer:<28.24}, Photo {str(i+1):<4} title {title:<35.35}')
            except Exception as e:
                printR(f'Error after {str(photos_done)}, at index {str(i+1)}, title {title}:\nException: {e}')

#---------------------------------------------------------------
def Play_slideshow(driver, time_interval):
    """Play slideshow of photos on the active photo page in browser.

    PROCESS:
    EXPECTING THE ACTIVE PAGE IN BROWSER IS THE PHOTOS PAGE
    - OPEN THE FIRST PHOTO BY CLICK ON IT
    - CLICK ON THE EXPAND ARROW TO MAXIMIZE THE DISPLAY AREA 
    - AFTER A GIVEN TIME INTERVAL, LOCATE THE NEXT BUTTON AND CLICK ON IT TO SHOW THE NEXT PHOTO
    - EXIT WHEN LAST PHOTO IS REACHED
    """
    photo_links_eles = check_and_get_all_elements_by_class_name(driver, 'photo_link')
    loaded_photos_count = len(photo_links_eles)
 
    if len(photo_links_eles) > 0:
        # show the first photo
        driver.execute_script("arguments[0].click();", photo_links_eles[0])
        
        # abort the action if the target objects failed to load within a timeout of 15s    
        if not Finish_Javascript_rendered_body_content(driver, time_out=15, class_name_to_check = 'entry-visible')[0]:
            return None, None	
        
        # suppress the sign-in popup that may appear if not login
        Hide_banners(driver)
        
        # locate the expand icon and click it to expand the photo
        expand_icon = check_and_get_ele_by_xpath(driver, '//*[@id="copyrightTooltipContainer"]/div/div[2]') 
        if expand_icon is not None:
            driver.execute_script("arguments[0].click();",expand_icon)
        time.sleep(time_interval)
        
        # locate the next icon and click it to show the next image, after a time interval
        next_icon = check_and_get_ele_by_xpath(driver, '//*[@id="copyrightTooltipContainer"]/div/div[1]/div') 
        while next_icon is not None:
            driver.execute_script("arguments[0].click();", next_icon)
            time.sleep(time_interval)
            next_icon = check_and_get_ele_by_xpath(driver,  '//*[@id="copyrightTooltipContainer"]/div/div[2]/div/div[2]')  

#---------------------------------------------------------------                           
def Like_n_photos_on_homefeed_page(driver, user_inputs):
    """Like n photos from the user's home feed page, excluding recommended photos and skipping consecutive photo(s) of the same user
   
    PROCESS:
    - EXPECTING THE USER HOME FEED PAGE IS THE ACTIVE PAGE IN THE BROWSER
    - GET THE LIST ELEMENTS REPRESENTING LOADED INTERESTED PHOTOS (THE ONES FROM PHOTOGRAPHERS THAT YOU ARE FOLLOWING)
    - FOR EACH ELEMENT IN THE LIST, TRAVERSE UP, DOWN THE XML TREE FOR PHOTO TITLE, OWNER NAME, LIKE STATUS, AND MAKE A DECISION TO CLICK THE LIKE ICON OR NOT
    - CONTINUE UNTIL THE REQUIRED NUMBER IS REACHED. ALONG THE WAY, STOP AND SCROLL DOWN TO LOAD MORE PHOTOS WHEN NEEDED 
    """
    photos_done = 0
    current_index = 0  # the index of the photo in the loaded photos list. We dynamically scroll down the page to load more photos as we go, so ...
                       # ... we use this index to keep track where we are after a list update 
    prev_photographer_name = ''
    print(f"Getting the loaded photos from {user_inputs.user_name}'s home feed page ...")
    img_eles = Get_IMG_element_from_homefeed_page(driver)
    loaded_photos_count = len(img_eles)
   
    while photos_done < user_inputs.number_of_photos_to_be_liked: 
        # check whether we have processed all loaded photos, if yes, scroll down 1 time to load more
        if current_index >= loaded_photos_count: 
            prev_loaded_photos = loaded_photos_count
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")                
            time.sleep(2)

            img_eles = Get_IMG_element_from_homefeed_page(driver)
            loaded_photos_count = len(img_eles)

            # stop when all photos are loaded
            if loaded_photos_count == prev_loaded_photos:
                break;

        for i in range(current_index, loaded_photos_count):
            # stop when done
            if photos_done >= user_inputs.number_of_photos_to_be_liked: 
                break
            current_index += 1
            photographer_name = ' '
            title = ' '
            parent2 = check_and_get_ele_by_xpath(img_eles[i], '../..')   
            if parent2 is None: 
                continue
                
            parent2_sib1 =  check_and_get_ele_by_xpath(parent2, './following-sibling::div') 
            if parent2_sib1 is None: 
                continue
                
            # Skip if this is your own photo. Show console log in Blue color 
            child_div_eles = check_and_get_all_elements_by_tag_name(parent2_sib1, 'div')  
            if len(child_div_eles) > 1:
                if child_div_eles[1].text.find('disabled') != -1: # this may be your own photo 
                    printB(f'Skipped  : photo {str(i + 1):<3}, from {photographer_display_name:<32.30}, {title:<35.35}')
                    continue

            parent2_sib2 =  check_and_get_ele_by_xpath(parent2_sib1, './following-sibling::div') 
            if parent2_sib2 is  None: 
                continue    
            # for logging message, get photo title, photogragpher display name and  user name
            title_ele = check_and_get_ele_by_tag_name(parent2_sib2, 'h3') #title  = parent2_sib2.find_element_by_tag_name('h3').text            
            title = title_ele.text if title_ele is not None else 'not determined'
           
            a_ele = check_and_get_ele_by_tag_name(parent2_sib2, 'a')  #a = parent2_sib2.find_element_by_tag_name('a')
            photographer_display_name  = a_ele.text if a_ele is not None else "not determined"
            photographer_name = a_ele.get_attribute('href').replace('https://500px.com/', '') if a_ele is not None else "not determined"

            # get like status
            photo_already_liked = False
            if  parent2_sib1.text.find('Outline') == -1:
                photo_already_liked = True
                 
            # get the like icon to click on           
            span_ele = check_and_get_ele_by_tag_name(parent2_sib1, 'span')  
            if span_ele is not None:
                span_ele.location_once_scrolled_into_view
            
            heart_icon = check_and_get_ele_by_xpath(span_ele, './following-sibling::div')
            # this may be your own photo
            if heart_icon is None:
                printB(f'Skipped:      photo {str(i + 1):3}, from {photographer_display_name:<32.30}, {title:<35.35}')
                continue

            Hover_by_element(driver, heart_icon)
            if  not photo_already_liked:      
                # skip consecutive photos of the same photographer
                if photographer_name == prev_photographer_name:
                    printY(f'Skipped:      photo {str(i + 1):3}, from {photographer_display_name:<32.30}, {title:<35.35}')
                    continue
                if heart_icon is not None:
                    driver.execute_script("arguments[0].click();", heart_icon) 
                    photos_done += 1
                    prev_photographer_name = photographer_name
                    printG(f'Like {photos_done:>3}/{user_inputs.number_of_photos_to_be_liked:<3}: photo {str(i + 1):<3}, from {photographer_display_name:<32.30}, {title:<40.40}')
                    time.sleep(1.5)  # slow down a bit to make it look more like a human

#---------------------------------------------------------------
def Count_And_Remove_Duplications(values):
    """Given a list containing the strings of display name and user name separated by a comma such as "John Doe, johndoe" .
       Count the  duplication then remove the duplicated entry. Append the count to each entry ."""
    output = []
    seen = set()
    count = 0
    for value in values:
        # If value has not been encountered yet, add it to the seen set then append count as "1" to value and add it to ouput list.
        if value not in seen:           
            seen.add(value)
            output.append(value + ', 1')
        else:
            indexes = (output.index(s) for s in output if value in s)
            index = next(indexes)
            list_items = output[index].split(',')
            try:
                if len(list_items) == 3:
                    new_count = int(list_items[2]) + 1
               # elif len(list_items) == 4: # just in crazy situation where display name has comma in it 
               #     new_count = int(list_items[3]) + 1
                output[index] = f'{list_items[0]},{list_items[1]},{new_count}'
            except:
                continue
    return output    

#---------------------------------------------------------------
def Scroll_down(driver, scroll_pause_time = 0.5, number_of_scrolls = 10, estimate_scrolls_needed = 3, message = ''):
    """Scrolling down the active window in a controllable fashion.

    PASSING THE scroll_pause_time ACCORDING TO THE CONTENT OF THE PAGE, TO MAKE SURE ALL ITEMS ARE LOADED BEFORE THE NEXT SCROLL. DEFAULT IS 0.5s
    THE PAGE COULD HAVE A VERY LONG LIST, OR ALMOST INFINITY, SO BY DEFAULT WE LIMIT IT TO 10 TIMES.
    IF number_of_scrolls =  0, RETURN WITHOUT SCROLLING
    IF number_of_scrolls = -1, KEEP SCROLLING UNTIL THE END IS REACHED ...
    FOR THIS CASE, IN ORDER TO HAVE A REALISTIC PROGRESS BAR, WE WILL USE estimate_scrolls_needed  ( TOTAL REQUEST ITEMS / LOAD ITEMS PER SCROLL )
    MESSAGE IS A STRING DESCRIBED THE TITLE OF THE PROGRESS BAr. IF EMPTY IS PASSED, THE PROGRESS BAR WILL NOT BE STIMULATED
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
                update_progress(scrolls_count_for_stimulated_progressbar / estimate_scrolls_needed, message)
            # here, we dont know when it ends (for example, we ask for all notifications, but we don't know how many the 500px server will provide) 
            else:
                notifications_loaded_so_far = scrolls_count_for_stimulated_progressbar * NOTIFICATION_PER_LOAD
                text = f'\r{message} {str(notifications_loaded_so_far)}'
                sys.stdout.write(text)
                sys.stdout.flush()
        elif iteration_count > 0:
            update_progress(iteration_count / number_of_scrolls, message)

        scrolls_count_for_stimulated_progressbar += 1

        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # Wait to load page
        time.sleep(scroll_pause_time)
        innerHTML = driver.execute_script("return document.body.innerHTML") #run JS body scrip after all photos are loaded

        # exit point #1 : number of scrolls requested has been reached
        if number_of_scrolls != -1:
            iteration_count = iteration_count + 1
            if iteration_count >= number_of_scrolls:
               break

        #  exit point #2: all items are loaded- calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # mark the end of the progress bar update    
    if number_of_scrolls == -1 and estimate_scrolls_needed == -1:   # indeterminate number of scrolls
        sys.stdout.write('\r\n')                                    # end the progress update with a line-feed
        sys.stdout.flush()
    else:
        update_progress(1, message)                                 # force the display of "100% Done" 
  
    time.sleep(scroll_pause_time)

#---------------------------------------------------------------
def Scroll_to_end_by_class_name(driver, class_name, likes_count):
    """Scroll the active window to the end, where the last element of the given class name become visible.

    THE likes_count ARGUMENT IS USED FOR CREATING A REALISTIC PROGRESS BAR
    """
    eles = driver.find_elements_by_class_name(class_name)
    count = 0
    new_count = len(eles)

    while new_count != count:
        try:
            update_progress(new_count / likes_count, f' - Scrolling to load more items {new_count}/{likes_count}:')
            the_last_in_list = eles[new_count - 1]
            the_last_in_list.location_once_scrolled_into_view 
            time.sleep(3)
            #WebDriverWait(driver, 5).until(EC.visibility_of(the_last_in_list))
            count = new_count
            eles = driver.find_elements_by_class_name(class_name)
            new_count = len(eles)
        except NoSuchElementException:
            pass
    if new_count < likes_count:
        update_progress(1, ' - Scrolling to load more items:{likes_count}/{likes_count}')

#---------------------------------------------------------------
def Login(driver, user_inputs):
    """Submit given credentials to the 500px login page. """

    if len(user_inputs.password) == 0 or len(user_inputs.user_name) == 0 or driver == None: 
        return False
    time_out = 3
    driver.get("https://500px.com/login" )
    try:
        user_name_ele = WebDriverWait(driver, time_out).until(EC.presence_of_element_located((By.ID, 'email')))
        user_name_ele.send_keys(user_inputs.user_name) 
        
        pwd_ele = WebDriverWait(driver, time_out).until(EC.presence_of_element_located((By.ID, 'password')))
        pwd_ele.send_keys(user_inputs.password) 

        submit_ele = WebDriverWait(driver, time_out).until(EC.presence_of_element_located((By.CLASS_NAME, 'unified_signup__submit_button')))
        submit_ele.click()
        
        # after a sucess login, 500px will automatically load the user's homefeed page. So after submitting the credentials, we
        # wait until one of an element in the login page become unavailable
        WebDriverWait(driver, time_out).until(EC.staleness_of(user_name_ele))
       
    except  NoSuchElementException:
        printR("Error accessing the login page. Please retry")
        return False
    except TimeoutException :
        printR(f'Time out while loading {user_inputs.user_name} home page. Please retry.')
        return False
    except:
        printR(f'Error loading {user_inputs.user_name} home page. Please retry.')
        return False  
    
    # username/password errors
    if check_and_get_ele_by_class_name(driver, 'error') is not None or \
       check_and_get_ele_by_class_name(driver, 'not_found') is not None or \
       check_and_get_ele_by_class_name(driver, 'missing') is not None:   
       printR(f'Error on loggin. Please retry with valid credentials')
       user_inputs.user_name = ''
       user_inputs.password = ''
       Close_chrome_browser(driver)
       return False
    return True

#---------------------------------------------------------------
def Write_string_to_text_file(input_string, file_name, encode = ''):
    """Write the given string to a given text file. Create new file if it does not exist."""

    if encode == '':
        open_file = open(file_name, "w")
    else:
        open_file = open(file_name, "w", encoding = encode)

    open_file.write(input_string)
    open_file.close()

#--------------------------------------------------------------- 
def Show_html_result_file(file_name):
    """Offer the given html file with the default system app. """

    if not os.path.isfile(file_name):
         return

    file_path, file_extension = os.path.splitext(file_name)
    if file_extension == ".html":
        os.startfile(file_name)

#--------------------------------------------------------------- 
def Find_encoding(file_name):
    """Return the encoding of a given text file """
    import chardet
    r_file = open(file_name, 'rb').read()
    result = chardet.detect(r_file)
    charenc = result['encoding']
    return charenc 

#--------------------------------------------------------------- 
def CSV_photos_list_to_HTML(csv_file_name):
    """Create a html file from a given photos list csv  file. Save it to disk and return the file name.

    SAVE THE HTML FILE USING THE SAME NAME BUT WITH EXTENSION '.html'
    EXPECTING THE FIRST LINE TO BE THE HEADERS, WHICH ARE  No., Page, ID, Title, Link
    USE THE LINK COLUMN AS A <a> TAG WITHIN THE TITLE COLUMN 
    """
    # file name and extension check
    file_path, file_extension = os.path.splitext(csv_file_name)
    if file_extension != ".csv":
        return None
    paths = file_path.split('\\')
    file_name = paths[len(paths) - 1]
    html_file = os.path.dirname(os.path.abspath(csv_file_name))+ '\\' + file_name + '.html'
    css_head_string='	<head><style>table {border-collapse: collapse;}table, th, td {border: 1px solid black;}</style></head>'
   
    with open(csv_file_name, newline='', encoding='utf-16') as csvfile:
        reader = csv.DictReader(row.replace('\0', '') for row in csvfile)
        headers = reader.fieldnames
        row_string = '<tr>'
        # photo list headers:  No., Page, ID, Title, Link
        for header in reader.fieldnames:
            if header == 'Link': continue
            row_string += f'<th align="left">{header}</th>'
        row_string += '</tr>'
        for row in reader:
            row_string += '<tr>'
            for i in range(len(headers) -1):   #, fn in enumerate(reader.fieldnames):
                if i == 3: 
                    row_string += f'<td><a href="{row[headers[i+1]]}">{row[headers[i]]}</a></td> \n'
                else:     
                   row_string += f'<td>{row[headers[i]]}</td> \n'
            row_string += '</tr>'
        html_string = f'<html> {css_head_string} <body> <h3>{html_file}</h3> <table {row_string} </table> </body> </html>'

        #write html file 
        with open(html_file, 'wb') as htmlfile:
            htmlfile.write(html_string.encode('utf-16'))

    return html_file

#--------------------------------------------------------------- 
def CSV_to_HTML(csv_file_name, ignore_columns=[]):
    """ Read a specific type of csv file into a table, render it in a html file and write file to disk . Return the saved html filename.
    
    THE EXPECTED CSV FILES HAS THESE COMMON CHARACTERISTICS: THE FIRST THREE COLUMNS ARE ALWAYS ORDER, DISPLAY NAME AND USER NAME.
    ON THE SECOND COLUMN, WE WILL ASSIGN A WEB LINK <A> SUCH AS <A HREF="HTTPS://500PX.COM/{USER NAME}" 
    THE SAVED HTML FILE HAS THE SAME NAME BUT WITH EXTENSION '.HTML' 
    THE FIRST LINE WILL BE USED AS HEADERS, WHICH ARE  ORDER, DISPLAY NAME, USER NAME, FOLLOWERS, STATUS
                                                       OR:  ORDER, NAME, USER NAME, CONTENT, PHOTO TITLE, TIME STAMP, STATUS
                                                       OR:  ORDER, NAME, USER NAME, COUNT
    THE ARGUMENT ignore_columns IS A LIST OF THE HEADER NAMES FOR WHICH WE WANT TO HIDE THE ENTIRE COLUMN
    """
    # file name and extension check
    file_path, file_extension = os.path.splitext(csv_file_name)
    if file_extension != ".csv":
        return None
    paths = file_path.split('\\')
    file_name = paths[len(paths) - 1]
    html_file = os.path.dirname(os.path.abspath(csv_file_name))+ '\\' + file_name + '.html'
    css_head_string='	<head><style>table {border-collapse: collapse;}table, th, td {border: 1px solid black;}</style></head>'
   
    with open(csv_file_name, newline='', encoding='utf-16') as csvfile:
        reader = csv.DictReader(row.replace('\0', '') for row in csvfile)
        headers = reader.fieldnames
        row_string = '<tr>'
        
        for header in reader.fieldnames:
            if header not in ignore_columns:
                row_string += f'<th align="left">{header}</th>'
        row_string += '</tr>'
        
        for row in reader:
            row_string += '<tr>'
            for i in range(len(headers)): 
                text = row[headers[i]]
                if i != 2:                                                     # insert <a href> in the third column User Name
                    if text.find('Following') != -1: 
                        row_string += f'<td bgcolor="#00FF00">{text}</td> \n'  # green cell for following users
                    elif headers[i].find('Followers') != -1: 
                        row_string += f'<td align="right">{text}</td> \n'      # align right for number of followers        
                    else:                            
                        row_string += f'<td>{text}</td> \n'
                else:
                    row_string += f'<td><a href="https://500px.com/{text}">{text}</a></td> \n'   
        row_string += '</tr>'
        html_string = f'<html> {css_head_string} <body> <h3>{html_file}</h3> <table {row_string} </table> </body> </html>'

        #write html file 
        with open(html_file, 'wb') as htmlfile:
            htmlfile.write(html_string.encode('utf-16'))

    return html_file

#--------------------------------------------------------------- 
def Validate_non_empty_input(prompt_message, user_inputs):
    """Prompt user for an input, make sure the input is not empty. Return True if Quit or Restart is requested. False otherwise """

    val = input(prompt_message)
    if val == 'q' or val == 'r':
        user_inputs.choice = val
        return val, True
    while len(val) == 0:        
        printR("Input cannot be empty! Please re-enter. Type 'q' to end or 'r' to restart")
        val = input(prompt_message)

    return val, False

#--------------------------------------------------------------- 
def Validate_input(prompt_message, user_inputs):
    """ Prompt for input and accepts nothing but digits or letter 'r' or 'q'. Return the valid input and a boolean (True if abort is requested, False otherwise."""

    val = input(prompt_message) 
    while True:

        if val == 'r' or val == 'q':
            user_inputs.choice = val
            return val, True

        # if we have error converting inputs to integer, then the input is invalid
        try: 
            dummy_int = int(val)
            return val, False
        except ValueError:
            printR("Invalid input! Please retry.")
            val = input(prompt_message)


#--------------------------------------------------------------- 
def Get_IMG_element_from_homefeed_page(driver):
    """Get all <img> elements on page then remove elmenents that are not from user's friends.

    WE WANT TO GET THE LIST OF LOADED PHOTOS ON THE USER HOME FEED PAGE, THE ONES FROM THE PHOTOGRAPHERS THAT YOU ARE FOLLOWING.
    SINCE ALL THE CLASS NAMES IN THE USER HOMEFEED PAGE ARE POSTFIXED WITH RANDOMIZED TEXTS. 
    A WORK-AROUND SOLUTION IS TO USE THE TAG IMG AS IDENTIFIER FOR A PHOTO 
    FROM THERE WE REMOVE IMG ITEM THAT ARE EITHER AVATARS, THUMBNAILS OR RECOMMENDED PHOTOS
    """
    # we are interested in items with the tag <img>
    img_eles = check_and_get_all_elements_by_tag_name(driver, 'img') 

    # img_eles list contains other img elements that we don't want, such as thumbnails, recommended photos..., we will remove them from the list
    for ele in reversed(img_eles):
        parent_4 = check_and_get_ele_by_xpath(ele, '../../../..') 
        if parent_4 is not None and parent_4.get_attribute('class').find('Elements__HomefeedPhotoBox') == -1:
            img_eles.remove(ele)
    return img_eles

#---------------------------------------------------------------
def update_progress(progress, message = ''):
    """Updates a text-based progress bar on the console.

    ACCEPTS A FLOAT BETWEEN 0 AND 1. ANY INT WILL BE CONVERTED TO A FLOAT.
    A VALUE UNDER 0 REPRESENTS A 'HALT'.
    A VALUE AT 1 OR BIGGER REPRESENTS 100%
    """
    if message == '':
        message = 'Progress'
    barLength = 15 # Modify this to change the length of the progress bar
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
    if progress >= 1:
        progress = 1
        status = "Done\r\n"
    block = int(round(barLength*progress))
    text = f'\r{message:<46.45}[{"."*block + " "*(barLength-block)}] {int(round(progress*100)):<3}% {status}'
    sys.stdout.write(text)
    sys.stdout.flush()

#---------------------------------------------------------------
def Hide_banners(driver):
    """Hide top and bottom banners that make elements beneath them inaccessible. And click away the sign-in window if it pops up.
    
    SPECIFICALLY, TOP BANNER IS IDENTIFIED BY THE ID 'hellobar'
    AND BOTOOM BANNERS ARE IDENTIFIED BY TAG 'w-div'
    """

    top_banner = check_and_get_ele_by_id(driver, 'hellobar')
    if top_banner is not None:
        driver.execute_script("arguments[0].style.display='none'", top_banner)

    bottom_banners = check_and_get_all_elements_by_tag_name(driver, 'w-div')
    for banner in bottom_banners:
        driver.execute_script("arguments[0].style.display='none'", banner)

    join_500px_banner_close_ele = check_and_get_ele_by_class_name(driver, 'unified_signup__close')
    if join_500px_banner_close_ele is not None:
        driver.execute_script("arguments[0].click();", join_500px_banner_close_ele)

#---------------------------------------------------------------
def Show_menu(user_inputs):
    """ Display main menu. Accept these inputs from users: user name, password  and the desired option. 
    
    INPUTS ARE STORED IN THE USER_INPUTS OBJECTS, WHICH IS PASSED BY REFERENCE.  
    THE RETURN VALUE IS A STRING CONTAINING EITHER 'r', 'q' or any digit characters
    """

    printC('')
    printC('--------- Chose one of these options: ---------')
    printY('      The following options require a user name:')
    printC('   1  Get user statistics (recent activities, last upload date, registration date ...')
    printC('   2  Get user photos list ')
    printC('   3  Get followers list ')
    printC('   4  Get following list ')
    printC('   5  Get a list of users who liked a given photo')
    printC('')
    printY('      The following options require user login:')
    printC('   6  Get n last notifications (max 5000) and the unique users on it')
    printC('   7  Check if a user is following you')
    printC('')
    printC('   8  Like n photos from a given user')
    printC('   9  Like n photos, starting at a given index, on various photo pages') 
    printC('  10  Like n photos of each user who likes a given photo or yours')
    printC('  11  Like n photos from your home-feed page, excluding recommended photos ')
    printC('  12  Like n photos of each users in your last m notifications')
    printC('')
    printY('      The following option does not need credentials:')
    printC('  13  Play slideshow on a given gallery')
    #printC(' 14  Get following statuses of users that you are following')
    printC('')
    printC('   r  Restart with different user')
    printC('   q  Quit')
    printC('')
    sel, abort = Validate_input('Enter your selection >', user_inputs)

    if abort:
        return 

    sel = int(sel)
    # play slideshow, no credentials needed
    if sel == 13:
        user_inputs.choice = str(sel)
        return 
    
    # user name is mandatory
    if user_inputs.user_name == '':
        user_inputs.user_name = input('Enter 500px user name >')
    printG(f'Current user: {user_inputs.user_name}')

    # password is optional
    if sel == 3 and user_inputs.password == '':
        expecting_password = input('If you also want to obtain your following status to each of your followers,\ntype in password to login now,\nor just press ENTER to ignore this: >')
        if expecting_password == 'q' or expecting_password == 'r':
            user_inputs.choice = sel
            return 
        else:
            user_inputs.password =expecting_password
   
    if sel < 6 or sel == 7 or sel == 15:
        user_inputs.choice = str(sel)
        return
    
    # password is mandatory ( quit or restart are also possible at this step )
    if sel >= 6 and sel <= 15:
        if user_inputs.user_name == '':
            user_inputs.user_name, abort = Validate_non_empty_input('Enter 500px user name >', user_inputs)
            if abort:
                return

        if user_inputs.password == '':
            user_inputs.password, abort =  Validate_non_empty_input('Enter password >', user_inputs)
            if abort:
                return
    
    user_inputs.choice = str(sel)        

#---------------------------------------------------------------
def Show_galllery_selection_menu(user_inputs):
    """ Menu to select a photo gallery for slideshow. Allow the user to abort during the input reception.
        Return three values: the photo href, the gallery name, and a boolean of True if an abort is requested, False otherwise. """

    printC('--------- Select the desired photos gallery: ---------')
    printC('    1  Popular')
    printC('    2  Popular-Undiscovered photographers')
    printC('    3  Upcoming')
    printC('    4  Fresh')
    printC("    5  Editor's Choice")
    printC("    6  User-specified gallery")
    # option to play slideshow on user's photos if a user name was provided 
    if user_inputs.choice == '13' and  user_inputs.user_name is not None: 
        printC("    7  My photos")

    printC('')
    printY('    r  Restart for different user')
    printY('    q  Quit')

    sel = input('Enter your selection >')
    # exit the program
    if sel == 'q' or sel == 'r':
        user_inputs.choice = sel
        return sel, '', True

    elif sel == '1': return 'https://500px.com/popular'                       , 'Popular', False
    elif sel == '2': return 'https://500px.com/popular?followers=undiscovered', 'Popular, Undiscovered', False
    elif sel == '3': return 'https://500px.com/upcoming'                      , 'Upcoming', False
    elif sel == '4': return 'https://500px.com/fresh'                         , 'Fresh', False
    elif sel == '5': return 'https://500px.com/editors'                       , "Editor's Choice", False
    elif sel == '6': 
        input_val, abort = Validate_non_empty_input('Enter the link to your desired photo gallery. It could be a public  \
                    gallery with filters, or a private gallery >', user_inputs), 
        if abort:
            return '', '', True
        else:
            return input_val, 'User-specified gallery', False

    elif sel == '7': return f'https://500px.com/{user_inputs.user_name}'                  , 'My photos', False

    else:
        Show_galllery_selection_menu(user_inputs)
#---------------------------------------------------------------
def Define_and_read_arguments(): 
    """ Define all optional user inputs and their default values. Then fill in with the actual values from command lines.
        Return a user_inputs objects filled with given arguments. 

    ALL ARGUMENTS ARE OPTIONAL (AS OPPOSED TO POSTIONAL).  IF OPTION --choice IS NOT SET, ALL OTHER ARGUMENTS WILL BE IGNORED WHETHER THEY ARE SET OR NOT.
        IN THAT CASE, THE ATTRIBUTE "USE_COMMAND_LINE_ARGS" WILL BE SET TO FALSE 
    """
    user_inputs = User_inputs()
    #define arguments and their default values
    ap = argparse.ArgumentParser()
    ap.add_argument("-c",  "--choice",                      required=False,           nargs='?', const=1, default='0', help="User selection(1-14)") #to set default value, add:  nargs='?', const=1, default=0
    ap.add_argument("-u",  "--user_name",                   required=False,           nargs='?', const=1, default='',  help="500px user name")
    ap.add_argument("-d",  "--password",                    required=False,           nargs='?', const=1, default='',  help="Password for current user")
    ap.add_argument("-p",  "--photo_href",                  required=False,           nargs='?', const=1, default='',  help="")
    ap.add_argument("-g",  "--gallery_href",                required=False,           nargs='?', const=1, default='',  help="")
    ap.add_argument("-l",  "--number_of_photos_to_be_liked",required=False, type=int, nargs='?', const=1, default=1,   help="")
    ap.add_argument("-i",  "--index_of_start_photo",        required=False, type=int, nargs='?', const=1, default=1,   help="")
    ap.add_argument("-n",  "--number_of_notifications",     required=False, type=int, nargs='?', const=1, default=200, help="")
    ap.add_argument("-a",  "--target_user_name",            required=False,           nargs='?', const=1, default='',  help="")
    ap.add_argument("-t",  "--time_interval",               required=False, type=int, nargs='?', const=1, default=4,   help="")   

      # read actual command line arguments
    args_dict= vars(ap.parse_args())
    for dict_name in args_dict:
        if DEBUG:
            print(f'{dict_name}: {args_dict[dict_name]}')
        setattr(user_inputs, dict_name, args_dict[dict_name])
    # if a choice is provided from the command line, we will switch to command line mode. 
    if user_inputs.choice != '0':
        user_inputs.use_command_line_args = True
    return user_inputs
#---------------------------------------------------------------
def Get_additional_user_inputs(user_inputs):
    """ Ask the user for additional inputs based on the option previously selected in user_inputs.choice.  

    ALLOW THE USER TO ABORT (QUIT OR RESTART) ANYTIME DURING THE INPUT RECEPTION. RETURN FALSE IF ABORTING, TRUE OTHERWISE    
    """

    if user_inputs.choice == 'q' or user_inputs.choice == 'r':
        return False

    # no additional input are required for options from 1 to 5
    choice = int(user_inputs.choice)
    if choice < 5:
        return True
 
    # 5. Get a list of users who liked a given photo: photo_href
    if choice == 5: 
        user_inputs.photo_href, abort = Validate_non_empty_input('Enter your photo href >', user_inputs)
        if abort:
            return False

    # 6. Get n last notifications (max 5000) and the unique users on it: number_of_notifications 
    if choice == 6 : 
        input_val, abort =  Validate_input(f'Enter the number of notifications you want to retrieve(max {MAX_NOTIFICATION_REQUEST}) >', user_inputs)
        if abort: 
            return False
        else:
            num = int(input_val)
            user_inputs.number_of_notifications = num if num < MAX_NOTIFICATION_REQUEST else MAX_NOTIFICATION_REQUEST
  
    # 7. Check if a user is following you : target user name
    elif choice == 7:
        user_inputs.target_user_name , abort =  Validate_non_empty_input('Enter target user name >', user_inputs)
        if abort:
            return False  

    # common input for 8 to 11: number of photo to be auto-liked
    elif choice >= 8 and choice <= 11:
        input_val, abort =  Validate_input('Enter the number of photos you want to auto-like >', user_inputs)
        if abort:
            return False
        else: 
            num = int(input_val)
            user_inputs.number_of_photos_to_be_liked = num if num < MAX_AUTO_LIKE_REQUEST else MAX_AUTO_LIKE_REQUEST         

        # 8.  Like n photos from a given user: target_user_name
        if choice == 8: 
            user_inputs.target_user_name, abort = Validate_non_empty_input('Enter target user name >', user_inputs)
            if abort:
                return False  

        # 9.  Like n photos, starting at a given index, on various photo pages:  gallery_href, index_of_start_photo
        elif choice == 9:  
            # gallery selection
            user_inputs.gallery_href, user_inputs.gallery_name, abort = Show_galllery_selection_menu(user_inputs)
            if abort:
                return False
            
            input_val, abort =  Validate_input('Enter the index of the start photo (1-500) >', user_inputs)
            if abort:
                return False  
            else: 
                user_inputs.index_of_start_photo = int(input_val)

        # 10.  Like n photos of each user who likes a given photo or yours: photo_href
        elif choice == 10: 
            user_inputs.photo_href, abort =  Validate_non_empty_input('Enter your photo href >', user_inputs)
            if abort: 
                return False             
    
    # 12. Like n photos of each users in your last m notifications         
    elif choice == 12: 
        input_val, abort =  Validate_input(f'Enter the number of notifications you want to process(max {MAX_NOTIFICATION_REQUEST}) >', user_inputs)
        if abort: 
            return False
        else: 
            num = int(input_val)
            user_inputs.number_of_notifications = num if num < MAX_NOTIFICATION_REQUEST else MAX_NOTIFICATION_REQUEST

        input_val, abort =  Validate_input('Enter the number of photos you want to auto-like for each user >', user_inputs)
        if abort:
            return False
        else: 
            num = int(input_val)
            user_inputs.number_of_photos_to_be_liked = num if num < MAX_AUTO_LIKE_REQUEST else MAX_AUTO_LIKE_REQUEST

    # 13.  Play slideshow on a given gallery 
    elif choice == 13:
        user_inputs.gallery_href, user_inputs.gallery_name, abort = Show_galllery_selection_menu(user_inputs)
        if abort:
            return False

        # allow a login for showing NSFW contents
        if user_inputs.user_name == '':
            printY('If you want to show NSFW contents, you need to login.\n Type your user name now or just press ENTER to ignore')
            user_inputs.user_name = input('>')
            if user_inputs.user_name == 'q' or user_inputs.user_name == 'r':
                user_inputs.choice = user_inputs.user_name
                return False               

        if user_inputs.user_name is not '' and user_inputs.password is '':
            printY('Type your password:')           
            user_inputs.password, abort = Validate_non_empty_input('> ', user_inputs)
            if abort:
                return False    

        input_val, abort = Validate_input('Enter the interval time between photos, in second>', user_inputs)
        if abort:
            return False
        else:
            user_inputs.time_interval = int(input_val)

            printY(f'Slideshow {user_inputs.gallery_name} will play in fullscreen, covering this control window.\n To stop the slideshow before it ends, and return to this window, press ESC three times.\n Now press ENTER to start >')
            wait_for_enter_key = input() 
        
  # 14. (in progress) Get following statuses of users you are following ( user_name, start index, number_of_users)
    elif choice == 14:
        input_val, abort =  Validate_non_empty_input('Enter the number of users >', user_inputs)
        if abort:
            return False  
        else: 
            user_inputs.number_of_users = int(input_val)
  
        input_val, abort =  Validate_non_empty_input('Enter the start index >' , user_inputs)
        if abort:
            return False  
        else: 
            user_inputs.index_of_start_user = int(input_val)

#---------------------------------------------------------------
def Handle_option_1(user_inputs, output_lists):
    """ Get user status."""

    time_start = datetime.datetime.now().replace(microsecond=0)
    date_string = time_start.strftime("%Y_%m_%d")

    driver = Start_chrome_browser()
    json_data, stats = Get_stats(driver, user_inputs, output_lists) 
    if json_data is None or len(json_data) == 0:
        printR(f'Error reading {user_inputs.user_name}\'s page. Please make sure a valid user name is used')
        if user_inputs.use_command_line_args == False:
            Show_menu(user_inputs)


    print(f"Getting user's statistics ...")
    html_file =  os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_stats_{date_string}.html')
    Write_string_to_text_file(Create_user_statistics_html(stats), html_file)
    Close_chrome_browser(driver)
    Show_html_result_file(html_file)

    # print summary report
    time_duration = (datetime.datetime.now().replace(microsecond=0) - time_start)
    print(f'The process took {time_duration} seconds') 

#---------------------------------------------------------------
def Handle_option_2(user_inputs, output_lists):
    """ Get user photos """

    time_start = datetime.datetime.now().replace(microsecond=0)
    date_string = time_start.strftime("%Y_%m_%d")

    csv_file = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_photos_{date_string}.csv')
    html_file = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_photos_{date_string}.html')
    
    # avoid to do the same thing twice: if list (in memory) has items AND output file exists on disk
    if output_lists.photos is not None and len(output_lists.photos) > 0 and os.path.isfile(html_file):
        printY(f'Results exists in memory and on disk. Showing the existing file at:\n{os.path.abspath(html_file)} ...')
        Show_html_result_file(html_file) 
        return

    driver = Start_chrome_browser()
    print(f"Getting {user_inputs.user_name}'s photos list ...")
    output_lists.photos = Get_photos_list(driver, user_inputs)
    Close_chrome_browser(driver)
    if output_lists.photos is None: 
        Show_menu(user_inputs)
        return
            
    if Write_photos_list_to_csv(user_inputs.user_name, output_lists.photos, csv_file) == True:
        Show_html_result_file(CSV_photos_list_to_HTML(csv_file)) 

    # print summary report
    time_duration = (datetime.datetime.now().replace(microsecond=0) - time_start)
    print(f'The process took {time_duration} seconds')
#---------------------------------------------------------------
def Handle_option_3(user_inputs, output_lists):
    """ Get followers"""
    
    time_start = datetime.datetime.now().replace(microsecond=0)
    date_string = time_start.strftime("%Y_%m_%d")

    # avoid to do the same thing twice: when the list (in memory) has items and output file exists on disk
    if output_lists.followers_list is not None and len(output_lists.followers_list) > 0:
        html_file = f'{user_inputs.user_name}_{len(output_lists.followers_list)}_followers_{date_string}.html'
        if os.path.isfile(html_file):
            printY(f'Results exists in memory and on disk. Showing the existing file at:\n{os.path.abspath(html_file)} ...')
            Show_html_result_file(html_file) 
            return
  
    driver = Start_chrome_browser()
    # if user provided password then login
    if user_inputs.password != '':
        if Login(driver, user_inputs) == False :
            return
    Hide_banners(driver)
    print(f"Getting the list of users who follow {user_inputs.user_name} ...")
    output_lists.followers_list = Get_followers_list(driver, user_inputs)
    Close_chrome_browser(driver)
    if output_lists.followers_list is not None and len(output_lists.followers_list) > 0:
        csv_file = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_{len(output_lists.followers_list)}_followers_{date_string}.csv')           
        if Write_users_list_to_csv(output_lists.followers_list, csv_file) == True:
            # show output and print summary report
            Show_html_result_file(CSV_to_HTML(csv_file)) 
            time_duration = (datetime.datetime.now().replace(microsecond=0) - time_start)
            print(f'The process took {time_duration} seconds') 
        else:
            printR(f'Error writing the output file\n:{csv_file}')
#---------------------------------------------------------------
def Handle_option_4(user_inputs, output_lists):
    """ Get followings (friends)"""
    
    time_start = datetime.datetime.now().replace(microsecond=0)
    date_string = time_start.strftime("%Y_%m_%d")

    # avoid to do the same thing twice: when the list (in memory) has items and output file exists on disk
    if output_lists.followings_list is not None and len(output_lists.followings_list) > 0:
        html_file = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_{len(output_lists.followings_list)}_followings_{date_string}.html')
        if os.path.isfile(html_file):
            printY(f'Results exists in memory and on disk. Showing the existing file at:\n{os.path.abspath(html_file)} ...')
            Show_html_result_file(html_file) 
            return

    driver = Start_chrome_browser()
    print(f"Getting the list of users that you are following ...")
    output_lists.followings_list = Get_followings_list(driver, user_inputs)
    Close_chrome_browser(driver)
    if len(output_lists.followings_list) > 0:
        csv_file = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_{len(output_lists.followings_list)}_followings_{date_string}.csv')
        if Write_users_list_to_csv(output_lists.followings_list, csv_file) == True:
            # show output and print summary report
            Show_html_result_file(CSV_to_HTML(csv_file, ['Status'])) #ignore column 'Status'
            time_duration = (datetime.datetime.now().replace(microsecond=0) - time_start)
            print(f'The process took {time_duration} seconds') 
        else:
            printR(f'Error writing the output file\n:{csv_file}')

#---------------------------------------------------------------
def Handle_option_5(user_inputs, output_lists):
    """ Get a list of users who liked a given photo."""
    
    time_start = datetime.datetime.now().replace(microsecond=0) 
    driver = Start_chrome_browser()      
    try:
        driver.get(user_inputs.photo_href)
    except:
        printR(f'Invalid href: {user_inputs.photo_href}. Please retry.')
        Close_chrome_browser(driver)
        Show_menu(user_inputs)        
        return

    time.sleep(1)
    Hide_banners(driver)
    print(f"Getting the list of unique users who liked the given photo ...")
    output_lists.like_actioners_list, csv_file = Get_like_actioners_list(driver, output_lists)
    Close_chrome_browser(driver)
    if output_lists.like_actioners_list is not None and \
       len(output_lists.like_actioners_list) > 0 and \
       Write_users_list_to_csv(output_lists.like_actioners_list, csv_file) == True:
        Show_html_result_file(CSV_to_HTML(csv_file, ['Status'])) 
    # print summary report
    time_duration = (datetime.datetime.now().replace(microsecond=0) - time_start)
    print(f'The process took {time_duration} seconds') 
#---------------------------------------------------------------
def Handle_option_6(user_inputs, output_lists):
    """ Get n last notifications details (max 5000). Show the detail list and the list of the unique users on it"""

    time_start = datetime.datetime.now().replace(microsecond=0)
    date_string = time_start.strftime("%Y_%m_%d")
    csv_file = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_{user_inputs.number_of_notifications}_notifications_{date_string}.csv')
    html_file = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_{user_inputs.number_of_notifications}_notifications_{date_string}.html')

    # avoid to do the same thing twice: when the list (in memory) has items and output file exists on disk
    if output_lists.notifications is not None and len(output_lists.notifications) > 0 and os.path.isfile(html_file):
        printY(f'Results exists in memory and on disk. Showing the existing file at:\n{os.path.abspath(html_file)} ...')        
        Show_html_result_file(html_file)
        return

    driver = Start_chrome_browser()
    if Login(driver, user_inputs) == False :
        return
    driver.get('https://500px.com/notifications')
    time.sleep(1)
  
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # abort the action if the target objects failed to load within a timeout of 15s        
    if not Finish_Javascript_rendered_body_content(driver, time_out=15, class_name_to_check='finished')[0]:
        return None, None	

    Hide_banners(driver)        
    print(f"Getting the last {user_inputs.number_of_notifications} notifications and the unique users in that list ...")

    output_lists.notifications, output_lists.unique_notificators = Get_notification_list(driver, user_inputs, True)
        
    if len(output_lists.notifications) == 0 and len(output_lists.unique_notificators) == 0:
        Show_menu(user_inputs)
        Close_chrome_browser(driver)
        return

    Close_chrome_browser(driver)
    
    # Write the list of unique users to csv and html files. Display html file on the browser 
    csv_file_2  = os.path.join(output_lists.output_dir, \
        f"{user_inputs.user_name}_{len(output_lists.unique_notificators)}_unique_users_in_last_{user_inputs.number_of_notifications}_notifications_{date_string}.csv")
    if len(output_lists.unique_notificators) > 0 and  Write_unique_notificators_list_to_csv(output_lists.unique_notificators, csv_file_2) == True:
        Show_html_result_file(CSV_to_HTML(csv_file_2))     
    
    # Write the notification list to csv and html files. Display html file on the browser         
    if len(output_lists.notifications) > 0 and  Write_notifications_to_csvfile(output_lists.notifications, csv_file) == True:
        Show_html_result_file(CSV_to_HTML(csv_file)) 

    # print summary report
    time_duration = (datetime.datetime.now().replace(microsecond=0) - time_start)
    print(f'The process took {time_duration} seconds') 
#---------------------------------------------------------------
def Handle_option_7(user_inputs, output_lists):
    """Check if a user is following you."""

    time_start = datetime.datetime.now().replace(microsecond=0)
    driver = Start_chrome_browser()
    print(f"Check if the user {user_inputs.target_user_name} follows {user_inputs.user_name} ...")
    result, detail_message = Does_this_user_follow_me(driver, user_inputs)
    if result == True:
        printG(f"User {user_inputs.target_user_name} follows {user_inputs.user_name} {detail_message} ")
    else:
        printY(f"User {user_inputs.target_user_name} does not follow {user_inputs.user_name}")
        
    Close_chrome_browser(driver)

    # print summary report
    time_duration = (datetime.datetime.now().replace(microsecond=0) - time_start)
    print(f'The process took {time_duration} seconds') 
#---------------------------------------------------------------
def Handle_option_8(user_inputs, output_lists):
    """ Like n photos from a given user."""

    time_start = datetime.datetime.now().replace(microsecond=0)
    driver = Start_chrome_browser()
    if Login(driver, user_inputs) == False :
        return
    if user_inputs.number_of_photos_to_be_liked == 1:
        print(f"Starting auto-like {user_inputs.number_of_photos_to_be_liked} photo of user {user_inputs.target_user_name} ...")
    else:
        print(f"Starting auto-like {user_inputs.number_of_photos_to_be_liked} photos of user {user_inputs.target_user_name} ...")
    Like_n_photos_from_user(driver, user_inputs.target_user_name, user_inputs.number_of_photos_to_be_liked, include_already_liked_photo_in_count=True, close_browser_on_error = False)
    Close_chrome_browser(driver)

    # print summary report
    time_duration = (datetime.datetime.now().replace(microsecond=0) - time_start)
    print(f'The process took {time_duration} seconds') 
#---------------------------------------------------------------
def Handle_option_9(user_inputs, output_lists):
    """Like n photos, starting at a given index, on various photo pages ."""

    time_start = datetime.datetime.now().replace(microsecond=0)
    driver = Start_chrome_browser()
    if Login(driver, user_inputs) == False :
        return
    driver.get(user_inputs.gallery_href)
    time.sleep(3)
    # abort the action if the target objects failed to load within a timeout of 15s    
    #if not Finish_Javascript_rendered_body_content(driver, time_out=15, class_name_to_check = 'entry-visible')[0]:
    #    return None, None	
    innerHtml = driver.execute_script("return document.body.innerHTML")  
    time.sleep(3)

    Hide_banners(driver)
    if user_inputs.number_of_photos_to_be_liked == 1:
        print(f"Starting auto-like {user_inputs.number_of_photos_to_be_liked} photo from {user_inputs.gallery_name} gallery, start index {user_inputs.index_of_start_photo}  ...")
    else:
        print(f"Starting auto-like {user_inputs.number_of_photos_to_be_liked} photos from {user_inputs.gallery_name} gallery, start index {user_inputs.index_of_start_photo} ...")

    Like_n_photos_on_current_page(driver, user_inputs.number_of_photos_to_be_liked, user_inputs.index_of_start_photo)
    Close_chrome_browser(driver)

    # print summary report
    time_duration = (datetime.datetime.now().replace(microsecond=0) - time_start)
    print(f'The process took {time_duration} seconds') 
#---------------------------------------------------------------
def Handle_option_10(user_inputs, output_lists):
    """Like n photos of each user who likes a given photo or yours."""

    time_start = datetime.datetime.now().replace(microsecond=0)
    driver = Start_chrome_browser()
    if Login(driver, user_inputs) == False :
        return
    try:
        driver.get(user_inputs.photo_href)
    except:
        printR(f'Invalid href: {user_inputs.photo_href}. Please retry.')
        Close_chrome_browser(driver)
        Show_menu(user_inputs)         
        return

    time.sleep(1)
    Hide_banners(driver)        
    print(f'Getting the list of users who liked this photo ...')
    output_lists.like_actioners_list, dummy_file_name = Get_like_actioners_list(driver, output_lists)
    if len(output_lists.like_actioners_list) == 0: 
        printG(f'The photo {photo_tilte} has no affection yet')
        Show_menu(user_inputs)
        return 
    actioners_count = len(output_lists.like_actioners_list)
    print(f"Starting auto-like {user_inputs.number_of_photos_to_be_liked} photos of each of {actioners_count} users on the list ...")
    include_already_liked_photo_in_count = True  # meaning: if you want to autolike 3 first photos, and you found out two of them are already liked, then you need to like just one photo.
                                                    # if this is set to False, then you will find 3 available photos and Like them 
    for i, actor in enumerate(output_lists.like_actioners_list):
        print(f'User {str(i+1)}/{actioners_count}: {actor.display_name}, {actor.user_name}')
        if Like_n_photos_from_user(driver, actor.user_name, user_inputs.number_of_photos_to_be_liked, include_already_liked_photo_in_count, close_browser_on_error=False) == False:
            continue
    Close_chrome_browser(driver)

    # print summary report
    time_duration = (datetime.datetime.now().replace(microsecond=0) - time_start)
    print(f'The process took {time_duration} seconds') 
#---------------------------------------------------------------
def Handle_option_11(user_inputs, output_lists):
    """Like n friend's photos in homefeed page."""
    
    time_start = datetime.datetime.now().replace(microsecond=0)
    driver = Start_chrome_browser()
    if Login(driver, user_inputs) == False :
        return

    # after a success login, the user's the homefeed page will automatically open
     
    Hide_banners(driver) 
    print(f"Like {user_inputs.number_of_photos_to_be_liked} photos from the {user_inputs.user_name}'s home feed page ...")
    Like_n_photos_on_homefeed_page(driver, user_inputs)     
    Close_chrome_browser(driver)

    # print summary report
    time_duration = (datetime.datetime.now().replace(microsecond=0) - time_start)
    print(f'The process took {time_duration} seconds') 
#---------------------------------------------------------------
def Handle_option_12(user_inputs, output_lists):
    """Like n photos of each user in the last m notifications.  """

    time_start = datetime.datetime.now().replace(microsecond=0)
    driver = Start_chrome_browser()
    print(f'Getting the list of unique users in the last {user_inputs.number_of_notifications} notifications ...')
    if Login(driver, user_inputs) == False :
        return
    driver.get('https://500px.com/notifications')
    time.sleep(1)        
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    
    # abort the action if the target objects failed to load within a timeout of 15s    
    if not Finish_Javascript_rendered_body_content(driver, time_out=15, class_name_to_check='finished')[0]:
      return None, None	

    Hide_banners(driver)  
        
    output_lists.unique_notificators = Get_notification_list(driver, user_inputs, True)[1]
    #if len(output_lists.unique_notificators) == 0:
        #   break 
        

    users_count = len(output_lists.unique_notificators)
    print(f"Starting auto-like {user_inputs.number_of_photos_to_be_liked} photos of each of {users_count} users on the list ...")
    for i, item in enumerate(output_lists.unique_notificators):
        name_pair = item.split(',')
        if len(name_pair) > 2: 
            print(f' User {name_pair[0]}/{users_count}: {name_pair[1]}, {name_pair[2]}')
            if Like_n_photos_from_user(driver, name_pair[2], user_inputs.number_of_photos_to_be_liked, include_already_liked_photo_in_count=True, close_browser_on_error=False) == False:
                continue
        else:
            continue
    Close_chrome_browser(driver)

    # print summary report
    time_duration = (datetime.datetime.now().replace(microsecond=0) - time_start)
    print(f'The process took {time_duration} seconds') 
#---------------------------------------------------------------
def Handle_option_13(user_inputs, output_lists):
    """ Play slideshow on a given gallery. """

    time_start = datetime.datetime.now().replace(microsecond=0)
    driver = Start_chrome_browser(["--kiosk", "--hide-scrollbars", "--disable-infobars"])
    #driver = Start_chrome_browser(["--hide-scrollbars", "--disable-infobars"])
    #driver.maximize_window()
    driver.get(user_inputs.gallery_href)
    driver.execute_script("return document.body.innerHTML")
    Hide_banners(driver)
    Play_slideshow(driver, int(user_inputs.time_interval))
    Close_chrome_browser(driver)
    # print summary report
    time_duration = (datetime.datetime.now().replace(microsecond=0) - time_start)
    print(f'The process took {time_duration} seconds') 
#---------------------------------------------------------------
def Handle_option_14(user_inputs, output_lists):
    """Get following statuses of users that you are following."""

    time_start = datetime.datetime.now().replace(microsecond=0)
    driver = Start_chrome_browser()
    print(f"Get the following statuses of the users that {user_inputs.user_name} is following ...")
    Get_following_statuses(driver, user_inputs, user_inputs.index_of_start_user, user_inputs.number_of_users,  output_lists.followings_list )
    Close_chrome_browser(driver)

    # print summary report
    time_duration = (datetime.datetime.now().replace(microsecond=0) - time_start)
    print(f'The process took {time_duration} seconds') 
    #---------------------------------------------------------------

def main():

    os.system('color')
    driver = None

    output_lists = Output_data()
    user_inputs = Define_and_read_arguments()
    
    if  user_inputs.use_command_line_args == False:
        Show_menu(user_inputs)
 
    # declare a dictionary so that functions can be refered as string from "1" to "14"
    Functions_dictionary = {   
            "1" : Handle_option_1, 
            "2" : Handle_option_2, 
            "3" : Handle_option_3,
            "4" : Handle_option_4, 
            "5" : Handle_option_5, 
            "6" : Handle_option_6, 
            "7" : Handle_option_7, 
            "8" : Handle_option_8, 
            "9" : Handle_option_9, 
            "10": Handle_option_10, 
            "11": Handle_option_11,
            "12": Handle_option_12, 
            "13": Handle_option_13,  
            "14": Handle_option_14 }

  
    while user_inputs.choice != 'q':
        #restart for different user
        if user_inputs.choice == 'r': 
            user_inputs.Reset()
            output_lists.Reset()
            Show_menu(user_inputs)
            continue
        else:
        # add user to enter additional inputs according to the selected options
            if not user_inputs.use_command_line_args and int(user_inputs.choice) >= 5:
                if Get_additional_user_inputs(user_inputs) == False:
                    continue
            # dynamically call the function to perform the task 
            Functions_dictionary[user_inputs.choice](user_inputs, output_lists)

        # after finishing a task, if we are in the command-line mode, we are done, since the specific task has finished 
        if  user_inputs.use_command_line_args:
            sys.exit()
             
        # if not, show the menu for another task selection  
        else:
            input("Press ENTER to continue")
            Show_menu(user_inputs)
            continue
    
    sys.exit()


#---------------------------------------------------------------
if __name__== "__main__":
  main()



