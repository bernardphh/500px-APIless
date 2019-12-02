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
import msvcrt
import pandas as pd
import glob
import random
import requests

from lxml import html
import os, sys, time, datetime, re, math, csv, json, codecs, argparse
import errno
from time import sleep
from enum import Enum
#from fake_useragent import UserAgent

from lxml.html import fromstring
from itertools import cycle
import traceback


PHOTOS_PER_PAGE = 50             # 500px currently loads 50 photos per page
LOADED_ITEM_PER_PAGE = 50        # it also loads 50 followers, or friends, at a time in the popup window
NOTIFICATION_PER_LOAD = 20       # currently notifications are requested to display ( by scrolling the window) 20 items at a time
MAX_NOTIFICATION_REQUEST = 5000  # self limitation to avoid abusing
MAX_AUTO_LIKE_REQUEST = 100      # self limitation to avoid abusing
MAX_FOLLOWINGS_STATUSES = 100    # max number of users you want to find the following statuses with you
DEBUG = False

DATE_FORMAT = "%Y-%m-%d"                    # ex. 2019-06-15
DATETIME_FORMAT = "%Y-%b-%d--Time%H-%M-%S"  # ex. 2019-Jun-15--Time13-21-45

# for simplicity, we keep everything in one file, including a short CSS and a Javascript constant strings below
HEAD_STRING_WITH_CSS_STYLE ="""
<head>
	 <style>
        table {border-collapse: collapse; width: 100%; table-layout:fixed;  text-align:center;}
 		table tr:nth-child(even){background-color: #f2f2f2;}
		table tr:hover {background-color: #ddd; }
		table, th, td {border: 1px solid #ddd; padding: 6px; word-wrap: break-word;}
        th { background-color: #248f8f; color: white; font-size: 16px; height:65;}
        img { height:50px; width: 50px; border-radius: 25px;}
        p {line-height:1;}
        div {text-align:left;}
        .photo{height:50px; width: 80px; style="vertical-align:top"; border-radius: 6px; }
        .alignLeft {text-align:left;}       
 	    .w40  {width:40px;} 
        .w80  {width:70px;} 
        .w100 {width:100px;} 
        .w120 {width:120px;} 
        .w200 {width:200px;}
        .w210 {width:210px;}
		.hdr_text   {float:left; vertical-align:top display:table-cell; height:100%;}
		.hdr_arrows {float:right; position:relative; right:1px; top:32px; font-size:60%;}
     </style
</head> """

sort_direction_arrows = """
			<div style="float:right;">
				<div id ="arrow-up-0">&#x25B2;</div>
				<div id ="arrow-down-0">&#x25BC;</div>
			</div>		
            """
SCRIPT_STRING = """<script>
/* Highly customized Sort table columns: Sort item is either the innerHTML of the "td" tag, or the text of "a" tag, within the second "div" tag 
   To trigger the specific sort, pass ANY value to the 2nd argument "special_sort"*/  
function sortTable(n, special_sort) {
   var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
    table = document.getElementsByTagName("table")[0] /* targer the first table instead of table with id-- getElementById("myTable"); */
    switching = true;
    dir = "asc";
    while (switching) {
        switching = false;
        rows = table.rows;
        for (i = 1; i < (rows.length - 1); i++) {
            shouldSwitch = false;
			x = rows[i].getElementsByTagName("TD")[n];
            y = rows[i + 1].getElementsByTagName("TD")[n];
			
            if (special_sort != undefined){
			    x =x.getElementsByTagName("DIV")[1].getElementsByTagName("a")[0].text;
			    y =y.getElementsByTagName("DIV")[1].getElementsByTagName("a")[0].text;
            }
			else
			{
				x = x.innerHTML;
				y = y.innerHTML;		    		
			}
 		    if (x == "" && y != "" && dir == "asc"){
		        shouldSwitch = true;	
			    break;
		    }	  
		    if (y == "" && x != ""  && dir == "desc"){
		        shouldSwitch = true;
			    break;
		    }	           
		    var xContent = (isNaN(x))
                ? ((x.toLowerCase() === "-")? 0 : x.toLowerCase() )
                : parseFloat(x);
            var yContent = (isNaN(y))
                ? ((y.toLowerCase() === "-")? 0 : y.toLowerCase() )
                : parseFloat(y);			  
            if (dir == "asc") {
                if (xContent > yContent) {
                    shouldSwitch= true;
                    break;
                }
            } else if (dir == "desc") {
                if (xContent < yContent) {
                    shouldSwitch= true;
                    break;
                }
            }
        }
        if (shouldSwitch) {
            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
            switching = true;
            switchcount ++;
        } else {
            if (switchcount == 0 && dir == "asc") {
                dir = "desc";
                switching = true;
            }
        }
	    if (dir == "asc") {
		    document.getElementById("arrow-down-" + n ).style.display = "none";
		    document.getElementById("arrow-up-" + n ).style.display = "block";
	    }
	    else {
		    document.getElementById("arrow-up-" + n).style.display = "none";
		    document.getElementById("arrow-down-" + n).style.display = "block";	  
	    }
    }
	var num_cols = table.rows[0].cells.length;	
	for ( i=0; i < num_cols; i++) {
		if ( i != n) {
			document.getElementById("arrow-up-" + i).style.display = "block";
			document.getElementById("arrow-down-" + i).style.display = "block";				
		}
	}	   	   	
}

</script>"""

class photo_stats:
    """ Photo statistics info """
    def __init__(self,  upload_date = '', views_count=0, votes_count=0, collections_count=0, comments_count=0, highest_pulse=0, rating=0, tags='' ):
        self.upload_date  = upload_date 
        self.views_count = views_count
        self.votes_count = votes_count 
        self.collections_count = collections_count
        self.comments_count = comments_count 
        self.highest_pulse = highest_pulse
        self.rating = rating
        self.tags = tags

class photo:
    """ Represent a photo info."""
    def __init__(self, author_name='', order='', id='', title='', href='', thumbnail='', galleries='', stats= photo_stats()):
        self.author_name= author_name
        self.order = order  # ascending order, with the latest uploaded photo being 1
        self.id = id
        self.title = title
        self.href = href
        self.thumbnail = thumbnail        
        self.galleries = galleries
        self.stats = stats

class notification:
    """ Represent a notification object."""
    def __init__(self, order, user_avatar, display_name, username, content, photo_thumb, photo_link, photo_title, timestamp, status):
        self.order = order
        self.user_avatar = user_avatar
        self.display_name = display_name
        self.username = username
        self.content = content
        self.photo_thumb = photo_thumb
        self.photo_link = photo_link
        self.photo_title = photo_title
        self.timestamp = timestamp
        self.status = status

    def print_screen(self):
        print(self.order + "\n" + self.user_avatar + self.display_name + "\n" + self.username + "\n" + self.content  +  "\n" + self.photo_thumb + "\n" + self.photo_link + "\n" + self.photo_title + "\n" + self.timestamp +  "\n" + self.status +  "\n"  )   
    def write_to_textfile(self):
        print(self.order + self.user_avatar + "\n" + self.display_name + "\n" + self.username + "\n" + self.content + self.photo_thumb  + "\n" + self.photo_link + "\n" + self.photo_title + "\n" + self.timestamp +  "\n" + self.status +  "\n"  +  "\n")

class notificator:
    """ Represent a user, with display name and user name, who generated a notification. """
    def __init__(self, display_name, username, user_avatar = ''):
        self.display_name = display_name
        self.username = username   
        self.user_avatar = user_avatar   
    def print_screen(self):
        print(self.display_name + "\n" + self.username + "\n"  + self.user_avatar + "\n")   
    def write_to_textfile(self):
        print(self.display_name + "\n" + self.username + "\n" + self.user_avatar + "\n")

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
    def __init__(self, order, user_avatar, display_name, user_name, number_of_followers, following_status = ''):
        self.order = order
        self.user_avatar = user_avatar
        self.display_name = display_name
        self.user_name = user_name
        self.number_of_followers = number_of_followers
        self.following_status = following_status
    
    def to_dict(self):
        return {
            'No': self.order,
            'Avatar': self.user_avatar,
            'Display Name': self.display_name,
            'User Name': self.user_name,
            'Followers': self.number_of_followers,
            'Status': self.following_status
        }


#class Output_file_type(Enum):
#   """ Enum representing 5 types of output list"""
#   NOT_DEFINED          = 0
#   FOLLOWERS_LIST       = 1                   
#   FOLLOWINGS_LIST      = 2                  
#   PHOTOS_LIST          = 3              
#   NOTIFICATIONS_LIST   = 4
#   UNIQUE_USERS_LIST    = 5        # Unique users with appearance count, extracted from Notifications list
#   STATISTICS_HTML_FILE = 6

class User_inputs():
    """ Represent the input entered by the user. 
    
    Choice is an character string representing available options: [1-13] or 'r','q' . The default value is zero which means commnand line arguments will not be used 
    """

    def __init__(self, use_command_line_args = False, choice='0', user_name='', password='', target_user_name='', photo_href='', gallery_href='', gallery_name='',
                 number_of_photos_to_be_liked=2 , index_of_start_photo=1, number_of_notifications=200, time_interval=3, index_of_start_user=1, number_of_users=100, csv_file=''):
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
        self.csv_file                       = csv_file

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
        self.csv_file                       = ''

