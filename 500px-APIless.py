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

from lxml import html
import os, sys, time, re, math, csv, json,codecs
from time import sleep
from enum import Enum
#import logging
#import getpass 


PHOTOS_PER_PAGE = 50        # 500px currently loads 50 photos per page
LOADED_ITEM_PER_PAGE = 50   # it also loads 50 followers, or friends, at a time in the popup window
NOTIFICATION_PER_LOAD = 20  # currently notifications are requested to display ( by scrolling the window) 20 items at a time
MAX_NOTIFICATION_REQUESTED = 1000 # set a limit for this time-consuming process
DEBUG = False

class photo:
    def __init__(self, id, on_page, desc, link):
        self.id = id
        self.on_page = on_page
        self.desc = str(desc)
        self.link = link
class notification:
    def __init__(self, name, username, content, photo_link, photo_title, timestamp, status):
        self.name = name
        self.username = username
        self.content = content
        self.photo_link = photo_link
        self.photo_title = photo_title
        self.timestamp = timestamp
        self.status = status
    def print_screen(self):
        print(self.name + "\n" + self.username + "\n" + self.content + "\n" + self.photo_link + "\n" + self.photo_title + "\n" + self.timestamp +  "\n" + self.status )   
    def write_to_textfile():
        print(self.name + "\n" + self.username + "\n" + self.content + "\n" + self.photo_link + "\n" + self.photo_title + "\n" + self.timestamp +  "\n" + self.status )
class notificator:
    def __init__(self, name, username):
        self.name = name
        self.username = username   
    def print_screen(self):
        print(self.name + "\n" + self.username + "\n" )   
    def write_to_textfile():
        print(self.name + "\n" + self.username + "\n")
class user_stats:
    def __init__(self, name='', display_name='', id='', location='', affection_note='', following_note='', affections_count='', views_count='', 
                 followers_count='', followings_count='', photos_count='', galleries_count='', registration_date='', last_upload_date='', user_status=''):
        self.name = name
        self.display_name = display_name
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
    def __init__(self, display_name, user_name, number_of_followers):
        self.display_name = display_name
        self.user_name = user_name
        self.number_of_followers = number_of_followers
class Output_file_type(Enum):
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
# USE SELENIUM WEBDRIVER TO START CHROME, WITH VARIOUS OPTIONS
def Start_chrome_browser():
    global driver
    options = webdriver.ChromeOptions()
    # maximize window
    #options.add_argument("--start-maximized")
    driver = webdriver.Chrome(chrome_options=options)    
    #customize zoom %
    #driver.get('chrome://settings/')
    #driver.execute_script('chrome.settingsPrivate.setDefaultZoom(.80);')
    #specify window size
    #river.set_window_size(400, 600)
    #driver.maximize_window()
    printY('DO NOT INTERACT WITH THE CHROME BROWSER. WHEN YOUR REQUEST IS DONE, IT WILL CLOSED')

#---------------------------------------------------------------
# CLOSE THE CHROME BROWSER, CARE-FREE OF EXCEPTIONS
def Close_chrome_browser():
    try:
        driver.close()
    except WebDriverException:
        pass
