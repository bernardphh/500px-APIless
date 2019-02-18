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
#not use yet
#from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
#from selenium.webdriver.chrome import service
#import pychromecast
#import logging
#import getpass 

from lxml import html
import os, sys, time, re, math, csv, json,codecs
from time import sleep
from enum import Enum

PHOTOS_PER_PAGE = 50            # 500px currently loads 50 photos per page
LOADED_ITEM_PER_PAGE = 50       # it also loads 50 followers, or friends, at a time in the popup window
NOTIFICATION_PER_LOAD = 20      # currently notifications are requested to display ( by scrolling the window) 20 items at a time
MAX_NOTIFICATION_REQUEST = 1000 # self limitation to avoid abusing
MAX_AUTO_LIKE_REQUEST = 100     # self limitation to avoid abusing
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
    def write_to_textfile():
        print(self.order + "\n" + self.display_name + "\n" + self.username + "\n" + self.content + "\n" + self.photo_link + "\n" + self.photo_title + "\n" + self.timestamp +  "\n" + self.status )

class notificator:
    """ Represent a user, with display name and user name, who generated a notification. """
    def __init__(self, display_name, username):
        self.display_name = display_name
        self.username = username   
    def print_screen(self):
        print(self.display_name + "\n" + self.username + "\n" )   
    def write_to_textfile():
        print(self.display_name + "\n" + self.username + "\n")
class user_stats:
    """ Represent basic statistics of a user. """
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
class Output_file_type(Enum):
   """ Enum representing 4 types of output list"""
   USERS_LIST = 0
   PHOTOS_LIST = 1
   NOTIFICATIONS_LIST = 2
   STATISTICS_HTML_FILE = 3

#global
json_data = []
photos = []
notifications = []
unique_notificators = []
followers_list = []
followings_list = []
like_actioners_list= []

stats = user_stats() 
user_name = ''
user_id = ''
password = ''
target_user_name = ''
number_of_photos_to_be_liked = 2 
index_of_start_photo = 0
number_of_notifications = 200
like_actioners_file_name = 'dummy'

# print colors text
def printR(text): print(f"\033[91m {text}\033[00m") #; logging.info(text)
def printG(text): print(f"\033[92m {text}\033[00m") #; logging.info(text)
def printY(text): print(f"\033[93m {text}\033[00m") #; logging.info(text)
def printC(text): print(f"\033[96m {text}\033[00m") #; logging.info(text) 
def printB(text): print(f"\033[94m {text}\033[00m") #; logging.info(text) 

#---------------------------------------------------------------
def Start_chrome_browser(options_list = []):
    """ use selenium webdriver to start chrome, with various options. Ex ["--start-maximized", "--log-level=3"] """
    global driver
    chrome_options = Options()
 
    for option in options_list:
        chrome_options.add_argument(option)
    
    chrome_options.add_argument('--log-level=3') 
    
    # atempt to suppress the ChromeDriver log to the console
    #service = service.Service(chrome_exe_path = r'C:\Windows\System32')
    #service.SuppressInitialDiagnosticInformation = True;
    #driver = webdriver.Remote(service.service_url,   desired_capabilities=chrome_options.to_capabilities())

    #caps = DesiredCapabilities.CHROME
    #caps['loggingPrefs'] = {'performance': 'ALL'} #, 'bufferUsageReportingInterval': '10000'
    #driver = webdriver.Chrome(options=chrome_options, desired_capabilities=caps)    
   
    driver = webdriver.Chrome(options=chrome_options)

    #customize zoom %
    #driver.get('chrome://settings/')
    #driver.execute_script('chrome.settingsPrivate.setDefaultZoom(.80);')
    #specify window size
    #driver.set_window_size(400, 600)
    #driver.maximize_window()
    printY('DO NOT INTERACT WITH THE CHROME BROWSER. WHEN YOUR REQUEST FINISHES, IT WILL BE CLOSED')

#---------------------------------------------------------------
def Close_chrome_browser():
    """ Close the chrome browser, care-free of exceptions. """
    if driver is None:
        return
    try:
        driver.close()
    except WebDriverException:
        pass