class Output_data():
    """ Represent all the output lists and data"""
    def __init__(self, output_dir = '', avatars_dir = '', thumbnails_dir = '', json_data = [], photos = [],notifications = [], unique_notificators = [], followers_list = [], followings_list = [], like_actioners_list= []):
        self.json_data = json_data      
        self.photos = photos         
        self.notifications = notifications  
        self.unique_notificators = unique_notificators
        self.followers_list = followers_list  
        self.followings_list = followings_list 
        self.like_actioners_list= like_actioners_list
        self.stats = user_stats()  
        
        # Set default output folder :  %PROGRAMDATA%\500px_APIless\Output (C:\ProgramData\500px_Apiless\Output)
        # TODO: use a config file and put this setting in it
        output_dir = os.path.join(os.getenv('ProgramData'), r'500px_Apiless\Output')
        os.makedirs(output_dir, exist_ok = True)
        self.output_dir = output_dir
        
        temp_dir1 =  os.path.join(output_dir, r'avatars')
        os.makedirs(temp_dir1, exist_ok = True)
        self.avatars_dir = temp_dir1
 
        temp_dir2 =  os.path.join(output_dir, r'thumbnails')
        os.makedirs(temp_dir2, exist_ok = True)
        self.thumbnails_dir = temp_dir2
 
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
    chrome_options.add_argument("--headless")  
    #chrome_options.add_argument('--disable-gpu')
    # TODO: move these options into a config file and maybe add the headless option
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
    if stats is None:
        return

    time_stamp = datetime.datetime.now().replace(microsecond=0).strftime(DATETIME_FORMAT)

    output = f'''
<html>\n\t<body>
        <h2>User statistics</h2>
        <p>Date: {time_stamp}</p>
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
            writer = csv.DictWriter(csv_file, fieldnames = ['No', 'ID', 'Photo Title', 'Href', 'Thumbnail', 'Views', 'Likes', 'Comments', 'Featured In Galleries', 'Highest Pulse', 'Rating', 'Date', 'Tags'])  
            writer.writeheader()
            for i, a_photo in enumerate(list_of_photos):
                writer.writerow({'No' : str(a_photo.order), 'ID': str(a_photo.id), 'Photo Title' : str(a_photo.title), 'Href' :a_photo.href, 'Thumbnail': a_photo.thumbnail, \
                                 'Views': str(a_photo.stats.views_count), 'Likes': str(a_photo.stats.votes_count), 'Comments': str(a_photo.stats.comments_count), \
                                 'Featured In Galleries': str(a_photo.galleries), 'Highest Pulse': str(a_photo.stats.highest_pulse), 'Rating': str(a_photo.stats.rating), \
                                 'Date': str(a_photo.stats.upload_date), 'Tags': a_photo.stats.tags}) 
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
    
    THE USERS LIST COULD BE ONE OF THE FOLLOWING: FOLLOWERS LIST, FRIENDS LIST OR UNIQUE USERS LIST 
    IF THE FILE IS CURRENTLY OPEN, GIVE THE USER A CHANCE TO CLOSE IT AND RE-SAVE
    """
    try:
        with open(csv_file_name, 'w', encoding = 'utf-16', newline='') as csv_file:  # could user utf-16be
            writer = csv.writer(csv_file)
            writer = csv.DictWriter(csv_file, fieldnames = ['No', 'User Avatar', 'Display Name', 'User Name', 'Followers', 'Status'])  
            writer.writeheader()
            for a_user in users_list:
                writer.writerow({'No' : a_user.order, 'User Avatar': a_user.user_avatar, 'Display Name' : a_user.display_name, \
                    'User Name': a_user.user_name, 'Followers': a_user.number_of_followers, 'Status': a_user.following_status}) 
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
            writer = csv.DictWriter(csv_file, fieldnames = ['No', 'User Avatar', 'Display Name', 'User Name', 'Content', \
                'Photo Thumbnail', 'Photo Title', 'Time Stamp', 'Status', 'Photo Link'])    
            writer.writeheader()
            for notif in notifications_list:
                writer.writerow({'No': notif.order, 'User Avatar': notif.user_avatar, 'Display Name': notif.display_name, \
                    'User Name': notif.username, 'Content': notif.content, 'Photo Thumbnail': notif.photo_thumb, \
                    'Photo Title': notif.photo_title, 'Time Stamp': notif.timestamp, 'Status': notif.status, 'Photo Link': notif.photo_link }) 
        printG('Notifications list is saved at:\n ' + os.path.abspath(csv_file_name))
        return True 
    except PermissionError:
        retry = input(f'Error writing to file {csv_file_name}.\n Make sure the file is not in use, then type r for retry >')
        if retry == 'r':  
            Write_notifications_to_csvfile(notifications_list, csv_file_name)
        else: 
            printR(f'Error writing file {csv_file_name}')
            return False

#---------------------------------------------------------------
def Write_unique_notificators_list_to_csv(unique_users_list, csv_file_name):
    """ Write the unique notifications list to a csv file with the given  name. Return True if success.
    
    IF THE FILE IS CURRENTLY OPEN, GIVE THE USER A CHANCE TO CLOSE IT AND RE-SAVE
    """
    try:
        with open(csv_file_name, 'w', encoding = 'utf-16', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer = csv.DictWriter(csv_file, fieldnames = ['No', 'User Avatar', 'Display Name', 'User Name', 'Count'])  
            writer.writeheader()

            for actor in unique_users_list:
                items = actor.split(',')
                if len(items) == 5:
                    writer.writerow({'No': items[0], 'User Avatar': items[1], 'Display Name': items[2], 'User Name': items[3], 'Count': items[4]}) 
            printG('Unique notificators is saved at:\n' + os.path.abspath(csv_file_name))
            return True 

    except PermissionError:
        retry = input(f'Error writing to file {csv_file_name}. Make sure the file is not in use. Then type r for retry >')
        if retry == 'r': 
            Write_unique_notificators_list_to_csv(unique_users_list, csv_file_name)
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
    if page is None or not xpath_string:
        return ''
    ele = page.xpath(xpath_string)
    if ele is not None and len(ele) > 0 : 
        return ele[0].text
    return ''

#---------------------------------------------------------------
def Get_element_attribute_by_ele_xpath(page, xpath, attribute_name):
    """Get the value of the given attribute name, at the element of the given xpath. Return '' if element not found."""
    if page is None or not xpath or not attribute_name:
        return ''
    ele = page.xpath(xpath)
    time.sleep(1)
    if ele is not None and len(ele) > 0:
        try:
            return ele[0].attrib[attribute_name] 
        except:
            printR(f'Error getting attribute {attribute_name}')
    return ''

#---------------------------------------------------------------
def check_and_get_ele_by_xpath(element, xpath):
    """ Find the web element from a given xpath, return none if not found.
    
    THE SEARCH CAN BE LIMITED WITHIN A GIVEN WEB ELEMENT, OR THE WHOLE DOCUMENT, BY PASSING THE BROWSER DRIVER
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
    
    THE SEARCH CAN BE LIMITED WITHIN A GIVEN WEB ELEMENT, OR THE WHOLE DOCUMENT, BY PASSING THE BROWSER DRIVER
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
    
    THE SEARCH CAN BE LIMITED WITHIN A GIVEN WEB ELEMENT, OR THE WHOLE DOCUMENT, BY PASSING THE BROWSER DRIVER
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

    THE SEARCH CAN BE LIMITED WITHIN A GIVEN WEB ELEMENT, OR THE WHOLE DOCUMENT, BY PASSING THE BROWSER DRIVER
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

    THE SEARCH CAN BE LIMITED WITHIN A GIVEN WEB ELEMENT,  OR ON THE WHOLE DOCUMENT IF THE BROWSER DRIVER IS PASSED
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

    THE SEARCH CAN BE LIMITED WITHIN A GIVEN WEB ELEMENT, OR ON THE WHOLE DOCUMENT IF THE BROWSER DRIVER IS PASSED
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

    THE SEARCH CAN BE LIMITED WITHIN A GIVEN WEB ELEMENT,  OR ON THE WHOLE DOCUMENT IF THE BROWSER DRIVER IS PASSED
    """
    if element is None or not selector:
        return []  
    try:
        return element.find_element_by_css_selector(selector)
    except NoSuchElementException:
        return []

#---------------------------------------------------------------
def check_and_get_all_elements_by_css_selector(element, selector):
    """Find the web elements of a given css selector, return none if not found.

    THE SEARCH CAN BE LIMITED WITHIN A GIVEN WEB ELEMENT,  OR ON THE WHOLE DOCUMENT IF THE BROWSER DRIVER IS PASSED
    """
    if element is None or not selector:
        return  [] 
    try:
        return element.find_elements_by_css_selector(selector)
    except NoSuchElementException:
        return []

#---------------------------------------------------------------
def Get_web_ele_text_by_xpath(element_or_driver, xpath):
    """ Use WebDriver function to find text from a given xpath, return empty string if not found.
    
    USE ABSOLUTE XPATH IF THE DRIVER IS PASSED
    USER RELATIVE XPATH IF AN WEB ELEMENT IS PASSED
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
def GetUploadDate(driver, photo_link):
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
def Open_user_home_page(driver, user_name):
    """Open the home page of a given user and wait for the page to load. If the user page is not found or timed out (30s),
       return False and the error message. If not, return True and a blank message """ 
       
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

    if check_and_get_ele_by_class_name(driver, 'not_found') is None and \
       check_and_get_ele_by_class_name(driver, 'missing') is None:
        return True, ''
    else:
        Close_chrome_browser(driver)
        return False, f'Error reading {user_name}\'s page. Please make sure a valid user name is used'

#---------------------------------------------------------------
def Finish_Javascript_rendered_body_content(driver, time_out=10, class_name_to_check='', css_selector_to_check='', xpath_to_check=''):
    """ Run the Javascript to render the body content. Log error if it happened. Return:
        1) The fail/success status, 
        2) The page content text 
           
    The completion of the js script, within a given timeout, is determined by checking the existance of one of the given elements. 
    Element to check is one of the following: class_name, css_selector, xpath, prioritied by this order
    """

    innerHtml = driver.execute_script("return document.body.innerHTML")  
    
    try:
        if class_name_to_check:
            element = WebDriverWait(driver, time_out).until(EC.presence_of_element_located((By.CLASS_NAME, class_name_to_check)))
        elif css_selector_to_check:
            element = WebDriverWait(driver, time_out).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector_to_check)))
        elif xpath_to_check:
            element = WebDriverWait(driver, time_out).until(EC.presence_of_element_located((By.XPATH, xpath_to_check)))
        else:
            printR('Internal error. No identifier was given for detecting the page loading completion ')
            return False, ''
    except TimeoutException :
        printR('Time out {time_out}s while loading. Please retry.')
        return False, '', 
    except:
        printR('Error loading. Please retry.')
        return False, ''   
    
    return True, innerHtml
#---------------------------------------------------------------


def Get_stats(driver, user_inputs, output_lists):
    """Get statistics of a given user: number of likes, views, followers, following, photos, last upload date...
       If success, return statistics object and a blank message. If not return None and the error message

       Process:
       - Open user home page https://500px.com/[user_name]
       - Run the document javascript to render the page content
       - Use lxml to extract interested data
       - Use regular expression to extract the json part in the body, and obtain more data from it.
    """

    success, message = Open_user_home_page(driver, user_inputs.user_name)
    if not success:
        if message.find('Error reading') != -1:
            user_inputs.user_name = ''
        return None, message
        
    Hide_banners(driver)
  
    # abort the action if the target objects failed to load within a given timeout
    success, innerHtml = Finish_Javascript_rendered_body_content(driver, time_out=30, class_name_to_check='finished')
    if not success:
        return None, f"Error loading user {user_inputs.user_name}'s photo page"
    # using lxml for html handling
    page = html.document_fromstring(innerHtml)

    # Affection note
    affection_note = Get_element_attribute_by_ele_xpath(page, "//li[@class='affection']", 'title' )
    # Following note
    following_note = Get_element_attribute_by_ele_xpath(page, "//li[@class='following']", 'title' )
    # Views count
    views_ele = check_and_get_ele_by_class_name(driver,'views' )
    if views_ele is not None:
        ele =  check_and_get_ele_by_tag_name(views_ele,'span')
        if ele is not None:
            views_count= ele.text

    # Location
    location =  Get_element_text_by_xpath(page,'//*[@id="content"]/div[1]/div[4]/ul/li[5]')
    loc_test = check_and_get_all_elements_by_class_name(driver, 'location')

    #using regex to extract from the javascript-rendered html the json part that holds user data 
    # Jul 26 2019: modification due to page structure changes: photos list is no longer included in userdata
    #   userdata = re.findall('"userdata":(.*),"viewer":', innerHtml)
    i = innerHtml.find('"userdata":') 
    j = innerHtml.find('</script>', i)
    userdata = innerHtml[i + 11 : j - 2]
    if len(userdata) == 0:
       return None, 'Error getting the user data'
    
    json_data = json.loads(userdata)
    print("Getting the last upload date ...")
    last_photo_href = Get_element_attribute_by_ele_xpath(page, './/*[@id="content"]/div[3]/div/div/div[1]/a', 'href')
    if not last_photo_href:
        #printR('Error getting the last photo href')
        return None, 'Error getting the last photo href'

    driver.get(r'https:/500px.com' + last_photo_href)
    time_out = 30
    try:  
        info_box = WebDriverWait(driver, time_out).until(EC.presence_of_element_located((By.XPATH, '//*[@id="root"]/div[3]/div/div[2]')) )
    except  TimeoutException:
        #printR(f'Time out ({time_out}s)! Please try again')
        return None, f'Time out ({time_out}s)! Please try again'

    last_upload_date = ''
    upload_date_ele = check_and_get_ele_by_xpath(info_box,  '//div[1]/div[2]/p/span')        
    if upload_date_ele is None:
        upload_date_ele = check_and_get_ele_by_xpath(info_box, '//div[3]/div[1]/div/p/span') 

    if upload_date_ele is not None:
        last_upload_date = upload_date_ele.text
 
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

    stats = user_stats(json_data['fullname'], user_inputs.user_name, json_data['id'], location, 
                       affection_note, following_note, json_data['affection'], views_count, json_data['followers_count'], json_data['friends_count'], 
                       json_data['photos_count'], json_data['galleries_count'], json_data['registration_date'][:10], last_upload_date, user_status)
    return stats, ''
      
#---------------------------------------------------------------

def Get_photos_list(driver, user_inputs):
    """Return the list of photos from a given user.

    Process: 
    - Open user home page, scroll down until all photos are loaded
    - Make sure the document javascript is called to get the full content of the page
    - Extract photo data: no, id, photo title, href, thumbnail, views, likes, comments, galleries, highest pulse, rating, date, tags
    """

    photos_list = []
    success, message = Open_user_home_page(driver, user_inputs.user_name)
    if not success:
        if message.find('Error reading') != -1:
            user_inputs.user_name = ''
        return [], message

    Hide_banners(driver)

    # We intend to scroll down an indeterminate number of times until the end is reached
    # In order to have a realistic progress bar, we need to give an estimate of the number of scrolls needed
    estimate_scrolls_needed = 3  #default value, just in case
    photos_count  = 1
    photos_count_ele = check_and_get_ele_by_css_selector(driver, '#content > div.profile_nav_wrapper > div > ul > li.photos.active > a > span')
    if photos_count_ele is not None:
        photos_count = int(photos_count_ele.text.replace('.', '').replace(',', ''))
        estimate_scrolls_needed =  math.floor( photos_count / PHOTOS_PER_PAGE) +1

    #Scroll_down(driver, 2, -1, estimate_scrolls_needed, ' - Scrolling down for more photos:') 
    Scroll_to_end_by_class_name(driver, 'photo_link', photos_count)
    #Scroll_down_until_the_end(driver, None, '', '', photos_count, 20, ' - Scrolling down to load more photos:' )
    
    # abort the action if the target objects failed to load within a given timeout
    success, innerHtml = Finish_Javascript_rendered_body_content(driver, time_out=15, class_name_to_check='finished')
    if not success:
        return [], f"Error loading user {user_inputs.user_name}'s photo page"

    #if DEBUG:
    #     Write_string_to_text_file(str(innerHtml.encode('utf-8')), user_inputs.user_name + '_innerHTML.txt')
    page = html.document_fromstring(innerHtml)

    #extract photo title and href (alt tag) using lxml and regex
    els = page.xpath("//a[@class='photo_link ']")  
    img_ele = page.xpath("//img[@data-src='']")
    num_item = len(els)
    if num_item == 0:
        return [], f'User {user_name} does not upload any photo'

    update_progress(0, f' - Extracting 0/{num_item} photos:')

    # Create the photos list
    for i in range(num_item): 
        update_progress(i / (num_item -1), f' - Extracting  {i + 1}/{num_item} photos:')

        # get photo link, title and thumbnail 
        photo_href = r'https://500px.com' + els[i].attrib["href"]
        if i < len(img_ele):
            src = img_ele[i].attrib["src"]
            title = img_ele[i].attrib["alt"]

        # open each photo page to get photo statistics
        time_out = 40
        id = ''
        galleries_list = []
        order = i + 1        
        try:  
            driver.get(photo_href)
            #time.sleep(1)
            info_box = WebDriverWait(driver, time_out).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="root"]/div[3]/div/div[2]')) )
        except  TimeoutException:
            return photos_list, f'Time out ({time_out}s)! Please try again'
 
        # using regular expression --------------------------------------------
        USING_REGULAR_EXPRESSION = True
 
        if USING_REGULAR_EXPRESSION :
            # uploade date
            info_box_text = info_box.text
            upload_date  =  re.search('Calendar.*\n(.*)', info_box_text)
            upload_date = '' if upload_date is None else str.strip(upload_date.group(1))        
            if upload_date and ('ago' not in upload_date):
                try:
                    dt = datetime.datetime.strptime(upload_date, "%b %d, %Y")
                    upload_date = dt.strftime("%Y %m %d")
                except:
                    # if error occured, write what are available sofar before jumping to the next photo
                    printR(f'Error converting date-time string: {upload_date}, on photo: {title}')
                    this_photo = photo(author_name=user_inputs.user_name, order=order, id='', title=title, href=photo_href, thumbnail=src, galleries='', stats = photo_stats() )      
                    photos_list.append(this_photo)
                    continue

            votes_count = re.search(r'Created with Sketch.*\n(.*)', info_box_text)
            votes_count = '' if votes_count is None else str.strip(votes_count.group(1)).replace(',','').replace('.','')

            highest_pulse  = re.search(r'Pulse\s*\n(.*)', info_box_text)      
            highest_pulse = '' if highest_pulse is None else str.strip(highest_pulse.group(1)).replace(',','').replace('.','')
            
            views_count  =   re.search(r'Views\s*\n(.*)', info_box_text)  
            views_count = '' if views_count is None else str.strip(views_count.group(1)).replace(',','').replace('.','')

            # comments count
            comments_count =  Get_web_ele_text_by_xpath(info_box, '//div/div[4]/div[2]/div/h4').split(' ')[0]  

            #category  =  re.search(r'Category(.*)', info_box_text)      
            #category = '' if category is None else str.strip(category.group(1))

            # list of tags
            tags = re.search(r'Category.*\n(.*)\nFeatured in these galleries', info_box_text, re.DOTALL).group(0).split('\n')
            tags.pop(0)
            tags.pop()
            tags.sort()

            # get galleries list, if user logged in
            if user_inputs.password is not '':
                view_all_ele = driver.find_elements_by_xpath("//*[contains(text(), 'View all')]")
                if len(view_all_ele) == 0 or (len(view_all_ele) == 1 and view_all_ele[0].tag_name == 'script'):
                    collections_count = 0
                else:
                    view_all_ele[0].location_once_scrolled_into_view
                    view_all_ele[0].click()         
                    time.sleep(1)
                    eles = driver.find_elements_by_class_name('ant-modal-body')       
                    galleries_count = 0

                    if len(eles)> 0:
                        containers = check_and_get_all_elements_by_xpath(eles[0],'./div/div')
                        if containers is not None and len(containers)> 0:
                            childs =  check_and_get_all_elements_by_xpath(containers[0], './div') #containers[0].find_elements_by_xpath("./div")
                            if childs is not None:
                                galleries_count = len(childs)
                                for child in childs:
                                    a_ele = check_and_get_ele_by_tag_name(child, 'a')
                                    if a_ele is  not None:
                                        galleries_list.append(a_ele.get_attribute('href'))

        # using selenium ----------------------------------------
        else:
            #upload date
            upload_date = Get_web_ele_text_by_xpath(info_box, '//div[3]/div[1]/div/p/span' )
            if upload_date and ('ago' not in upload_date):
                try:
                    dt = datetime.datetime.strptime(upload_date, "%b %d, %Y")
                    upload_date = dt.strftime("%Y %m %d")
                except:
                    printR(f'Error converting date-time string: {upload_date}, on photo: {title}')
                    this_photo = photo(author_name=user_inputs.user_name, order=order, id='', title=title, href=photo_href, thumbnail=src, galleries='', stats = photo_stats() )      
                    photos_list.append(this_photo)
                    continue

            #views count
            views_count =  Get_web_ele_text_by_xpath(info_box, '//div/div[2]/div[3]/div[3]/div[2]/h3/span').replace(',','').replace('.','')      
                                          
            # highest pulse
            highest_pulse =  Get_web_ele_text_by_xpath(info_box, '//div/div[2]/div[3]/div[3]/div[1]/h3') 
        
            # Get votes (likes) count
            try:
                photo_likes_count_ele = WebDriverWait(driver, time_out).until(EC.presence_of_element_located((By.XPATH, '//a[@data-id="photo-likes-count"]')) )
            except  TimeoutException:
                return [], f'Time out ({time_out}s! Please try again'
            votes_count = photo_likes_count_ele.text.replace(',','').replace('.','')

            # comments count
            comments_count =  Get_web_ele_text_by_xpath(info_box, '//div/div[4]/div[2]/div/h4').split(' ')[0].replace(',','').replace('.','')

            #tags
            tags = []
            container =  check_and_get_ele_by_xpath(info_box, '//div/div[2]/div[3]/div[6]')
            if container is not None:
                a_eles = check_and_get_all_elements_by_tag_name(container, 'a')
                if a_eles is not None:
                    for item in a_eles:
                        tag = item.text                  
                        if tag is not '': tags.append(tag)
                    tags.sort()

            # get galleries list, if user logged in
            if user_inputs.password is not '':
                view_all_ele = driver.find_elements_by_xpath("//*[contains(text(), 'View all')]")
                if len(view_all_ele) == 0 or (len(view_all_ele) == 1 and view_all_ele[0].tag_name == 'script'):
                    collections_count = 0
                else:
                    view_all_ele[0].location_once_scrolled_into_view
                    view_all_ele[0].click()         
                    time.sleep(1)
                    eles = driver.find_elements_by_class_name('ant-modal-body')       
                    galleries_count = 0

                    if len(eles)> 0:
                        containers = check_and_get_all_elements_by_xpath(eles[0],'./div/div')
                        if containers is not None and len(containers)> 0:
                            childs =  check_and_get_all_elements_by_xpath(containers[0], './div') 
                            if childs is not None:
                                galleries_count = len(childs)
                                for child in childs:
                                    a_ele = check_and_get_ele_by_tag_name(child, 'a')
                                    if a_ele is  not None:
                                        galleries_list.append(a_ele.get_attribute('href'))

 
        # common
        statistics = photo_stats(upload_date=upload_date, views_count=views_count, 
                                 votes_count=votes_count, collections_count=0, 
                                 comments_count=comments_count, 
                                 highest_pulse=highest_pulse,rating=0, tags=",".join(tags) )
 
        this_photo = photo(author_name=user_inputs.user_name, order=order, id='', title=title, href=photo_href, 
                           thumbnail=src, galleries=",".join(galleries_list), stats = statistics )      

        photos_list.append(this_photo)

    return photos_list, ''

#---------------------------------------------------------------

def Get_followers_list(driver, user_inputs):
    """Given a user name, return the list of followers, the link to theis pages and the number of their followers.

    Process:
    - Open the user home page, locate the text followers and click on it to open the modal windonw containing followers list
    - Scroll to the end for all items to be loaded
    - Make sure the document js is running for all the data to load in the page body
    - ExtraCT INFO AND PUT IN A LIST. RETURN THE LIST
    """

    followers_list = []
    success, message = Open_user_home_page(driver, user_inputs.user_name)
    if not success:
        if message.find('Error reading') != -1:
            user_inputs.user_name = ''
        return None, message

    Hide_banners(driver)
    # click on the Followers text to open the modal window
    ele = check_and_get_ele_by_class_name(driver, "followers")    
    if ele is not None:
       ele.click()

    # abort the action if the target objects failed to load within a given timeout
    if not Finish_Javascript_rendered_body_content(driver, time_out=15, class_name_to_check='actors')[0]:
        return [], f"Error loading {user_inputs.user_name}'s followers page"

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

    # abort the action if the target objects failed to load within a given timeout
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

    for i, actor_info in enumerate(actor_infos):
        if i > 0:
            update_progress( i / (len(actor_infos) - 1), f' - Extracting data {i + 1}/{followers_count}:')
  
        try:
            # get user name 
            name_ele = check_and_get_ele_by_class_name(actor_info, 'name')  
            if name_ele is not None:
                follower_page_link = name_ele.get_attribute('href')
                follower_user_name = follower_page_link.replace('https://500px.com/', '')
            
            # get user avatar
            avatar_href = ''
            actor_parent_ele = check_and_get_ele_by_xpath(actor_info, '..')   
            if actor_parent_ele is not None:
                avatar_ele = check_and_get_ele_by_class_name(actor_parent_ele, 'avatar')
                if avatar_ele is not None:
                    style = avatar_ele.get_attribute('style')
                    avatar_href =  style[style.find('https'): style.find('\")')]

        except NoSuchElementException:
            continue  #ignore if follower name not found

        # if logged-in, we can determine if this user has been followed or not
        if user_inputs.password != '':
            try:          
                class_name_ele = check_and_get_ele_by_xpath(actor_info, '../..')  #class_name = actor.find_element_by_xpath('../..').get_attribute('class')
                if class_name_ele is not None:
                    class_name = class_name_ele.get_attribute('class')
                    following_status = 'Following' if class_name.find('following') != -1  else 'Not Follow'
            except NoSuchElementException:
                pass
        # get followers count
        number_of_followers = ''
        texts = actor_info.text.split('\n')
        if len(texts) > 1: 
            follower_name = texts[0] 
            count = texts[1]
            number_of_followers =  count.replace(' followers', '').replace(' follower', '') 
        
        # create user object and add it to the result list 
        followers_list.append(user(str(i+1), avatar_href, follower_name, follower_user_name, number_of_followers, following_status))
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
 
    success, message = Open_user_home_page(driver, user_inputs.target_user_name)
    if not success:
        if message.find('Error reading') != -1:
            user_inputs.target_user_name = ''
        return False, message
  
    Hide_banners(driver)     
    ele = check_and_get_ele_by_xpath(driver, '//*[@id="content"]/div[1]/div[4]/ul/li[4]')   
    
    # extract number of following                       
    following_count_ele = check_and_get_ele_by_tag_name(ele, 'span')    
    if following_count_ele is None or following_count_ele.text == '0':
        return  False, "Status unknown. Timed out on getting the Following Count"
    else:
        following_count = int(following_count_ele.text.replace(",", "").replace(".", ""))
        print(f' - User {user_inputs.target_user_name} is following {str(following_count)} user(s)')
  
    # click on the Following text to open the modal window
    if ele is not None:

       driver.execute_script("arguments[0].click();", ele)

    # abort the action if the target objects failed to load within a given timeout
    if not Finish_Javascript_rendered_body_content(driver, time_out=30, class_name_to_check='actors')[0]:
        return  False, "Status unknown. Timed out on loading more users"

    # start the progress bar
    update_progress(0, ' - Processing loaded data:')
    iteration_num = math.floor(following_count / LOADED_ITEM_PER_PAGE) + 1    

    users_done = 0
    current_index = 0   # the index of the photo in the loaded photos list. We dynamically scroll down the page to load more photos as we go, so ...
                        # ... more photos are appended at the end of the list. We use this current_index to keep track where we were after a list update 
    
 
    actor_infos = driver.find_elements_by_class_name('actor_info')
    loaded_users_count = len(actor_infos)
    while users_done < following_count: 
        # check if we have processed all loaded users, then we have to load more  
        if current_index >= loaded_users_count: 
            prev_loaded_users = loaded_users_count
            # loading more users by scrolling into view the last loaded item
            last_item_on_page =  current_index -1  #i * LOADED_ITEM_PER_PAGE - 1
            try:
                last_loaded_item = check_and_get_ele_by_xpath(driver, '//*[@id="modal_content"]/div/div/div/div/div[2]/ul/li[' + str(last_item_on_page) + ']')                                                                   
                if last_loaded_item is not None:
                    last_loaded_item.location_once_scrolled_into_view
                    time.sleep(1)
            except NoSuchElementException:
                pass

            # abort the action if the target objects failed to load within a given timeout 
            if not Finish_Javascript_rendered_body_content(driver, time_out=30, class_name_to_check='finished')[0]:
               return  False, "Status unknown. Timed out loading more user"
            time.sleep(1)

            # update list with more users
            actor_infos = driver.find_elements_by_class_name('actor_info')
            time.sleep(1)
            loaded_users_count = len(actor_infos)
 
            # stop when all photos are loaded
            if loaded_users_count == prev_loaded_users:
                if loaded_users_count < following_count:
                    return False, f'Status unknown. Timed out {loaded_users_count}/{following_count}'
                break;

        following_user_name = ''
        following_user_page_link = ''
        for i in range(current_index, min(loaded_users_count, following_count)):
            if current_index > loaded_users_count: 
                break
            current_index += 1
            actor = actor_infos[i]
            update_progress(current_index / following_count, f' - Processing loaded data {current_index}/{following_count}:')  
            try:
                ele = check_and_get_ele_by_class_name(actor, 'name')  
                if ele is not None:
                    following_user_page_link = ele.get_attribute('href')
                    following_user_name = following_user_page_link.replace('https://500px.com/', '')

                    if following_user_name is not None and following_user_name == user_inputs.user_name:
                        update_progress(1, f' - Processing loaded data {current_index}/{following_count}:')
                        return True, f'Following you ({current_index}/{following_count})'

            except NoSuchElementException:
                continue  #ignore if follower name not found
        users_done = current_index
    return False, "Not following"

#---------------------------------------------------------------
# This is a time-consuming process, in need for a better solution, either limiting the request number, or doing it in a certain range ( in-progress)
def Get_following_statuses(driver, user_inputs, output_lists, csv_file):
    """ Get the follow statuses of the users that you are following, with the option to specify the range of user in the following list.
   
    start_user_index IS 1-BASED AND WILL BE CONVERTED TO 0-BASED
    number_of_users : THIS IS A LENGTHY PROCESS, SO WE PROVIDE THIS OPTION TO LIMIT THE NUMBER OF USERS WE WILL PROCESS. PASSING -1 TO IGNORE THIS LIMIT
    """

    # do main task
    df = pd.read_csv(csv_file, encoding='utf-16') #, usecols=["User Name"])     
    # a trick to force column Status content as string instead of the default float      
    df.Status = df.Status.fillna(value="")             
    # make sure the user's inputs stay in range with the size of the following list
    #followings_count = df.shape[0]
    user_inputs.index_of_start_user = min(user_inputs.index_of_start_user, df.shape[0] -1)
    print('Updating the following statuses on')
    printY(f'{csv_file}')
    print(f'({user_inputs.number_of_users} users, starting from {user_inputs.index_of_start_user + 1}) ...')
   
    # process each user in dataframe
    count = 0
    for index, row in df.iterrows():
        if index < user_inputs.index_of_start_user:
            continue
        if user_inputs.number_of_users != -1 and index > user_inputs.index_of_start_user + user_inputs.number_of_users - 1:
            break
        user_inputs.target_user_name = row["User Name"]
        count += 1
        #print(f'User {user_inputs.target_user_name} {count}(index {index})/{user_inputs.number_of_users}:')
        print(f'User {count}/{user_inputs.number_of_users} (index {index + 1}):')
        result, message = Does_this_user_follow_me(driver, user_inputs)
        if result == True:
            printG('- ' + message)
            # update the status column in the dataframe with following status
            df.at[index, 'Status'] = message 
        else:
            printR('- ' + message) if 'User name not found' in message else printY('- ' + message)
            continue
    try:
        # write back dataframe to csv file
        df.to_csv(csv_file, encoding='utf-16', index = False)
        #return csv_file
    except: # pd.Errors.csv_file:
        printR(f'Error writing file {os.path.abspath(csv_file)}.\nMake sure the file is not in use. Then type r for retry >')
        retry = input()
        if retry == 'r': 
            df.to_csv(csv_file, encoding='utf-16', index = False)
            #return csv_file
        else:
            printR('Error writing file' + os.path.abspath(csv_file))
            #return ''


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
    success, message = Open_user_home_page(driver, user_inputs.user_name)
    if not success:
        if message.find('Error reading') != -1:
            user_inputs.user_name = ''
        return [], message

    Hide_banners(driver)                  
                                          
    # click on the Following text to open the modal window
    ele = check_and_get_ele_by_xpath(driver, '//*[@id="content"]/div[1]/div[4]/ul/li[4]')     
    if ele is not None:
        ele.click()
    
    # abort the action if the target objects failed to load within a given timeout    
    success, _  = Finish_Javascript_rendered_body_content(driver, time_out=15, class_name_to_check='actors')
    if not success:
        return [], 'Error loading'
            
    # extract number of following                      
    following_ele = check_and_get_ele_by_xpath(driver, '//*[@id="modal_content"]/div/div/div/div/div[1]/span') 
    if following_ele is None:
        return [], ''

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
    update_progress(0, ' - Extracting data 0/{following_count}:')
    actor_infos = driver.find_elements_by_class_name('actor_info')
    lenght = len(actor_infos)
    following_name = ''
    followings_page_link = ''
    count = '' 

    for i, actor_info in enumerate(actor_infos):
        if i > 0:
            update_progress( i / (len(actor_infos) - 1), f' - Extracting data {i + 1}/{following_count}:')

        try:
            # get user name 
            ele = check_and_get_ele_by_class_name(actor_info, 'name')
            if ele is not None:
                following_page_link = ele.get_attribute('href')
                following_user_name = following_page_link.replace('https://500px.com/', '')

            # get user avatar
            avatar_href = ''
            actor_info_parent_ele = check_and_get_ele_by_xpath(actor_info, '..')   
            if actor_info_parent_ele is not None:
                avatar_ele = check_and_get_ele_by_class_name(actor_info_parent_ele, 'avatar')
                if avatar_ele is not None:
                    style = avatar_ele.get_attribute('style')
                    avatar_href =  style[style.find('https'): style.find('\")')]

        except NoSuchElementException:
            printR(f'Error getting an user')
            continue  #ignore if either follower name or id or avatar not found

        # get followers count
        texts = actor_info.text.split('\n')
        if len(texts) > 0: following_name = texts[0] 
        if len(texts) > 1: count = texts[1]; 
        number_of_followers =  count.replace(' followers', '').replace(' follower', '')  

        # create user object and add it to the result list 
        followings_list.append(user(str(i+1), avatar_href, following_name, following_user_name, number_of_followers))
    return followings_list, '' 

#---------------------------------------------------------------
def Process_notification(item, request_number, notifications_list):
    """Given a notification element, extract detail info from it into a notification object, then append the object to the notification list. 
       Show the progress bar on console

       THE ARGUMENT 'notifications_list' IS ALSO SERVED AS AN OUTPUT (IT IS MUTABLE OBJECT) 
    """

    count_sofar = len(notifications_list)
    # do nothing if the request number of notifications is reached
    if count_sofar >=  request_number:
        return 
  
    # get user_name, display_name
    actor = check_and_get_ele_by_class_name(item, 'notification_item__actor') 
    if actor is None:
        return
    display_name = actor.text

    # ignore Quest notification
    user_name = actor.get_attribute('href').replace('https://500px.com/', '')
    if 'quests/' in user_name:
        return 

    # get user avatar
    user_avatar = ''
    avatar_ele = check_and_get_ele_by_class_name(item, 'notification_item__avatar_img') 
    if avatar_ele is None:
        return 
    user_avatar = avatar_ele.get_attribute('src')        

    count_sofar += 1

    # advance the progress bar
    update_progress(count_sofar/request_number, f' - Extracting data {count_sofar}/{request_number}:') 
          
    # the type of notificication
    item_text = check_and_get_ele_by_class_name(item, 'notification_item__text')  
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

    # photo title, photo link
    photo_ele = check_and_get_ele_by_class_name(item_text, 'notification_item__photo_link')
    photo_title = ''
    photo_link = ''        
    status = ''
    # in case of a new follow, instead of a photo element, there will be 2 overlapping boxes, Follow and Following. We will determine if whether or not this actor has been followered  
    if photo_ele is None:  
        following_box = check_and_get_ele_by_class_name(item, 'following')
        if following_box is not None and following_box.is_displayed():        
            status = 'Following'
        else:  
            status = 'Not Follow' 
 
    else: 
        photo_title = photo_ele.text
        photo_link = photo_ele.get_attribute('href') 

    # get photo thumbnail
    photo_thumbnail = ''
    photo_thumb_ele = check_and_get_ele_by_class_name(item, 'notification_item__photo_img') 
    if photo_thumb_ele is not None:
        photo_thumbnail = photo_thumb_ele.get_attribute('src')
        
    # time stamp
    ele = check_and_get_ele_by_class_name(item, 'notification_item__timestamp')  
    timestamp  = ele.text if ele is not None else ""

    # creating the notification object
    new_notitication_item = notification(order=str(count_sofar), user_avatar=user_avatar, display_name=display_name, username=user_name, 
                                        content=content, photo_thumb=photo_thumbnail, photo_link=photo_link, photo_title=photo_title, timestamp=timestamp, status=status)
    notifications_list.append(new_notitication_item)
   
    return

#---------------------------------------------------------------

def Process_notification_element(notification_element):
    """Given a notification element, extract detail info from it into a notification object, then append the object to the notification list. 
       Show the progress bar on console

       THE ARGUMENT 'notifications_list' IS ALSO SERVED AS AN OUTPUT (IT IS MUTABLE OBJECT) 
    """

    # get user_name, display_name
    actor = check_and_get_ele_by_class_name(notification_element, 'notification_item__actor') 
    if actor is None:
        return None
    display_name = actor.text

    # ignore Quest notification
    #user_name = actor.get_attribute('href')
    user_name = actor.get_attribute('href').replace('https://500px.com/', '')

    if 'quests/' in user_name:
        return None

    # get user avatar
    user_avatar = ''
    avatar_ele = check_and_get_ele_by_class_name(notification_element, 'notification_item__avatar_img') 
    if avatar_ele is None:
        return None
    user_avatar = avatar_ele.get_attribute('src')        

    # the type of notificication
    item_text = check_and_get_ele_by_class_name(notification_element, 'notification_item__text')  
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

    # photo title, photo link
    photo_ele = check_and_get_ele_by_class_name(item_text, 'notification_item__photo_link')
    photo_title, photo_link, status = '', '', ''
 
    # in case of a new follow, instead of a photo element, there will be 2 overlapping boxes, Follow and Following. We will determine if whether or not this actor has been followered  
    if photo_ele is None:  
        following_box = check_and_get_ele_by_class_name(notification_element, 'following')
        if following_box is not None and following_box.is_displayed():        
            status = 'Following'
        else:  
            status = 'Not Follow' 
 
    else: 
        photo_title = photo_ele.text
        photo_link = photo_ele.get_attribute('href') 

    # get photo thumbnail
    photo_thumbnail = ''
    photo_thumb_ele = check_and_get_ele_by_class_name(notification_element, 'notification_item__photo_img') 
    if photo_thumb_ele is not None:
        photo_thumbnail = photo_thumb_ele.get_attribute('src')
        
    # time stamp
    ele = check_and_get_ele_by_class_name(notification_element, 'notification_item__timestamp')  
    timestamp  = ele.text if ele is not None else ""

    # creating and return the notification object
    return notification(order=0, user_avatar=user_avatar, display_name=display_name, username=user_name, 
                        content=content, photo_thumb=photo_thumbnail, photo_link=photo_link, photo_title=photo_title, timestamp=timestamp, status=status)
   
#---------------------------------------------------------------
def Process_notifications(request_number, items):

    notifications =[]
    for i, item in enumerate(items):
        count_sofar = len(notifications)    
        if count_sofar >= request_number:
            break
        
        new_notification = Process_notification_element(item)
        if new_notification is not None:
            count_sofar += 1
            new_notification.order = count_sofar
            notifications.append(new_notification)
            # advance the progress bar
            update_progress(count_sofar/request_number, f' - Extracted data {count_sofar}/{request_number}:') 
    return notifications

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

    unique_notificators, notifications_list, simplified_list = [],[], []

    Scroll_down_active_page(driver, None, 'notification_item__photo_link', '', user_inputs.number_of_notifications, ' - Scrolling down for more notifications:' ) 

    # get the info now that all we got all the available notifications
    items = driver.find_elements_by_class_name('notification_item')  


    ## main task no mp
    #for i, item in enumerate(items): 
    #    Process_notification(i, item, user_inputs.number_of_notifications, notifications_list)
    notifications_list = Process_notifications(user_inputs.number_of_notifications, items)
    
    if len(notifications_list) == 0 and len(unique_notificators) == 0: 
        printG(f'User {user_inputs.user_name} has no notification')
        return [], []

    # create the simplified list from the notifications list for easy manipulation
    simplified_list = [f'{item.user_avatar},{item.display_name.replace(",", " ")},{item.username}' for item in notifications_list]
    
    # extract the unique users and the number of times they appear in the notifications list  
    unique_notificators = Count_And_Remove_Duplications(simplified_list)

    # add order number at the beginning of each row
    for j in range(len(unique_notificators)):
        unique_notificators[j] = f'{str(j+1)},{unique_notificators[j]}'


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
    time_out = 20
    actioners_list = []
    date_string = datetime.datetime.now().replace(microsecond=0).strftime(DATE_FORMAT)

    try:  
        info_box = WebDriverWait(driver, time_out).until(EC.presence_of_element_located((By.XPATH, '//*[@id="root"]/div[3]/div/div[2]')) )
    except  TimeoutException:
        printR(f'Time out ({time_out}s)! Please try again')
        return [], ''
  
    print(' - Getting photo details ...')
    # get photographer name
    photographer_ele = check_and_get_ele_by_xpath(info_box, '//div[2]/div[1]/p[1]/span/a')
    if photographer_ele is None: 
        photographer_name = ''
        printR('Error getting photographer name')
    else:
        photographer_name = photographer_ele.text
        printG(f'   Photogapher: {photographer_name}')

    # get photo title
    title_ele = check_and_get_ele_by_xpath(info_box, '//div[2]/div[1]/h3')
    if title_ele is None: 
        photo_title = ''
        printR('Error getting photo title')
    else:
        photo_title = title_ele.text
        printG(f'   Photo title: {photo_title}')

    # Get the like-count-button and click on it to open the modal window that host the actioners list
    try:
        photo_likes_count_ele = WebDriverWait(driver, time_out).until(EC.presence_of_element_located((By.XPATH, '//a[@data-id="photo-likes-count"]')) )
    except  TimeoutException:
        printR(f'Time out ({time_out}s! Please try again')
        return [], ''

    likes_count_string = photo_likes_count_ele.text
    likes_count = int(likes_count_string.replace('.','').replace(',',''))
    printG(f"   This photo has {likes_count} likes")

    photo_likes_count_ele.click()
    
    try:
        WebDriverWait(driver, time_out).until( EC.presence_of_element_located((By.CLASS_NAME, 'ant-modal-body')) )
    except  TimeoutException:
        printR(f'Time out ({time_out}s! Not all elements are loaded. You may try again later.')
 
    # make a meaningful output file name
    like_actioners_file_name = os.path.join(output_lists.output_dir, \
        f"{photographer_name.replace(' ', '-')}_{likes_count}_likes_{photo_title.replace(' ', '-')}_{date_string}.csv")

    #get a container element containing all actors
    container= check_and_get_ele_by_class_name(driver,'ant-modal-body')
    time.sleep(2)
    if container is None:
        return [], ''
    #scrolling down until all the actors are loaded
    img_eles = Scroll_to_end_by_tag_name_within_element(driver, container, 'img', likes_count)
    #Scroll_down_active_page(driver, container, '', 'img', likes_count, ' - Scrolling down for more items:' ) 
   
    # create actors list
    actors_count = len(img_eles )
    display_name = ''
    u_name = ''
    followers_count = ''
    avatar = ''
    for i, img in enumerate(img_eles):
        update_progress(i / (actors_count - 1), f' - Extracting data {i+1}/{actors_count}:')
        try: 
            display_name = img.get_attribute('alt')
            avatar= img.get_attribute('src')
            img_ele_parent =  check_and_get_ele_by_xpath(img, '..')
            if img_ele_parent is None:
                continue
            u_name = img_ele_parent.get_attribute('href').replace('https://500px.com/','')

            follower_count_text_ele =  check_and_get_ele_by_xpath(img_ele_parent, '..') 
            if follower_count_text_ele is None: 
                continue
            texts = follower_count_text_ele.text.split('\n')
            if len(texts) > 1:
                followers_count  = re.sub('[^\d]+', '', texts[1]) 
            
            # get following status
            following_status = 'Not follow'
            following_status_ele = check_and_get_ele_by_xpath(img, '../../../../div[2]/a/span')
            if following_status_ele is None:
                continue
            if 'Unfollow' in following_status_ele.get_attribute("innerHTML"):
                following_status = 'Following'

            actioners_list.append(user(str(i+1), avatar, display_name, u_name, str(followers_count), following_status) )
        except NoSuchElementException:
            continue
         
    return actioners_list, like_actioners_file_name 
#---------------------------------------------------------------
def Like_n_photos_from_user(driver, target_user_name, number_of_photos_to_be_liked, include_already_liked_photo_in_count = True, close_browser_on_error = True):
    """Like n photo of a given user, starting from the top. Return False and error message if error occured, True and blank string otherwise

    IF THE include_already_liked_photo IS TRUE (DEFAULT), THE ALREADY-LIKED PHOTO WILL BE COUNTED AS DONE BY THE AUTO-LIKE PROCESS
    FOR EXAMPLE, IF YOU NEED TO AUTO-LIKE 3 PHOTOS FROM A USER, BUT TWO PHOTOS IN THE FIRST THREE PHOTOS ARE ALREADY LIKED, 
    THEN YOU ONLY NEED TO DO ONE
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

    success, message = Open_user_home_page(driver, target_user_name)
    if not success:
        #if message.find('Error reading') != -1:
        #    user_inputs.target_user_name = ''
        return False
    
    # pause a random time between 0.5s, 1.5s for human-like effect
    time.sleep(random.randint(5, 10) / 10)   
    # abort the action if the target objects failed to load within a given timeout    
    success = Finish_Javascript_rendered_body_content(driver, time_out=30, class_name_to_check='finished')[0]
    if not success:
        printR(f"Error loading user {user_inputs.target_user_name}'s photo page")
        return False, 
    time.sleep(random.randint(5, 10) / 10)   

    Hide_banners(driver)        
    
    new_fav_icons =  check_and_get_all_elements_by_css_selector(driver, '.button.new_fav.only_icon') 
    time.sleep(random.randint(5, 10) / 10)   
    if len(new_fav_icons) == 0:
        printY('  - user has no photos')
    done_count = 0

    for i, icon in enumerate(new_fav_icons):
        icon.location_once_scrolled_into_view
        # skip already-liked photo. Count it as done if requested so
        if done_count < number_of_photos_to_be_liked and 'heart' in icon.get_attribute('class'): 
            if include_already_liked_photo_in_count == True:
                done_count = done_count + 1          
            printY(f'  - liked #{str(done_count):3} Photo { str(i+1):2} - already liked')

            continue        

        # check limit
        if done_count >= number_of_photos_to_be_liked:  
            break
        
        Hover_by_element(driver, icon) # not necessary, but good for visual demonstration
        time.sleep(random.randint(5, 10) / 10)
        try:
            title =  icon.find_element_by_xpath('../../../../..').find_element_by_class_name('photo_link').find_element_by_tag_name('img').get_attribute('alt')
            driver.execute_script("arguments[0].click();", icon) 
            done_count = done_count + 1
            printG(f'  - liked #{str(done_count):3} Photo {str(i + 1):2} - {title:.50}')
            # pause a randomized time between 0.5 to 2 seconds between actions 
            #time.sleep(random.randint(5, 20) / 10)

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
    title = ''
    photographer = ''
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
                time.sleep(random.randint(10,25)/10)  

                photo_link = icon.find_element_by_xpath('../../../../..').find_element_by_class_name('photo_link')
                title =  photo_link.find_element_by_tag_name('img').get_attribute('alt')
                photographer_ele = check_and_get_ele_by_class_name(photo_link, 'photographer')

                if photographer_ele is not None:
                    photographer_ele.location_once_scrolled_into_view
                    Hover_by_element(driver, photographer_ele)
                    photographer = photographer_ele.text
                    photographer_ele.location_once_scrolled_into_view
                    Hover_by_element(driver, photographer_ele)
                    photographer = photographer_ele.text
                else:
                # if the current photos page is a user's gallery, there would be no photographer class.
                # We will extract the photographer name from the photo href, replacing any hex number in it with character, for now '*'
                    href =  photo_link.get_attribute('href')
                    subStrings = href.split('-by-')
                    if len(subStrings) > 1:
                        photographer =  re.sub('%\w\w', '*', subStrings[1].replace('-',' '))

                driver.execute_script("arguments[0].click();", icon) 
                photos_done = photos_done + 1

                printG(f'Liked {str(photos_done):>3}/{number_of_photos_to_be_liked:<3}, {photographer:<28.24}, Photo {str(i+1):<4} title {title:<35.35}')
            except Exception as e:
                printR(f'Error after {str(photos_done)}, at index {str(i+1)}, title {title}:\nException: {e}')
                printY('The page structure of this photo gallery is not recognizable. The process will stop.')
                # we set this to end the outer loop, while:
                photos_done = number_of_photos_to_be_liked
                break

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
        time.sleep(1)
					    
        # abort the action if the target objects failed to load within a given timeout    
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

            parent2_sib2 =  check_and_get_ele_by_xpath(parent2_sib1, './following-sibling::div') 
            if parent2_sib2 is  None: 
                continue    
            # for logging message, get photo title, photogragpher display name and  user name
            title_ele = check_and_get_ele_by_tag_name(parent2_sib2, 'h3') #title  = parent2_sib2.find_element_by_tag_name('h3').text            
            title = title_ele.text if title_ele is not None else 'not determined'
           
            a_ele = check_and_get_ele_by_tag_name(parent2_sib2, 'a')  #a = parent2_sib2.find_element_by_tag_name('a')
            photographer_display_name  = a_ele.text if a_ele is not None else "not determined"
            photographer_name = a_ele.get_attribute('href').replace('https://500px.com/', '') if a_ele is not None else "not determined"

            child_div_eles = check_and_get_all_elements_by_tag_name(parent2_sib1, 'div')
            if len(child_div_eles) > 2:
                heart_icon = child_div_eles[2]
                #get like status
                photo_already_liked = False
                svg_ele = check_and_get_ele_by_tag_name(heart_icon, 'svg')
                if svg_ele is not None:
                    title_ele = check_and_get_ele_by_tag_name(svg_ele, 'title')
                    if title_ele is not None:     
                        like_status = title_ele.get_attribute('innerHTML')
                        # skip if the photo is one of yours
                        if like_status.find('disabled') != -1:
                            printB(f'Skipped:      photo {str(i + 1):3}, from {photographer_display_name:<32.30}, {title:<35.35}')
                            continue                           
                        elif like_status.find('Filled') != -1:  # already liked: 'Filled', not-yet like: 'Outline', your own photo: 'disabled'
                            photo_already_liked = True
                        if  not photo_already_liked:      
                            # skip consecutive photos of the same photographer
                            if photographer_name == prev_photographer_name:
                                printY(f'Skipped:      photo {str(i + 1):3}, from {photographer_display_name:<32.30}, {title:<35.35}')
                                continue
                            if heart_icon is not None:
                                Hover_by_element(driver, heart_icon)
                                driver.execute_script("arguments[0].click();", heart_icon) 
                                photos_done += 1
                                prev_photographer_name = photographer_name
                                printG(f'Like {photos_done:>3}/{user_inputs.number_of_photos_to_be_liked:<3}: photo {str(i + 1):<3}, from {photographer_display_name:<32.30}, {title:<40.40}')
                                time.sleep(random.randint(10,20)/10)  # slow down a bit to make it look more like a human

#---------------------------------------------------------------
def Count_And_Remove_Duplications(values):
    """Given a list containing the strings of display name and user name separated by a comma such as "John Doe, johndoe, http://..." .
       Count the  duplication then remove the duplicated entry. Append the count to each entry's count column.
       An output list item has this form: "John Doe, johndoe, http://..., count ". """

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
                if len(list_items) == 4:
                    new_count = int(list_items[3]) + 1
               # elif len(list_items) == 4: # just in crazy situation where display name has comma in it 
               #     new_count = int(list_items[3]) + 1
                output[index] = f'{list_items[0]},{list_items[1]},{list_items[2]},{new_count}'
            except:
                continue
    return output    


#---------------------------------------------------------------
def Scroll_down_active_page(driver, web_element, class_name_to_check, tag_name_to_check, number_of_items_requested = 100, message = '', time_out= 60):
    """Scrolling down the active window until all the request items of a given class name or a tag name, are loaded.

    - THE PROCESS MONITORS THE CHANGE OF THE PAGE HEIGHT TO DECIDE IF ANOTHER SCROLL DOWN IS NEEDED
      AFTER A SCROLL DOWN, IF THE SERVER FAILS TO LOAD NEW ITEMS WITHIN A GIVEN TIME OUT (DEFAULT IS 60s), THE PROCESS WILL STOP 
    - IF BOTH CLASS NAME AND TAG NAME ARE GIVEN, CLASS NAME TAKE PRIORITY. IF NONE IS GIVEN, NO ACTION IS TAKEN
    - MESSAGE IS THE TEXT SHOWN ON THE PROGRESS BAR

"""
    if web_element is None:
        web_element = driver    
    if class_name_to_check: 
        items = web_element.find_elements_by_class_name(class_name_to_check) 
    elif tag_name_to_check: 
        items = web_element.find_elements_by_tag_name(tag_name_to_check) 
    else:
        printR('Items were not specified. The process stopped.')
        return
    if items is None or len(items) == 0:
        printR('No items found.')
        return
      
    if len(items) >= number_of_items_requested:
        return    
     
    # get the current height of the page
    last_scroll_height = driver.execute_script("return document.body.scrollHeight")

    time_out_count_down = time_out
    count_sofar = 0
    if number_of_items_requested == -1:
        number_of_items_requested  = MAX_NOTIFICATION_REQUEST

    while count_sofar < number_of_items_requested :   
        update_progress(count_sofar / number_of_items_requested, f' - Scrolling down {count_sofar}/{number_of_items_requested}')
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
            printR(f'\r Time out ({time_out}s)! {count_sofar}/{number_of_items_requested} items obtained. You may try again at another time')
            break
 
    # normal termination of while loop: show completed progress bar
    else:
        update_progress(1, f' - Scrolling down {number_of_items_requested}/{number_of_items_requested}')


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
            the_last_in_list = eles[-1]
            the_last_in_list.location_once_scrolled_into_view 
            #time.sleep(1)
            WebDriverWait(driver, timeout = 10).until(EC.visibility_of(the_last_in_list))
            count = new_count
            eles = driver.find_elements_by_class_name(class_name)
            new_count = len(eles)
        except TimeoutException :
            printR(f'Time out while scrolling down. Please retry.')
        except NoSuchElementException:
            pass
    if new_count < likes_count:
        update_progress(1, ' - Scrolling to load more items:{likes_count}/{likes_count}')

#---------------------------------------------------------------
def Scroll_to_end_by_tag_name_within_element(driver, element, tag_name, likes_count):
    """Scroll the active window to the end, where the last element of the given tag name is loaded and visible.

    THE likes_count ARGUMENT IS USED FOR SHOWING A REALISTIC PROGRESS BAR
    """
    eles = check_and_get_all_elements_by_tag_name(element, tag_name)
    count = 0
    new_count = len(eles)
    time_out = 20
    count_down_timer = time_out
    while new_count != count:
        try:
            update_progress(new_count / likes_count, f' - Scrolling to load more items {new_count}/{likes_count}:')
            the_last_in_list = eles[-1]
            the_last_in_list.location_once_scrolled_into_view 
            time.sleep(1)
            WebDriverWait(driver, time_out).until(EC.visibility_of(the_last_in_list))
            count = new_count
            eles = check_and_get_all_elements_by_tag_name(element, tag_name)
            new_count = len(eles)

            # give the slow server a chance to load the new items 
            while new_count == count and count_down_timer >= 0 and new_count < likes_count:
                count_down_timer -= 1
                the_last_in_list.location_once_scrolled_into_view 
                time.sleep(1)

        except TimeoutException :
            printR(f'Time out ({time_out}s) while scrolling down. Please retry.')
        except NoSuchElementException:
            pass
    if new_count < likes_count:
        update_progress(1, ' - Scrolling to load more items:{likes_count}/{likes_count}')
    return eles

#---------------------------------------------------------------
def Login(driver, user_inputs):
    """Submit given credentials to the 500px login page. Display error message if error occured. Return True/False loggin status 
    """

    if len(user_inputs.password) == 0 or len(user_inputs.user_name) == 0 or driver == None: 
        return False
    time_out = 30
    driver.get("https://500px.com/login" )
    try:
        user_name_ele = WebDriverWait(driver, time_out).until(EC.presence_of_element_located((By.ID, 'emailOrUsername'))) # 'email')))
        user_name_ele.send_keys(user_inputs.user_name) 
        
        pwd_ele = WebDriverWait(driver, time_out).until(EC.presence_of_element_located((By.ID, 'password')))
        pwd_ele.send_keys(user_inputs.password) 

        submit_ele =  check_and_get_ele_by_xpath(user_name_ele, '../following-sibling::button') 
        if submit_ele is not None: 
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
    
    if not input_string or not file_name:
        return

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
def CSV_photos_list_to_HTML(csv_file_name, ignore_columns=[]):
    """Create a html file from a given photos list csv  file. Save it to disk and return the file name.

    SAVE THE HTML FILE USING THE SAME NAME BUT WITH EXTENSION '.html'
    EXPECTING THE FIRST LINE TO BE THE COLUMN HEADERS, WHICH ARE  No, Page, ID, Title, Link, Src
    HIDE THE COLUMNS IN THE GIVEN ignore_columns LIST, BUT THE DATA IN THESE COLUMNS ARE USED TO FORM THE WEB LINK TAG <a href=...>
    """
    CUSTOMED_COLUMN_WIDTHS = """
    <colgroup>
		<col style="width:4%">
		<col style="width:21%">
		<col span= "3" style="width:6%" >
		<col style="width:14%">	
		<col style="width:7%" >
		<col style="width:6%" >
		<col style="width:25%" >				
	</colgroup>
    """

# file name and extension check
    file_path, file_extension = os.path.splitext(csv_file_name)
    if file_extension != ".csv":
        return None

    html_file = file_path + '.html'

    # Create the document description based on the given file name.
    # Ref: Photo list filename:  [path]\_[user name]\_[count]\_[types of document]\_[date].html
    # Example of filename: C:\ProgramData\500px_Apiless\Output\johndoe_16_photos_2019-06-17.html
    file_name = file_path.split('\\')[-1]
    splits = file_name.split('_')
    title_string = ''
    if len(splits) >=4:
        title_string = f'\
    <h2>Photo lists ({splits[1]})</h2>\n\
    <p> User / Date: {splits[0]} / {splits[-1]}</p>\n\
    <p> File: {html_file} </p>\n'

    with open(csv_file_name, newline='', encoding='utf-16') as csvfile:
        reader = csv.DictReader(row.replace('\0', '') for row in csvfile)
        headers = reader.fieldnames

        row_string = '\t<tr>\n'
        # Ref:
        # Columns    : 0   1   2            3     4           5      6      7         8                      9              10      11    12  
        # Photo List : No, ID, Photo Title, Href, Thumbnail,  Views, Likes, Comments, Featured In Galleries, Highest Pulse, Rating, Date, Tags

        # write headers and assign sort method for appropriate columns   
        # each header cell has 2 DIVs: the left DIV for the header name, the right DIV for sort direction arrows     
        ignore_columns_count = 0
        for i, header in enumerate(reader.fieldnames):
            if header == 'Comments':
                header = 'Com-<br>ments'
            elif header == 'Highest Pulse':
                header = 'Highest<br>Pulse'    
                
            if header in ignore_columns:
                ignore_columns_count += 1
                continue  
            
            sort_direction_arrows = f"""
            <div class="hdr_arrows">
				<div id ="arrow-up-{i-ignore_columns_count}">&#x25B2;</div>
				<div id ="arrow-down-{i-ignore_columns_count}">&#x25BC;</div></div>"""

            left_div = f'''
            <div class="hdr_text">{header}</div>'''

            if header == "No":
                first_left_div = f'\t\t\t<div class="hdr_text">{header}</div>'
                # the No column is initially in ascending order, so we donot show the down arrow
                ascending_arrow_only = f"""
                <div class="hdr_arrows">
				    <div id ="arrow-up-{i-ignore_columns_count}">&#x25B2;</div>
				    <div id ="arrow-down-{i-ignore_columns_count}" hidden>&#x25BC;</div></div>"""
                row_string += f'\t\t<th onclick="sortTable({i-ignore_columns_count})">\n{first_left_div}{ascending_arrow_only}</th>\n'
            
            elif header == "Photo Title":
                row_string += f'\t\t<th onclick="sortTable({i-ignore_columns_count}, true)">{left_div}{sort_direction_arrows}</th>\n'

            else:
                row_string += f'\t\t<th onclick="sortTable({i-ignore_columns_count})">{left_div}{sort_direction_arrows}</th>\n'

        # write each row 
        row_string += '\t</tr>\n'
        for row in reader:
            row_string += '\t<tr>\n'
            for i in range(len(headers) ):
                col_header = headers[i]
                if col_header in ignore_columns:
                    continue  
                text = row[headers[i]]     
                # In Photo Tile column, show photo thumbnail and photo title with <a href> link
                if  col_header == 'Photo Title': 
                    # write empty html tags if photo thumbnail is empty
                    if row[headers[5]] == '':
                        row_string += f'\t\t<td><div"><div>{text}</div></div></td> \n' 
                    else:
                        photo_thumbnail = row[headers[4]]
                        photo_link =  row[headers[3]]                 
                        row_string += f'\t\t<td>\n\t\t\t<div>\n\t\t\t\t<a href="{photo_link}" target="_blank">\n'
                        row_string += f'\t\t\t\t<img class="photo" src={photo_thumbnail}></a>\n'
                        row_string += f'\t\t\t\t<div><a href="{photo_link}" target="_blank">{text}</a></div></div></td>\n'
                elif  col_header == 'Tags':
                    row_string += f'\t\t<td class="alignLeft">{text}</td> \n' 
                
                elif  col_header == 'Featured In Galleries' and text != '':
                    # a gallery link has this format: https://500px.com/[photographer_name]/galleries/[gallery_name]
                    row_string += f'\t\t<td>\n'
                    galleries = text.split(',')
                    for j, gallery in enumerate(galleries):
                        gallery_name = gallery[gallery.rfind('/') + 1:]    
                        row_string += f'\t\t\t<a href="{gallery}" target="_blank">{gallery_name}</a>'
                        if j < len(galleries) -1:
                            row_string += ',\n'                    
                    row_string += f'\t\t</td> \n'
                                
                else: 
                    row_string += f'\t\t<td>{text}</td> \n' 
            row_string += '\t</tr>\n'

        html_string = f'<html>\n{HEAD_STRING_WITH_CSS_STYLE}\n\n<body> \n{title_string}<table> {CUSTOMED_COLUMN_WIDTHS}\n{row_string} </table>\n{SCRIPT_STRING}</body> </html>'

        #write html file 
        with open(html_file, 'wb') as htmlfile:
            htmlfile.write(html_string.encode('utf-16'))

    return html_file

#--------------------------------------------------------------- 
def CSV_to_HTML(csv_file_name, ignore_columns=[]):
    """ Convert csv file of various types into html file and write it to disk . Return the saved html filename.
    
    EXPECTED 5 CSV FILES TYPES: Notifications list , Unique users list, Followers list, Followings list, List of users who like a photo.
    THE SAVED HTML FILE HAS THE SAME NAME BUT WITH EXTENSION '.HTML' 
    EXPECTING FIRST LINE IS COLUMN HEADERS, WHICH VARIES DEPENDING ON THE CSV TYPES
    THE ARGUMENT ignore_columns IS A LIST OF THE COLUMN HEADERS FOR WHICH WE WANT TO HIDE THE ENTIRE COLUMN
    """
    if csv_file_name == '':
        return ''
    # file extension check
    file_path, file_extension = os.path.splitext(csv_file_name)
    if file_extension != ".csv":
        return ''

    html_full_file_name = file_path + '.html'

    # Create document title and description based on these predefined file names:
    # Notifications   :    [user name]_[count]_notifications_                       [date].html
    # Unique users    :    [user name]_[count]_unique-users-last-n-notifications_   [date].html
    # Followers List  :    [user name]_[count]_followers_                           [date].html
    # Followings List :    [user name]_[count]_followings_                          [date].html
    # Users like photo:    [user name]_[count]_likes_[photo title]_                 [date].html

    file_name = file_path.split('\\')[-1]
    splits = file_name.split('_')  
    title = ''
    title_string = ''
    table_width =  'style="width:500"'
    if len(splits) >=4:
        if 'unique' in html_full_file_name:
            parts = splits[2].split('-')
            title = f'{splits[1]} unique users in the last {parts[-1]} notifications'
            table_width = 'style="width:310"'
        elif 'notifications' in html_full_file_name:
            title = f'Last {splits[1]} notifications'
            table_width =  'style="width:80%"'
        elif 'followers' in html_full_file_name:
            title = f'List of {splits[1]} followers'
        elif 'followings' in html_full_file_name:
            title = f'List of {splits[1]} followings'
            table_width = 'style="width:500"'
        elif 'likes' in html_full_file_name:
            title = f'List of {splits[1]} users who liked photo {splits[-2].replace("-", " ")}'
        
        title_string = f'\
    <h2>{title}</h2>\n\
    <p> User / Date: {splits[0]} / {splits[-1]}</p>\n\
    <p> File: {html_full_file_name} </p>\n'
 
    with open(csv_file_name, newline='', encoding='utf-16') as csvfile:
        reader = csv.DictReader(row.replace('\0', '') for row in csvfile)
        headers = reader.fieldnames
        if len(headers) < 4:
            printR(f'File {csv_file_name} is in wrong format!')
            return ''

        row_string = '\n\t<tr>\n'
  
        # write headers and assign sort method for appropriate columns   
        # each header cell has 2 part: the left div for the header name, the right div for sort direction arrows     
        ignore_columns_count = 0
        for i, header in enumerate(reader.fieldnames):
            if header in ignore_columns:
                ignore_columns_count += 1
                continue
 
            sort_direction_arrows = f"""
            <div class="hdr_arrows">
				<div id ="arrow-up-{i-ignore_columns_count}">&#x25B2;</div>
				<div id ="arrow-down-{i-ignore_columns_count}">&#x25BC;</div></div>"""

            left_div = f'''
            <div class="hdr_text">{header}</div>'''
           
            if header == "No":
                first_left_div = f'\t\t\t<div class="hdr_text">{header}</div>'
                # the No column is initially in ascending order, so we donot show the down arrow
                ascending_arrow_only = f"""
                <div class="hdr_arrows">
				    <div id ="arrow-up-{i-ignore_columns_count}">&#x25B2;</div>
				    <div id ="arrow-down-{i-ignore_columns_count}" hidden>&#x25BC;</div>
			    </div>"""
                row_string += f'\t\t<th class="w40" onclick="sortTable({i-ignore_columns_count})">\n{first_left_div}{ascending_arrow_only}</th>\n'
            
            elif header == "Display Name" or header == "Photo Title":
                row_string += f'\t\t<th class="w200" onclick="sortTable({i-ignore_columns_count}, true)">{left_div}{sort_direction_arrows}</th>\n'
 
            elif header == "Followers" or header == "Count":
                row_string += f'\t\t<th class="w100" onclick="sortTable({i-ignore_columns_count})">{left_div}{sort_direction_arrows}</th>\n'
            
            elif header == "Status"or header == "Content":
                row_string += f'\t\t<th class="w210" onclick="sortTable({i-ignore_columns_count})">{left_div}{sort_direction_arrows}</th>\n'
            
            elif header == "Time Stamp":
                row_string += f'\t\t<th class="w120" onclick="sortTable({i-ignore_columns_count})">{left_div}{sort_direction_arrows}</th>\n'
            
            else:
                row_string += f'\t\t<th onclick="sortTable({i-ignore_columns_count})">{left_div}{sort_direction_arrows}</th>\n'

        # create rows for html table 
        row_string += '\t</tr>'       
        for row in reader:
            row_string += '\n\t<tr>\n'
            # Table columns vary depending on 5 different csv files:
            # Columns:         0   1            2             3          4          5                6            7           8       9
            # Notifications  : No, User Avatar, Display Name, User Name, Content,   Photo Thumbnail, Photo Title, Time Stamp, Status, Photo Link
            # Unique users   : No, User Avatar, Display Name, User Name, Count
            # Followers List : No, User Avatar, Display Name, User Name, Followers, Status
            # Followings List: No, User Avatar, Display Name, User Name, Followers, Status

            for i in range(len(headers)): 
                col_header = headers[i]   
                # ignore unwanted columns
                if col_header in ignore_columns:
                    continue

                text = row[col_header]

                # In Display Name column, show user's avatar and the display name with link 
                if col_header == 'Display Name' : 
                    avatar_src = row[headers[1]]                            
                    user_home_page = f'https://500px.com/{row[headers[3]]}'        
                    user_name = row[headers[2]]
                    row_string += f'\t\t<td>\n\t\t\t<div>\n\t\t\t\t<a href="{user_home_page}" target="_blank">\n'
                    row_string += f'\t\t\t\t<img src={avatar_src}></a>\n'
                    row_string += f'\t\t\t\t<div><a href="{user_home_page}" target="_blank">{user_name}</a></div></div></td>\n'
               
                # Column 4 varies depending on csv file types
                elif i == 4:  
                    # Unique Users, Followers or Followings Lists:   
                    if col_header == 'Followers' or col_header == 'Count': 
                            row_string += f'\t\t<td>{text}</td> \n'   # align right for a count number 
                    # Notifications or Unique users csv files: 
                    elif col_header == 'Count' or col_header == 'Content':      # write as is    
                        row_string += f'\t\t<td>{text}</td> \n'
                    
                # Column 5 on Followers or Followings list or column 8 on Notifications list
                elif col_header == 'Status':
                    if text.find('Following') != -1: 
                        row_string += f'\t\t<td class="alignLeft" bgcolor="#00FF00">{text}</td> \n'   # green cell for following users                    
                    else:  
                        row_string += f'\t\t<td class="alignLeft">{text}</td> \n'          
  
                # In Photo Tile column, show photo thumbnail and photo title with <a href> link
                elif  col_header == 'Photo Title': 
                     if row[headers[5]] == '':
                         row_string += f'\t\t<td><div><div></div></div></td> \n' # write empty tags if photo thumbnail is empty
                     else:
                         photo_thumbnail = row[headers[5]]
                         photo_link =  row[headers[9]]                 
                         row_string += f'\t\t<td>\n\t\t\t<div>\n\t\t\t\t<a href="{photo_link}" target="_blank">\n'
                         row_string += f'\t\t\t\t<img class="photo" src={photo_thumbnail}></a>\n'
                         row_string += f'\t\t\t\t<div>{text}</div></div></td>\n'

                # All other columns such as 0:No, 7:Time Stamp,...: write text as is
                else:                            
                     row_string += f'\t\t<td>{text}</td> \n'

            row_string += '\t</tr>'

        
        html_string = f'<html>\n{HEAD_STRING_WITH_CSS_STYLE}\n\n<body>\n{title_string}<table {table_width}> {row_string} </ztable>\n{SCRIPT_STRING}</body> </html>'

        #write html file 
        with open(html_full_file_name, 'wb') as htmlfile:
            htmlfile.write(html_string.encode('utf-16'))

    return html_full_file_name

#--------------------------------------------------------------- 
# The getpass.win_getpass() does not work properly on Windows. We implement this for the desired effect.
# Credit: atbagga from https://github.com/microsoft/knack
def win_getpass(prompt='Password: ', stream=None):
    """Mask the passwork characters with * character, supporting the backspace key """
 
    shown_prompt=''
    for c in prompt:
        msvcrt.putwch(c)
        shown_prompt += c
    pw = ""
    while 1:
        c = msvcrt.getwch()
        if c == '\r' or c == '\n':
            break
        if c == '\003':
            raise KeyboardInterrupt
        if c == '\b':
            pw = pw[:-1]
            # rewrite the stdout
            shown_pwd = '*' * len(pw)
            shown_pwd += ' '    
            sys.stdout.write('\r' + shown_prompt + shown_pwd + '\b')
            sys.stdout.flush()
        else:
            msvcrt.putwch('*')
            pw = pw + c
   
    msvcrt.putwch('\r')
    msvcrt.putwch('\n')
    return pw

#--------------------------------------------------------------- 
def Validate_non_empty_input(prompt_message, user_inputs):
    """Prompt user for an input, make sure the input is not empty. Return True if Quit or Restart is requested. False otherwise """

    if 'password' in prompt_message:
        val = win_getpass(prompt=prompt_message)
    else:
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
    """ Prompt for input and accepts nothing but digits or letter 'r' or 'q'. 
    Return the valid input and a boolean (True if r(estar)t or q(uit) is requested, False otherwise."""

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
    SINCE ALL THE CLASS NAMES IN THE USER HOMEFEED PAGE ARE NOW POSTFIXED WITH RANDOMIZED TEXTS,
    WE WILL USE THE IMG TAG AS IDENTIFIER FOR A PHOTO, 
    FROM THERE, WE REMOVE NON-INTERESTED IMG ITEMS SUCH AS AVATARS, THUMBNAILS OR RECOMMENDED PHOTOS
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
    """Hide or close top popup banners that make elements beneath them inaccessible. And click away the sign-in window if it pops up.
    
    SPECIFICALLY, TOP BANNER IS IDENTIFIED BY THE ID 'hellobar',
    BOTTOM BANNERS ARE IDENTIFIED BY TAG 'w-div' AND
    SIGN-UP BANNER IS IDENTIFIED BY CLASS 'join_500px_banner_close_ele'
    """

    top_banner = check_and_get_ele_by_id(driver, 'hellobar')
    if top_banner is not None:
        try:
            driver.execute_script("arguments[0].style.display='none'", top_banner)
        except:
            pass

    bottom_banners = check_and_get_all_elements_by_tag_name(driver, 'w-div')
    for banner in bottom_banners:
        close_ele = check_and_get_ele_by_tag_name(banner, 'span')
        if close_ele is not None:
            try:
                driver.execute_script("arguments[0].click();", close_ele)
            except:
                pass   

    join_500px_banner_close_ele = check_and_get_ele_by_class_name(driver, 'unified_signup__close')
    if join_500px_banner_close_ele is not None:
        try:
            driver.execute_script("arguments[0].click();", join_500px_banner_close_ele)
        except:
            pass

#---------------------------------------------------------------
def Show_menu(user_inputs, special_message=''):
    """ Display main menu. Validate and accept these inputs from users: user name, password  and the desired option. 
    
    - Inputs are stored in the user_inputs objects, which is passed by reference.  
    - The return value is a string containing either 'r', 'q' or any digit characters
    - The special_message, if given, will be displayed near the end of the menu. It could be used as an alert, warning or error
      from the last operation.
    """

    printC('')
    printC('--------- Chose one of these options: ---------')
    printY('      The following options require a user name:')
    printC('   1  Get user statistics')
    printC('   2  Get user photos list (login is optional)')
    printC('   3  Get followers list   (login is optional)')
    printC('   4  Get followings list ')
    printC('   5  Get a list of users who liked a given photo (login is optional)')

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
    printC('  13  Play slideshow on a given gallery (login is optional)')
    printC('')
    printC('   r  Restart with different user')
    printC('   q  Quit')
    printC('')
  
    if special_message:
        printY(special_message)
  
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

    # password is optional:
    #  - 2  Get user photos list: if logged in, we can get the list of galleries that each of your photo is featured in
    #  - 3  Get followers list: if logged in, we can get your following status to each of your followers
    #  - 5  Get a list of users who liked a given photo: if logged in, we can get your following status to each user in the list
    if (sel == 2 or sel == 3 or sel == 5) and user_inputs.password == '':
        prompt_message = 'Optional: you can get info in greater detail if you log in,\npress ENTER to ignore this option, or type in the password now >'
        expecting_password = win_getpass(prompt=prompt_message)
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
        input_val, abort = Validate_non_empty_input('Enter the link to your desired photo gallery.\n\
 It could be a public gallery with filters, or a private gallery >', user_inputs)
        if abort:
            return '', '', True
        else:
            return input_val, 'User-specified gallery', False

    elif sel == '7': return f'https://500px.com/{user_inputs.user_name}'                  , 'My photos', False

    else:
        Show_galllery_selection_menu(user_inputs)
#---------------------------------------------------------------
def Define_and_read_command_line_arguments(): 
    """ Define all optional user inputs and their default values. Then fill in with the actual values from command lines.
        Return a user_inputs objects filled with given arguments. 

    ALL COMMAND LINE ARGUMENTS ARE OPTIONAL (AS OPPOSED TO POSTIONAL).  IF THE ARGURMENT '--choice' IS NOT SET, ALL OTHER ARGUMENTS WILL BE IGNORED WHETHER 
    THEY ARE SET OR NOT, AND THE ATTRIBUTE "USE_COMMAND_LINE_ARGS" WILL BE SET TO FALSE 
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
            #photo_href
            user_inputs.photo_href, abort =  Validate_non_empty_input('Enter your photo href >', user_inputs)
            if abort: 
                return False    
            # these additional options are for next version
            ## index_of_start_user
            #input_val, abort =  Validate_input('Enter the start index of the user (default 1)>' , user_inputs)
            #if abort:
            #    return False  
            #else: 
            #    int_val = int(input_val)
            #    # the end user will use 1-based index, so we will convert the input to 0-based
            #    if int_val > 0: int_val -= 1
            #    user_inputs.index_of_start_user = int_val   
            
            ## number of users    
            #input_val, abort =  Validate_input('Enter the number of users you want to process>' , user_inputs)
            #if abort:
            #    return False  
            #else: 
            #    int_val = int(input_val)
            #    user_inputs.number_of_users = int_val        
    
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
            user_inputs.password, abort = Validate_non_empty_input('Type your password> ', user_inputs)
            if abort:
                return False    

        input_val, abort = Validate_input('Enter the interval time between photos, in second>', user_inputs)
        if abort:
            return False
        else:
            user_inputs.time_interval = int(input_val)

            printY(f'Slideshow {user_inputs.gallery_name} will play in fullscreen, covering this control window.\n To stop the slideshow before it ends, and return to this window, press ESC three times.\n Now press ENTER to start >')

            wait_for_enter_key = input() 
    
    # Like n photos of m followers of yours, from a given start index
    elif choice == 15:
        # number of followers
        input_val, abort =  Validate_input('Enter the number of followers you want to process >', user_inputs)
        if abort:
            return False  
        else: 
            user_inputs.number_of_users = int(input_val)

        # start index of the user
        input_val, abort =  Validate_input('Enter the user start index (1-based)>' , user_inputs)
        if abort:
            return False  
        else: 
            int_val = int(input_val)
            # the end user will use 1-based index, so we will convert the input to 0-based
            if int_val > 0: int_val -= 1
            user_inputs.index_of_start_user = int_val 

        #number of photos
        input_val, abort =  Validate_input('Enter the number of photos you want to auto-like >', user_inputs)
        if abort:
            return False
        else: 
            num = int(input_val)
            user_inputs.number_of_photos_to_be_liked = num if num < MAX_AUTO_LIKE_REQUEST else MAX_AUTO_LIKE_REQUEST 
        
        user_inputs.csv_file, abort =  Validate_non_empty_input('Enter the csv full file name>', user_inputs)
        if abort: 
            return False                
 
#---------------------------------------------------------------
def Handle_option_1(user_inputs, output_lists):
    """ Get user status."""

    time_start = datetime.datetime.now().replace(microsecond=0)
    date_string = time_start.strftime(DATE_FORMAT)

    # do task
    driver = Start_chrome_browser()
    stats, error_message = Get_stats(driver, user_inputs, output_lists) 
    if error_message:
        printR(error_message)
        Close_chrome_browser(driver)
        if user_inputs.use_command_line_args == False:
            Show_menu(user_inputs, error_message)
    
    # write result to html file, show it on browser
    print(f"Getting user's statistics ...")
    html_file =  os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_stats_{date_string}.html')
    Write_string_to_text_file(Create_user_statistics_html(stats), html_file, 'utf-16')
    Close_chrome_browser(driver)
    Show_html_result_file(html_file)

    # print summary report
    time_duration = (datetime.datetime.now().replace(microsecond=0) - time_start)
    print(f'The process took {time_duration} seconds') 

#---------------------------------------------------------------
def Handle_option_2(user_inputs, output_lists):
    """ Get user photos """

    time_start = datetime.datetime.now().replace(microsecond=0)
    date_string = time_start.strftime(DATE_FORMAT)
   
    # avoid to do the same thing twice: if list (in memory) has items AND output file (on disk) exists
    if output_lists.photos is not None and len(output_lists.photos) > 0:
        html_file = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_{len(output_lists.photos)}_photos_{date_string}.html')
        if  os.path.isfile(html_file):
            printY(f'Results exists in memory and on disk. Showing the existing file at:\n{os.path.abspath(html_file)} ...')
            Show_html_result_file(html_file) 
            return

    # do the action
    driver = Start_chrome_browser()
    # if user provided password then login (logged-in users can see the list galleries that feature theirs photos
    if user_inputs.password != '':
        if Login(driver, user_inputs) == False :
            Close_chrome_browser(driver)
            return
    Hide_banners(driver)
    print(f"Getting {user_inputs.user_name}'s photos list ...")
    output_lists.photos, error_message = Get_photos_list(driver, user_inputs)
    Close_chrome_browser(driver)
    if error_message:
        printR(error_message)
        if len(output_lists.photos) == 0:
            return


    # write result to csv, convert it to html, show html in browser
    if output_lists.photos is not None and len(output_lists.photos) > 0:
        csv_file = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_{len(output_lists.photos)}_photos_{date_string}.csv')           
        if Write_photos_list_to_csv(user_inputs.user_name, output_lists.photos, csv_file) == True:
            Show_html_result_file(CSV_photos_list_to_HTML(csv_file, ignore_columns=['ID', 'Href', 'Thumbnail', 'Rating']))  
            
            time_duration = (datetime.datetime.now().replace(microsecond=0) - time_start)
            print(f'The process took {time_duration} seconds') 
        else:
            printR(f'Error writing the output file\n:{csv_file}')

#---------------------------------------------------------------
def Handle_option_3(user_inputs, output_lists):
    """ Get followers"""
    
    time_start = datetime.datetime.now().replace(microsecond=0)
    date_string = time_start.strftime(DATE_FORMAT)

    # avoid to do the same thing twice: when the list (in memory) has items and output file exists on disk
    if output_lists.followers_list is not None and len(output_lists.followers_list) > 0:
        html_file = f'{user_inputs.user_name}_{len(output_lists.followers_list)}_followers_{date_string}.html'
        if os.path.isfile(html_file):
            printY(f'Results exists in memory and on disk. Showing the existing file at:\n{os.path.abspath(html_file)} ...')
            Show_html_result_file(html_file) 
            return
   
    # do task
    driver = Start_chrome_browser()
    # if user provided password then login
    if user_inputs.password != '':
        if Login(driver, user_inputs) == False :
            Close_chrome_browser(driver)
            return
    Hide_banners(driver)
    print(f"Getting the list of users who follow {user_inputs.user_name} ...")
    output_lists.followers_list = Get_followers_list(driver, user_inputs)
    Close_chrome_browser(driver)

    # write result to csv, convert it to html, show html in browser
    if output_lists.followers_list is not None and len(output_lists.followers_list) > 0:
        csv_file = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_{len(output_lists.followers_list)}_followers_{date_string}.csv')           
        if Write_users_list_to_csv(output_lists.followers_list, csv_file) == True:
            # show output and print summary report
            Show_html_result_file(CSV_to_HTML(csv_file, ignore_columns=['User Avatar', 'User Name'])) 
            time_duration = (datetime.datetime.now().replace(microsecond=0) - time_start)
            print(f'The process took {time_duration} seconds') 
        else:
            printR(f'Error writing the output file\n:{csv_file}')
#---------------------------------------------------------------
def Handle_option_4(user_inputs, output_lists):
    """ Get followings (friends)"""
    
    time_start = datetime.datetime.now().replace(microsecond=0)
    date_string = time_start.strftime(DATE_FORMAT)

    # avoid to do the same thing twice: when the list (in memory) has items and output file exists on disk
    if output_lists.followings_list is not None and len(output_lists.followings_list) > 0:
        # find the latest html file on disk and show it
        files = [f for f in glob.glob(output_lists.output_dir + f"**/{user_inputs.user_name}*followings*.html")]
        files.sort(key=lambda x: os.path.getmtime(x))
        html_file = files[-1]
        if os.path.isfile(html_file):
            printY(f'Results exist in memory and on disk. Showing the existing file:\n{os.path.abspath(html_file)} ...')
            Show_html_result_file(html_file) 
            return

    # do task
    driver = Start_chrome_browser()
    print(f"Getting the list of users that you are following ...")
    output_lists.followings_list, error_message = Get_followings_list(driver, user_inputs)
    Close_chrome_browser(driver)
    if error_message:
        printR(error_message)
        return
    # write result to csv, convert it to html, show html in browser
    if len(output_lists.followings_list) > 0:
        csv_file = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_{len(output_lists.followings_list)}_followings_{date_string}.csv')
        if Write_users_list_to_csv(output_lists.followings_list, csv_file) == True:
            # show output and print summary report
            Show_html_result_file(CSV_to_HTML(csv_file, ignore_columns=['User Avatar', 'User Name', 'Status'])) 
            time_duration = (datetime.datetime.now().replace(microsecond=0) - time_start)
            print(f'The process took {time_duration} seconds') 
        else:
            printR(f'Error writing the output file\n:{csv_file}')

#---------------------------------------------------------------
def Handle_option_5(user_inputs, output_lists):
    """ Get a list of users who liked a given photo."""
    
    time_start = datetime.datetime.now().replace(microsecond=0) 
    driver = Start_chrome_browser()      

    # if user provided password then login
    if user_inputs.password != '':
        if Login(driver, user_inputs) == False :
            Close_chrome_browser(driver)    
            return

    try:
        driver.get(user_inputs.photo_href)
    except:
        printR(f'Invalid href: {user_inputs.photo_href}. Please retry.')
        Close_chrome_browser(driver)
        Show_menu(user_inputs)        
        return

    # do task
    time.sleep(1)
    Hide_banners(driver)
    print(f"Getting the list of unique users who liked the given photo ...")
    output_lists.like_actioners_list, csv_file = Get_like_actioners_list(driver, output_lists)
    Close_chrome_browser(driver)

    # write result to csv, convert it to html, show html in browser
    if output_lists.like_actioners_list is not None and \
       len(output_lists.like_actioners_list) > 0 and \
       Write_users_list_to_csv(output_lists.like_actioners_list, csv_file) == True:
        Show_html_result_file(CSV_to_HTML(csv_file, ['User Avatar', 'User Name'])) 

    # print summary report
    time_duration = (datetime.datetime.now().replace(microsecond=0) - time_start)
    print(f'The process took {time_duration} seconds') 
#---------------------------------------------------------------
def Handle_option_6(user_inputs, output_lists):
    """ Get n last notifications details (max 5000). Show the detail list and the list of the unique users on it"""

    time_start = datetime.datetime.now().replace(microsecond=0)
    date_string = time_start.strftime(DATETIME_FORMAT)
    #csv_file = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_{user_inputs.number_of_notifications}_notifications_{date_string}.csv')
    html_file = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_{user_inputs.number_of_notifications}_notifications_{date_string}.html')

    # avoid to do the same thing twice: when the list (in memory) has items and output file exists on disk
    if output_lists.notifications is not None and len(output_lists.notifications) > 0 and os.path.isfile(html_file):
        printY(f'Results exists in memory and on disk. Showing the existing file at:\n{os.path.abspath(html_file)} ...')        
        Show_html_result_file(html_file)
        return

 
    driver = Start_chrome_browser()
    if Login(driver, user_inputs) == False :
        Close_chrome_browser(driver)
        return
    #time.sleep(1)
    driver.get('https://500px.com/notifications')
    time.sleep(1)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # abort the action if the target objects failed to load within a given timeout        
    if not Finish_Javascript_rendered_body_content(driver, time_out=15, class_name_to_check='finished')[0]:
        return	

    Hide_banners(driver)
    if user_inputs.number_of_notifications == -1:
        print(f"Getting the up to {MAX_NOTIFICATION_REQUEST} notifications and the unique users on that ...")
    else: 
        print(f"Getting the last {user_inputs.number_of_notifications} notifications and the unique users in that list ...")

    # do task   
    output_lists.notifications, output_lists.unique_notificators = Get_notification_list(driver, user_inputs, True)
        
    if len(output_lists.notifications) == 0 and len(output_lists.unique_notificators) == 0:
        Show_menu(user_inputs)
        Close_chrome_browser(driver)
        return

    Close_chrome_browser(driver)
    
    csv_file = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_{len(output_lists.notifications)}_notifications_{date_string}.csv')
    html_file = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_{user_inputs.number_of_notifications}_notifications_{date_string}.html')

    # write unique users list to csv. Convert it to html, show it in browser
    csv_file_unique_users  = os.path.join(output_lists.output_dir, \
        f"{user_inputs.user_name}_{len(output_lists.unique_notificators)}_unique-users-in-last-{len(output_lists.notifications)}_notifications_{date_string}.csv")
    if len(output_lists.unique_notificators) > 0 and  Write_unique_notificators_list_to_csv(output_lists.unique_notificators, csv_file_unique_users) == True:
        Show_html_result_file(CSV_to_HTML(csv_file_unique_users, ignore_columns=['User Avatar', 'User Name', 'Photo Thumbnail', 'Photo Link']))     
    
    # Write the notification list to csv. Convert it to html, show it in browser        
    if len(output_lists.notifications) > 0 and  Write_notifications_to_csvfile(output_lists.notifications, csv_file) == True:
        Show_html_result_file(CSV_to_HTML(csv_file, ignore_columns=['User Avatar', 'User Name', 'Photo Thumbnail',  'Photo Link'])) 

    # print summary report
    time_duration = (datetime.datetime.now().replace(microsecond=0) - time_start)
    print(f'The process took {time_duration} seconds') 
#---------------------------------------------------------------
def Handle_option_7(user_inputs, output_lists):
    """Check if a user is following you."""

    time_start = datetime.datetime.now().replace(microsecond=0)

    # do task
    driver = Start_chrome_browser()
    print(f"Check if user {user_inputs.target_user_name} follows {user_inputs.user_name} ...")
    result, message = Does_this_user_follow_me(driver, user_inputs)

    if result == True:
        printG(message)
    else:
        printR(message) if 'User name not found' in message else printR(message)

    ## show result on screen
    #if result == True:
    #    printG(f"User {user_inputs.target_user_name} follows {user_inputs.user_name} {detail_message} ")
    #else:
    #    printY(f"User {user_inputs.target_user_name} does not follow {user_inputs.user_name}")
        
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
        Close_chrome_browser(driver)
        return

    print(f"Starting auto-like {user_inputs.number_of_photos_to_be_liked} photo(s) of user {user_inputs.target_user_name} ...")
    
    # do task   
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
        Close_chrome_browser(driver)
        return
    driver.get(user_inputs.gallery_href)
    time.sleep(3)
    # abort the action if the target objects failed to load within a given timeout    
    #if not Finish_Javascript_rendered_body_content(driver, time_out=15, class_name_to_check = 'entry-visible')[0]:
    #    return None, None	
    innerHtml = driver.execute_script("return document.body.innerHTML")  
    time.sleep(3)

    Hide_banners(driver)
    print(f"Starting auto-like {user_inputs.number_of_photos_to_be_liked} photo(s) from {user_inputs.gallery_name} gallery, start index {user_inputs.index_of_start_photo} ...")

    # do task
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
        Close_chrome_browser(driver)
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

    # do preliminary task: get the list of users who liked your given photo
    output_lists.like_actioners_list, dummy_file_name = Get_like_actioners_list(driver, output_lists)
    if len(output_lists.like_actioners_list) == 0: 
        #printG(f'The photo {photo_tilte} has no affection yet')
        Show_menu(user_inputs)
        return 
    actioners_count = len(output_lists.like_actioners_list)
    print(f"Starting auto-like {user_inputs.number_of_photos_to_be_liked} photos of each of {actioners_count} users on the list ...")
    include_already_liked_photo_in_count = True  # meaning: if you want to autolike 3 first photos, and you found out two of them are already liked, then you need to like just one photo.
                                                    # if this is set to False, then you will find 3 available photos and Like them 

    # do main task
    # we may have option to process only part of the users list. 
    # Since the list may be quite large and we don't want to stretch the server by sending too many requests. 
    #start_index = max(0, user_inputs.index_of_start_user)
    #end_index   = min(start_index + user_inputs.number_of_users, len(output_lists.like_actioners_list) - 1)
    #for i, actor in enumerate(output_lists.like_actioners_list[start_index : end_index]):  

    for i, actor in enumerate(output_lists.like_actioners_list):  
        print(f'User {str(i+1)}/{actioners_count}: {actor.display_name}, {actor.user_name}')
        Like_n_photos_from_user(driver, actor.user_name, user_inputs.number_of_photos_to_be_liked, include_already_liked_photo_in_count, close_browser_on_error=False)
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
        Close_chrome_browser(driver)
        return

    # after a success login, the user's the homefeed page will automatically open     
    # we may consider this: abort the action if the photos fail to load within a given timeout    
    #if not Finish_Javascript_rendered_body_content(driver, time_out=30, class_name_to_check='finished')[0]:
    #  return None, None	    
  
    Hide_banners(driver) 
 
    
    print(f"Like {user_inputs.number_of_photos_to_be_liked} photos from the {user_inputs.user_name}'s home feed page ...")

    # do task
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
        Close_chrome_browser(driver)
        return
    driver.get('https://500px.com/notifications')
    time.sleep(1)        
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    
    # abort the action if the target objects failed to load within a given timeout    
    if not Finish_Javascript_rendered_body_content(driver, time_out=30, class_name_to_check='finished')[0]:
      return None, None	

    Hide_banners(driver)  
       
    # do preliminary task
    output_lists.unique_notificators = Get_notification_list(driver, user_inputs, True)[1]
    #if len(output_lists.unique_notificators) == 0:
        #   break 
        
    # do main task
    users_count = len(output_lists.unique_notificators)
    print(f"Starting auto-like {user_inputs.number_of_photos_to_be_liked} photos of each of {users_count} users on the list ...")
    for i, notification_element in enumerate(output_lists.unique_notificators):
        name_pair = notification_element.split(',')
        if len(name_pair) > 3: 
            print(f' User {name_pair[0]}/{users_count}: {name_pair[2]}, {name_pair[3]}')
            Like_n_photos_from_user(driver, name_pair[3], user_inputs.number_of_photos_to_be_liked, include_already_liked_photo_in_count=True, close_browser_on_error=False)
    Close_chrome_browser(driver)

    # print summary report
    time_duration = (datetime.datetime.now().replace(microsecond=0) - time_start)
    print(f'The process took {time_duration} seconds') 
#---------------------------------------------------------------
def Handle_option_13(user_inputs, output_lists):
    """ Play slideshow on a given gallery. """

    time_start = datetime.datetime.now().replace(microsecond=0)
    driver = Start_chrome_browser(["--kiosk", "--hide-scrollbars", "--disable-infobars"])
    #driver.maximize_window()

    # login if credentials are provided
    if user_inputs.user_name !='' and user_inputs.password != '':
        if Login(driver, user_inputs) == False :
            printR('Error logging in. Slideshow will be played without a user login.')  
        
    driver.get(user_inputs.gallery_href)
    driver.execute_script("return document.body.innerHTML")
    time.sleep(1)
    Hide_banners(driver)

    # do task
    Play_slideshow(driver, int(user_inputs.time_interval))
    
    Close_chrome_browser(driver)
    # print summary report
    time_duration = (datetime.datetime.now().replace(microsecond=0) - time_start)
    print(f'The process took {time_duration} seconds') 
#---------------------------------------------------------------
#EXTRA OPTIONS
def Handle_option_14(user_inputs, output_lists):
    """Check/Update following statused of people you are following."""

    time_start = datetime.datetime.now().replace(microsecond=0)
    date_string = time_start.replace(microsecond=0).strftime(DATE_FORMAT)
    if user_inputs.number_of_users == -1:
        message = f'Get the following statuses of all users that {user_inputs.user_name} is following'
    else:
        message = f'Get the following statuses of {user_inputs.number_of_users} users, starting from index {user_inputs.index_of_start_user + 1} ...'
    print(message)

    # Provide option whether to use the last Followings list on disk or to start from scratch
    files = [f for f in glob.glob(output_lists.output_dir + f"**/{user_inputs.user_name}*followings*.csv")]
    files.sort(key=lambda x: os.path.getmtime(x))
    if len(files) > 0:
        print('Existing Followings list on disk:')
        printY(f"{files[-1]}")
        sel = input("Using this file? (y/n) > ")
        # use the existing followings list
        if sel =='y':
            csv_file = files[-1]
        # redo the followings list:        
        else:
            print(f"Getting {user_inputs.user_name}'s Followings list ...")
            driver = Start_chrome_browser()
            output_lists.followings_list = Get_followings_list(driver, user_inputs, output_lists)
            Close_chrome_browser(driver)
            # write result to csv
            if len(output_lists.followings_list) == 0:
                printR(f'User {user_inputs.user_name} does not follow anyone or error on getting the followings list')
                return ''
            csv_file = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_{len(output_lists.followings_list)}_followings_{date_string}.csv')
            if Write_users_list_to_csv(output_lists.followings_list, csv_file) == False:
                printR(f'Error writing the output file\n:{csv_file}')
                return ''
    # do task
    driver = Start_chrome_browser()
    Get_following_statuses(driver, user_inputs, output_lists, csv_file )
    Close_chrome_browser(driver)
    Show_html_result_file(CSV_to_HTML(csv_file, ignore_columns=['User Avatar', 'User Name'])) 

    # print summary report
    time_duration = (datetime.datetime.now().replace(microsecond=0) - time_start)
    print(f'The process took {time_duration} seconds') 
#---------------------------------------------------------------
def Handle_option_15(user_inputs, output_lists, sort_column_header='No', ascending=True):
    """Like n photos of m users from a given csv files, starting at a given index. 
    There is option to process part of the list, by specifying the start index and the number of users   
    """
    time_start = datetime.datetime.now().replace(microsecond=0)
    date_string = time_start.replace(microsecond=0).strftime(DATE_FORMAT)


    # do main task
    dframe = pd.read_csv(user_inputs.csv_file, encoding='utf-16')    
    print(f"Like {user_inputs.number_of_photos_to_be_liked} photos from {user_inputs.number_of_users} users, starting from index {user_inputs.index_of_start_user} from the file:")
    printG({user_inputs.csv_file})    
    print(f'There are {dframe.shape[1]} columns:')
    printG(list(dframe))
    sort_header = input('Enter the desired sort column >')
    if not sort_header:
        sort_header = "No" 
    sort_ascending = True
    ans = input('Sort descending ?(y/n) >')
    if ans == 'y':
        sort_ascending = False
    df = dframe.sort_values(sort_header, ascending = sort_ascending )   
    
    driver = Start_chrome_browser()
    if Login(driver, user_inputs) == False :
        Close_chrome_browser(driver)
        return
    count = 0

    # if requesting all items:
    if user_inputs.index_of_start_user == -1:
        start_index = 0
        end_index = df.shape[0] -1
    else:
        # make sure the user's inputs stay within the size of the csv file 
        start_index = min(user_inputs.index_of_start_user, df.shape[0] -1)
        end_index   = min(user_inputs.index_of_start_user + user_inputs.number_of_users, df.shape[0] -1)

    for index, row in df.iloc[start_index:end_index].iterrows():
        user_inputs.target_user_name = row["User Name"]
        count += 1
    
        # process each user in datafram3
        print(f'User #{count}: {row["Display Name"]}  at row {row["No"]}   ({row[sort_header]} likes):')
        Like_n_photos_from_user(driver, user_inputs.target_user_name, user_inputs.number_of_photos_to_be_liked, include_already_liked_photo_in_count=True, close_browser_on_error = False)

    Close_chrome_browser(driver)
 
    # print summary report
    time_duration = (datetime.datetime.now().replace(microsecond=0) - time_start)
    print(f'The process took {time_duration} seconds') 
#---------------------------------------------------------------
def Save_avatar(url, path):
    """ Save the 500px user avatar to the given path on disk. 500px avatar file has this format "stock-photo-[user ID].jpg". 
        We will extracted it automatically from the header, and use just the id for filename. We also return the id
     
    This function is meant to be called repeatedly in the loop, so for better performance, we don't chech the existance of the given path
    We have to make sure the given path is valid prio to calling this. 
    """ 
    r = requests.get(url, allow_redirects=True)
    #os.makedirs(path ,mode=0o777, exist_ok=True)
    try:
        file_name =  r.headers.get('content-disposition').replace('filename=stock-photo-','')
    except:
        # default avatar if user does not have one: https://pacdn.500px.org/userpic.png
        file_name = url.split('/')[-1]

    full_file_name = os.path.join(path + "\\", file_name)
    if not os.path.isfile(full_file_name):
        with open(full_file_name, 'wb+') as f:
            f.write(r.content)
    return os.path.splitext(file_name)[0]

#---------------------------------------------------------------
def main():
    os.system('color')
    driver = None


    # declare a dictionary so that functions can be referred to from a string from "1" to "14"
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
            "14": Handle_option_14,
            "15": Handle_option_15}

    output_lists = Output_data()
    user_inputs = Define_and_read_command_line_arguments()
 
    if  user_inputs.use_command_line_args == False:
        Show_menu(user_inputs)  
   
    while user_inputs.choice != 'q':
        #restart for different user
        if user_inputs.choice == 'r': 
            printY('Restarted for a different user.')
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