#---------------------------------------------------------------
# WRITE USER STATISTIC OBJECT stats TO AN HTML FILE
def Create_user_statistics_html(stats):
    output = f'''
<html>\n\t<body>\n\t<table>
            <tr>                <td><b>User name</b></td>           <td>{stats.name}</td>\n</tr>         
            <tr>                <td><b>Display name</b></td>        <td>{stats.name}</td>\n</tr>
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
# WRITE THE GLOBAL VARIABLE PHOTOS LIST photos TO A GIVEN CSV FILE
# IF THE FILE IS CURRENTLY OPEN, GIVE THE USER A CHANCE TO CLOSE IT AND RE-SAVE
def Write_photos_list_to_csv(csv_file_name):
   try:
        with open(csv_file_name, 'w', encoding = 'utf-16', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer = csv.DictWriter(csv_file, fieldnames = ['No.', 'Page', 'ID', 'Title', 'Link'])  
            writer.writeheader()
            for i, photo in enumerate(photos):
                writer.writerow({'No.' : str(i + 1), 'Page': str(photo.on_page), 'ID': str(photo.id), 'Title' : str(photo.desc), 'Link' :photo.link}) 
            printG(f"User {user_name}\'s photos list is saved at:\n{os.path.abspath(csv_file_name)}")
        return True

   except PermissionError:
        retry = input(f'Error writing file {os.path.abspath(csv_file_name)}.\nMake sure the file is not in use. Then type r for retry >')
        if retry == 'r': 
            Write_photos_list_to_csv(csv_file_name)
        else:
            printR('Error witing file' + os.path.abspath(csv_file_name))
            return False

#---------------------------------------------------------------
# WRITE A GIVEN USER LIST users_list TO A GIVEN CSV FILE
# IF THE FILE IS CURRENTLY OPEN, GIVE THE USER A CHANCE TO CLOSE IT AND RE-SAVE
def Write_users_list_to_csv(csv_file_name, users_list):
   try:
        with open(csv_file_name, 'w', encoding = 'utf-16', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer = csv.DictWriter(csv_file, fieldnames = ['Display Name', 'User Name', 'Number Of Followers'])  
            writer.writeheader()
            for a_user in users_list:
                writer.writerow({'Display Name' : a_user.display_name, 'User Name': a_user.user_name, 'Number Of Followers': a_user.number_of_followers}) 
        printG('The users list is saved at:\n ' + os.path.abspath(csv_file_name) )
        return True
   except PermissionError:
        retry = input(f'Error writing to file {csv_file_name}. Make sure the file is not in use. Then type r for retry >')
        if retry == 'r': 
            Write_photos_list_to_csv(csv_file_name,user_list)
        else:
            printG('Error writing file\n' + os.path.abspath(csv_file_name))
            return False 

#---------------------------------------------------------------
# WRITE THE GLOBAL VARIABLE LIST notifications TO A GIVEN CSV FILE
# IF THE FILE IS CURRENTLY OPEN, GIVE THE USER A CHANCE TO CLOSE IT AND RE-SAVE
def Write_notifications_to_csvfile(csv_file_name):
    try:
        with open(csv_file_name, 'w', encoding = 'utf-16', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer = csv.DictWriter(csv_file, fieldnames = ['Name', 'User Name', 'Content', 'Photo Title', 'Time Stamp', 'Status'])    
            writer.writeheader()
            for notif in notifications:
                writer.writerow({'Name' : notif.name, 'User Name': notif.username, 'Content': notif.content, 'Photo Title' : notif.photo_title, 'Time Stamp' : notif.timestamp, 'Status' : notif.status}) 
        printG('Notifications list is saved at:\n ' + os.path.abspath(csv_file_name))
        return True 
    except PermissionError:
        retry = input(f'Error writing to file {csv_file_name}.\n Make sure the file is not in use, then type r for retry >')
        if retry == 'r':  
            Write_notifications_to_csvfile(csv_file_name)
        else: 
            printR(f'Error writing file {csv_file_name}')
            return False
#---------------------------------------------------------------
# WRITE THE GLOBAL VARIABLE LIST unique_notificators TO A GIVEN CSV FILE
# IF THE FILE IS CURRENTLY OPEN, GIVE THE USER A CHANCE TO CLOSE IT AND RE-SAVE
def Write_unique_notificators_list_to_csv(csv_file_name):
    try:
        with open(csv_file_name, 'w', encoding = 'utf-16', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer = csv.DictWriter(csv_file, fieldnames = ['Name', 'User Name'])  
            writer.writeheader()

            for actor in unique_notificators:
                items = actor.split(',')
                if len(items) == 2:
                    writer.writerow({'Name' : items[0], 'User Name': items[1]}) 
            printG('Unique notificators is saved at:\n' + os.path.abspath(csv_file_name))
            return True 

    except PermissionError:
        retry = input(f'Error writing to file {csv_file_name}. Make sure the file is not in use. Then type r for retry >')
        if retry == 'r': 
            Write_unique_notificators_list_to_csv(csv_file_name)
        else: 
            printR(f'Error writing file {csv_file_name}')
            return False

#---------------------------------------------------------------
# HOVER THE MOUSE ON AN ELEMENT SPECIFIED BY THE GIVEN XPATH.
def Hover_element_by_its_xpath(xpath):
    element = driver.find_element_by_xpath(xpath)
    hov = ActionChains(driver).move_to_element (element)
    hov.perform()

#---------------------------------------------------------------
# HOVER THE MOUSE OVER A GIVEN ELEMENT 
def Hover_by_element(element):
    hov = ActionChains(driver).move_to_element (element)
    hov.perform()

#---------------------------------------------------------------
# RETURN THE TEXT OF ELEMENT, SPECIFIED BY THE ELEMENT XPATH
def Get_element_text_by_xpath(page, xpath_string):
    ele = page.xpath(xpath_string)
    if len(ele) > 0 : return ele[0].text
    return ''

#---------------------------------------------------------------
# RETURN THE ATTRIBUTE CONTAIN OF A ELEMENT, SPECIFIED BY THE ELEMENT XPATH
def Get_element_attribute_by_ele_xpath(page, xpath, attribute_name):
    ele = page.xpath(xpath)
    if len(ele) > 0:
        return ele[0].attrib[attribute_name] 
    return ''
#---------------------------------------------------------------
# FIND THE WEB ELEMENT FROM A GIVEN XPATH, RETURN NONE IF NOT FOUND
# THE SEARCH CAN BE LIMITED WITHIN A GIVEN WEB ELEMENT, OR THE WHOLE DOCUMENT, BY PASSING THE BROWSER DRIVER
def check_and_get_ele_by_xpath(element, xpath):
    try:
        return element.find_element_by_xpath(xpath)
    except NoSuchElementException:
        return None
    return web_ele

#---------------------------------------------------------------
# FIND THE WEB ELEMENT OF A GIVEN CLASS NAME, RETURN NONE IF NOT FOUND
# THE SEARCH CAN BE LIMITED WITHIN A GIVEN WEB ELEMENT, OR THE WHOLE DOCUMENT, BY PASSING THE BROWSER DRIVER
def check_and_get_ele_by_class_name(element, class_name):
    try:
        return element.find_element_by_class_name(class_name) 
    except NoSuchElementException:
        return None
    return web_ele

#---------------------------------------------------------------
# FIND THE WEB ELEMENT OF A GIVEN CSS SELECTOR, RETURN NONE IF NOT FOUND
# THE SEARCH CAN BE LIMITED WITHIN A GIVEN WEB ELEMENT, OR THE WHOLE DOCUMENT USING THE BROWSER DRIVER
def check_and_get_ele_by_css_selector(element, selector):
    try:
        return element.find_element_by_css_selector(selector)
    except NoSuchElementException:
        return None
    return web_ele

#---------------------------------------------------------------
# GIVEN A PHOTO LINK, RETURNS THE DATE OR TIME THAT PHOTO WAS UPLOADED
def GetUploadDate(photo_link):
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
# OPEN THE HOME PAGE OF A GIVEN USER.  RETURN TRUE IF THE PAGE OPENS SUCCESSFULLY
# IF THE USER PAGE IS NOT FOUND, PRINT ERROR AND RETURN FALSE
def Open_user_home_page(user_name):
    driver.get('https://500px.com/' + user_name)
    # waiting until the page is opened
    main_window_handle = None
    while not main_window_handle:
        main_window_handle = driver.current_window_handle
    if check_and_get_ele_by_class_name(driver, 'missing') is None:
        return True
    else:
        printR('Page not found for user ' + user_name)
        return False

#---------------------------------------------------------------
# GET STATISTICS OF A GIVEN USER: NUMBER OF LIKES, VIEWS, FOLLOWERS, FOLLOWING, PHOTOS; AND  FIRST, LAST UPLOAD DATE
# IF include_photos_list IS TRUE, GET THE LIST OF PHOTOS (ID, TITLE, LINK...) AND SAVED TO A CSV FILE
# PROCESS: OPEN USER HOME PAGE, SCROLL DOWN UNTIL ALL PHOTOS ARE LOADED
def Get_stats(user_name):
    global photo, user_stats, stats, user_id
    if Open_user_home_page(user_name) == False:
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

    #extract json part in the javascript-rendered html that holds user data 
    #start_mark = '"userdata":'
    #end_mark   = ',"viewer":'
    #start_index = innerHtml.find(start_mark) + len(start_mark)
    #end_index = innerHtml.find(end_mark)
    #wanted_string = innerHtml[start_index:end_index:1]
    #json_data = json.loads(wanted_string)

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

    stats = user_stats(user_name, json_data['fullname'], user_id, location, 
                       affection_note, following_note, json_data['affection'], views_count, json_data['followers_count'], json_data['friends_count'], 
                       json_data['photos_count'], json_data['galleries_count'], json_data['registration_date'][:10], last_upload_date, user_status)
    return json_data, stats
      
#---------------------------------------------------------------
# RETURN THE PHOTOS LIST OF A GIVEN USER: NUMBER OF LIKES, VIEWS, FOLLOWERS, FOLLOWING, PHOTOS; AND  FIRST, LAST UPLOAD DATE
# PROCESS: 
# - OPEN USER HOME PAGE, SCROLL DOWN UNTIL ALL PHOTOS ARE LOADED
# - MAKE SURE THE DOCUMENT JAVASCRIPT IS CALLED TO GET THE FULL CONTAIN OF THE PAGE
# - EXTRACT THE user_data, the json section that contains all the photos data
def Get_photos_list(user_name):
    global photo, user_id

    if Open_user_home_page(user_name) == False:
        return None
    Scroll_down(1.5, -1) # scroll down until end, pause 1.5s between scrolls, 
    innerHtml = driver.execute_script("return document.body.innerHTML") #run JS body scrip after page content is loaded
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

    # by some unknown reason the json.loads() method just loads the first 50 photos, 
    # for now we have to use the traditional way (parsing the xml by using lxml) 

    #photos count
    photos_count_str = Get_element_text_by_xpath(page,'//*[@id="content"]/div[3]/div/ul/li[1]/a/span')
    photos_count = int( photos_count_str.replace('.', '').replace(',', ''))
    #extract photo ids and descriptions (alt tag) using lxml and regex. put them to a list
    els = page.xpath("//a[@class='photo_link ']")
    titles = page.xpath("//img[@data-src='']")
    num_item = len(els)
    if num_item == 0:
        printR(f'User {user_name} does not upload any photo')
        return None

    # Create list of photos
    for i in range(num_item): 
        reg = "/photo/([0-9]*)/"  
        photoId = re.findall(reg, els[i].attrib["href"])
        if len(photoId) != 0:
            pId = photoId[0] 
        else:
            pId = 0
        on_page = math.floor(i / PHOTOS_PER_PAGE ) + 1
        link = f"https://500px.com{els[i].attrib['href']}?ctx_page={on_page}&from=user&user_id={user_id}"

        new_photo = photo(pId, on_page, str(titles[i].attrib["alt"]), link)
        photos.append(new_photo)
 
    return photos

#---------------------------------------------------------------
# GIVEN A USER NAME, RETURN THE LIST OF FOLLOWERS, THE LINK TO THEIS PAGES AND THE NUMBER OF FOLLOWERS OF EACH OF THEM
# PROCESS:
# - OPEN THE USER HOME PAGE, LOCATE THE TEXT followers AND CLICK ON IT TO OPEN THE MODAL WINDONW CONTAINING FOLLOWERS LIST
# - SCROLL TO THE END FOR ALL ITEMS TO BE LOADED
# - MAKE SURE THE DOCUMENT JS IS RUNNING FOR ALL THE DATA TO LOAD IN THE PAGE BODY
# - EXTRACT INFO AND PUT IN A LIST. RETURN THE LIST
def Get_followers_list(user_name):
    global user
    followers_list = []
    if Open_user_home_page(user_name) == False:
        choice = Show_menu(False)
        return None

    # click on the Followers text to open the modal window
    driver.find_element_by_class_name("followers").click()
    time.sleep(2)

    # extract number of followers                 
    followers_ele = check_and_get_ele_by_xpath(driver, '//*[@id="modal_content"]/div/div/div/div/div[1]/span')
    if followers_ele is None:
        return None
    # remode thousand separator character, if existed
    followers_count = int(followers_ele.text.replace(",", "").replace(".", ""))

    # keep scrolling the modal window, 50 followers at a time, until the end, where the followers count is reached 
    iteration_num = math.floor(followers_count / LOADED_ITEM_PER_PAGE) + 1 
    for i in range(1, iteration_num):
        last_item_on_page = i * LOADED_ITEM_PER_PAGE - 1
        try:
            the_last_in_list = driver.find_elements_by_xpath('//*[@id="modal_content"]/div/div/div/div/div[2]/ul/li[' + str(last_item_on_page) + ']')[-1]
            the_last_in_list.location_once_scrolled_into_view
            time.sleep(3)
        except NoSuchElementException:
            pass

    # now that we have all followers loaded, start extracting the info
    innerHTML = driver.execute_script("return document.body.innerHTML") #run JS body scrip after all photos are loaded
    time.sleep(5)
    if True: #DEBUG
        Write_string_to_text_file(str(innerHTML.encode('utf-8')), user_name + '_followers_innerHTML.txt')

    actor_infos = driver.find_elements_by_class_name('actor_info')
    lenght = len(actor_infos)
    printG(f'User {user_name} has {str(lenght)} follower(s)')
    #printG('............')

    follower_name = ''
    follower_page_link = ''
    count = ' '

    for actor in actor_infos:
        try:
            follower_page_link = actor.find_element_by_class_name('name').get_attribute('href')
            follower_user_name = follower_page_link.replace('https://500px.com/', '')
        except NoSuchElementException:
            continue  #ignore if follower name not found

        texts = actor.text.split('\n')
        if len(texts) > 0: follower_name = texts[0] 
        if len(texts) > 1: count = texts[1]; number_of_followers =  count.replace(' followers', '').replace(' follower', '') 
        followers_list.append(user(follower_name, follower_user_name, number_of_followers))

    return  followers_list 

#---------------------------------------------------------------
# GET THE LIST OF FOLLOWINGS, THE LINK TO THEIS PAGES AND THE NUMBER OF FOLLOWERS OF EACH OF THEM
# PROCESS:
# - OPEN THE USER HOME PAGE, LOCATE THE TEXT followers AND CLICK ON IT TO OPEN THE MODAL WINDONW CONTAINING FOLLOWERS LIST
# - SCROLL TO THE END FOR ALL ITEMS TO BE LOADED
# - MAKE SURE THE DOCUMENT JS IS RUNNING FOR ALL THE DATA TO LOAD IN THE PAGE BODY
# - EXTRACT INFO AND PUT IN A LIST. RETURN THE LIST
def Get_followings_list(user_name):
    global user
    followings_list = []
    if Open_user_home_page(user_name) == False:
        choice = Restart_menu(True)
        return

    # click on the Following text to open the modal window
    driver.find_element_by_xpath('//*[@id="content"]/div[2]/div[4]/ul/li[4]').click()  # not working: driver.find_element_by_class_name("following").click()     
    time.sleep(2)
      
    # extract number of following
    following_ele = check_and_get_ele_by_xpath(driver, '//*[@id="content"]/div[2]/div[4]/ul/li[4]/span') 
    if following_ele is None:
        return None

    # remode thousand separator character, if existed
    following_count = int(following_ele.text.replace(",", "").replace(".", ""))

    # keep scrolling the modal window, 50 followers at a time, until the end, where the followers count is reached 
    iteration_num = math.floor(following_count / LOADED_ITEM_PER_PAGE) + 1 
    for i in range(1, iteration_num):
        last_item_on_page = i * LOADED_ITEM_PER_PAGE - 1
        try:
            the_last_in_list = driver.find_elements_by_xpath('//*[@id="modal_content"]/div/div/div/div/div[2]/ul/li[' + str(last_item_on_page) + ']')[-1]                                                             
            the_last_in_list.location_once_scrolled_into_view
            time.sleep(3)
        except NoSuchElementException:
            pass

    # now that we have all followers loaded, start extracting info
    actor_infos = driver.find_elements_by_class_name('actor_info')
    lenght = len(actor_infos)
    printG(f'User {user_name} is following { str(lenght)} user(s)')
    following_name = ''
    followings_page_link = ''
    count = '' 

    for actor in actor_infos:
        try:
            following_page_link = actor.find_element_by_class_name('name').get_attribute('href')
            following_user_name = following_page_link.replace('https://500px.com/', '')

        except NoSuchElementException:
            continue  #ignore if follower name not found

        texts = actor.text.split('\n')
        if len(texts) > 0: following_name = texts[0] 
        if len(texts) > 1: count = texts[1]; number_of_followings =  count.replace(' followers', '').replace(' follower', '')  
        followings_list.append(user(following_name, following_user_name, number_of_followings))

    return followings_list 

#---------------------------------------------------------------
# GET N LAST NOTIFICATIONS. 
# A DETAILED NOTIFICATION ITEM CONTAINS FULL_NAME, USER NAME, THE CONTENT OF THE NOTIFICATION, TITLE OF THE PHOTO IN QUESTION, THE TIME STAMP AND A STATUS
# A SHORT NOTIFICATION ITEM CONTAINS JUST FULL NAME AND USER NAME
# A UNIQUE NOTIFICATION LIST IS A SHORT NOTIFICATION LIST WHERE ALL THE DUPLICATION ARE REMOVED.
#
# IF THE GIVEN get_full_detail IS TRUE, RETURN THE DETAILED LIST, IF FALSE, RETURN THE UNIQUE LIST
# PROCESS:
# - EXPECTING THE ACTIVE PAGE IN THE BROWSER IS THE USER HOME PAGE
# - LOCATE THE CORRECT NOTIFICATION ICON AND CLICK ON IT TO OPEN THE MODAL WINDOW HOSTING THE NOTIFICATION ITEMS
# - LOCATE THE TEXT See all notifications AND CLICK ON IT TO OPEN THE NEW PAGE CONTAINING ALL THE NOTIFICATION ITEMS
# - SCROLL DOWN  N TIMES, CALCULATED BY THE GIVEN number_of_notifications, FOR ALL REQUIRED ITEMS TO BE LOADED 
# - EXTRACT INFO, RETURN THE FULL LIST OF A UNIQUE LIST DEPENTING ON THE REQUEST
def Get_notification_list(get_full_detail = True, number_of_notifications = MAX_NOTIFICATION_REQUESTED):
    global notification, notificator, unique_notificators

    notifications_list = []
    short_list = []
    # find the correct Notification icon and click it to open the modal window, where the notifications are loaded, 20 items at a time
    # there are 2 overlapped icons. If there exist an active notification, clickable item is 'number icon', otherwise it is 'bell icon'
    number_icon =  check_and_get_ele_by_xpath(driver, '//*[@id="nav_notifications"]/span[1]')    #number_icon =  driver.find_element_by_xpath('//*[@id="nav_notifications"]/span[1]')
    bell_icon = check_and_get_ele_by_xpath(driver, '//*[@id="nav_notifications"]/span[2]') #driver.find_element_by_xpath('//*[@id="nav_notifications"]/span[2]')
    
    if number_icon is None and bell_icon is None:
        printR('Error processing. Please retry, making sure your credentials are correct. ')
        return [], []

    # WORK-AROUND: SCROLL DOWN ONE TIME(already perform prior to calling this function) AND SEND CTRL-HOME TO GO BACK TO TOP OF THE PAGE
    #driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.HOME)
    #time.sleep(5)
 
    if not number_icon.text:
        driver.execute_script("arguments[0].click();", bell_icon) #bell_icon.click()
    else:
        driver.execute_script("arguments[0].click();", number_icon) #number_icon.click()
    
    main_window = driver.window_handles[0]

    # Find "See all notifications" text and click it
    see_all_button = driver.find_element_by_xpath('//*[@id="popup_notifications"]/div[2]/div/a')
    driver.execute_script("arguments[0].click();", see_all_button)

    all_windows_handles = driver.window_handles
    if len(all_windows_handles) > 1:
        driver.switch_to_window(all_windows_handles[1])

    if number_of_notifications == -1: # secret switch: -1 for requesting all available notifications from server (could be time-consuming process)
        scrolls_needed = -1
    else:                             # Notifications are loaded 20 items at a time. Ex. to get 80 items we need to scroll 4 times 
        scrolls_needed =  math.floor(number_of_notifications / NOTIFICATION_PER_LOAD) +1

    pause_between_scrolls = 1.5
    Scroll_down(pause_between_scrolls, scrolls_needed ) 

    # get the info now that all the needed notifications are loaded
    items = driver.find_elements_by_class_name('notification_item')  #notification_item__text   notification_item__actor  notification_item__content
    count = len(items)                                                                #notification_item
    for i, item in enumerate(items):
        if number_of_notifications != -1 and i >=  number_of_notifications:
            break

        actor = check_and_get_ele_by_class_name(item, 'notification_item__actor') 
        if actor is None:
            continue
        display_name = actor.text
        code_name = actor.get_attribute('href').replace('https://500px.com/', '')
        if get_full_detail:
            item_text = item.find_element_by_class_name('notification_item__text')
            if item_text.text.find('liked') != -1: content = 'liked'
            elif item_text.text.find('followed') != -1: content = 'followed'
            elif item_text.text.find('added') != -1: content = 'added to gallery'
            elif item_text.text.find('commented') != -1: content = 'commented'
            else: content = item_text.text

            photo_ele = check_and_get_ele_by_class_name(item_text, 'notification_item__photo_link')
            photo_title = ''
            photo_link = ''        
            status = ''
            # in case of a new follow, instead of a photo, there will be 2 overlapping boxex, Follow and Following. We will determine if whether or not this actor has been followered  
            if photo_ele is None:
                follow_box = check_and_get_ele_by_css_selector(item, '.button.follow.mini_button')     
                following_box = check_and_get_ele_by_css_selector(item, 'button.following.mini_button')
                if follow_box is not None and follow_box.is_displayed(): 
                    status = 'you followed' 
                elif following_box is not None and following_box.is_displayed():
                    status = 'you did not follow'        
                #print(status)
            else: 
                photo_title = photo_ele.text
                photo_link = photo_ele.get_attribute('href') 
        
            timestamp = item.find_element_by_class_name('notification_item__timestamp').text
            notifications_list.append(notification(display_name, code_name, content, photo_link, photo_title, timestamp, status))                  

        short_list.append(f'{display_name},{code_name}')
        
    unique_notificators = remove_duplicates(short_list)
    if len(notifications_list) == 0 and len(unique_notificators) == 0: 
        printG(f'User {user_name} has no notification')
   
    return notifications_list, unique_notificators

#---------------------------------------------------------------
# GET THE LIST OF USERS WHO LIKED A GIVEN PHOTO.
# PROCESS:
# - EXPECTING THE ACTIVE PAGE IN THE BROWSER IS THE GIVEN PHOTO PAGE
# - FORCE THE DOCUMENT JS TO RUN TO FILL THE PAGE BODY
# - EXTRACT PHOTO TITLE AND PHOTOGRAPHER NAME
# - LOCATE THE LIKE COUNT NUMBER THEN CLICK ON IT TO OPEN THE MODAL WINDOW HOSTING THE LIST OF ACTIONER USER
# - SCROLL DOWN TO THE END AND EXTRACT RELEVANT INFO, PUT ALL TO THE LIST AND RETURN IT
def Get_like_actioners_list():
    global user, like_actioners_file_name
    actioners_list = []

    innerHtml = driver.execute_script("return document.body.innerHTML") #run JS body scrip after page content is loaded
    time.sleep(3)

    owner_ele = check_and_get_ele_by_xpath(driver, '//*[@id="content"]/div/div/div[2]/div/div[1]/div[2]/div[1]/a')
    owner = owner_ele.text
    printG(f'Photogapher: {owner}')

    # make sure the  photo title is visible
    parent_6 = owner_ele.find_element_by_xpath('../../../../../..')
    parent_6.location_once_scrolled_into_view
    # extract photo title                      
    title_ele = parent_6.find_element_by_tag_name('h3')
    if title_ele is not None: 
        title = title_ele.text
        printG(f'Photo title: {title}')
 
    # find the like-count element and click on it  to open the modal window
    like_count_button = check_and_get_ele_by_xpath(driver, '//*[@id="content"]/div/div/div[2]/div/div[1]/div[1]/div[1]/a') #'//*[@id="modal_content"]/div/div/div[2]/div/div[1]/div[1]/div[1]/a') #
    if like_count_button is None:                           
        printR('Error getting like_actioners list')
        return actioners_list
    else:
        driver.execute_script("arguments[0].click();", like_count_button)
        time.sleep(3)   

    # extract number of likes ( on the newly-opened model window)                 
    likes_ele = check_and_get_ele_by_xpath(driver, '//*[@id="rcDialogTitle0"]/h4[2]')  #//*[@id="rcDialogTitle0"]  //*[@id="rcDialogTitle0"]/h4[2]
    if likes_ele is None :
        printR('Error getting like_actioners list')
        return actioners_list

    elif likes_ele.text == '0':
        printG('This photo currently has zero like')
        return actioners_list

    likes_count = re.sub('[^\d]+', '', likes_ele.text)         
    printG(f'This photo has {likes_count} like(s)')
  
    like_actioners_file_name = f"{owner.replace(' ', '-')}_{title.replace(' ', '-')}_{likes_count}_ like_actioners.csv"

    # scroll to the end for all elements of the given class name to load
    Scroll_to_end_by_class_name('ifsGet')
        
    actioners = driver.find_elements_by_class_name('ifsGet')
    for actioner in actioners:
        try:    
            texts = actioner.text.split('\n')
            if len(texts) > 0: 
                display_name = texts[0] 
            if len(texts) > 1:
                followers_count  = re.sub('[^\d]+', '', texts[1]) 
            name = actioner.find_element_by_tag_name('a').get_attribute('href').replace('https://500px.com/','')
            actioners_list.append(user(display_name, name, str(followers_count)) )
        except NoSuchElementException:
            continue 

    return actioners_list 
#---------------------------------------------------------------
# LIKE N PHOTO OF A GIVEN USER, STARTING FROM THE TOP
# IF THE include_already_liked_photo IS TRUE, THE ALREADY-LIKED PHOTO WILL BE COUNTED AS DONE BY THE AUTO-LIKE PROCESS
# FOR EXAMPLE, IF YOU NEED TO AUTO-LIKE 3 PHOTOS FROM A USER, BUT THE FIRST TWO ARE ALREADY LIKED, THEN YOU ONLY NEED TO DO ONE
# IF THE include_already_liked_photo_in_count IS FALSE (DEFAULT), THE PROCESS WILL AUTO-LIKE THE EXACT NUMBER REQUESTED
# PROCESS:
# - OPEN THE USER HOME PAGE
# - FORCE DOCUMENT JS TO RUN TO FILL THE VISIBLE BODY
# - LOCATE THE FIRST PHOTO, CHECK IF IT IS ALREADY-LIKED OR NOT, IF YES, GO THE NEXT PHOTO, IT NO, CLICK ON IT TO LIKE THE PHOTO
# - CONTINUE UNTIL THE ASKING NUMBER OF PHOTOS IS REACHED. 
# - WHEN WE HAVE PROCESSED ALL THE LOADED PHOTOS BUT THE REQUIRED NUMBER IS NOT REACHED YET, 
#   ... SCROLL DOWN ONCE TO LOAD MORE PHOTOS ( CURRENTLY 500PX LOADS 50 PHOTOS AT A TIME) AND REPEAT THE STEPS UNTIL DONE
def Autolike_photos(target_user_name, number_of_photos_to_be_liked, include_already_liked_photo_in_count = True):
    if Open_user_home_page(target_user_name) == False:
        return

    innerHtml = driver.execute_script("return document.body.innerHTML") #run JS body scrip after page content is loaded
    time.sleep(3)
    
    new_fav_icons =  driver.find_elements_by_css_selector('.button.new_fav.only_icon')
    if len(new_fav_icons) == 0:
        printY('  - user has no photos')
    # available_icons = len(new_fav_icons)
    done_count = 0

    for i, icon in enumerate(new_fav_icons):
       # skip already-liked photo. Count it as done if requested so
        if done_count < number_of_photos_to_be_liked and 'heart' in icon.get_attribute('class'): 
            if include_already_liked_photo_in_count == True:
                done_count = done_count + 1          
            #printY(f'User {target_user_name:25} liked #{str(done_count):3} Photo { str(i):3} already liked')
            printY(f'  - liked #{str(done_count):3} Photo { str(i):3} already liked')

            continue        

        # check limit
        if done_count >= number_of_photos_to_be_liked:  
            break
        
        Hover_by_element(icon) # not neccessary, but good for visual demonstration
        try:
            # slowing  down a bit to make it look more like human
            time.sleep(1)
            title =  icon.find_element_by_xpath('../../../../..').find_element_by_class_name('photo_link').find_element_by_tag_name('img').get_attribute('alt')
            driver.execute_script("arguments[0].click();", icon) 
            done_count = done_count + 1
            printG(f'  - liked #{str(done_count):3} Photo {str(i + 1):3} title {title:.50}')

        except Exception as e:
            printR(f'Error after {str(done_count)}, at index {str(i)}, title {title}:\nException: {e}')

#---------------------------------------------------------------
# LIKE N PHOTOS ON THE ACTIVE PHOTO PAGE. IT COULD BE EITHER POPULAR, POPULAR-UNDISCOVERED, UPCOMING, FRESH OR EDITOR'S CHOICE PAGE
# THIS WILL AUTOMATICALLY SCROLL DOWN IF MORE PHOTOS ARE NEEDED
# PROCESS:
# - SIMILAR TO THE PREVIOUS METHOD ( Autolike_photos() )
def Like_n_photos_on_current_page(number_of_photos_to_be_liked, index_of_start_photo):
    if True: # new impl: dynamic scrolling 
        photos_done = 0
        current_index = 0  # the index of the photo in the loaded photos list. We dynamically scroll down the page to load more photos as we go, so ...
                            # ... we use this index to keep track where we are after a list update 
            
        # debug info: without scrolling, it would load 50 photos or so
        new_fav_icons =  driver.find_elements_by_css_selector('.button.new_fav.only_icon')
        loaded_photos_count = len(new_fav_icons)
            
        while photos_done < number_of_photos_to_be_liked: 
            # if we have processed all loaded photos, if yes, scroll down 1 time for more to load
            if current_index >= loaded_photos_count: 
                prev_loaded_photos = loaded_photos_count
                Scroll_down(1, 1)
                time.sleep(2)
                new_fav_icons =  driver.find_elements_by_css_selector('.button.new_fav.only_icon')
                loaded_photos_count = len(new_fav_icons)

                # stop when all photos are loaded
                if loaded_photos_count == prev_loaded_photos:
                    break;

            #for i, icon in enumerate(new_fav_icons):
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
                    time.sleep(1.5)
                    title =  icon.find_element_by_xpath('../../../../..').find_element_by_class_name('photo_link').find_element_by_tag_name('img').get_attribute('alt')
                    photographer = icon.find_element_by_xpath('../../../..').find_element_by_class_name('photographer').text
                    driver.execute_script("arguments[0].click();", icon) 
                    photos_done = photos_done + 1
                    printG(f'Like #{str(photos_done):<3}, {photographer:<28.24}, Photo {str(i+1):<4} title {title:<35.35}')
                except Exception as e:
                    printR(f'Error after {str(photos_done)}, at index {str(i+1)}, title {title}:\nException: {e}')

    else:  # old implementation, skept for referenc purpose
           # based on user request, estimate how many times we need to scroll down to get all the needed photos to load.
           # this approach is flawed: there will be photos that are already-liked and we will skip them, and we don't know beforehand how many of them. We may come up short.
        number_of_photos_need_to_be_loaded = index_of_start_photo + number_of_photos_to_be_liked
        if number_of_photos_need_to_be_loaded <= PHOTOS_PER_PAGE:
            number_of_scroll_required = 0
        else:
            number_of_scroll_required = math.floor(number_of_photos_need_to_be_loaded / PHOTOS_PER_PAGE) + 1 # 10 extra scrolls (500 photos) are added to compensate for skipped photos 
        Scroll_down(1, number_of_scroll_required)
        new_fav_icons =  driver.find_elements_by_css_selector('.button.new_fav.only_icon')
        # available_icons = len(new_fav_icons)
        photos_done = 0
        for i, icon in enumerate(new_fav_icons):
            # stop when limit reaches
            if photos_done >= number_of_photos_to_be_liked:  
                break            
            # skip un-interested items  
            if i < index_of_start_photo - 1 :
                continue
 
            # skip already liked photo: 'liked' class is a subclass of 'new_fav_only_icon', so these elements are also included in the list
            if 'heart' in icon.get_attribute('class'): 
                continue
            Hover_by_element(icon) # not required, but good for visual demonstration
            time.sleep(0.5)
            try:
                # might want to slow down a bit to make it look more like human
                time.sleep(1.5)
                title =  icon.find_element_by_xpath('../../../../..').find_element_by_class_name('photo_link').find_element_by_tag_name('img').get_attribute('alt')
                photographer = icon.find_element_by_xpath('../../../..').find_element_by_class_name('photographer').text
                driver.execute_script("arguments[0].click();", icon) 
                photos_done = photos_done + 1
                printG(f'Like #{str(photos_done):<3}, {photographer:<30.28}, Photo {str(i+1):<4} title {title:<40.40}')
            except Exception as e:
                printR(f'Error after {str(photos_done)}, at index {str(i+1)}, title {title}:\nException: {e}')

        printG(f'{str(number_of_photos_to_be_liked)} photos from popular-undiscover photos list have been auto-liked, started from index {index_of_start_photo}')
    # end old impl

#---------------------------------------------------------------
# LIKE N PHOTOS FROM THE USER'S HOME FEED PAGE, EXCLUDING RECOMMENDED PHOTOS
# SKIP CONSECUTIVE PHOTO(S) OF THE SAME USER
# PROCESS:
# - EXPECTING THE USER HOME FEED PAGE IS THE ACTIVE PAGE IN THE BROWSER
# - GET THE LIST ELEMENTS REPRESENTING LOADED INTERESTED PHOTOS (THE ONES FROM PHOTOGRAPHERS THAT YOU ARE FOLLOWING)
# - FOR EACH ELEMENT IN THE LIST, TRAVERSE UP, DOWN THE XML TREE FOR PHOTO TITLE, OWNER NAME, LIKE STATUS, AND MAKE A DECISION TO CLICK THE LIKE ICON OR NOT
# - CONTINUE UNTIL THE REQUIRED NUMBER IS REACHED. ALONG THE WAY, STOP AND SCROLL DOWN TO LOAD MORE PHOTOS WHEN NEEDED 
def Like_n_photos_on_homefeed_page(number_of_photos_to_be_liked):
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
            print(f'Scrolling down to load more photos ...')
            prev_loaded_photos = loaded_photos_count
            Scroll_down(1, 1)
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
                
            # check to see if this is your own photo
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
                printB(f'Skipped  : photo {str(i + 1):<3}, from {photographer_display_name:<32.30}, {title:<35.35}')
                continue

            Hover_by_element(heart_icon)
            if  not photo_already_liked:      
                # skip consecutive photos of the same photographer
                if photographer_name == prev_photographer_name:
                    printY(f'Skipped  : photo {str(i + 1):<3}, from {photographer_display_name:<32.30}, {title:<35.35}')
                    continue
                if heart_icon is not None:
                    driver.execute_script("arguments[0].click();", heart_icon) 
                    photos_done += 1
                    prev_photographer_name = photographer_name
                    printG(f'Like #{photos_done:<3}: photo {str(i + 1):<3}, from {photographer_display_name:<32.30}, {title:<40.40}')
                    time.sleep(1.5)  # slow down a bit to make it look more like a human

#---------------------------------------------------------------
# GIVEN A LIST CONTAINING THE PAIRS OF DISPLAY NAME AND USER NAME,
# RETURN THE LIST THAT HAS NO DUPLICATION PAIR IN IT
def remove_duplicates(values):
    output = []
    seen = set()
    for value in values:
        # If value has not been encountered yet,
        # ... add it to both list and set.
        if value not in seen:
            output.append(value)
            seen.add(value)
    return output    

#---------------------------------------------------------------
# SCROLLING DOWN THE ACTIVE WINDOW IN A CONTROLLABLE FASHION
# PASSING THE scroll_pause_time ACCORDING TO THE CONTENT OF THE PAGE, TO MAKE SURE ALL ITEMS ARE LOADED BEFORE THE NEXT SCROLL. DEFAULT IS 0.5s
# THE PAGE COULD HAVE A VERY LONG LIST, OR ALMOST INFINITY, SO BY DEFAULT WE LIMIT IT TO 10 TIMES.
# PASSING -1 to iteration_limit WILL SCROLL UNLIMITEDLY UNTIL THE END IS REACHED
# PASSING 0 WILL RESULT IN NO SCROLLING AT ALL
def Scroll_down(scroll_pause_time = 0.5, iteration_limit = 10):
    if iteration_limit == 0 :
        return
    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")
    iteration_count = 0
    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # Wait to load page
        time.sleep(scroll_pause_time)
        innerHTML = driver.execute_script("return document.body.innerHTML") #run JS body scrip after all photos are loaded

        if iteration_limit != -1:
            iteration_count = iteration_count + 1
            if iteration_count >= iteration_limit:
                break

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    
    time.sleep(scroll_pause_time)

#---------------------------------------------------------------
# SCROLL THE ACTIVE WINDOW TO THE END, WHERE THE LAST ELEMENT OF THE GIVEN CLASS NAME BECOME VISIBLE
def Scroll_to_end_by_class_name(class_name):
        eles = driver.find_elements_by_class_name('ifsGet')
        count = 0
        new_count = len(eles)
        while new_count != count:
            try:
                the_last_in_list = eles[new_count - 1]
                the_last_in_list.location_once_scrolled_into_view 
                time.sleep(1)
                WebDriverWait(driver, 5).until(EC.visibility_of(the_last_in_list))
                count = new_count
                eles = driver.find_elements_by_class_name('ifsGet')
                new_count = len(eles)
            except NoSuchElementException:
                pass

#---------------------------------------------------------------
# READ CREDENTIALS FROM USER INPUT AND SUBMIT TO THE 500PX LOGIN PAGE
def Login(user_name, password):
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
# WRITE THE GIVEN STRING TO A DISK AS A GIVEN FILE NAME
def Write_string_to_text_file(input_string, file_name, encode = ''):
    if encode == '':
        open_file = open(file_name, "w")
    else:
        open_file = open(file_name, "w", encoding = encode)
    
    open_file.write(input_string)
    open_file.close()

#--------------------------------------------------------------- 
# OFFER TO OPEN THE GIVEN FILE WITH THE DEFAULT SYSTEM APP. GIVEN FILES ARE ONE OF THE CSV OUTPUT FILES WE HAVE CREATED
# FOR BETTER VIEWING, WE CONVERT THE CSV FILE TO A HTML 
# ALSO CLOSE THE BROWSER <--SHOULD NOT DO THIS HERE, BUT TOO CONVENIENT TO DO SO 
def Offer_to_open_file(file_name, list_type):
    try:
        driver.close()
    except WebDriverException:
        pass
    open_request = input('Press o to open the file or ENTER to continue >')
    if open_request == 'o':
        file_path, file_extension = os.path.splitext(file_name)
        if file_extension != ".csv":
            os.startfile(file_name)
        else:
            # convert csv file to html and display it with system app
            # the photo csv file has special structure so we have to do it separately
            # all other csv files, (followers, following lists, unique, notification lists) have the same first 2 columns 
            # so they can be done the same way 
            if list_type is Output_file_type.PHOTOS_LIST:
                os.startfile(CSV_photos_list_to_HTML(file_name))
            else: 
                os.startfile(CSV_to_HTML(file_name))

#--------------------------------------------------------------- 
# READ A CSV FILE ON DISK AND CONVERT IT TO HTML
# SAVE THE HTML FILE  USING THE SAME NAME BUT WITH EXTENSION '.html'
# EXPECTING THE FIRST LINE TO BE THE HEADERS
def CSV_generic_list_to_HTML(csv_file_name):
    # file name and extension check
    file_path, file_extension = os.path.splitext(csv_file_name)
    if file_extension != ".csv":
        return None
    paths = file_path.split('\\')
    file_name = paths[len(paths) - 1]

    # assign html file name
    html_file = os.path.dirname(os.path.abspath(csv_file_name))+ '\\' + file_name + '.html'
    
    #customize the table properies
    css_head_string='	<head><style>table {border-collapse: collapse;}table, th, td {border: 1px solid black;}</style></head>'
    
    with open(csv_file_name, newline='', encoding='utf-16') as csvfile:
        reader = csv.DictReader(row.replace('\0', '') for row in csvfile)
        headers = reader.fieldnames
        row_string = '<tr>'

        # write headers row
        for header in reader.fieldnames:
            row_string += f'<th align="left">{header}</th>'
        row_string += '</tr>'

        # write table rows
        for row in reader:
            row_string += '<tr>'
            for field_name in reader.fieldnames:
                row_string += f'<td>{row[field_name]}</td> \n'
            row_string += '</tr>'
        
        html_string = f'<html> {css_head_string} <body> <table {row_string} </table> </body> </html>'

        #write html file 
        with open(html_file, 'wb') as htmlfile:
            htmlfile.write(html_string.encode('utf-16'))

    return html_file

#--------------------------------------------------------------- 
# READ A CSV PHOTOS LIST FILE ON DISK AND CONVERT IT TO HTML
# SAVE THE HTML FILE USING THE SAME NAME BUT WITH EXTENSION '.html'
# EXPECTING THE FIRST LINE TO BE THE HEADERS, WHICH ARE  No., Page, ID, Title, Link
# USE THE LINK COLUMN AS A <a> TAG WITHIN THE TITLE COLUMN 
def CSV_photos_list_to_HTML(csv_file_name):
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
        html_string = f'<html> {css_head_string} <body> <table {row_string} </table> </body> </html>'

        #write html file 
        with open(html_file, 'wb') as htmlfile:
            htmlfile.write(html_string.encode('utf-16'))

    return html_file

#--------------------------------------------------------------- 
# READ A CSV FILE FILE (THAT IS NOT A PHOTO CSV FILE) ON DISK AND CONVERT IT TO HTML
# SAVE THE HTML FILE USING THE SAME NAME BUT WITH EXTENSION '.html'
# EXPECTING THE FIRST LINE TO BE THE HEADERS, WHICH ARE  Display Name, User Name, Number Of Followers
#                                                   OR:  Name, User Name, Content, Photo Title, Time Stamp, Status
#                                                   OR:  Name, User Name
# INSERT A <a> TAG WITHIN THE User Name COLUMN : <a href="https://500px.com/{User Name}"  
def CSV_to_HTML(csv_file_name):
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
            for i in range(len(headers)):   #, fn in enumerate(reader.fieldnames):
                if i != 1: 
                    row_string += f'<td>{row[headers[i]]}</td> \n'
                else:     
                    row_string += f'<td><a href="https://500px.com/{row[headers[i]]}">{row[headers[i]]}</a></td> \n'
        row_string += '</tr>'
        html_string = f'<html> {css_head_string} <body> <table {row_string} </table> </body> </html>'

        #write html file 
        with open(html_file, 'wb') as htmlfile:
            htmlfile.write(html_string.encode('utf-16'))

    return html_file

#--------------------------------------------------------------- 
# PROMPT USER FOR A NUMBER INPUT, VALIDATE AND CONVERT IT TO INT. LOOPING UNTIL SUCCESS
def Validate_int(prompt_message):
    num_str = input(prompt_message)
    while True:        
        try: 
            return int(num_str)
        except ValueError:
            printR("Invalid input! Please retry.")
            num_str = input(prompt_message)

#--------------------------------------------------------------- 
# PROMPT USER FOR AN INPUT, MAKE SURE THE INPUT IS NOT EMPTY
def Validate_non_empty_input(prompt_message):
    val = input(prompt_message)
    while len(val) == 0:        
        printR("Input cannot be empty! Please re-enter.")
        val = input(prompt_message)
    return  val

#--------------------------------------------------------------- 
# WE WANT TO GET THE LIST OF LOADED PHOTOS ON THE USER HOME FEED PAGE, THE ONES FROM THE PHOTOGRAPHERS THAT YOU ARE FOLLOWING.
# SINCE ALL THE CLASS NAMES IN THE USER HOMEFEED PAGE ARE POSTFIXED WITH RANDOMIZED TEXTS. 
# A WORK-AROUND SOLUTION IS TO USE THE TAG IMG AS IDENTIFIER FOR A PHOTO 
# FROM THERE WE REMOVE IMG ITEM THAT ARE EITHER AVATARS, THUMBNAILS OR RECOMMENDED PHOTOS
def Get_IMG_element_from_homefeed_page():
    # we are interested in items with the tag <img>
    img_eles = driver.find_elements_by_tag_name('img')
    # img_eles list has many img elements that we don't want, such as thumbnails, recommended photos..., we will remove them from the list
    for ele in reversed(img_eles):
        parent_4 = ele.find_element_by_xpath('../../../..')
        if parent_4.get_attribute('class').find('Elements__HomefeedPhotoBox') == -1:
            img_eles.remove(ele)
    return img_eles
#---------------------------------------------------------------
# DISPLAY MENU
def Show_menu(start_with_current_user = True):
    global user_name 
    if not start_with_current_user:
        user_name = input('Enter 500px user name >')
    printC('--------- Chose one of these options: ---------')
    printC('   1  Get user statistics (recent activities, last upload date, registration date ...')
    printC('   2  Get user photos list ')
    printC('   3  Get followers list ')
    printC('   4  Get following list ')
    printC('   5  Get a list of unique users who liked a given photo')
    printC('')
    printY('      The following options require user login:')
    printC('')
    printC('   6  Get list of unique users who generated last n notifications (liked, commented, followed ...)')
    printC('   7  Get n last notifications details (max 1000)')
    printC('')
    printC('   8  Like n photos from a given user')
    printC('   9  Like n photos, starting at a given index, on various photo pages') 
    printC('  10  Like n photos of each user who likes a given photo or yours')
    printC('  11  Like n photos from your home-feed page, excluding recommended photos ')
    printC('  12  Like n photos of each users in your last m notifications')
    printC('')
    printC('   r  Restart for different user')
    printC('   q  Quit')
    printC('')
    return Validate_non_empty_input('Enter your selection >')

#---------------------------------------------------------------
def Show_sub_menu():
    printC('--------- Select the desired photos pages : ---------')
    printC('    1  Popular')
    printC('    2  Popular of Undiscovered photographers ')
    printC('    3  Upcoming')
    printC('    4  Fresh')
    printC("    5  Editor's Choice")
    return Validate_int('Enter your selection >')
#======================================================================================================================
# MAIN PROGRAM STARTS HERE. TODO: put this in __main__
#======================================================================================================================
os.system('color')
driver = None
#logging.basicConfig(filename='500px.log', filemode='w', format='%(asctime)s - %(message)s', level=logging.INFO)
choice = Show_menu(False)

while choice != 'q':
    #---------------------------------------------------------------
    # Get statistics
    if choice == '1':
        Start_chrome_browser()
        json_data, stats = Get_stats(user_name) 
        if json_data is None or len(json_data) == 0:
            printR(f'Error reading {user_name}\'s page')
            choice = Show_menu(False)
            continue

        print(f"Getting user's statistics ...")
        output_file =  user_name + "_stats.html"
        Write_string_to_text_file(Create_user_statistics_html(stats), output_file)
        Close_chrome_browser()
        Offer_to_open_file(output_file, Output_file_type.STATISTICS_HTML_FILE)
        choice = Show_menu()
    #---------------------------------------------------------------
    # Get photos list
    elif choice == '2':
        outfile = user_name + "_photos.csv"
        # avoid to do the same thing twice: if list (in memory) has items AND output file exists on disk
        if len(photos) > 0 and os.path.isfile(outfile):
            printY('Photo list existed at: ' + os.path.abspath(outfile))
            Offer_to_open_file(outfile, Output_file_type.PHOTOS_LIST) 
            choice = Show_menu()
            continue
        else:
            Start_chrome_browser()
            photos = Get_photos_list(user_name)
            Close_chrome_browser()
            if photos is None: 
                choice = Show_menu()
                continue
            
            print(f"Getting the list of your photos ...")
            photos_list_file_name = user_name + "_photos.csv"
            if Write_photos_list_to_csv(photos_list_file_name) == True:
                Offer_to_open_file(photos_list_file_name, Output_file_type.PHOTOS_LIST) 
            choice = Show_menu()
            continue
    #---------------------------------------------------------------
    # Get Followers list
    elif choice == '3':
        outfile = user_name + '_followers.csv'
        # avoid to do the same thing twice: when the list (in memory) has items and output file exists on disk
        if len(followers_list) > 0  and os.path.isfile(outfile):
            printY('Followers list existed at: ' + os.path.abspath(outfile))
            Offer_to_open_file(outfile, Output_file_type.USERS_LIST) 
            choice = Show_menu()
            continue
        else:
            Start_chrome_browser()
            print(f"Getting the list of users that followed you ...")
            followers_list = Get_followers_list(user_name)
            Close_chrome_browser()
            if len(followers_list) > 0 and Write_users_list_to_csv(outfile, followers_list) == True:
                Offer_to_open_file(outfile, Output_file_type.USERS_LIST) 

            choice = Show_menu()
            continue
    #---------------------------------------------------------------
    # Get Followings list
    elif choice == '4':
        outfile = user_name + '_followings.csv'
        # avoid to do the same thing twice: when the list (in memory) has items and output file exists on disk
        if len(followings_list) > 0  and os.path.isfile(outfile):
            printY('Followings list existed at:\n ' + os.path.abspath(outfile))
            Offer_to_open_file(outfile, Output_file_type.USERS_LIST) 
            choice = Show_menu()
            continue
        else:
            Start_chrome_browser()
            
            print(f"Getting the list of users that you are following ...")
            followings_list = Get_followings_list(user_name)
            Close_chrome_browser()
            if len(followings_list) > 0 and Write_users_list_to_csv(outfile, followings_list) == True:
                 Offer_to_open_file(outfile, Output_file_type.USERS_LIST) 

            choice = Show_menu()
            continue
    #---------------------------------------------------------------  
    # Get a list of unique users who liked a given photo      
    elif choice == '5':
        photo_href = input('Enter photo href >')
        if len(photo_href) == 0:
            printR('Invalid input. Please retry')
            choice = Show_menu()
            continue   

        Start_chrome_browser()
        driver.get(photo_href)
        #Scroll_down(0.5, 1)
        time.sleep(1)

        print(f"Getting the list of unique users who liked the given photo ...")
        like_actioners_list = Get_like_actioners_list()
        Close_chrome_browser()
        if len(like_actioners_list) > 0 and Write_users_list_to_csv(like_actioners_file_name, like_actioners_list) == True:
             Offer_to_open_file(like_actioners_file_name, Output_file_type.USERS_LIST) 
        choice = Show_menu()
        continue   

    #---------------------------------------------------------------  
    # Get list of unique users who generated last n notifications (liked, commented, followed, added to galleries ...)
    elif choice == '6':
        if password == '': password = Validate_non_empty_input('Enter password >')  

        outfile = user_name + '_unique_notificators.csv'     
        ## avoid repeating work: when the list (in memory) has items AND output file exists on disk
        #if len(unique_notificators) > 0 and os.path.isfile(outfile):
        #    printG('List existed at: ' + os.path.abspath(outfile))
        #    Offer_to_open_file(outfile)
        #    choice = Show_menu()
        #    continue        

        number_of_notifications =  Validate_int('Enter the number of notifications you want to retrieve(max 1000) >')
        #  limit maximum number of notifications to retrieve to MAX_NOTIFICATION_REQUESTED 
        if number_of_notifications > MAX_NOTIFICATION_REQUESTED: 
            number_of_notifications = MAX_NOTIFICATION_REQUESTED
 
        Start_chrome_browser()
        Login(user_name, password)
        Open_user_home_page(user_name)         
        Scroll_down(0.5, 1)
        innerHtml = driver.execute_script("return document.body.innerHTML")
        time.sleep(5)

        if number_of_notifications == -1:
            print(f"Getting the unique users that interact with your photos in all of your notifications ...")
        else:
            print(f"Getting the unique users that interact with your photos in the last {number_of_notifications} notifications ...")

        dummy_notifications, unique_notificators = Get_notification_list(True, number_of_notifications)
        Close_chrome_browser()
        if len(unique_notificators) >= 0 and Write_unique_notificators_list_to_csv(outfile) == True: 
             Offer_to_open_file(outfile, Output_file_type.NOTIFICATIONS_LIST) 

        choice = Show_menu()
        continue
    #---------------------------------------------------------------    
    # Get n last notifications details (max 1000)
    elif choice == '7':
        if password == '': password = Validate_non_empty_input('Enter password >')  

        outfile = user_name + '_notification.csv'
        # avoid to do the same thing twice: when the list (in memory) has items and output file exists on disk
        if len(notifications) > 0 and os.path.isfile(outfile):
            printG('List existed at:\n ' + os.path.abspath(outfile))
            Offer_to_open_file(outfile, Output_file_type.NOTIFICATIONS_LIST)
            choice = Show_menu()
            continue

        number_of_notifications =  Validate_int('Enter the number of notifications you want to retrieve(max 1000) >')
        #  limit maximum number of notifications to retrieve to MAX_NOTIFICATION_REQUESTED 
        if number_of_notifications > MAX_NOTIFICATION_REQUESTED: 
            number_of_notifications = MAX_NOTIFICATION_REQUESTED
 
        Start_chrome_browser()
        Login(user_name, password)
        Open_user_home_page(user_name)      
        Scroll_down(0.5, 1)
        innerHtml = driver.execute_script("return document.body.innerHTML")
        time.sleep(5)
        
        print(f"Getting the details of the last {number_of_notifications} notifications ...")
        notifications, unique_notificators = Get_notification_list(True, number_of_notifications)
        Close_chrome_browser()
        if len(notifications) > 0 and  Write_notifications_to_csvfile(outfile) == True:
            Offer_to_open_file(outfile, Output_file_type.NOTIFICATIONS_LIST)

        choice = Show_menu()
        continue    
    #-------------------------------------------------------------- 
    # Auto-like the first n not-yet-liked photos of a given user'
    elif choice == '8':
        if password == '': password = Validate_non_empty_input('Enter password >')  
        number_of_photos_to_be_liked = Validate_int('Enter the number of photos you want to auto-like >')

        target_user_name = input('Enter target user name >')
        if len(password) == 0 or target_user_name is None: 
            printR('Invalid input(s). Please re-enter')
            choice = Show_menu()
            continue
  
        Start_chrome_browser()
        Login(user_name, password)

        print(f"Starting auto-like {number_of_photos_to_be_liked} photo(s) of user {target_user_name} ...")
        include_already_liked_photos_in_count = True
        Autolike_photos(target_user_name, int(number_of_photos_to_be_liked), include_already_liked_photos_in_count)
        Close_chrome_browser()
        choice = Show_menu()     
        continue    
    #---------------------------------------------------------------  
    # Like n photos, starting from a given index,  on either one of following photo pages:     
    # Popular, Popular Undiscovered, Upcoming Fresh, Editor's choice
    elif choice == '9':
        if password == '': password = Validate_non_empty_input('Enter password >')  
        number_of_photos_to_be_liked = Validate_int('Enter the number of photos you want to auto-like >')
        index_of_start_photo =  Validate_int('Enter the index of the start photo (1-500) >')

        selection = Show_sub_menu()
        if   selection == 1: href = 'https://500px.com/popular'
        elif selection == 2: href = 'https://500px.com/popular?followers=undiscovered'
        elif selection == 3: href = 'https://500px.com/upcoming' 
        elif selection == 4: href = 'https://500px.com/fresh'
        elif selection == 5: href = 'https://500px.com/editors'
        else                 : href = ''
        
        if password == '' or href is None: 
            printR('Invalid input(s). Please re-enter')
            choice = Show_menu()
            continue
        
        Start_chrome_browser()
        Login(user_name, password)
        driver.get(href)
        inner_html = driver.execute_script("return document.body.innerHTML") #run JS body script after all photos are loaded
        time.sleep(2)
        
        print(f"Starting auto-like {number_of_photos_to_be_liked} photo(s), begining at index {index_of_start_photo} ...")
        Like_n_photos_on_current_page(number_of_photos_to_be_liked, index_of_start_photo)
  
        Close_chrome_browser()
        choice = Show_menu()         
        continue
    #---------------------------------------------------------------  
    # Like n photos (from top)  of each user who likes a given photo or yours
    # if the first photo is already liked, do nothing
    elif choice == '10':
        # do as in option 5, get the list of users who like a given photo, but this time we need to login
        if password == '': password = input('Enter password >')  
        photo_href = Validate_non_empty_input('Enter your photo href >')
        number_of_photos_to_be_liked = Validate_int('Enter the number of photos you want to auto-like for each user >')

        Start_chrome_browser()
        Login(user_name, password)
        driver.get(photo_href)
        time.sleep(1)
        
        print(f'Getting the list of users who liked this photo ...')
        like_actioners_list = Get_like_actioners_list()
        if len(like_actioners_list) == 0: 
            printG(f'The photo {photo_tilte} has no affection yet')
            choice = Show_menu()
            continue 
        
        print(f"Starting auto-like {number_of_photos_to_be_liked} photos of each of {len(like_actioners_list)} users on the list ...")
        include_already_liked_photos_in_count = True  # meaning: if you want to autolike 3 first photos, and you found out two of them are already liked, then you need to like just one photo.
                                                      # if this is set to False, then you will do 3 photos, no matter what
        for i, actor in enumerate(like_actioners_list):
            print(f'User {str(i+1)}: {actor.display_name}, {actor.user_name}:')
            Autolike_photos(actor.user_name, number_of_photos_to_be_liked, include_already_liked_photos_in_count)

        Close_chrome_browser()
        choice = Show_menu()
        continue
    #---------------------------------------------------------------  
    # Like n photos from your home-feed page, excluding the recommended photos from 500px
    # skip all consecutive photos of the same user
    elif choice == '11':
        if password == '': password = Validate_non_empty_input('Enter password >')  
        number_of_photos_to_be_liked = Validate_int('Enter the number of photos you want to auto-like >')
   
        Start_chrome_browser()
        Login(user_name, password)
        time.sleep(2)
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
        
        print(f"Like {number_of_photos_to_be_liked} photos from the {user_name}'s home feed page ...")
        Like_n_photos_on_homefeed_page(number_of_photos_to_be_liked)

        Close_chrome_browser()
        choice = Show_menu(True)
        continue 
    #---------------------------------------------------------------  
    # Like n photos of each users in your last m notifications
    elif choice == '12':
        if password == '': password = input('Enter password >')  
        number_of_photos_to_be_liked = Validate_int('Enter the number of photos you want to like for each user >')
        number_of_notifications =  Validate_int('Enter the number of notifications you want to retrieve(max 1000) >')

        #  limit maximum number of notifications to retrieve to MAX_NOTIFICATION_REQUESTED 
        if number_of_notifications > MAX_NOTIFICATION_REQUESTED:
            number_of_notifications = MAX_NOTIFICATION_REQUESTED
        
        ## check whether option 6 or 7 have been done recently, we may be able to skip some work
        #if len(unique_notificators) > 0 and os.path.isfile(outfile) and int(intput_number) <= int(number_of_notifications):
        #    print(f' Using the existing list of users at: { os.path.abspath(outfile)} ')
        #else:

        # do as in option 6 to get the list of unique users from the last m notifications
        Start_chrome_browser()
        print(f'Getting the list of unique users in the last {number_of_notifications} notifications ...')
        Login(user_name, password)
        Open_user_home_page(user_name)         
        Scroll_down(0.5, 1)
        innerHtml = driver.execute_script("return document.body.innerHTML")
        time.sleep(5)       
        dummy_notifications, unique_notificators = Get_notification_list(True, number_of_notifications)
        
        include_already_liked_photo_in_count = True  # meaning: if you want to autolike 3 first photos, and you found out two of them ...
        # are already liked, then you need to like just one photo, not three. A False here means you will do 3 photos, no matter what
        print(f"Starting auto-like {number_of_photos_to_be_liked} photos of each of {len(unique_notificators)} users on the list ...")
        for i, item in enumerate(unique_notificators):
            name_pair = item.split(',')
            if len(name_pair) > 1: 
                printG(f'User {str(i+1)}: {name_pair[0]}, {name_pair[1]}:')
                Autolike_photos(name_pair[1], int(number_of_photos_to_be_liked), include_already_liked_photo_in_count)
            else:
                continue
        Close_chrome_browser()
        choice = Show_menu()
        continue
    #---------------------------------------------------------------
    elif choice == 'r':  #restart for different user
        # reset global variables
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
        number_of_notifications = MAX_NOTIFICATION_REQUESTED
        index_of_start_photo = 0
        like_actioners_file_name = 'dummy'
        choice = Show_menu(False)
        continue
    #---------------------------------------------------------------
    else: 
        choice = Show_menu(False)
        continue
# END 
#======================================================================================================================