#---------------------------------------------------------------
def Create_user_statistics_html(stats):
    """ write user statistic object stats to an html file. """
    output = f'''
<html>\n\t<body>
        <h3>User statistics</h3>
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

def Write_photos_list_to_csv(list_of_photos, csv_file_name):
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
            Write_photos_list_to_csv(list_of_photos, csv_file_name)
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
            writer = csv.DictWriter(csv_file, fieldnames = ['Order', 'Display Name', 'User Name'])  
            writer.writeheader()

            for actor in unique_notifications_list:
                items = actor.split(',')
                if len(items) == 3:
                    writer.writerow({'Order' : items[0], 'Display Name' : items[1], 'User Name': items[2]}) 
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
def Hover_element_by_its_xpath(xpath):
    """ hover the mouse on an element specified by the given xpath. """
    element = driver.find_element_by_xpath(xpath)
    hov = ActionChains(driver).move_to_element (element)
    hov.perform()

#---------------------------------------------------------------
def Hover_by_element(element):
    """ Hover the mouse over a given element. """               
    #element.location_once_scrolled_into_view
    hov = ActionChains(driver).move_to_element (element)
    hov.perform()

#---------------------------------------------------------------
def Get_element_text_by_xpath(page, xpath_string):
    """Return the text of element, specified by the element xpath. Return '' if element not found. """
    ele = page.xpath(xpath_string)
    if len(ele) > 0 : return ele[0].text
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
    return web_ele

#---------------------------------------------------------------
def check_and_get_ele_by_class_name(element, class_name):
    """Find the web element of a given class name, return none if not found.
    
    THE SEARCH CAN BE LIMITED WITHIN A GIVEN WEB ELEMENT, OR THE WHOLE DOCUMENT, BY PASSING THE BROWSER DRIVER
    """
    try:
        return element.find_element_by_class_name(class_name) 
    except NoSuchElementException:
        return None
    return web_ele
#---------------------------------------------------------------
def check_and_get_ele_by_id(element, id_name):
    """Find the web element of a given id, return none if not found.

    THE SEARCH CAN BE LIMITED WITHIN A GIVEN WEB ELEMENT, OR THE WHOLE DOCUMENT, BY PASSING THE BROWSER DRIVER
    """
    try:
        return element.find_element_by_id(id_name) 
    except NoSuchElementException:
        return None
    return web_ele
#---------------------------------------------------------------
def check_and_get_ele_by_tag_name(element, tag_name):
    """Find the web element of a given class name, return none if not found.

    THE SEARCH CAN BE LIMITED WITHIN A GIVEN WEB ELEMENT,  OR ON THE WHOLE DOCUMENT IF THE BROWSER DRIVER IS PASSED
    """
    try:
        return element.find_element_by_tag_name(tag_name) 
    except NoSuchElementException:
        return None
    return web_ele
#---------------------------------------------------------------
def check_and_get_all_eles_by_class_name(element, class_name):
    """Find all the web elements of a given class name, return none if not found.

    THE SEARCH CAN BE LIMITED WITHIN A GIVEN WEB ELEMENT, OR ON THE WHOLE DOCUMENT IF THE BROWSER DRIVER IS PASSED
    """
    try:
        return element.find_elements_by_class_name(class_name) 
    except NoSuchElementException:
        return None
    return web_ele

#---------------------------------------------------------------
def check_and_get_ele_by_css_selector(element, selector):
    """Find the web element of a given css selector, return none if not found.

    THE SEARCH CAN BE LIMITED WITHIN A GIVEN WEB ELEMENT,  OR ON THE WHOLE DOCUMENT IF THE BROWSER DRIVER IS PASSED
    """
    try:
        return element.find_element_by_css_selector(selector)
    except NoSuchElementException:
        return None
    return web_ele

#---------------------------------------------------------------
def GetUploadDate(photo_link):
    """Given a photo link, returns the date or time when the photo was uploaded. """

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
def Open_user_home_page(user_name):
    """Open the home page of a given user. If the user page is not found, print error and return false. """ 
    driver.get('https://500px.com/' + user_name)
    # waiting until the page is opened
    main_window_handle = None
    while not main_window_handle:
        main_window_handle = driver.current_window_handle
    if check_and_get_ele_by_class_name(driver, 'missing') is None:
        return True
    else:
        printR(f'Error reading {user_name}\'s page. Please make sure a valid user name is used')
        Close_chrome_browser()
        return False

#---------------------------------------------------------------
def Get_stats(user_name):
    """Get statistics of a given user: number of likes, views, followers, following, photos, last upload date...

    OPEN USER HOME PAGE https://500px.com/[user_name]
    RUN THE DOCUMENT JAVASCRIPT TO RENDER THE PAGE CONTENT
    USE LXML TO EXTRACT INTERESTED DATA
    USE REGULAR EXPRESSION TO EXTRACT THE JSON PART IN THE BODY, AND OBTAIN MORE DATA FROM IT.
    """

    global photo, user_stats, stats, user_id
    if Open_user_home_page(user_name) == False:
        choice = Show_menu()
        return None, None

    innerHtml = driver.execute_script("return document.body.innerHTML") #run JS body scrip after page content is loaded
    time.sleep(3)
    if DEBUG:
        Write_string_to_text_file(str(innerHtml.encode('utf-8')), user_name + '_innerHTML.txt')
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
        Write_string_to_text_file(jason_string, user_name + "_stats_json.txt")

    stats = user_stats(json_data['fullname'], user_name,  user_id, location, 
                       affection_note, following_note, json_data['affection'], views_count, json_data['followers_count'], json_data['friends_count'], 
                       json_data['photos_count'], json_data['galleries_count'], json_data['registration_date'][:10], last_upload_date, user_status)
    return json_data, stats
      
#---------------------------------------------------------------
def Get_photos_list(user_name):
    """Return the list of photos from a given user.

    PROCESS: 
    - OPEN USER HOME PAGE, SCROLL DOWN UNTIL ALL PHOTOS ARE LOADED
    - MAKE SURE THE DOCUMENT JAVASCRIPT IS CALLED TO GET THE FULL CONTENT OF THE PAGE
    - EXTRACT THE user_data, the json section that contains all the photos data
    """
    global photo, user_id

    if Open_user_home_page(user_name) == False:
        choice = Show_menu()
        return []

    # We intend to scroll down an indeterminate number of times until the end is reached
    # In order to have a realistic progress bar, we need give an estimate of the number of scrolls needed
    estimate_scrolls_needed = 3  #default value, just in case error occurs
    photos_count  = 1
    photos_count_ele = check_and_get_ele_by_css_selector(driver, '#content > div.profile_nav_wrapper > div > ul > li.photos.active > a > span')
    if photos_count_ele is not None:
        photos_count = int(photos_count_ele.text.replace('.', '').replace(',', ''))
        estimate_scrolls_needed =  math.floor( photos_count / PHOTOS_PER_PAGE) +1

    Scroll_down(1.5, -1, estimate_scrolls_needed, ' - Scrolling down for more photos:') # scroll down until end, pause 1.5s between scrolls, 
    innerHtml = driver.execute_script("return document.body.innerHTML") #run JS body scrip after page content is loaded
    update_progress(0, ' - Extracting data:')
    time.sleep(3)
    if DEBUG:
        Write_string_to_text_file(str(innerHtml.encode('utf-8')), user_name + '_innerHTML.txt')
    page = html.document_fromstring(innerHtml)

    if user_id == '':
        userdata = re.findall('"userdata":(.*),"viewer":', innerHtml)
        if len(userdata) == 0:
            return None
        json_data = json.loads(userdata[0]) 
        user_id = json_data['id']

    # TOTO: by some unknown reason the json.loads() method just loads the first 50 photos, 
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
        photos.append(new_photo)
 
    return photos

#---------------------------------------------------------------
def Get_followers_list(user_name):
    """Given a user name, return the list of followers, the link to theis pages and the number of followers of each of them.

    PROCESS:
    - OPEN THE USER HOME PAGE, LOCATE THE TEXT followers AND CLICK ON IT TO OPEN THE MODAL WINDONW CONTAINING FOLLOWERS LIST
    - SCROLL TO THE END FOR ALL ITEMS TO BE LOADED
    - MAKE SURE THE DOCUMENT JS IS RUNNING FOR ALL THE DATA TO LOAD IN THE PAGE BODY
    - EXTRACT INFO AND PUT IN A LIST. RETURN THE LIST
    """
    global user
    followers_list = []
    if Open_user_home_page(user_name) == False:
        choice = Show_menu()
        return []
    time.sleep(4)
    # click on the Followers text to open the modal window
    driver.find_element_by_class_name("followers").click()
    #TODO: WAIT.EC HERE
    time.sleep(2)

    # extract number of followers                 
    followers_ele = check_and_get_ele_by_xpath(driver, '//*[@id="modal_content"]/div/div/div/div/div[1]/span')
    if followers_ele is None:
        return None
    # remode thousand separator character, if existed
    followers_count = int(followers_ele.text.replace(",", "").replace(".", ""))

    # keep scrolling the modal window, 50 followers at a time, until the end, where the followers count is reached 
    iteration_num = math.floor(followers_count / LOADED_ITEM_PER_PAGE) + 1 
    if followers_count == 1:
        printG(f'User {user_name} has {str(followers_count)} follower')
    else:
        printG(f'User {user_name} has {str(followers_count)} followers')
        
    for i in range(1, iteration_num):
        update_progress(i / (iteration_num -1), ' - Scrolling down to load all followers:')
        last_item_on_page = i * LOADED_ITEM_PER_PAGE - 1
        try:
            the_last_in_list = driver.find_elements_by_xpath('//*[@id="modal_content"]/div/div/div/div/div[2]/ul/li[' + str(last_item_on_page) + ']')[-1]
            the_last_in_list.location_once_scrolled_into_view
            time.sleep(3)
        except NoSuchElementException:
            pass
    # now that we have all followers loaded, start extracting the info
    update_progress(0, ' - Extracting data:')
    innerHTML = driver.execute_script("return document.body.innerHTML") #run JS body scrip after all photos are loaded
    time.sleep(5)
    if True: #DEBUG
        Write_string_to_text_file(str(innerHTML.encode('utf-8')), user_name + '_followers_innerHTML.txt')

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
            update_progress( i / (len(actor_infos) - 1), ' - Extracting data:')

  
        try:
            follower_page_link = actor.find_element_by_class_name('name').get_attribute('href')
            follower_user_name = follower_page_link.replace('https://500px.com/', '')
        except NoSuchElementException:
            continue  #ignore if follower name not found

        # if logged-in, we can determine if this user is followed or not
        if password != '':
            try:          
                class_name = actor.find_element_by_xpath('../..').get_attribute('class')
                if class_name.find('following') != -1 :
                    following_status = 'Following'
                else:
                    following_status = 'Not yet follow'           
            except NoSuchElementException:
                pass

        number_of_followers = ''
        texts = actor.text.split('\n')
        if len(texts) > 0: 
            follower_name = texts[0] 
        if len(texts) > 1: 
            count = texts[1]
            number_of_followers =  count.replace(' followers', '').replace(' follower', '') 
        followers_list.append(user(str(i+1), follower_name, follower_user_name, number_of_followers, following_status))
    return  followers_list 

#---------------------------------------------------------------
def Get_followings_list(user_name):
    """Get the list of followings, the link to theis pages and the number of followers of each of them.

    PROCESS:
    - OPEN THE USER HOME PAGE, LOCATE THE TEXT followers AND CLICK ON IT TO OPEN THE MODAL WINDONW CONTAINING FOLLOWERS LIST
    - SCROLL TO THE END FOR ALL ITEMS TO BE LOADED
    - MAKE SURE THE DOCUMENT JS IS RUNNING FOR ALL THE DATA TO LOAD IN THE PAGE BODY
    - EXTRACT INFO AND PUT IN A LIST. RETURN THE LIST
    """
    global user
    followings_list = []
    if Open_user_home_page(user_name) == False:
        choice = Show_menu()
        return []

    # click on the Following text to open the modal window
    driver.find_element_by_xpath('//*[@id="content"]/div[2]/div[4]/ul/li[4]').click()  # not working: driver.find_element_by_class_name("following").click()     
    time.sleep(2)
      
    # extract number of following
    following_ele = check_and_get_ele_by_xpath(driver, '//*[@id="content"]/div[2]/div[4]/ul/li[4]/span') 
    if following_ele is None:
        return None

    # remode thousand separator character, if existed
    following_count = int(following_ele.text.replace(",", "").replace(".", ""))
    if following_count == 1: 
        printG(f'User {user_name} is following { str(following_count)} user')
    else:
        printG(f'User {user_name} is following { str(following_count)} users')
    

    # keep scrolling the modal window, 50 followers at a time, until the end, where the followers count is reached 
    iteration_num = math.floor(following_count / LOADED_ITEM_PER_PAGE) + 1 
    for i in range(1, iteration_num):
        update_progress(i / (iteration_num -1 ), ' - Scrolling down to load all following users')
        last_item_on_page = i * LOADED_ITEM_PER_PAGE - 1
        try:
            the_last_in_list = driver.find_elements_by_xpath('//*[@id="modal_content"]/div/div/div/div/div[2]/ul/li[' + str(last_item_on_page) + ']')[-1]                                                             
            the_last_in_list.location_once_scrolled_into_view
            time.sleep(3)
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
            update_progress( i / (len(actor_infos) - 1), ' - Extracting data:')
        try:
            following_page_link = actor.find_element_by_class_name('name').get_attribute('href')
            following_user_name = following_page_link.replace('https://500px.com/', '')

        except NoSuchElementException:
            continue  #ignore if follower name not found

        texts = actor.text.split('\n')
        if len(texts) > 0: following_name = texts[0] 
        if len(texts) > 1: count = texts[1]; number_of_followings =  count.replace(' followers', '').replace(' follower', '')  
        followings_list.append(user(str(i+1), following_name, following_user_name, number_of_followings))
    return followings_list 

#---------------------------------------------------------------
def Get_notification_list(get_full_detail = True, number_of_notifications = MAX_NOTIFICATION_REQUEST):
    """Get n last notifications.
    
    A DETAILED NOTIFICATION ITEM CONTAINS FULL_NAME, USER NAME, THE CONTENT OF THE NOTIFICATION, TITLE OF THE PHOTO IN QUESTION, THE TIME STAMP AND A STATUS
    A SHORT NOTIFICATION ITEM CONTAINS JUST FULL NAME AND USER NAME
    A UNIQUE NOTIFICATION LIST IS A SHORT NOTIFICATION LIST WHERE ALL THE DUPLICATION ARE REMOVED.
    IF THE GIVEN get_full_detail IS TRUE, RETURN THE DETAILED LIST, IF FALSE, RETURN THE UNIQUE LIST
    PROCESS:
    - EXPECTING THE USER WAS LOGGED IN, AND THE NOTIFICATION PAGE IS THE ACTIVE PAGE
    - SCROLL DOWN  N TIMES, CALCULATED BY THE GIVEN number_of_notifications, FOR ALL REQUIRED ITEMS TO BE LOADED 
    - EXTRACT INFO, RETURN THE FULL LIST OF A UNIQUE LIST DEPENTING ON THE REQUEST
    """
    global notification, notificator, unique_notificators

    notifications_list = []
    short_list = []

    if number_of_notifications == -1: # secret switch: -1 for requesting all available notifications from server (could be time-consuming process)
        scrolls_needed = -1
    else:                             # Notifications are loaded 20 items at a time. Ex. to get 80 items we need to scroll 4 times 
        scrolls_needed =  math.floor(number_of_notifications / NOTIFICATION_PER_LOAD) +1

    pause_between_scrolls = 1.5
    estimate_scrolls_needed = scrolls_needed
    # estimate_scrolls_needed is used only when we want unlimited scrolls times (scrolls_needed = -1). We pass irrelevant value here to Scroll_down() just to fill the function signature 
    Scroll_down(pause_between_scrolls, scrolls_needed, estimate_scrolls_needed, ' - Scrolling down for more notifications:' ) 

    # get the info now that all the needed notifications are loaded
    items = driver.find_elements_by_class_name('notification_item')  
    count = len(items)                                                                
    for i, item in enumerate(items):
        if number_of_notifications != -1 and i >=  number_of_notifications:
            update_progress(1, ' - Extracting data:')
            break
        if i > 0:
            update_progress( i / (count-1), ' - Extracting data:')

        actor = check_and_get_ele_by_class_name(item, 'notification_item__actor') 
        if actor is None:
            continue
        display_name = actor.text
        user_name = actor.get_attribute('href').replace('https://500px.com/', '')
        
        #if get_full_detail:
        item_text = item.find_element_by_class_name('notification_item__text')
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
        
        timestamp = item.find_element_by_class_name('notification_item__timestamp').text
        notifications_list.append(notification(str(i+1), display_name, user_name, content, photo_link, photo_title, timestamp, status))                  

        short_list.append(f'{display_name},{user_name}')

    unique_notificators = Remove_duplicates(short_list)

    # add order number at the begining of each row
    for j in range(len(unique_notificators)):
        unique_notificators[j] = f'{str(j+1)},{unique_notificators[j]}'

    if len(notifications_list) == 0 and len(unique_notificators) == 0: 
        printG(f'User {user_name} has no notification')
   
    return notifications_list, unique_notificators

#---------------------------------------------------------------
def Get_like_actioners_list():
    """Get the list of users who liked a given photo.

    PROCESS:
    - EXPECTING THE ACTIVE PAGE IN THE BROWSER IS THE GIVEN PHOTO PAGE
    - RUN THE DOCUMENT JS TO RENDER THE PAGE BODY
    - EXTRACT PHOTO TITLE AND PHOTOGRAPHER NAME
    - LOCATE THE LIKE COUNT NUMBER THEN CLICK ON IT TO OPEN THE MODAL WINDOW HOSTING THE LIST OF ACTIONER USER
    - SCROLL DOWN TO THE END AND EXTRACT RELEVANT INFO, PUT ALL TO THE LIST AND RETURN IT
    """
    global user, like_actioners_file_name
    actioners_list = []

    innerHtml = driver.execute_script("return document.body.innerHTML") #run JS body scrip after page content is loaded
    time.sleep(3)
    if DEBUG:
        Write_string_to_text_file(str(innerHtml.encode('utf-8')), 'photo_innerHTML.txt')
    # find an ancestor element that cover all needed elements
    react_photos_index_container = driver.find_element_by_class_name('react_photos_index_container')
    if react_photos_index_container is None:
        printR('Error getting like_actioners list')
        return []
    print(' - Getting photo details ...')
    styled_link =  check_and_get_ele_by_xpath(react_photos_index_container, '//div/div/div[2]/div/div[2]/div[2]/div[1]/a')
    if styled_link is not None: photographer_name = styled_link.text
    else:                       photographer_name = 'Name not found'
    printG(f'   Photogapher: {photographer_name}')

    styled_layout_box = check_and_get_ele_by_xpath(react_photos_index_container, '//div/div/div[2]/div/div[2]/div[2]/div[1]/h3')
    if styled_layout_box is None: 
        printR('Error getting like_actioners list')
        return []
    photo_title = styled_layout_box.text
    printG(f'   Photo title: {photo_title}')

    # make sure the  photo title is visible
    styled_layout_box.location_once_scrolled_into_view
    # find the like-count element, get the likes count and click on it  to open the modal window
    like_count_button = check_and_get_ele_by_xpath(react_photos_index_container, '//div/div/div[2]/div/div[2]/div[1]/div[1]/a')
    if like_count_button is None:                           
        printG('   Photo has 0 like')
        return []
 
    likes_count_string = like_count_button.text
    likes_count = int(likes_count_string.replace('.','').replace(',',''))

    printG(f'   This photo has {likes_count} likes')
    driver.execute_script("arguments[0].click();", like_count_button)
    time.sleep(3)   
    # make a meaningful output file name
    like_actioners_file_name = f"{photographer_name.replace(' ', '-')}_{photo_title.replace(' ', '-')}_{likes_count}_ like_actioners.csv"

    # scroll to the end for all elements of the given class name to load all actioners
    Scroll_to_end_by_class_name('ifsGet', likes_count)
    
    # create actionners list
    actioners = driver.find_elements_by_class_name('ifsGet')
    actioners_count = len(actioners)
    for i, actioner in enumerate(actioners):
        update_progress(i / (actioners_count - 1), ' - Extracting data:')
        try:    
            texts = actioner.text.split('\n')
            if len(texts) > 0: 
                display_name = texts[0] 
            if len(texts) > 1:
                followers_count  = re.sub('[^\d]+', '', texts[1]) 
            name = actioner.find_element_by_tag_name('a').get_attribute('href').replace('https://500px.com/','')
            actioners_list.append(user(str(i+1), display_name, name, str(followers_count)) )
        except NoSuchElementException:
            continue
    return actioners_list 
#---------------------------------------------------------------
def Autolike_photos(target_user_name, number_of_photos_to_be_liked, include_already_liked_photo_in_count = True):
    """Like n photo of a given user, starting from the top.

    IF THE include_already_liked_photo IS TRUE, THE ALREADY-LIKED PHOTO WILL BE COUNTED AS DONE BY THE AUTO-LIKE PROCESS
    FOR EXAMPLE, IF YOU NEED TO AUTO-LIKE 3 PHOTOS FROM A USER, BUT THE FIRST TWO ARE ALREADY LIKED, THEN YOU ONLY NEED TO DO ONE
    IF THE include_already_liked_photo_in_count IS FALSE (DEFAULT), THE PROCESS WILL AUTO-LIKE THE EXACT NUMBER REQUESTED
    PROCESS:
    - OPEN THE USER HOME PAGE
    - FORCE DOCUMENT JS TO RUN TO FILL THE VISIBLE BODY
    - LOCATE THE FIRST PHOTO, CHECK IF IT IS ALREADY-LIKED OR NOT, IF YES, GO THE NEXT PHOTO, IT NO, CLICK ON IT TO LIKE THE PHOTO
    - CONTINUE UNTIL THE ASKING NUMBER OF PHOTOS IS REACHED. 
    - WHEN WE HAVE PROCESSED ALL THE LOADED PHOTOS BUT THE REQUIRED NUMBER IS NOT REACHED YET, 
      ... SCROLL DOWN ONCE TO LOAD MORE PHOTOS ( CURRENTLY 500PX LOADS 50 PHOTOS AT A TIME) AND REPEAT THE STEPS UNTIL DONE
      """
    if Open_user_home_page(target_user_name) == False:
        return

    innerHtml = driver.execute_script("return document.body.innerHTML") #run JS body scrip after page content is loaded
    time.sleep(3)
    
    new_fav_icons =  driver.find_elements_by_css_selector('.button.new_fav.only_icon')
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
        
        Hover_by_element(icon) # not neccessary, but good for visual demonstration
        try:
            title =  icon.find_element_by_xpath('../../../../..').find_element_by_class_name('photo_link').find_element_by_tag_name('img').get_attribute('alt')
            driver.execute_script("arguments[0].click();", icon) 
            done_count = done_count + 1
            printG(f'  - liked #{str(done_count):3} Photo {str(i + 1):2} - {title:.50}')
            # slowing  down a bit to make it look more like human
            time.sleep(1)

        except Exception as e:
            printR(f'Error after {str(done_count)}, at index {str(i)}, title {title}:\nException: {e}')

#---------------------------------------------------------------
def Like_n_photos_on_current_page(number_of_photos_to_be_liked, index_of_start_photo):
    """Like n photos on the active photo page. It could be either popular, popular-undiscovered, upcoming, fresh or editor's choice page.

    THIS WILL AUTOMATICALLY SCROLL DOWN IF MORE PHOTOS ARE NEEDED
    PROCESS:
    - SIMILAR TO THE PREVIOUS METHOD ( Autolike_photos() )
    """
    photos_done = 0
    current_index = 0   # the index of the photo in the loaded photos list. We dynamically scroll down the page to load more photos as we go, so ...
                        # ... we use this index to keep track where we are after a list update 
            
    # debug info: without scrolling, it would load (PHOTOS_PER_PAGE = 50) photos
    new_fav_icons =  driver.find_elements_by_css_selector('.button.new_fav.only_icon')
    loaded_photos_count = len(new_fav_icons)

    #optimization: at the begining, scrolling down to the desired index instead of repeatedly scroll & check 
    if index_of_start_photo > PHOTOS_PER_PAGE:
        estimate_scrolls_needed =  math.floor( index_of_start_photo / PHOTOS_PER_PAGE) +1
        Scroll_down(1, estimate_scrolls_needed, estimate_scrolls_needed, f' - Scrolling down to photos #{index_of_start_photo}:') 
        time.sleep(2)
        loaded_photos_count = len(new_fav_icons)
          
    while photos_done < number_of_photos_to_be_liked: 
        # if all loaded photos have been processed, scroll down 1 time to load more
        if current_index >= loaded_photos_count: 
            prev_loaded_photos = loaded_photos_count
  
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            driver.execute_script("return document.body.innerHTML")

            new_fav_icons =  driver.find_elements_by_css_selector('.button.new_fav.only_icon')
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
            
            Hover_by_element(icon) # not required, but good for visual demonstration
            time.sleep(0.5)
            try:
                # might want to slow down a bit to make it look more like human
                time.sleep(1)
                title =  icon.find_element_by_xpath('../../../../..').find_element_by_class_name('photo_link').find_element_by_tag_name('img').get_attribute('alt')
                photographer_ele = icon.find_element_by_xpath('../../../..').find_element_by_class_name('photographer')
                photographer_ele.location_once_scrolled_into_view
                Hover_by_element(photographer_ele)
                #driver.execute_script("arguments[0].scrollIntoView();", photographer_ele)
                photographer = photographer_ele.text
                driver.execute_script("arguments[0].click();", icon) 
                photos_done = photos_done + 1
                printG(f'Liked {str(photos_done):>3}/{number_of_photos_to_be_liked:<3}, {photographer:<28.24}, Photo {str(i+1):<4} title {title:<35.35}')
            except Exception as e:
                printR(f'Error after {str(photos_done)}, at index {str(i+1)}, title {title}:\nException: {e}')

#---------------------------------------------------------------
def Play_slideshow(time_interval):
    """Play slideshow of photos on the active photo page in browser.

    PROCESS:
    EXPECTING THE ACTIVE PAGE IN BROWSER IS THE PHOTOS PAGE
    - OPEN THE FIRST PHOTO BY CLICK ON IT
    - CLICK ON THE EXPAND ARROW TO MAXIMIZE THE DISPLAY AREA 
    - AFTER A GIVEN TIME INTERVAL, LOCATE THE NEXT BUTTON AND CLICK ON IT TO SHOW THE NEXT PHOTO
    - EXIT WHEN LAST PHOTO IS REACHED
    """
    photo_links_eles = check_and_get_all_eles_by_class_name(driver, 'photo_link')
    loaded_photos_count = len(photo_links_eles)
 
    if len(photo_links_eles) > 0:
        # show the first photo
        driver.execute_script("arguments[0].click();", photo_links_eles[0])
        innerHTML = driver.execute_script("return document.body.innerHTML")
        time.sleep(3)
        expand_icon = check_and_get_ele_by_xpath(driver, '//*[@id="copyrightTooltipContainer"]/div/div[2]') 
        driver.execute_script("arguments[0].click();",expand_icon)
        time.sleep(time_interval)
        
        next_icon = check_and_get_ele_by_xpath(driver, '//*[@id="copyrightTooltipContainer"]/div/div[1]/div') 
        while next_icon is not None:
            driver.execute_script("arguments[0].click();", next_icon)
            time.sleep(time_interval)
            next_icon = check_and_get_ele_by_xpath(driver,  '//*[@id="copyrightTooltipContainer"]/div/div[2]/div/div[2]')  

#---------------------------------------------------------------                           
def Like_n_photos_on_homefeed_page(number_of_photos_to_be_liked):
    """Like n photos from the user's home feed page, excluding recommended photos.

    SKIP CONSECUTIVE PHOTO(S) OF THE SAME USER
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
    print(f"Getting the loaded photos from {user_name}'s home feed page ...")
    img_eles = Get_IMG_element_from_homefeed_page()
    loaded_photos_count = len(img_eles)
   
    while photos_done < number_of_photos_to_be_liked: 
        # check whether we have processed all loaded photos, if yes, scroll down 1 time to load more
        if current_index >= loaded_photos_count: 
            prev_loaded_photos = loaded_photos_count
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")                
            time.sleep(2)

            img_eles = Get_IMG_element_from_homefeed_page()
            loaded_photos_count = len(img_eles)

            # stop when all photos are loaded
            if loaded_photos_count == prev_loaded_photos:
                break;

        for i in range(current_index, loaded_photos_count):
            # stop when done
            if photos_done >= number_of_photos_to_be_liked: 
                break
            current_index += 1
            photographer_name = ' '
            title = ' '
            parent2 = check_and_get_ele_by_xpath(img_eles[i], '../..')   #img_eles[i].find_element_by_xpath('../..')
            if parent2 is None: continue
                
            parent2_sib1 =  check_and_get_ele_by_xpath(parent2, './following-sibling::div') #parent2.find_element_by_xpath('./following-sibling::div')
            if parent2_sib1 is None: continue
                
            # Skip if this is your own photo. Show console log in Blue color 
            child_div_eles = parent2_sib1.find_elements_by_tag_name('div')
            if len(child_div_eles) > 1:
                if child_div_eles[1].text.find('disabled') != -1: # this may be your own photo 
                    printB(f'Skipped  : photo {str(i + 1):<3}, from {photographer_display_name:<32.30}, {title:<35.35}')
                    continue

            parent2_sib2 =  check_and_get_ele_by_xpath(parent2_sib1, './following-sibling::div') #parent2_sib1.find_element_by_xpath('./following-sibling::div')
            if parent2_sib2 is  None: continue    
            # for logging message, get photo title, photogragpher display name and  user namegging
            title  = parent2_sib2.find_element_by_tag_name('h3').text
            a = parent2_sib2.find_element_by_tag_name('a')
            photographer_display_name  = a.text
            photographer_name = a.get_attribute('href').replace('https://500px.com/', '')

            # get like status
            photo_already_liked = False
            if  parent2_sib1.text.find('Outline') == -1:
                photo_already_liked = True
                 
            # get the like icon to click on
            span = parent2_sib1.find_element_by_tag_name('span')
            span.location_once_scrolled_into_view
            heart_icon = check_and_get_ele_by_xpath(span, './following-sibling::div')
            # this may be your own photo
            if heart_icon is None:
                printB(f'Skipped:      photo {str(i + 1):3}, from {photographer_display_name:<32.30}, {title:<35.35}')
                continue

            Hover_by_element(heart_icon)
            if  not photo_already_liked:      
                # skip consecutive photos of the same photographer
                if photographer_name == prev_photographer_name:
                    printY(f'Skipped:      photo {str(i + 1):3}, from {photographer_display_name:<32.30}, {title:<35.35}')
                    continue
                if heart_icon is not None:
                    driver.execute_script("arguments[0].click();", heart_icon) 
                    photos_done += 1
                    prev_photographer_name = photographer_name
                    printG(f'Like {photos_done:>3}/{number_of_photos_to_be_liked:<3}: photo {str(i + 1):<3}, from {photographer_display_name:<32.30}, {title:<40.40}')
                    time.sleep(1.5)  # slow down a bit to make it look more like a human

#---------------------------------------------------------------
def Remove_duplicates(values):
    """Given a nested list containing the pairs of display name and user name. Return the list that has no duplication pair in it."""
    output = []
    seen = set()
    for value in values:
        # If value has not been encountered yet, add it to both list and set.
        if value not in seen:
            output.append(value)
            seen.add(value)
    return output    

#---------------------------------------------------------------
def Scroll_down(scroll_pause_time = 0.5, number_of_scrolls = 10, estimate_scrolls_needed = 3, message = ''):
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
            # here, we dont know when it ends (for example, we ask for all pass notifications, but we don't know how many the 500px server will provide) 
            else:
                notifications_loaded_so_far = scrolls_count_for_stimulated_progressbar * NOTIFICATION_PER_LOAD
                text = f'\r{message:} Estimate number of notifications so far {str(notifications_loaded_so_far)} '
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
def Scroll_to_end_by_class_name(class_name, likes_count):
    """Scroll the active window to the end, where the last element of the given class name become visible.

    THE likes_count ARGUMENT IS USED FOR CREATING A REALISTIC PROGRESS BAR
    """
    eles = driver.find_elements_by_class_name(class_name)
    count = 0
    new_count = len(eles)

    while new_count != count:
        try:
            update_progress(new_count / likes_count, ' - Scrolling to load more items:')
            the_last_in_list = eles[new_count - 1]
            the_last_in_list.location_once_scrolled_into_view 
            time.sleep(1)
            WebDriverWait(driver, 5).until(EC.visibility_of(the_last_in_list))
            count = new_count
            eles = driver.find_elements_by_class_name(class_name)
            new_count = len(eles)
        except NoSuchElementException:
            pass
    if new_count < likes_count:
        update_progress(1, ' - Scrolling to load more items:')

#---------------------------------------------------------------
def Login(user_name, password):
    """Submit given credentials to the 500px login page. """
    if len(password) == 0 or len(user_name) == 0: 
        return ''
    driver.get("https://500px.com/login" )
    name_field = driver.find_element_by_name("email")   #username form field
    pwd_field = driver.find_element_by_name("password") #password form field
    name_field.send_keys(user_name)
    pwd_field.send_keys(password)
    submitButton = driver.find_element_by_class_name("unified_signup__submit_button") 
    submitButton.click()
    time.sleep(3) #important: need this for the default page to load and some JS to run to get user's stats

#---------------------------------------------------------------
def Write_string_to_text_file(input_string, file_name, encode = ''):
    """Write the given string to a disk as a given file name. """
    if encode == '':
        open_file = open(file_name, "w")
    else:
        open_file = open(file_name, "w", encoding = encode)
    
    open_file.write(input_string)
    open_file.close()

#--------------------------------------------------------------- 
def Offer_to_open_file(file_name, list_type):
    """Offer to open the given file with the default system app. given files are one of the csv output files we have created.

    FOR BETTER VIEWING, WE CONVERT THE CSV FILE TO A HTML 
    """
    Close_chrome_browser() #TODO: move this out of the method
    open_request = input('Press o to open the file or ENTER to continue >')
    if open_request == 'o':
        file_path, file_extension = os.path.splitext(file_name)
        if file_extension != ".csv":
            os.startfile(file_name)
        else:
            ## later: option to sort by column
            #with open(file_name, newline='', encoding='utf-16') as csvfile:
            #   # dynamically create a column selection menu 
            #    reader = csv.reader(csvfile)
            #    headers = next(reader, None)
            #    col_count = len(headers)
            #    sub_menu_string = ''
            #    for i, header in enumerate(headers):
            #        sub_menu_string += f'{i}  {header}'
            #        if i < col_count - 1:
            #            sub_menu_string += '\n'
            #    printC(f'Please select a sort column:\n{sub_menu_string}\n> ')
            #    sort_column_index = Validate_input('')
            #    # TODO: determine if the selected column is string or number  
            #    # then do the sorting with selected column
            #    sorted_list = sorted(reader, key=lambda row: int(row[3]))
            #    # put back the columns headers
            #    sorted_list.insert(0, headers)

            # Convert csv file to html. Save and show it with system browser app
            # the photos list csv file has special structure so we handle it diffenrently than
            # other csv files, (followers, following lists, unique, notification lists, all have common first 3 columns ( Order, Display Name, User Name)  )
            if list_type is Output_file_type.PHOTOS_LIST:
                os.startfile(CSV_photos_list_to_HTML(file_name))
            else: 
                os.startfile(CSV_to_HTML(file_name))
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
def CSV_to_HTML(csv_file_name):
    """ Read a specific type of csv file into a table, put it to a html file and write it to disk . Return the filename.
    
    THE EXPECTED CSV FILES HAS THIS FEATURE: THE FIRST THREE COLUMNS ARE ALWAYS ORDER, DISPLAY NAME AND USER NAME.
    ON THE SECOND COLUMN, WE WILL ASSIGN A WEB LINK <A> SUCH AS <A HREF="HTTPS://500PX.COM/{USER NAME}" 
    SAVE THE HTML FILE USING THE SAME NAME BUT WITH EXTENSION '.HTML' 
    THE FIRST LINE WILL BE USED AS HEADERS, WHICH ARE  ORDER, DISPLAY NAME, USER NAME, FOLLOWERS, STATUS
                                                       OR:  ORDER, NAME, USER NAME, CONTENT, PHOTO TITLE, TIME STAMP, STATUS
                                                       OR:  ORDER, NAME, USER NAME
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
def Validate_non_empty_input(prompt_message):
    """Prompt user for an input, make sure the input is not empty. """

    val = input(prompt_message)
    if val == 'q' or val == 'r':
        return val
    while len(val) == 0:        
        printR("Input cannot be empty! Please re-enter.")
        val = input(prompt_message)
    return  val
#--------------------------------------------------------------- 
def Validate_input(prompt_message):
    """ Prompt for input and accepts nothing but digits or letter 'r' or 'q'. """

    val = input(prompt_message)        
    while True:
        if val == 'r' or val == 'q':
            return val
        try: 
            return int(val)
        except ValueError:
            printR("Invalid input! Please retry.")
            val = input(prompt_message)

#--------------------------------------------------------------- 
def Get_IMG_element_from_homefeed_page():
    """Get all <img> elements on page then remove elmenents that are not from user's friends.

    WE WANT TO GET THE LIST OF LOADED PHOTOS ON THE USER HOME FEED PAGE, THE ONES FROM THE PHOTOGRAPHERS THAT YOU ARE FOLLOWING.
    SINCE ALL THE CLASS NAMES IN THE USER HOMEFEED PAGE ARE POSTFIXED WITH RANDOMIZED TEXTS. 
    A WORK-AROUND SOLUTION IS TO USE THE TAG IMG AS IDENTIFIER FOR A PHOTO 
    FROM THERE WE REMOVE IMG ITEM THAT ARE EITHER AVATARS, THUMBNAILS OR RECOMMENDED PHOTOS
    """
    # we are interested in items with the tag <img>
    img_eles = driver.find_elements_by_tag_name('img')
    # img_eles list has many img elements that we don't want, such as thumbnails, recommended photos..., we will remove them from the list
    for ele in reversed(img_eles):
        parent_4 = ele.find_element_by_xpath('../../../..')
        if parent_4.get_attribute('class').find('Elements__HomefeedPhotoBox') == -1:
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
def Hide_banners():
    """Hide top and bottom banners that make elements beneath them inaccessible."""

    top_banner = check_and_get_ele_by_id(driver, 'hellobar')
    if top_banner is not None:
        driver.execute_script("arguments[0].style.display='none'", top_banner)
    bottom_banner = check_and_get_ele_by_tag_name(driver, 'w-div')
    if bottom_banner is not None:
        driver.execute_script("arguments[0].style.display='none'", bottom_banner)

#---------------------------------------------------------------
def Reset_global_variables():
    """ Reset global variables."""

    global json_data, photos, notifications, unique_notificator, followers_list, followings_list, like_actioners_list, \
           stats, user_name, user_id, password, targer_user_name, number_of_notofications, index_of_start_photo, like_actioners_file_name
    json_data = []
    photos = []
    notifications = []
    unique_notificators = []
    followers_list = []
    followings_list = []
    like_actioners_list= []

    stats = user_stats() 
    user_name = ''
    user_id = ''
    password = ''
    target_user_name = ''
    number_of_photos_to_be_liked = 2
    number_of_notifications = MAX_NOTIFICATION_REQUEST
    index_of_start_photo = 0
    like_actioners_file_name = 'dummy'
#---------------------------------------------------------------
def Show_menu():
    """ Display main menu. Added user credentials according to the user selection. Return the selection"""

    global user_name, password 
   
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
    #printC('')
    printC('   6  Get n last notifications details (max 1000)')
    printC('   7  Get list of unique users who generated last n notifications (liked, commented, followed ...)')
    printC('')
    printC('   8  Like n photos from a given user')
    printC('   9  Like n photos, starting at a given index, on various photo pages') 
    printC('  10  Like n photos of each user who likes a given photo or yours')
    printC('  11  Like n photos from your home-feed page, excluding recommended photos ')
    printC('  12  Like n photos of each users in your last m notifications')
    printC('')
    printY('      The following option does not need credentials:')
    printC('  13  Play slideshow on a given gallery')
    printC('')
    printC('   r  Restart with different user')
    printC('   q  Quit')
    printC('')
    sel = Validate_input('Enter your selection >')

    # exit the program
    if sel == 'q':
        os.sys.exit()

    # restart with different user
    elif sel == 'r': 
       Reset_global_variables()
       user_name = input('Enter 500px user name >')
       printG(f'      Current user: {user_name}')
       return Show_menu()

    # play slideshow, no credentials needed
    elif sel == 13:
       return sel
    
    # user name is mandatory
    if user_name == '':
        user_name = input('Enter 500px user name >')
    printG(f'Current user: {user_name}')

    # password is optional
    if sel == 3 and password == '':
        password = input('Type in password if you want to get the following statuses. To ignore, just press ENTER: >')
    
    # password is mandatory 
    if sel >= 6 and sel <= 13:
        if user_name == '':
            user_name = input('Enter 500px user name >')
        if password == '':
            password = Validate_non_empty_input('Enter password >')        
    return sel


#---------------------------------------------------------------
def Show_galllery_selection_menu():
    """ Show sub menu for selection of a photo gallery for playing slideshow. Wait for user input."""
    printC('--------- Select the desired photos page for the slideshow: ---------')
    printC('    1  Popular')
    printC('    2  Popular-Undiscovered photographers')
    printC('    3  Upcoming')
    printC('    4  Fresh')
    printC("    5  Editor's Choice")
    printC("    6  Your photos")
    printC("    7  My specific gallery")
    printC('')
    printC('    r  Restart for different user')
    printC('    q  Quit')

    sel = input('Enter your selection >')
    # exit the program
    if sel == 'q'or sel == 'r':
        return sel, ''
    elif sel == '1': return 'https://500px.com/popular'                       , 'Popular'
    elif sel == '2': return 'https://500px.com/popular?followers=undiscovered', 'Popular, Undiscovered'
    elif sel == '3': return 'https://500px.com/upcoming'                      , 'Upcoming'
    elif sel == '4': return 'https://500px.com/fresh'                         , 'Fresh'
    elif sel == '5': return 'https://500px.com/editors'                       , "Editor's Choice"
    elif sel == '6': return f'https://500px.com/{user_name}'                  , 'My photo gallery'
    elif sel == '7': return Validate_non_empty_input('Enter the link to your desired photo gallery. It could be a public gallery with filters, or a private gallery >'), 'My specific gallery' 
    else:
        Show_galllery_selection_menu()

#======================================================================================================================
# MAIN PROGRAM STARTS HERE. TODO: put this in __main__
#======================================================================================================================
os.system('color')
driver = None
#logging.basicConfig(filename='500px.log', filemode='w', format='%(asctime)s - %(message)s', level=logging.INFO)
if True:
    choice = Show_menu()
else:
# bypassing menu for quick test
    choice = ''
    gallery_href = ''
    time_interval = 2
    user_name ='' 
    password = ''
    photo_href = ''
    number_of_notifications = 1
    choice = Show_menu()

while choice != 'q':
    #---------------------------------------------------------------
    # Get statistics
    if choice == 1:
        Start_chrome_browser()
        Hide_banners()
        json_data, stats = Get_stats(user_name) 
        if json_data is None or len(json_data) == 0:
            printR(f'Error reading {user_name}\'s page. Please make sure a valid user name is used')
            choice = Show_menu()
            continue

        print(f"Getting user's statistics ...")
        output_file =  user_name + "_stats.html"
        Write_string_to_text_file(Create_user_statistics_html(stats), output_file)
        Close_chrome_browser()
        Offer_to_open_file(output_file, Output_file_type.STATISTICS_HTML_FILE)
        choice = Show_menu()
    #---------------------------------------------------------------
    # Get photos list
    elif choice == 2:
        outfile = user_name + "_photos.csv"
        # avoid to do the same thing twice: if list (in memory) has items AND output file exists on disk
        if len(photos) > 0 and os.path.isfile(outfile):
            printY('Photo list existed at: ' + os.path.abspath(outfile))
            Offer_to_open_file(outfile, Output_file_type.PHOTOS_LIST) 
            choice = Show_menu()
            continue
        else:
            Start_chrome_browser()
            Hide_banners()
            print(f"Getting {user_name}'s photos list ...")
            photos = Get_photos_list(user_name)
            Close_chrome_browser()
            if photos is None: 
                choice = Show_menu()
                continue
            
            photos_list_file_name = user_name + "_photos.csv"
            if Write_photos_list_to_csv(photos, photos_list_file_name) == True:
                Offer_to_open_file(photos_list_file_name, Output_file_type.PHOTOS_LIST) 
            choice = Show_menu()
            continue
    #---------------------------------------------------------------
    # Get Followers list
    elif choice == 3:
        outfile = user_name + '_followers.csv'
        # avoid to do the same thing twice: when the list (in memory) has items and output file exists on disk
        if len(followers_list) > 0  and os.path.isfile(outfile):
            printY('Followers list existed at: ' + os.path.abspath(outfile))
            Offer_to_open_file(outfile, Output_file_type.USERS_LIST) 
            choice = Show_menu()
            continue
        else:
            Start_chrome_browser()
            Login(user_name, password)
            Hide_banners()
            print(f"Getting the list of users who follow you ...")
            followers_list = Get_followers_list(user_name)
            Close_chrome_browser()
            if len(followers_list) > 0 and Write_users_list_to_csv(followers_list, outfile) == True:
                Offer_to_open_file(outfile, Output_file_type.USERS_LIST) 

            choice = Show_menu()
            continue
    #---------------------------------------------------------------
    # Get Followings list
    elif choice == 4:
        outfile = user_name + '_followings.csv'
        # avoid to do the same thing twice: when the list (in memory) has items and output file exists on disk
        if len(followings_list) > 0  and os.path.isfile(outfile):
            printY('Followings list existed at:\n ' + os.path.abspath(outfile))
            Offer_to_open_file(outfile, Output_file_type.USERS_LIST) 
            choice = Show_menu()
            continue
        else:
            Start_chrome_browser()
            Hide_banners()        
            print(f"Getting the list of users that you are following ...")
            followings_list = Get_followings_list(user_name)
            Close_chrome_browser()
            if len(followings_list) > 0 and Write_users_list_to_csv(followings_list, outfile, ) == True:
                 Offer_to_open_file(outfile, Output_file_type.USERS_LIST) 

            choice = Show_menu()
            continue
    #---------------------------------------------------------------  
    # Get a list of unique users who liked a given photo      
    elif choice == 5:
        photo_href = input('Enter photo href >')
        if len(photo_href) == 0:
            printR('Invalid input. Please retry')
            choice = Show_menu()
            continue   

        Start_chrome_browser()
        
        try:
            driver.get(photo_href)
        except:
            printR(f'Invalid href: {photo_href}. Please retry.')
            Close_chrome_browser()
            choice = Show_menu()        
            continue

        time.sleep(1)
        Hide_banners()
        print(f"Getting the list of unique users who liked the given photo ...")
        like_actioners_list = Get_like_actioners_list()
        Close_chrome_browser()
        if len(like_actioners_list) > 0 and Write_users_list_to_csv(like_actioners_list, like_actioners_file_name, ) == True:
             Offer_to_open_file(like_actioners_file_name, Output_file_type.USERS_LIST) 
        choice = Show_menu()
        continue   
    #---------------------------------------------------------------    
    # Get n last notifications details (max 1000)
    elif choice == 6:
        outfile = user_name + '_notification.csv'
        # avoid to do the same thing twice: when the list (in memory) has items and output file exists on disk
        if len(notifications) > 0 and os.path.isfile(outfile):
            printG('List existed at:\n ' + os.path.abspath(outfile))
            Offer_to_open_file(outfile, Output_file_type.NOTIFICATIONS_LIST)
            choice = Show_menu()
            continue

        user_input =  Validate_input('Enter the number of notifications you want to retrieve(max 1000) >')
        if user_input == 'q' or user_input == 'r':
            choice = user_input
            continue
        else: 
            number_of_notifications = int(user_input)
        
        if number_of_notifications > MAX_NOTIFICATION_REQUEST: # prevent abusing
            number_of_notifications = MAX_NOTIFICATION_REQUEST
 
        Start_chrome_browser()
        Login(user_name, password)
        driver.get('https://500px.com/notifications')
        time.sleep(1)
  
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)        
        
        innerHtml = driver.execute_script("return document.body.innerHTML")
        time.sleep(4)
        Hide_banners()        
        if number_of_notifications == -1:
            print(f"Getting the unique users that interact with your photos in all of your notifications ...")
        else:
            print(f"Getting the unique users that interact with your photos in the last {number_of_notifications} notifications ...")

        notifications, unique_notificators = Get_notification_list(True, number_of_notifications)
        
        if len(notifications) == 0 and len(unique_notificators) == 0:
            choice = Show_menu()
            Close_chrome_browser()
            continue

        Close_chrome_browser()
        if len(notifications) > 0 and  Write_notifications_to_csvfile(notifications, outfile) == True:
            Offer_to_open_file(outfile, Output_file_type.NOTIFICATIONS_LIST)

        choice = Show_menu()
        continue    
    #---------------------------------------------------------------  
    # Get list of unique users who generated last n notifications (liked, commented, followed, added to galleries ...)
    elif choice == 7:
        outfile = user_name + '_unique_notificators.csv'     
        ## avoid repeating work: when the list (in memory) has items AND output file exists on disk
        #if len(unique_notificators) > 0 and os.path.isfile(outfile):
        #    printG('List existed at: ' + os.path.abspath(outfile))
        #    Offer_to_open_file(outfile)
        #    choice = Show_menu()
        #    continue        

        user_input =  Validate_input('Enter the number of notifications you want to retrieve(max 1000) >')
        if user_input == 'q' or user_input == 'r':
            choice = user_input
            continue
        else: 
            number_of_notifications = int(user_input)
        
        if number_of_notifications > MAX_NOTIFICATION_REQUEST:  # prevent abusing
            number_of_notifications = MAX_NOTIFICATION_REQUEST
 
        Start_chrome_browser()
        Login(user_name, password)
        driver.get('https://500px.com/notifications')
        time.sleep(1)

        #scrol down one time
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

        innerHtml = driver.execute_script("return document.body.innerHTML")
        time.sleep(5)
        Hide_banners()
        if number_of_notifications == -1:
            print(f"Getting the unique users that interact with your photos in all of your notifications ...")
        else:
            print(f"Getting the unique users that interact with your photos in the last {number_of_notifications} notifications ...")

        dummy_notifications, unique_notificators = Get_notification_list(True, number_of_notifications)
        if len(dummy_notifications) == 0 and len(unique_notificators) == 0:
            choice = Show_menu()
            Close_chrome_browser()
            continue
                
        if number_of_notifications == -1:
            print(f'There are {len(unique_notificators)} unique users in all the notifications')
        else:
            print(f'There are {len(unique_notificators)} unique users in the last {number_of_notifications} notifications')
        
        Close_chrome_browser()
        if len(unique_notificators) >= 0 and Write_unique_notificators_list_to_csv(unique_notificators, outfile) == True: 
             Offer_to_open_file(outfile, Output_file_type.NOTIFICATIONS_LIST) 

        choice = Show_menu()
        continue
 
    #-------------------------------------------------------------- 
    # Auto-like the first n not-yet-liked photos of a given user'
    elif choice == 8:
        target_user_name = Validate_non_empty_input('Enter target user name >')

        user_input =  Validate_input('Enter the number of photos you want to auto-like >')
        if user_input == 'q' or user_input == 'r':
            choice = user_input
            continue
        else: 
            number_of_photos_to_be_liked = int(user_input)
        
        #  avoid abusing the server
        if number_of_photos_to_be_liked > MAX_AUTO_LIKE_REQUEST: 
            number_of_photos_to_be_liked = MAX_AUTO_LIKE_REQUEST
  
        Start_chrome_browser()
        Login(user_name, password)

        if number_of_photos_to_be_liked == 1:
            print(f"Starting auto-like {number_of_photos_to_be_liked} photo of user {target_user_name} ...")
        else:
            print(f"Starting auto-like {number_of_photos_to_be_liked} photos of user {target_user_name} ...")
        Hide_banners()        
        include_already_liked_photos_in_count = True
        Autolike_photos(target_user_name, int(number_of_photos_to_be_liked), include_already_liked_photos_in_count)
        Close_chrome_browser()
        choice = Show_menu()   
        continue    
    #---------------------------------------------------------------  
    # Like n photos, starting from a given index,  on either one of following photo pages:     
    # Popular, Popular Undiscovered, Upcoming Fresh, Editor's choice
    elif choice == 9:
        user_input =  Validate_input('Enter the number of photos you want to auto-like >')
        if user_input == 'q' or user_input == 'r':
            choice = user_input
            continue
        else: 
            number_of_photos_to_be_liked = int(user_input)
        
        #  avoid abusing the server
        if number_of_photos_to_be_liked > MAX_AUTO_LIKE_REQUEST: 
            number_of_photos_to_be_liked = MAX_AUTO_LIKE_REQUEST

        user_input =  Validate_input('Enter the index of the start photo (1-500) >')
        if user_input == 'q' or user_input == 'r':
            choice = user_input
            continue
        else: 
            index_of_start_photo = int(user_input)

        gallery_href, gallery_name = Show_galllery_selection_menu()
        if   gallery_href == 'q':
            sys.exit()
        elif gallery_href == 'r': 
            choice = Show_menu(); 
            continue    
        
        Start_chrome_browser()
        Login(user_name, password)
        driver.get(gallery_href)
        inner_html = driver.execute_script("return document.body.innerHTML") 
        time.sleep(5)
        Hide_banners()
        if number_of_photos_to_be_liked == 1:
            print(f"Starting auto-like {number_of_photos_to_be_liked} photo from {gallery_name} gallery, start index {index_of_start_photo}  ...")
        else:
            print(f"Starting auto-like {number_of_photos_to_be_liked} photos from {gallery_name} gallery, start index {index_of_start_photo} ...")

        Like_n_photos_on_current_page(number_of_photos_to_be_liked, index_of_start_photo)
  
        Close_chrome_browser()
        choice = Show_menu()         
        continue
    #---------------------------------------------------------------  
    # Like n photos (from top)  of each user who likes a given photo or yours
    elif choice == 10:
        # do as in option 5, get the list of users who like a given photo, but this time we need to login 
        photo_href = Validate_non_empty_input('Enter your photo href >')

        user_input =  Validate_input('Enter the number of photos you want to auto-like for each user >')
        if user_input == 'q' or user_input == 'r':
            choice = user_input
            continue
        else: 
            number_of_photos_to_be_liked = int(user_input)
        
        #  avoid abusing the server
        if number_of_photos_to_be_liked > MAX_AUTO_LIKE_REQUEST: 
            number_of_photos_to_be_liked = MAX_AUTO_LIKE_REQUEST	

        Start_chrome_browser()
        Login(user_name, password)
        try:
            driver.get(photo_href)
        except:
            printR(f'Invalid href: {photo_href}. Please retry.')
            Close_chrome_browser()
            choice = Show_menu()         
            continue

        time.sleep(1)
        Hide_banners()        
        print(f'Getting the list of users who liked this photo ...')
        like_actioners_list = Get_like_actioners_list()
        if len(like_actioners_list) == 0: 
            printG(f'The photo {photo_tilte} has no affection yet')
            choice = Show_menu()
            continue 
        actioners_count = len(like_actioners_list)
        print(f"Starting auto-like {number_of_photos_to_be_liked} photos of each of {actioners_count} users on the list ...")
        include_already_liked_photos_in_count = True  # meaning: if you want to autolike 3 first photos, and you found out two of them are already liked, then you need to like just one photo.
                                                      # if this is set to False, then you will do 3 photos, no matter what
        for i, actor in enumerate(like_actioners_list):
            print(f'User {str(i+1)}/{actioners_count}: {actor.display_name}, {actor.user_name}')
            Autolike_photos(actor.user_name, number_of_photos_to_be_liked, include_already_liked_photos_in_count)

        Close_chrome_browser()
        choice = Show_menu()
        continue
    #---------------------------------------------------------------  
    # Like n photos from your home-feed page, excluding the recommended photos from 500px
    # skip all consecutive photos of the same user
    elif choice == 11: 
        user_input =  Validate_input('Enter the number of photos you want to auto-like >')
        if user_input == 'q' or user_input == 'r':
            choice = user_input
            continue
        else: 
            number_of_photos_to_be_liked = int(user_input)
    
        #  avoid abusing the server
        if number_of_photos_to_be_liked > MAX_AUTO_LIKE_REQUEST: 
            number_of_photos_to_be_liked = MAX_AUTO_LIKE_REQUEST	   

        Start_chrome_browser()
        Login(user_name, password)
        # locate 500px icon and click on it to open the user home-feed page
        home_feed_icon = check_and_get_ele_by_xpath(driver, '//*[@id="root"]/nav/a')
        if home_feed_icon is not None:
            driver.execute_script("arguments[0].click();", home_feed_icon) 
        time.sleep(1)
        inner_html = driver.execute_script("return document.body.innerHTML")
        time.sleep(3)
        if DEBUG:
            debug_file = open(user_name + "_home_feed_innerHTML.txt", "w")
            debug_file.write(str(inner_html.encode('utf-8')))
            debug_file.close()
        Hide_banners() 
        print(f"Like {number_of_photos_to_be_liked} photos from the {user_name}'s home feed page ...")
        Like_n_photos_on_homefeed_page(number_of_photos_to_be_liked)

        Close_chrome_browser()
        choice = Show_menu()
        continue 
    #---------------------------------------------------------------  
    # Like n photos of each users in your last m notifications
    elif choice == 12:
        user_input =  Validate_input('Enter the number of photos you want to like for each user >')
        if user_input == 'q' or user_input == 'r':
            choice = user_input
            continue
        else: 
            number_of_photos_to_be_liked = int(user_input)
        
        #  avoid abusing the server
        if number_of_photos_to_be_liked > MAX_AUTO_LIKE_REQUEST: 
            number_of_photos_to_be_liked = MAX_AUTO_LIKE_REQUEST			

        user_input =  Validate_input('Enter the number of notifications you want to retrieve(max 1000) >')
        if user_input == 'q' or user_input == 'r':
            choice = user_input
            continue
        else: 
            number_of_notifications = int(user_input)
       
        if number_of_notifications > MAX_NOTIFICATION_REQUEST: 
            number_of_notifications = MAX_NOTIFICATION_REQUEST

        ## check whether option 6 or 7 have been done recently, we may be able to skip some work
        #if len(unique_notificators) > 0 and os.path.isfile(outfile) and int(intput_number) <= int(number_of_notifications):
        #    print(f' Using the existing list of users at: { os.path.abspath(outfile)} ')
        #else:

        # do as in option 6 to get the list of unique users from the last m notifications
        Start_chrome_browser()
        print(f'Getting the list of unique users in the last {number_of_notifications} notifications ...')
        Login(user_name, password)
        driver.get('https://500px.com/notifications')
        time.sleep(1)
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)      
        
        innerHtml = driver.execute_script("return document.body.innerHTML")
        time.sleep(4)       
        
        dummy_notifications, unique_notificators = Get_notification_list(True, number_of_notifications)
        if len(dummy_notifications) == 0 and len(unique_notificators) == 0:
            choice = Show_menu()
            Close_chrome_browser()
            continue
        
        include_already_liked_photo_in_count = True  # meaning: if you want to autolike 3 first photos, and you found out two of them ...
        # are already liked, then you need to like just one photo, not three. A False here means you will do 3 photos, no matter what
        Hide_banners()
        users_count = len(unique_notificators)
        print(f"Starting auto-like {number_of_photos_to_be_liked} photos of each of {users_count} users on the list ...")
        for i, item in enumerate(unique_notificators):
            name_pair = item.split(',')
            if len(name_pair) > 2: 
                print(f' User {name_pair[0]}/{users_count}: {name_pair[1]}, {name_pair[2]}')
                Autolike_photos(name_pair[2], int(number_of_photos_to_be_liked), include_already_liked_photo_in_count)
            else:
                continue
        Close_chrome_browser()
        choice = Show_menu()
        continue
    #---------------------------------------------------------------  
    # Play slideshow on a given gallery  
    # Popular, Upcoming, Fresh, Editor's choice or a spefic photo gallery
    elif choice == 13:
        gallery_href, gallery_name = Show_galllery_selection_menu()
        if   gallery_href == 'q': 
            sys.exit()
        elif gallery_href == 'r': 
            choice = Show_menu(); 
            continue

        if user_name == '':
            printY('If you want to show NSFW contents, you need to login.\n Type your user name now or just press ENTER to ignore')
            user_name = input('>')
        if user_name is not '' and password is '':
            printY('Type your password:')           
            user_input = Validate_non_empty_input('> ')
            if   user_input == 'q': 
                sys.exit()
            elif user_input == 'r': 
                choice = Show_menu();        
                continue
            else:
                password =  user_input

        time_interval = Validate_input('Enter the interval time between photos, in second>')
        printY(f'Slideshow {gallery_name} will play in fullscreen, covering this control window.\n To stop the slideshow before it ends, and return to this window, press ESC three times.\n Now press ENTER to start > ')
        wait_for_enter_key = input()
        
        #---- CHROMECAST      
        if False:
            device_friendly_name = "abcde"
            chromecasts = pychromecast.get_chromecasts()
            # select Chromecast device
            cast = next(cc for cc in chromecasts if cc.device.friendly_name == device_friendly_name)
            # wait for the device
            cast.wait()
            print(cast.device)
            print(cast.status)
            chrome_options = Options()
    
            # get list of flags selenium adds that we want to exclude
            excludeList = ['disable-default-apps', 'disable-background-networking', 'ignore-certificate-errors' ]
            chrome_options.add_experimental_option('excludeSwitches', excludeList)
            driver = webdriver.Chrome(options=chrome_options)    
            printY('DO NOT INTERACT WITH THE CHROME BROWSER. WHEN YOUR REQUEST FINISHES, IT WILL BE CLOSED')
        else:
            Start_chrome_browser(["--kiosk", "--hide-scrollbars", "--disable-infobars"]) #, "--disable-overlay-scrollbar"])

        if password is not None:
            Login(user_name, password)
        
        driver.get(gallery_href)
        dummy = driver.execute_script("return document.body.innerHTML") 
        time.sleep(2)
        Hide_banners()
 
        Play_slideshow(time_interval)  
        Close_chrome_browser()
        choice = Show_menu()         
        continue
    #---------------------------------------------------------------
    elif choice == 'r':  #restart for different user
        Reset_global_variables()
        choice = Show_menu()
        continue
    #---------------------------------------------------------------
    else: 
        choice = Show_menu()
        continue
    
sys.exit()
# END 
#======================================================================================================================



