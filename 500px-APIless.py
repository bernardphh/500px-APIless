import common.apiless as apiless
import common.config as config
import common.utils as utils
import common.webtools as webtools
import common.database as db
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
import pandas as pd
from lxml import html
import glob, random, requests, sqlite3
import os, sys, time, datetime, re, math, json, argparse

from time import sleep
from os import listdir
from os.path import isfile, join
from dateutil.relativedelta import relativedelta
import multiprocessing as mp  
from threading import Thread
import queue

# print colors text on console with option to log the same text to file on disk
def printG(text, write_log=True):  print(f"\033[92m {text}\033[00m"); logger.info(text) if write_log else None 
def printY(text, write_log=True):  print(f"\033[93m {text}\033[00m"); logger.info(text) if write_log else None
def printR(text, write_log=True):  print(f"\033[91m {text}\033[00m"); logger.error(text)if write_log else None
def printC(text, write_log=False): print(f"\033[96m {text}\033[00m"); logger.info(text)if write_log else None 
def printB(text, write_log=False): print(f"\033[94m {text}\033[00m"); logger.info(text)if write_log else None 
def print_and_log(text): print(text); logger.info(text)
        
#---------------------------------------------------------------
def logged_in(driver):
    """ Check if any user is currently logged in the current session"""

    logged = True
    print('    - Checking login status ...')
    # need to be on 500px domain first
    if not '500px.com' in driver.current_url:
        driver.get('https://500px.com')
        time.sleep(2)
    login_elements = driver.find_elements_by_xpath("//*[contains(text(), 'Log in')]")
    if len(login_elements) == 0:
        return logged
    else:
        for ele in login_elements: 
           if ele.tag_name != 'script':
               return not logged
        return logged

#---------------------------------------------------------------
def get_stats(driver, user_inputs, output_lists):
    """Get statistics of a given user: number of likes, views, followers, following, photos, last upload date...
       If success, return statistics object and a blank message. If not return None and the error message

       Process:
       - Open user home page https://500px.com/[user_name]
       - Run the document javascript to render the page content
       - Use lxml to extract interested data
       - Use regular expression to extract the json part in the body, and obtain more data from it.
    """

    success, message = webtools.open_user_home_page(driver, user_inputs.user_name)
    if not success:
        if message.find('Error reading') != -1:
            user_inputs.user_name,  user_inputs.db_path = '', ''
        return None, message
        
    hide_banners(driver)
  
    # abort the action if the target objects failed to load within a given timeout
    success, innerHtml = webtools.finish_Javascript_rendered_body_content(driver, time_out=30, class_name_to_check='finished')
    if not success:
        return None, f"Error loading user {user_inputs.user_name}'s photo page"
    # using lxml for html handling
    page = html.document_fromstring(innerHtml)

    # Affection note
    affection_note = webtools.get_element_attribute_by_ele_xpath(page, "//li[@class='affection']", 'title' )
    # Following note
    following_note = webtools.get_element_attribute_by_ele_xpath(page, "//li[@class='following']", 'title' )
    # Views count
    views_ele = webtools.check_and_get_ele_by_class_name(driver,'views' )
    if views_ele is not None:
        ele =  webtools.check_and_get_ele_by_tag_name(views_ele,'span')
        if ele is not None:
            views_count= ele.text

    # Location
    location = webtools.get_element_text_by_xpath(page,'//*[@id="content"]/div[1]/div[4]/ul/li[5]')
    loc_test = webtools.check_and_get_all_elements_by_class_name(driver, 'location')

    #using regex to extract from the javascript-rendered html the json part that holds user data 
    # Jul 26 2019: modification due to page structure changes: photos list is no longer included in userdata
    #   userdata = re.findall('"userdata":(.*),"viewer":', innerHtml)
    i = innerHtml.find('"userdata":') 
    j = innerHtml.find('</script>', i)
    userdata = innerHtml[i + 11 : j - 2]
    if len(userdata) == 0:
       return None, 'Error getting the user data'
    
    last_upload_date = ''
    json_data = json.loads(userdata)
    print("    - Getting the last upload date ...")
    last_photo_href = webtools.get_element_attribute_by_ele_xpath(page, './/*[@id="content"]/div[3]/div/div/div[1]/a', 'href')
    if last_photo_href:
        driver.get(r'https:/500px.com' + last_photo_href)
        time_out = 30
        try:  
            info_box = WebDriverWait(driver, time_out).until(EC.presence_of_element_located((By.XPATH, '//*[@id="root"]/div[3]/div/div[2]')) )
            upload_date_ele = webtools.check_and_get_ele_by_xpath(info_box,  '//div[1]/div[2]/p/span')        
            if upload_date_ele is None:
                upload_date_ele = webtools.check_and_get_ele_by_xpath(info_box, '//div[3]/div[1]/div/p/span') 
            if upload_date_ele is not None:
                last_upload_date = upload_date_ele.text
        except  TimeoutException:
            printR(f'   - Time out ({time_out}s)! Last upload date will not be available')
 
    active_int = json_data['active'] 
    if   active_int == 0 : user_status = 'Not Active'
    elif active_int == 1 : user_status = 'Active'
    elif active_int == 2 : user_status = 'Deleted by user'
    elif active_int == 3 : user_status = 'Banned'

    # write to file the userdata in json for debugging
    if config.DEBUG:
        jason_string = json.dumps(json_data, indent=2, sort_keys=True) 
        time_stamp = datetime.datetime.now().replace(microsecond=0).strftime("%Y_%m_%d__%H_%M_%S")
        utils.write_string_to_text_file(jason_string, os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_stats_json_{time_stamp}.txt'))

    stats = apiless.UserStats(json_data['fullname'], user_inputs.user_name, json_data['id'], location, 
                       affection_note, following_note, json_data['affection'], views_count, json_data['followers_count'], json_data['friends_count'], 
                       json_data['photos_count'], json_data['galleries_count'], json_data['registration_date'][:10], last_upload_date, user_status)
    return stats, ''
      
#---------------------------------------------------------------
def process_a_photo_element(driver, index, items_count, photo_link_ele, img_ele, user_name, user_password, thumbnails_list, thumbnails_dir):
    """Extract photo info from web element, return a photo object"""

    utils.update_progress(index / (items_count -1), f'    - Extracting  {index + 1}/{items_count} photos:')
    # reset variables
    photo_id, title, photo_thumbnail_href, photo_thumbnail_local = '', '0', '', ''
    photo_stats = apiless.PhotoStats()        
    
    # get photo link, 
    photo_href = r'https://500px.com' + photo_link_ele.attrib["href"]

    # photo id
    photo_id  =  re.search('\/photo\/(\d+)', photo_href).group(1)

    # title and thumbnail 
    if img_ele is not None:
        title = img_ele.attrib["alt"]

        photo_thumbnail_href = img_ele.attrib["src"]
        # save the photo thumbnail to disk
        if config.USE_LOCAL_THUMBNAIL:
            photo_thumbnail_local = photo_id + '.jpg'
            if not photo_thumbnail_local in  thumbnails_list:
                #time.sleep(random.randint(5, 10) / 10)  
                photo_thumbnail_local = utils.save_photo_thumbnail(photo_thumbnail_href, thumbnails_dir )

    # open each photo page to get photo statistics
    time_out = 30
    id = ''
    galleries_list = []
    order = index + 1        
    try:  
        driver.get(photo_href)
        #time.sleep(random.randint(1, 5) / 10)
        info_box = WebDriverWait(driver, time_out).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="root"]/div[3]/div/div[2]')) )
    except  TimeoutException:
        # log error, add the current photo with what are extracted so far, then go on with the next photo
        printR(f'   - Time out ({time_out}s). Photo #{index + 1}, {title} will have incomplete info')
        return apiless.Photo(author_name = user_name, id = photo_id, title = title, thumbnail_href = photo_thumbnail_href, 
                             thumbnail_local = photo_thumbnail_local, stats = photo_stats ) 

    #category  
    category_ele = driver.find_element_by_xpath("//span[contains(.,'Category')]")
    if category_ele:
        photo_stats.category  = webtools.get_web_ele_text_by_xpath(category_ele, '../following-sibling::a' ) 

    #upload date    //*[@id="modal_content"]/div/div/div[2]/div/div[2]/div[3]/div[1]/div[2]/p/span
    upload_date = webtools.get_web_ele_text_by_xpath(info_box, '//div[3]/div[1]/div/p/span' )
        
    if upload_date and ('ago' not in upload_date):
        try:
            dt = datetime.datetime.strptime(upload_date, "%b %d, %Y")
            photo_stats.upload_date = dt.strftime("%Y %m %d")
        except:
            printR(f'   - Error converting date-time string: {upload_date}, on photo: {title}')

    #views count
    views_count =  webtools.get_web_ele_text_by_xpath(info_box, '//div/div[2]/div[3]/div[3]/div[2]/h3/span')
    try:
        photo_stats.views_count  =  int(re.sub('[.,.]', '', views_count))
    except:
        printR(f'   - Error getting views count on {title}')
                                          
    # highest pulse
    photo_stats.highest_pulse =  webtools.get_web_ele_text_by_xpath(info_box, '//div/div[2]/div[3]/div[3]/div[1]/h3') 
        
    # Get votes (likes) count
    try:
        photo_likes_count_ele = WebDriverWait(driver, time_out).until(EC.presence_of_element_located((By.XPATH, '//a[@data-id="photo-likes-count"]')) )
    except  TimeoutException:               
        printR(f'   - Time out ({time_out}s) getting votes count. Photo #{index + 1}, {title}.')

    # votes count
    photo_stats.votes_count = photo_likes_count_ele.text.replace(',','').replace('.','')

    # comments count
    photo_stats.comments_count =  webtools.get_web_ele_text_by_xpath(info_box, '//div/div[4]/div[2]/div/h4').split(' ')[0].replace(',','').replace('.','')

    #tags   
    tags = []
    container = webtools.check_and_get_ele_by_xpath(category_ele, '../../following-sibling::div')
    if container is not None:
        a_eles = webtools.check_and_get_all_elements_by_tag_name(container, 'a')
        if a_eles is not None:
            for item in a_eles:
                tag = item.text                  
                if tag != '': tags.append(tag)
            tags.sort()
            photo_stats.tags =  ",".join(tags)

    # get galleries list, if user logged in
    if user_password:
        view_all_ele = driver.find_elements_by_xpath("//*[contains(text(), 'View all')]")
        if len(view_all_ele) == 0 or (len(view_all_ele) == 1 and view_all_ele[0].tag_name == 'script'):
            photo_stats.collections_count = 0
        else:
            view_all_ele[0].location_once_scrolled_into_view
            view_all_ele[0].click()         
            time.sleep(1)
            eles = driver.find_elements_by_class_name('ant-modal-body')       
            galleries_count = 0

            if len(eles)> 0:
                containers = webtools.check_and_get_all_elements_by_xpath(eles[0],'./div/div')
                if containers is not None and len(containers)> 0:
                    childs =  webtools.check_and_get_all_elements_by_xpath(containers[0], './div') 
                    if childs is not None:
                        galleries_count = len(childs)
                        for child in childs:
                            a_ele = webtools.check_and_get_ele_by_tag_name(child, 'a')
                            if a_ele is  not None:
                                galleries_list.append(a_ele.get_attribute('href'))

    #print(photo_stats.__dict__)
    return apiless.Photo(author_name = user_name, order = order, id = photo_id, title = title, href = photo_href, 
                        thumbnail_href = photo_thumbnail_href, thumbnail_local = photo_thumbnail_local, galleries = ",".join(galleries_list), stats = photo_stats )  

#---------------------------------------------------------------
#utils.@profile
def get_photos_list(driver, user_inputs, output_lists):
    """Return the list of photos from a given user.

    Process: 
    - Open user home page, scroll down until all photos are loaded
    - Make sure the document javascript is called to get the full content of the page
    - Extract photo data: no, id, photo title, href, thumbnail, views, likes, comments, galleries, highest pulse, rating, date, category, tags
    """

    photos_list = []
    success, message = webtools.open_user_home_page(driver, user_inputs.user_name)
    if not success:
        if message.find('Error reading') != -1:
            user_inputs.user_name,  user_inputs.db_path = '', ''
        return [], message

    hide_banners(driver)

    # We intend to scroll down an indeterminate number of times until the end is reached
    # In order to have a realistic progress bar, we need to give an estimate of the number of scrolls needed
    estimate_scrolls_needed = 3  #default value, just in case
    photos_count  = 1
    photos_count_ele = webtools.check_and_get_ele_by_css_selector(driver, '#content > div.profile_nav_wrapper > div > ul > li.photos.active > a > span')
    if photos_count_ele is not None:
        try:
            photos_count = int(photos_count_ele.text.replace('.', '').replace(',', ''))
        except:
            photos_count = 0
        estimate_scrolls_needed =  math.floor( photos_count / config.PHOTOS_PER_PAGE) +1

    webtools.scroll_to_end_by_class_name(driver, 'photo_link', photos_count)
    
    # abort the action if the target objects failed to load within a given timeout
    success, innerHtml = webtools.finish_Javascript_rendered_body_content(driver, time_out=30, class_name_to_check='finished')
    if not success:
        return [], f"Error loading user {user_inputs.user_name}'s photo page"

    page = html.document_fromstring(innerHtml)

    #extract photo title and href (alt tag) using lxml and regex
    photo_link_eles = page.xpath("//a[@class='photo_link ']")  
    img_eles = page.xpath("//img[@data-src='']")
    items_count = len(photo_link_eles)
    if items_count == 0:
        return [], f'User {user_inputs.user_name} does not upload any photo'

    utils.update_progress(0, f'    - Extracting 0/{items_count} photos:')

    # Create the photos list
    for i in range(items_count): 
        this_photo = process_a_photo_element(driver, i, items_count, photo_link_eles[i], img_eles[i], 
                                          user_inputs.user_name, user_inputs.password, output_lists.thumbnails_list, output_lists.thumbnails_dir)
        photos_list.append(this_photo)
    return photos_list, ''

#---------------------------------------------------------------
def get_followers_list(driver, user_inputs, output_lists):
    """Get the list of users who follow me. Info for each item in the list are: 
       No, Avatar Href, Avatar Local, Display Name, User Name, ID, Followers, Status
       If logged in, we can extract my following status to each of my followers  ( whether or not I'm alse following my follower)  
    Process:
    - Open the user home page, locate the text "followers" and click on it to open the modal windonw that hosts the followers list
    - Scroll to the end for all items to be loaded
    - Make sure the document js is running for all the data to load in the page body
    - Extract info and put in a list. 
    - Return the list
    """

    followers_list = []
    followers_count = 0
    if driver.current_url != 'https://500px.com/' + user_inputs.user_name:
        success, message = webtools.open_user_home_page(driver, user_inputs.user_name)
        if not success:
            printR('   - ' + message)
            if message.find('Error reading') != -1:
                user_inputs.user_name,  user_inputs.db_path = '', ''
            return followers_list

    hide_banners(driver)
    # click on the Followers text to open the modal window
    ele = webtools.check_and_get_ele_by_class_name(driver, "followers")    
    if ele is None:
        printR('   - Error on getting the followers list')
        return followers_list
    else:
        ele.click()

    # abort the action if the target objects failed to load within a given timeout
    if not webtools.finish_Javascript_rendered_body_content(driver, time_out=30, class_name_to_check='actors')[0]:
        return followers_list

    # extract number of followers                 
    followers_ele = webtools.check_and_get_ele_by_xpath(driver, '//*[@id="modal_content"]/div/div/div/div/div[1]/span')
    if followers_ele is None:
        printF('Error while getting the number off followers')
        return followers_list

    # remove thousand-separator character, if existed
    try:
        followers_count = int(followers_ele.text.replace(",", "").replace(".", ""))
    except:
        printR(f'   Error converting followers count to int: {followers_count}')
    else:
        printG(f'   {user_inputs.user_name.capitalize()} has {str(followers_count)} follower(s)' )

    # keep scrolling the modal window (config.LOADED_ITEM_PER_PAGE items are loaded at a time), until the end, where the followers count is reached 
    iteration_num = math.floor(followers_count / config.LOADED_ITEM_PER_PAGE) + 1 
           
    for i in range(1, iteration_num + 1):
        utils.update_progress(i / (iteration_num), f'    - Scrolling down to load more user')
        index_of_last_item_on_page = i * config.LOADED_ITEM_PER_PAGE -1
        try:
            last_ele = webtools.check_and_get_ele_by_xpath(driver, '//*[@id="modal_content"]/div/div/div/div/div[2]/ul/li[' + str(index_of_last_item_on_page) + ']')            
            if last_ele is not None:
                last_ele.location_once_scrolled_into_view
                time.sleep(random.randint(10, 20) / 10)  
        except NoSuchElementException:
            printR('Error while scrolling down to load more item')

    # now that we have all followers loaded, start extracting the info
    utils.update_progress(0, f'    - Extracting data 0/{followers_count}:')

    # abort the action if the target objects failed to load within a given timeout
    if not webtools.finish_Javascript_rendered_body_content(driver, time_out=30, class_name_to_check='finished')[0]:
        return followers_list

    actor_infos = driver.find_elements_by_class_name('actor_info')
    actors_following =  driver.find_elements_by_css_selector('.actor.following')
    len_following = len(actors_following)

    lenght = len(actor_infos)

    for i, actor_info in enumerate(actor_infos):
        if i > 0:
            utils.update_progress( i / (len(actor_infos) - 1), f'    - Extracting data {i + 1}/{followers_count}:')

        user_name, display_name, follower_page_link, following_status = ('' for i in range(4))
        count = ' '
  
        try:
            # get user name 
            name_ele = webtools.check_and_get_ele_by_class_name(actor_info, 'name')  
            if name_ele is not None:
                follower_page_link = name_ele.get_attribute('href')
                user_name = follower_page_link.replace('https://500px.com/', '')
            
            # get user avatar, user id and save the user avatar image to disk
            avatar_href, avatar_local, user_id = '', ' ', '0'
            actor_parent_ele = webtools.check_and_get_ele_by_xpath(actor_info, '..')   
            if actor_parent_ele is not None:
                avatar_ele = webtools.check_and_get_ele_by_class_name(actor_parent_ele, 'avatar')
                if avatar_ele is not None:
                    style = avatar_ele.get_attribute('style')
                    avatar_href =  style[style.find('https'): style.find('\")')]
                    # if user has default avatar
                    if 'userpic.png' in avatar_href:
                        if config.USE_LOCAL_THUMBNAIL:
                            avatar_local = 'userpic.png'
                    else:
                        user_id  =  re.search('\/user_avatar\/(\d+)\/', avatar_href).group(1)
                        avatar_local = user_id + '.jpg'
                        
                    avatar_full_file_name = os.path.join(config.OUTPUT_PATH, 'avatars', avatar_local)
                    # save avatar to disk if requested, and if it does not already exist
                    if config.USE_LOCAL_THUMBNAIL and not os.path.isfile(avatar_full_file_name):  
                        utils.save_avatar(avatar_href, avatar_full_file_name)

            # get followers count
            number_of_followers = ''
            texts = actor_info.text.split('\n')
            if len(texts) > 1: 
                display_name = texts[0] 
                count = texts[1]
                number_of_followers =  count.replace(' followers', '').replace(' follower', '') 

        except:  # log any errors during the process but do not stop 
            printR(f'\n   Error on getting user # {i + 1}: name: {display_name}, user name: {user_name}.Some info may be missing!')

        followers_list.append(apiless.User(order = str(i+1), avatar_href = avatar_href, avatar_local = avatar_local, display_name= display_name, 
                                   user_name = user_name, id = user_id, number_of_followers = number_of_followers, following_status = following_status))
    return followers_list 

#---------------------------------------------------------------
def does_this_user_follow_me(driver, user_inputs):
    """Check if a target_user follows a given user

    PROCESS:
    Get the list of users that the target user is following, then check if the list containt the given user name
    for better performance, we do not load the full list but rather one scroll-down at a time. We will scrolling down for more only if needed:
    - open the targer user home page, locate the text following and click on it to open the modal windonw containing following users list
    - scroll to the last loaded item to make all data available
    - make sure the document js is running for all the data to load in the page body
    - compare the user name of each load item to the given my_user_name. stop if a match is found, or continue to the next item until all the loaded items...
      are processed. scrolling down to load more items and repeat the process.
    """
    if driver.current_url != 'https://500px.com/' + user_inputs.target_user_name: 
        success, message = webtools.open_user_home_page(driver, user_inputs.target_user_name)
        if not success:
            if message.find('Error reading') != -1:
                user_inputs.target_user_name = ''
            return False, message
  
    hide_banners(driver)     
    ele = webtools.check_and_get_ele_by_xpath(driver, '//*[@id="content"]/div[1]/div[4]/ul/li[4]')   
    
    # extract number of following
    following_count = 0                       
    following_count_ele = webtools.check_and_get_ele_by_tag_name(ele, 'span')    
    if following_count_ele is None or following_count_ele.text == '0':
        return  False, "Status unknown. Timed out on getting the Following Count"
    else:
        try:
            following_count = int(following_count_ele.text.replace(",", "").replace(".", ""))
        except:
            printR(f'   Error converting followers count to int: {following_count}')
        else:
            printG(f'   - User {user_inputs.target_user_name} is following {str(following_count)} user(s)')
  
    # click on the Following text to open the modal window
    if ele is not None:

       driver.execute_script("arguments[0].click();", ele)

    # abort the action if the target objects failed to load within a given timeout
    if not webtools.finish_Javascript_rendered_body_content(driver, time_out=30, class_name_to_check='actors')[0]:
        return  False, "Status unknown. Timed out on loading more users"

    # start the progress bar
    utils.update_progress(0, '    - Processing loaded data:')
    iteration_num = math.floor(following_count / config.LOADED_ITEM_PER_PAGE) + 1    

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
            last_item_on_page =  current_index -1  #i * config.LOADED_ITEM_PER_PAGE - 1
            try:
                last_loaded_item = webtools.check_and_get_ele_by_xpath(driver, '//*[@id="modal_content"]/div/div/div/div/div[2]/ul/li[' + str(last_item_on_page) + ']')                                                                   
                if last_loaded_item is not None:
                    last_loaded_item.location_once_scrolled_into_view
                    time.sleep(1)
            except NoSuchElementException:
                pass

            # abort the action if the target objects failed to load within a given timeout 
            if not webtools.finish_Javascript_rendered_body_content(driver, time_out=30, class_name_to_check='finished')[0]:
               return  False, "Status unknown. Timed out loading more user"
            time.sleep(1)

            # update list with more users
            actor_infos = driver.find_elements_by_class_name('actor_info')
            #time.sleep(1)
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
            utils.update_progress(current_index / following_count, f'    - Processing loaded data {current_index}/{following_count}:')  
            try:
                ele = webtools.check_and_get_ele_by_class_name(actor, 'name')  
                if ele is not None:
                    following_user_page_link = ele.get_attribute('href')
                    following_user_name = following_user_page_link.replace('https://500px.com/', '')

                    if following_user_name is not None and following_user_name == user_inputs.user_name:
                        utils.update_progress(1, f'    - Processing loaded data {current_index}/{following_count}:')
                        return True, f'Following you ({current_index}/{following_count})'

            except NoSuchElementException:
                continue  #ignore if follower name not found
        users_done = current_index
    return False, "Not following"

#---------------------------------------------------------------
# This is a time-consuming process for users that have thousands of following user. This option is taken off from the main menu. 
# I'm evaluating the multiprocessing approach, on processing the already loaded data, not on multiple requests to the server.Stay tuned. For now I have a limit on the request number.
def get_following_statuses(driver, user_inputs, output_lists, csv_file):
    """ Get the following statuses of the users that you are following, with the option to specify the range of user in the following list.
   
    - start_user_index is 1-based and will be converted to 0-based
    - number_of_users : this is a lengthy process, so we provide this option to limit the number of users we will process. passing -1 to ignore this limit
    """

    # do main task
    df = pd.read_csv(csv_file, encoding='utf-16') #, usecols=["User Name"])     
    # a trick to force column Status content as string instead of the default float      
    df.Status = df.Status.fillna(value="")             
    # make sure the user's inputs stay in range with the size of the following list
    user_inputs.index_of_start_user = min(user_inputs.index_of_start_user, df.shape[0] -1)
    print('    Updating the following statuses on')
    printY(f'    {csv_file}', write_log=False)
    print(f'    ({user_inputs.number_of_users} users, starting from {user_inputs.index_of_start_user + 1}) ...')
   
    # process each user in dataframe
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
        if index < user_inputs.index_of_start_user:
            continue
        if user_inputs.number_of_users != -1 and index > user_inputs.index_of_start_user + user_inputs.number_of_users - 1:
            break
        user_inputs.target_user_name = row["User Name"]
        count += 1
        print(f'    User {count}/{user_inputs.number_of_users} (index {index + 1}):')
        result, message = does_this_user_follow_me(driver, user_inputs)
        if result == True:
            printG('   - ' + message)
            # update the status column in the dataframe with following status
            df.at[index, 'Status'] = message 
        else:
            printR('   - ' + message) if 'User name not found' in message else printY('   - ' + message)
            continue
    try:
        # write back dataframe to csv file
        df.to_csv(csv_file, encoding='utf-16', index = False)
        #return csv_file
    except: # pd.Errors.csv_file:
        printR(f'   Error writing file {os.path.abspath(csv_file)}.\nMake sure the file is not in use. Then type r for retry >')
        retry = input()
        if retry == 'r': 
            df.to_csv(csv_file, encoding='utf-16', index = False)
            #return csv_file
        else:
            printR('   Error writing file' + os.path.abspath(csv_file))
            #return ''

#---------------------------------------------------------------
def get_followings_list(driver, user_inputs, output_lists):
    """Get the list of users who I'm  following. Info for each item in the list are: 
       No, Avatar Href, Avatar Local, Display Name, User Name, ID, Followers, Status

    PROCESS:
    - Open the user home page, locate the text "followings" and click on it to open the modal windonw that hosts followers list
    - Scroll to the end for all items to be loaded
    - Make sure the document js is completed for all the data to load in the page body
    - Extract info and put in a list. 
    - Return the list
    """

    followings_list = []
    following_count = 0
    if driver.current_url != 'https://500px.com/' + user_inputs.user_name:
        success, message = webtools.open_user_home_page(driver, user_inputs.user_name)
        if not success:
            printR('   - ' + message)
            if message.find('Error reading') != -1:
                user_inputs.user_name,  user_inputs.db_path = '', ''
            return followings_list

    hide_banners(driver)                  
                                          
    # click on the Following text to open the modal window
    ele = webtools.check_and_get_ele_by_xpath(driver, '//*[@id="content"]/div[1]/div[4]/ul/li[4]')     
    try:
        if ele is None:
            printR('   Error on getting the followings list')
            return followings_list
        else:
            ele.click()
    except:
        # you may get an exception here because of the tooltip on the element
        #printR("   Error on opening the Following list. Please try again.")
        pass

    # abort the action if the target objects failed to load within a given timeout    
    if not webtools.finish_Javascript_rendered_body_content(driver, time_out=15, class_name_to_check='actors')[0]:
        return followings_list
            
    # extract number of following                      
    following_ele = webtools.check_and_get_ele_by_xpath(driver, '//*[@id="modal_content"]/div/div/div/div/div[1]/span') 
    if following_ele is None:
        return followings_list

    # remove thousand separator character, if existed
    try:
        following_count = int(following_ele.text.replace(",", "").replace(".", ""))
    except:
        printR(f'   Error converting followers count to int: {following_count}')
    else:
        printG(f'   {user_inputs.user_name.capitalize()} is following { str(following_count)} user(s)')

    # keep scrolling the modal window, 50 followers at a time, until the end, where the followings count is reached 
    iteration_num = math.floor(following_count / config.LOADED_ITEM_PER_PAGE) + 1 
    for i in range(1, iteration_num):
        utils.update_progress(i / (iteration_num -1 ), f'    - Scrolling down to load more users:')
        last_item_on_page = i * config.LOADED_ITEM_PER_PAGE - 1
        try:
            the_last_in_list = driver.find_elements_by_xpath('//*[@id="modal_content"]/div/div/div/div/div[2]/ul/li[' + str(last_item_on_page) + ']')[-1]                                                             
            the_last_in_list.location_once_scrolled_into_view
            time.sleep(1)
        except:
            printR('    Error while scrolling down to load more item. We may not get all requested items.')
 
    # now that we have all followers loaded, start extracting info
    utils.update_progress(0,f'    - Extracting data 0/{following_count}:')
    actor_infos = driver.find_elements_by_class_name('actor_info')
    lenght = len(actor_infos)

    for i, actor_info in enumerate(actor_infos):
        if i > 0:
            utils.update_progress( i / (len(actor_infos) - 1), f'    - Extracting data {i + 1}/{following_count}:')

        user_name, display_name, followings_page_link, count, number_of_followers = ('' for i in range(5)) 
        avatar_href, avatar_local, user_id = '', ' ', '0'
        try:
            # get user name 
            ele = webtools.check_and_get_ele_by_class_name(actor_info, 'name')
            #time.sleep(random.randint(5, 10) / 10)   
            if ele is not None:
                following_page_link = ele.get_attribute('href')
                user_name = following_page_link.replace('https://500px.com/', '')

            # get user avatar and user id
            actor_info_parent_ele = webtools.check_and_get_ele_by_xpath(actor_info, '..')   
            if actor_info_parent_ele is not None:
                avatar_ele = webtools.check_and_get_ele_by_class_name(actor_info_parent_ele, 'avatar')
                if avatar_ele is not None:
                    style = avatar_ele.get_attribute('style')
                    avatar_href =  style[style.find('https'): style.find('\")')]                   
                    # if user has default avatar
                    if 'userpic.png' in avatar_href:
                        if config.USE_LOCAL_THUMBNAIL:
                            avatar_local = 'userpic.png'
                    else:
                        user_id  =  re.search('\/user_avatar\/(\d+)\/', avatar_href).group(1)
                        avatar_local = user_id + '.jpg'
                    
                    avatar_full_file_name = os.path.join(config.OUTPUT_PATH, 'avatars', avatar_local)
                    # save avatar to disk if requested, and if it does not already exist
                    if config.USE_LOCAL_THUMBNAIL and not os.path.isfile(avatar_full_file_name):  
                        utils.save_avatar(avatar_href, avatar_full_file_name)

            # get followers count
            texts = actor_info.text.split('\n')
            if len(texts) > 0: display_name = texts[0] 
            if len(texts) > 1: count = texts[1]; 
            number_of_followers =  count.replace(' followers', '').replace(' follower', '')  

        except:  # log any errors during the process but do not stop 
            printR(f'\n   Error on getting user # {i + 1}: name: {display_name}, user name: {user_name}.Some info may be missing!')

        # create user object and add it to the result list 
        followings_list.append(apiless.User(order = str(i+1), avatar_href = avatar_href, avatar_local = avatar_local, display_name = display_name, 
                                    user_name = user_name, id = user_id, number_of_followers = number_of_followers))   
    return followings_list

#---------------------------------------------------------------
def process_notification_element(notification_element, output_lists):
    """Process one notification item. Return a notification object of the following detail:
    No, Avatar Href, Avatar Local, Display Name, User Name, ID, Content, Photo Thumbnail Href, Photo Thumbnail Local, Photo Title, Time Stamp, Status, Photo Link

    """
    # Note that we initialize string with a space instead of an empty string. This is because the database sqlite treats empty string as NULL, 
    # which will cause problem if we choose a NULL column as one of primary key (it will fail to identify the record duplication)

    display_name, photo_title, status, avatar_href, avatar_local, photo_thumbnail_href, photo_thumbnail_local, abs_timestamp = ('' for i in range(8))
    user_name, content, relative_time_string, photo_link = (' ' for i in range(4))
    user_id, photo_id=  '0', '0'

    try:
        # get user_name, display_name
        actor = webtools.check_and_get_ele_by_class_name(notification_element, 'notification_item__actor') 
        if actor is None:
            return None
        display_name = actor.text

        user_name = actor.get_attribute('href').replace('https://500px.com/', '')

        # ignore Quest notification
        if 'quests/' in user_name:
            return None

        # get user avatar, user id   
        avatar_ele = webtools.check_and_get_ele_by_class_name(notification_element, 'notification_item__avatar_img')             
        #time.sleep(random.randint(5, 10) / 10)  

        if avatar_ele is None:
            return None
        avatar_href = avatar_ele.get_attribute('src')
        # if user has default avatar
        if 'userpic.png' in avatar_href:
            if config.USE_LOCAL_THUMBNAIL:
                avatar_local = 'userpic.png'
        else:
            user_id  =  re.search('\/user_avatar\/(\d+)\/', avatar_href).group(1)
            avatar_local = user_id + '.jpg'
            avatar_full_file_name = os.path.join(config.OUTPUT_PATH, 'avatars', avatar_local)
            # save avatar to disk if requested, and if it does not already exist
            if config.USE_LOCAL_THUMBNAIL and not os.path.isfile(avatar_full_file_name):  
                utils.save_avatar(avatar_href, avatar_full_file_name)

        # the type of notificication
        item_text = webtools.check_and_get_ele_by_class_name(notification_element, 'notification_item__text')  
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
        photo_ele = webtools.check_and_get_ele_by_class_name(item_text, 'notification_item__photo_link')
 
        # in case of a new follow, instead of a photo element, there will be 2 overlapping boxes, Follow and Following. We will determine if whether or not this actor has been followered  
        if photo_ele is None:  
            following_box = webtools.check_and_get_ele_by_class_name(notification_element, 'following')
            if following_box is not None and following_box.is_displayed():        
                status = 'Following'
            else:  
                status = 'Not Follow'  
        else: 
            photo_title = photo_ele.text
            photo_link = photo_ele.get_attribute('href') 

        # get photo thumbnail
        photo_thumb_ele = webtools.check_and_get_ele_by_class_name(notification_element, 'notification_item__photo_img') 
        #time.sleep(random.randint(5, 10) / 10)
        if photo_thumb_ele is not None:
            photo_thumbnail_href = photo_thumb_ele.get_attribute('src')
            # save the photo thumbnail to disk
            if config.USE_LOCAL_THUMBNAIL:
                photo_thumbnail_local = utils.save_photo_thumbnail(photo_thumbnail_href, output_lists.thumbnails_dir )
                if photo_thumbnail_local:
                    photo_id = os.path.splitext(photo_thumbnail_local)[0]
        
        # time stamp       
        time_stamp_ele = webtools.check_and_get_ele_by_class_name(notification_element, 'notification_item__timestamp')  
	
        # we convert the relative time(e.g "4 hours ago") to absolute time (e.g. 2020-03-08. 10:30:12AM)
        # so that we can put the notifications into a database without duplication, regardless of when we extracted them
        if time_stamp_ele: 
            abs_timestamp = utils.convert_relative_datetime_string_to_absolute_date(time_stamp_ele.text, format = "%Y %m %d")

    except:  # log any errors during the process but do not stop 
        printR(f'   Error on getting notification: actor: {display_name}, photo: {photo_title}.\nSome info may be missing!')

    # creating and return the notification object
    the_actor = apiless.User(avatar_href = avatar_href, avatar_local = avatar_local, display_name = display_name, user_name = user_name, id = user_id)
    the_photo = apiless.Photo(thumbnail_href = photo_thumbnail_href, thumbnail_local = photo_thumbnail_local, id = photo_id, href = photo_link, title = photo_title)

    return apiless.Notification(order = 0, actor = the_actor, the_photo = the_photo, content = content, timestamp = abs_timestamp,  status = status)

#---------------------------------------------------------------
def process_notifications(request_number, start_index, items, output_lists):
    """Given a list of notification web elements and a number of requested notifications, extract info and return a list of notification objects """

    notifications =[]
    for i, item in enumerate(items):
        count_sofar = len(notifications)    
        if count_sofar >= request_number:
            break
        
        new_notification = process_notification_element(item, output_lists)
        if new_notification is not None:
            count_sofar += 1
            new_notification.order = count_sofar + start_index
            notifications.append(new_notification)
            # advance the progress bar
            utils.update_progress(count_sofar/request_number, f'    - Extracted data {count_sofar}/{request_number}') 
    return notifications

#---------------------------------------------------------------
#@utils.profile
def get_notification_list(driver, user_inputs, output_lists, get_full_detail = True ):
    """Get n last notification items. Return 2 lists, notifications list and a list of unique users from it, along with the count of appearances of each user
    
    A detailed notification item contains full_name, user name, the content of the notification, title of the photo in question, the time stamp and a status
    A short notification item contains just full name and user name
    A unique notification list is a short notification list where all the duplication are removed.
    If the given GET_FULL_DETAIL is true, return the detailed list, if false, return the unique list
    PROCESS:
    - expecting the user was logged in, and the notification page is the active page
    - scroll down until all the required number of notifications are loaded
    - extract info.
    - Return two lists, the notifications list, and a simplified list, containing the unique users on the first list. 
    """

    unique_notificators, notifications_list, simplified_list = [], [], []

    # Feb 19 2020: we now can get the notifications from a certain index
    start_index = user_inputs.index_of_start_notification
    length_required = user_inputs.number_of_notifications
    length_needed = start_index + length_required

    webtools.scroll_down_active_page(driver, None, 'notification_item__photo_link', '', length_needed, '    - Scrolling down for more notifications:' ) 

    # get the info now that all we got all the available notifications
    items = driver.find_elements_by_class_name('notification_item')  
    notifications_list = process_notifications(user_inputs.number_of_notifications, user_inputs.index_of_start_notification, items, output_lists)
    if len(notifications_list) == 0 and len(unique_notificators) == 0: 
        printG(f'   User {user_inputs.user_name} has no notification')
        return [], []

    # create the simplified list from the notifications list for easy manipulation
    # each item in the list is a comma-separated string of avatar link, display name and user name
    simplified_list = [f'{item.actor.avatar_href},{item.actor.avatar_local},{item.actor.display_name.replace(",", " ")},{item.actor.user_name},{item.actor.id} ' for item in notifications_list]
    
    # extract the unique users and the number of times they appear in the notifications list  
    unique_notificators = utils.count_And_Remove_Duplications(simplified_list)

    # add order number at the beginning of each row
    for j in range(len(unique_notificators)):
        unique_notificators[j] = f'{str(j+1)},{unique_notificators[j]}'

    return notifications_list, unique_notificators

#---------------------------------------------------------------
def get_like_actioners_list(driver, user_inputs, output_lists, get_name_only = True):
    """Get the list of users who liked a given photo. If get_name_only=True, only extract user_name and display name, else get all other info.
       Return the list and  a suggested file name that includes owner name, photo title and the like count

    PROCESS:
    - Expecting the active page in the browser is the given photo page
    - Run the document js to render the page body
    - Extract photo title and photographer name
    - Locate the like count number then click on it to open the modal window hosting the list of actioner user
    - Scroll down to the end and extract relevant info, put all to the list and return it
    """
    time_out = 20
    actioners_list = []
    date_string = datetime.datetime.now().replace(microsecond=0).strftime(config.DATE_FORMAT)

    try:  
        info_box = WebDriverWait(driver, time_out).until(EC.presence_of_element_located((By.XPATH, '//*[@id="root"]/div[3]/div/div[2]')) )
    except  TimeoutException:
        printR(f'   Time out ({time_out}s)! Please try again')
        return [], ''
  
    print('     - Getting photo details ...')
    # get photographer name
    photographer_ele = webtools.check_and_get_ele_by_xpath(info_box, '//div[2]/div[1]/p[1]/span/a')
    if photographer_ele is None: 
        photographer_name = ''
        printR('   Error getting photographer name')
    else:
        photographer_name = photographer_ele.text
        printG(f'   Photogapher: {photographer_name}')

    # get photo title
    photo_title = ''
    title_ele = webtools.check_and_get_ele_by_xpath(info_box, '//div[2]/div[1]/h3')
    if title_ele is None: 
        printR('   Error getting photo title')
    else:
        photo_title = title_ele.text
        printG(f'   Photo title: {photo_title}')

    # Get the like-count-button and click on it to open the modal window that host the actioners list
    try:
        photo_likes_count_ele = WebDriverWait(driver, time_out).until(EC.presence_of_element_located((By.XPATH, '//a[@data-id="photo-likes-count"]')) )
    except  TimeoutException:
        printR(f'   Time out ({time_out}s! Please try again')
        return [], ''

    likes_count_string = photo_likes_count_ele.text
    try:
        likes_count = int(likes_count_string.replace('.','').replace(',',''))
    except:
        likes_count = 0
        printR(f'Error getting likes count on {photo_title}')
    else:
        printG(f"   This photo has {likes_count} likes")

    photo_likes_count_ele.click()
    
    try:
        WebDriverWait(driver, time_out).until( EC.presence_of_element_located((By.CLASS_NAME, 'ant-modal-body')) )
    except  TimeoutException:
        printR(f'   Time out ({time_out}s! Not all elements are loaded. You may try again later.')
 
    # make a meaningful output file name
    like_actioners_file_name = os.path.join(output_lists.output_dir, \
        f"{photographer_name.replace(' ', '-')}_{likes_count}_likes_{photo_title.replace(' ', '-')}_{date_string}.csv")

    #get a container element containing all actors
    container= webtools.check_and_get_ele_by_class_name(driver,'ant-modal-body')
    time.sleep(1)
    if container is None:
        return [], ''
    #scrolling down until all the actors are loaded
    img_eles = webtools.scroll_to_end_by_tag_name_within_element(driver, container, 'img', likes_count)
   
    # create actors list
    actors_count = len(img_eles )

    for i, img in enumerate(img_eles):
        utils.update_progress(i / (actors_count - 1), f'    - Extracting data {i+1}/{actors_count}:')

        display_name, user_name, followers_count, following_status = ('' for i in range(4))
        avatar_href, avatar_local, user_id = '', ' ', '0'

        try: 
            display_name = img.get_attribute('alt')
            img_ele_parent =  webtools.check_and_get_ele_by_xpath(img, '..')
            if img_ele_parent is None:
                continue
            user_name = img_ele_parent.get_attribute('href').replace('https://500px.com/','')
            if get_name_only:
                actioners_list.append(apiless.User(display_name = display_name, user_name = user_name))
                continue
            
            # get more details on each user
            avatar_href= img.get_attribute('src')      
            # if user has default avatar
            if 'userpic.png' in avatar_href:
                if config.USE_LOCAL_THUMBNAIL:
                    avatar_local = 'userpic.png'
            else:
                user_id  =  re.search('\/user_avatar\/(\d+)\/', avatar_href).group(1)
                avatar_local = user_id + '.jpg'
                # save avatar to disk if requested, and only if it does not exist
                # this means that if the users changed theirs avatars we won't see the change. 
                # To get the latest version of an avatar, we have to identify the file on the list and delete it before running the script
            
            avatar_full_file_name = os.path.join(config.OUTPUT_PATH, 'avatars', avatar_local)
            # save avatar to disk if requested, and if it does not already exist
            if config.USE_LOCAL_THUMBNAIL and not os.path.isfile(avatar_full_file_name):  
                utils.save_avatar(avatar_href, avatar_full_file_name)

            #img_ele_parent =  webtools.check_and_get_ele_by_xpath(img, '..')
            #if img_ele_parent is None:
            #    continue
            #user_name = img_ele_parent.get_attribute('href').replace('https://500px.com/','')

            follower_count_text_ele =  webtools.check_and_get_ele_by_xpath(img_ele_parent, '..') 
            if follower_count_text_ele is None: 
                continue
            texts = follower_count_text_ele.text.split('\n')
            if len(texts) > 1:
                followers_count  = re.sub('[^\d]+', '', texts[1]) 
            
            # get following status
            if not user_inputs.password:
                following_status = 'Unknown'
            else:    
                following_status = 'Not follow'
                following_status_ele = webtools.check_and_get_ele_by_xpath(img, '../../../../div[2]/a/span')
                if following_status_ele is None:
                    continue
                if 'Unfollow' in following_status_ele.get_attribute("innerHTML"):
                    following_status = 'Following'

        except:  # log any errors during the process but do not stop 
            printR(f'\n   Error on getting user # {i + 1}: name: {display_name}, user name: {user_name}.Some info may be missing!')

        actioners_list.append(apiless.User(order = str(i+1), avatar_href = avatar_href, avatar_local = avatar_local, display_name = display_name, 
                                    user_name = user_name, id = user_id, number_of_followers = str(followers_count), following_status = following_status) )        
    return actioners_list, like_actioners_file_name

#---------------------------------------------------------------
def like_n_photos_from_user(driver, target_user_name, number_of_photos_to_be_liked, include_already_liked_photo_in_count = True, close_browser_on_error = True):
    """Like n photo of a given user, starting from the top. Return False and error message if error occured, True and blank string otherwise

    If the include_already_liked_photo is true (default), the already-liked photo will be counted as done by the auto-like process
    for example, if you need to auto-like 3 photos from a user, but two photos in the first three photos are already liked, 
    then you only need to do one
    If the include_already_liked_photo_in_count is false, the process will auto-like the exact number requested
    the argument close_browser_on_error needs to be false if this function is called in a loop: if errors occur, we want to process the next item
    PROCESS:
    - Open the user home page
    - Force document js to run to fill the visible body
    - Locate the first photo, check if it is already-liked or not, if yes, go the next photo, it no, click on it to like the photo
    - Continue until the asking number of photos is reached. 
    - When we have processed all the loaded photos but the required number is not reached yet, 
      scroll down once to load more photos ( currently 500px loads 50 photos at a time) and repeat the steps until done
      """

    success, message = webtools.open_user_home_page(driver, target_user_name)
    if not success:
        return False
    
    # abort the action if the target objects failed to load within a given timeout    
    if not webtools.finish_Javascript_rendered_body_content(driver, time_out=60, class_name_to_check='finished')[0]:
        return False, 

    hide_banners(driver)        
    
    new_fav_icons =  webtools.check_and_get_all_elements_by_css_selector(driver, '.button.new_fav.only_icon') 
    time.sleep(random.randint(5, 10) / 10)   
    if len(new_fav_icons) == 0:
        printY('   User has no photos')
    done_count = 0

    for i, icon in enumerate(new_fav_icons):
        icon.location_once_scrolled_into_view
        # skip already-liked photo. Count it as done if requested so
        if done_count < number_of_photos_to_be_liked and 'heart' in icon.get_attribute('class'): 
            if include_already_liked_photo_in_count == True:
                done_count = done_count + 1          
            printY(f'    - Liked #{str(done_count):3} Photo { str(i+1):2} - already liked')
            continue        

        # check limit
        if done_count >= number_of_photos_to_be_liked:  
            break
        if not config.HEADLESS_MODE:
            webtools.hover_by_element(driver, icon) # not necessary, but good for visual demonstration
        #time.sleep(random.randint(5, 10) / 10)
        try:
            title =  icon.find_element_by_xpath('../../../../..').find_element_by_class_name('photo_link').find_element_by_tag_name('img').get_attribute('alt')
            if title and title == 'Photo':
                title = 'Untitled'
            driver.execute_script("arguments[0].click();", icon) 
            done_count = done_count + 1
            printG(f"    - Liked #{str(done_count):3}: '{title:.50}'")
            # pause a randomized time between 0.5 to 2 seconds between actions 
            #time.sleep(random.randint(5, 20) / 10)

        except Exception as e:
            printR(f'   Error after {str(done_count)}, at index {str(i)}, title {title}:\nException: {e}')
            return False
    return True

#---------------------------------------------------------------
def like_n_photos_on_current_page(driver, number_of_photos_to_be_liked, index_of_start_photo):
    """Like n photos on the active photo page. It could be either popular, popular-undiscovered, upcoming, fresh or editor's choice page."""

    title = ''
    photographer = ''
    photos_done = 0
    current_index = 0   # the index of the photo in the loaded photos list. We dynamically scroll down the page to load more photos as we go, so ...
                        # ... more photos are appended at the end of the list. We use this current_index to keep track where we were after a list update 
            
    # debug info: without scrolling, it would load (config.PHOTOS_PER_PAGE = 50) photos
    new_fav_icons = webtools.check_and_get_all_elements_by_css_selector(driver, '.button.new_fav.only_icon')  #driver.find_elements_by_css_selector('.button.new_fav.only_icon')
    loaded_photos_count = len(new_fav_icons)

    #optimization: at the begining, scrolling down to the desired index instead of repeatedly scrolling & checking 
    if index_of_start_photo > config.PHOTOS_PER_PAGE:
        estimate_scrolls_needed =  math.floor( index_of_start_photo / config.PHOTOS_PER_PAGE) +1
        webtools.scroll_down(driver, 1, estimate_scrolls_needed, estimate_scrolls_needed, f' - Scrolling down to photos #{index_of_start_photo}:') 
        
        # instead of a fixed waiting time, we wait until the desired photo to be loaded  
        while loaded_photos_count < index_of_start_photo:
            new_fav_icons = webtools.check_and_get_all_elements_by_css_selector(driver, '.button.new_fav.only_icon')
            loaded_photos_count = len(new_fav_icons)
          
    while photos_done < number_of_photos_to_be_liked: 
        # if all loaded photos have been processed, scroll down 1 time to load more
        if current_index >= loaded_photos_count: 
            prev_loaded_photos = loaded_photos_count
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # instead of a fixed waiting time, we wait until the desired photo to be loaded, within a given timeout  
            time_out = 15
            while loaded_photos_count <= current_index and time_out > 0:
                time_out -= 1
                new_fav_icons =  webtools.check_and_get_all_elements_by_css_selector(driver, '.button.new_fav.only_icon')  
                time.sleep(1)
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
            
            webtools.hover_by_element(driver, icon) # not needed, but good to have a visual demonstration
            try:
                #intentional slowing down a bit to make it look more like human
                time.sleep(random.randint(5,10)/10)  

                photo_link = icon.find_element_by_xpath('../../../../..').find_element_by_class_name('photo_link')
                title =  photo_link.find_element_by_tag_name('img').get_attribute('alt')
                photographer_ele = webtools.check_and_get_ele_by_class_name(photo_link, 'photographer')

                if photographer_ele is not None:
                    photographer_ele.location_once_scrolled_into_view
                    webtools.hover_by_element(driver, photographer_ele)
                    photographer = photographer_ele.text
                    photographer_ele.location_once_scrolled_into_view
                    webtools.hover_by_element(driver, photographer_ele)
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

                printG(f'   - Liked {str(photos_done):>3}/{number_of_photos_to_be_liked:<3}, {photographer:<28.24}, Photo {str(i+1):<4} title {title:<35.35}')
            except Exception as e:
                printR(f'   Error after {str(photos_done)}, at index {str(i+1)}, title {title}:\nException: {e}')
                printY('   The page structure of this photo gallery is not recognizable. The process will stop.')
                # we set this to end the outer loop, while:
                photos_done = number_of_photos_to_be_liked
                break

#---------------------------------------------------------------
def play_slideshow(driver, time_interval):
    """Play slideshow of photos on the active photo page in browser.

    PROCESS:
    Expecting the active page in browser is the photos page
    - Open the first photo by click on it
    - Click on the expand arrow to maximize the display area 
    - After a given time interval, locate the next button and click on it to show the next photo
    - Exit when last photo is reached
    """
    photo_links_eles = webtools.check_and_get_all_elements_by_class_name(driver, 'photo_link')
    loaded_photos_count = len(photo_links_eles)
 
    if len(photo_links_eles) > 0:
        # show the first photo
        driver.execute_script("arguments[0].click();", photo_links_eles[0])

        # abort the action if the target objects failed to load within a given timeout    
        if not webtools.finish_Javascript_rendered_body_content(driver, time_out=30, id_to_check = 'copyrightTooltipContainer')[0 ]:
            return None, None	        
        #setup a keypress listener on the document and a variable to store the request
        driver.execute_script('''
            document.requestedInput = 'c';              /* default c for CONTINUE*/
            document.addEventListener("keydown", keyDownPress, false);
            function keyDownPress(e) { 
                if(e.keyCode != 37 && e.keyCode != 39)  /* ignore forward/backward navigation by arrow keys*/
                    if(e.keyCode == 80 )                /* p for PAUSE */
                        document.requestedInput = 'p';              
                    else if (e.keyCode == 67 )          /* c for CONTINUE*/       
                        document.requestedInput = 'c';              
                    else       
                        document.requestedInput = 's';  /* any other keys will be considered as 's', for STOP */                                                       
           } ''')    

        # abort the action if the target objects failed to load within a given timeout    
        if not webtools.finish_Javascript_rendered_body_content(driver, time_out=15, class_name_to_check = 'entry-visible')[0]:
            return None, None	        

        # suppress the sign-in popup that may appear if not login
        hide_banners(driver)        
        
        # locate the expand icon and click it to expand the photo
        expand_icon = webtools.check_and_get_ele_by_xpath(driver, '//*[@id="copyrightTooltipContainer"]/div/div[2]') 
        if expand_icon is not None:
            driver.execute_script("arguments[0].click();",expand_icon)
        time.sleep(time_interval)
        
        #locate the right arrow icon that can be use to navigate to the next photo
        next_icon = webtools.check_and_get_ele_by_xpath(driver, '//*[@id="copyrightTooltipContainer"]/div/div[1]/div') 
        
        #use the next photo icon as a flag to signal the end of the gallery
        while next_icon is not None:
            requested_input = driver.execute_script('return document.requestedInput')
            
            # go to the next photo
            if requested_input == 'c':
                ActionChains(driver).send_keys(Keys.RIGHT).perform()            
            while requested_input == 'p':
                time.sleep(0.5)
                requested_input = driver.execute_script('return document.requestedInput')
            
            if requested_input == 's':
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                return
            time.sleep(time_interval)                
            next_icon = webtools.check_and_get_ele_by_xpath(driver,  '//*[@id="copyrightTooltipContainer"]/div/div[2]/div/div[2]')  

#---------------------------------------------------------------                           
def like_n_photos_on_homefeed_page(driver, user_inputs):
    """Like n photos from the user's home feed page, excluding recommended photos and skipping consecutive apiless.photo(s) of the same user
   
    PROCESS:
    - Expecting the user home feed page is the active page in the browser
    - Get the list elements representing loaded interested photos (the ones from photographers that you are following)
    - For each element in the list, traverse up, down the xml tree for photo title, owner name, like status, and make a decision to click the like icon or not
    - Continue until the required number is reached. along the way, stop and scroll down to load more photos when needed 
    """
    photos_done = 0
    current_index = 0  # the index of the photo in the loaded photos list. We dynamically scroll down the page to load more photos as we go, so ...
                       # ... we use this index to keep track where we are after a list update 
    prev_photographer_name = ''
    print(f"    - Getting the loaded photos from {user_inputs.user_name}'s home feed page ...")
    img_eles = webtools.get_IMG_element_from_homefeed_page(driver)
    if not img_eles or (img_eles and len(img_eles)) == 0:
        print(f"    - No photos found on {user_inputs.user_name}'s home feed page")
        return

    loaded_photos_count = len(img_eles)
   
    while photos_done < user_inputs.number_of_photos_to_be_liked: 
        # check whether we have processed all loaded photos, if yes, scroll down 1 time to load more
        if current_index >= loaded_photos_count: 
            prev_loaded_photos = loaded_photos_count
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")                
            time.sleep(2)

            img_eles = webtools.get_IMG_element_from_homefeed_page(driver)
            if not img_eles or (img_eles and len(img_eles)) == 0:
                print(f"    - No photos found on {user_inputs.user_name}'s home feed page")
                return
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
            parent2 = webtools.check_and_get_ele_by_xpath(img_eles[i], '../..')   
            if parent2 is None: 
                continue
                
            parent2_sib1 =  webtools.check_and_get_ele_by_xpath(parent2, './following-sibling::div') 
            if parent2_sib1 is None: 
                continue

            parent2_sib2 =  webtools.check_and_get_ele_by_xpath(parent2_sib1, './following-sibling::div') 
            if parent2_sib2 is  None: 
                continue    
            # for logging message, get photo title, photogragpher display name and  user name
            title_ele = webtools.check_and_get_ele_by_tag_name(parent2_sib2, 'h3') #title  = parent2_sib2.find_element_by_tag_name('h3').text            
            title = title_ele.text if title_ele is not None else 'not determined'
           
            a_ele = webtools.check_and_get_ele_by_tag_name(parent2_sib2, 'a')  #a = parent2_sib2.find_element_by_tag_name('a')
            photographer_display_name  = a_ele.text if a_ele is not None else "not determined"
            photographer_name = a_ele.get_attribute('href').replace('https://500px.com/', '') if a_ele is not None else "not determined"

            child_div_eles = webtools.check_and_get_all_elements_by_tag_name(parent2_sib1, 'div')
            if len(child_div_eles) > 2:
                heart_icon = child_div_eles[2]
                #get like status
                photo_already_liked = False
                svg_ele = webtools.check_and_get_ele_by_tag_name(heart_icon, 'svg')
                if svg_ele is not None:
                    title_ele = webtools.check_and_get_ele_by_tag_name(svg_ele, 'title')
                    if title_ele is not None:     
                        like_status = title_ele.get_attribute('innerHTML')
                        # skip if the photo is one of yours
                        if like_status.find('disabled') != -1:
                            printB(f'   Skipped:      photo {str(i + 1):3}, from {photographer_display_name:<32.30}, {title:<35.35}')
                            continue                           
                        elif like_status.find('Filled') != -1:  # already liked: 'Filled', not-yet like: 'Outline', your own photo: 'disabled'
                            photo_already_liked = True
                        if  not photo_already_liked:      
                            # skip consecutive photos of the same photographer
                            if photographer_name == prev_photographer_name:
                                printY(f'   Skipped:      photo {str(i + 1):3}, from {photographer_display_name:<32.30}, {title:<35.35}')
                                continue
                            if heart_icon is not None:
                                webtools.hover_by_element(driver, heart_icon)
                                driver.execute_script("arguments[0].click();", heart_icon) 
                                photos_done += 1
                                prev_photographer_name = photographer_name
                                printG(f'   - Like {photos_done:>3}/{user_inputs.number_of_photos_to_be_liked:<3}: photo {str(i + 1):<3}, from {photographer_display_name:<32.30}, {title:<40.40}')
                                time.sleep(random.randint(10, 20)/10)  # slow down a bit to make it look more like a human

#---------------------------------------------------------------
def login(driver, user_inputs):
    """Submit given credentials to the 500px login page. Display error message if error occured. Return True/False loggin status """

    if len(user_inputs.password) == 0 or len(user_inputs.user_name) == 0 or driver == None: 
        return False
    print(f'    - Logging in user {user_inputs.user_name} ...')
    time_out = 30
    driver.get("https://500px.com/login" )
    try:
        user_name_ele = WebDriverWait(driver, time_out).until(EC.presence_of_element_located((By.ID, 'emailOrUsername'))) # 'email')))
        user_name_ele.send_keys(user_inputs.user_name) 
        
        pwd_ele = WebDriverWait(driver, time_out).until(EC.presence_of_element_located((By.ID, 'password')))
        pwd_ele.send_keys(user_inputs.password) 

        submit_ele =  webtools.check_and_get_ele_by_xpath(user_name_ele, '../following-sibling::button') 
        if submit_ele is not None: 
            submit_ele.click()
        
        # after a sucess login, 500px will automatically load the user's homefeed page. So after submitting the credentials, we
        # wait until one of an element in the login page become unavailable
        WebDriverWait(driver, time_out).until(EC.staleness_of(user_name_ele))
       
    except  NoSuchElementException:
        printR("   Error accessing the login page. Please retry")
        return False
    except TimeoutException :
        printR(f'   Time out while loading {user_inputs.user_name} home page. Please retry.')
        return False
    except:
        printR(f'   Error loading {user_inputs.user_name} home page. Please retry.')
        return False  
    
    # username/password errors
    if webtools.check_and_get_ele_by_class_name(driver, 'error') is not None or \
       webtools.check_and_get_ele_by_class_name(driver, 'not_found') is not None or \
       webtools.check_and_get_ele_by_class_name(driver, 'missing') is not None:   
       printR(f'Error on loggin. Please retry with valid credentials')
       user_inputs.user_name, user_inputs.password,  user_inputs.db_path = ('' for i in range(3))
       return False
    return True

#---------------------------------------------------------------
def hide_banners(driver):
    """Hide or close popup banners that make elements beneath them inaccessible. And click away the sign-in window if it pops up.
    
    Specifically, top banner is identified by the id 'hellobar',
    Bottom banners are identified by tag 'w-div' and
    Sign-up banner is identified by class 'join_500px_banner_close_ele'
    """

    top_banner = webtools.check_and_get_ele_by_id(driver, 'hellobar')
    if top_banner is not None:
        try:
            driver.execute_script("arguments[0].style.display='none'", top_banner)
        except:
            pass

    bottom_banners = webtools.check_and_get_all_elements_by_tag_name(driver, 'w-div')
    for banner in bottom_banners:
        close_ele = webtools.check_and_get_ele_by_tag_name(banner, 'span')
        if close_ele is not None:
            try:
                driver.execute_script("arguments[0].click();", close_ele)
            except:
                pass   

    join_500px_banner_close_ele = webtools.check_and_get_ele_by_class_name(driver, 'unified_signup__close')
    if join_500px_banner_close_ele is not None:
        try:
            driver.execute_script("arguments[0].click();", join_500px_banner_close_ele)
        except:
            pass

#---------------------------------------------------------------
def show_menu(user_inputs, special_message=''):
    """ Display main menu. Validate and accept these inputs from users: user name, password  and the desired option. 
    
    - Inputs are stored in the user_inputs objects, which is passed by reference.  
    - The return value is a string containing either 'r', 'q' or any digit characters
    - The special_message, if given, will be displayed near the end of the menu. It could be used as an alert, warning or error
      from the last operation.
    """

    printC('')
    printC('--------- Chose one of these options: ---------')
    printY('      The following options require a user name:', write_log=False)
    printC('   1  Get user statistics')
    printC('   2  Get user photos list (login is optional)')
    printC('   3  Get followers list')
    printC('   4  Get followings list')
    printC('   5  Get a list of users who liked a given photo (login is optional)')

    printC('')
    printY('      The following options require user login:', write_log=False)
    printC('   6  Get n last notifications (max 5000) and the unique users on it')
    printC('   7  Check if a user is following you')
    printC('')
    printC('   8  Like n photos from a given user')
    printC('   9  Like n photos, starting at a given index, on various photo pages') 
    printC('  10  Like n photos of each user who likes a given photo or yours')
    printC('  11  Like n photos from your home-feed page, excluding recommended photos ')
    printC('  12  Like n photos of each users in your last m notifications')
    printC('')
    printY('      The following option does not need credentials:', write_log=False)
    printC('  13  Play slideshow on a given gallery (login is optional)')
    printC('')
    printY('      Data Analysis:', write_log=False)
    printC('  14  Categorize users based on following statuses')
    printC('  15  Create a local database from the latest csv files on disk')

    printC('')
 
    printC('   r  Restart with different user')
    printC('   q  Quit')
    printC('')
  
    if special_message:
        printY(special_message)
  
    sel, abort = utils.validate_input('Enter your selection >', user_inputs)

    if abort:
        return 

    sel = int(sel)
    # No credentials needed for playing slideshow
    if sel == 13:
        user_inputs.choice = str(sel)
        return 
    
    # user name is mandatory for all options, except playing the slideshow
    if user_inputs.user_name == '':
        user_inputs.user_name = input('Enter 500px user name >')
        user_inputs.db_path =  config.OUTPUT_PATH +  r'\500px_' + user_inputs.user_name + '.db'
    printG(f'Current user: {user_inputs.user_name}', write_log=False)

    # analysis for users' relationship and creating local database options need nothing else
    if sel == 14 or sel == 15:
        user_inputs.choice = str(sel)
        return 

    # password is optional:
    #  - 2  Get user photos list: if logged in, we can get the list of galleries that each of your photo is featured in
    #  - 5  Get a list of users who liked a given photo: if logged in, we can get your following status to each user in the list
    if (sel == 2  or sel == 5) and user_inputs.password == '':
        prompt_message = 'Optional: if loggin, you can get the galleries that featured your photos,\npress ENTER to ignore this option, or type in the password now >'
        expecting_password = utils.win_getpass(prompt=prompt_message)
        if expecting_password != 'q' and expecting_password != 'r':
            user_inputs.password = expecting_password
        else:
            user_inputs.choice = expecting_password
            return 
            
    if sel < 6 or sel == 7:
        user_inputs.choice = str(sel)
        return
    
    # password is mandatory ( quit or restart are also possible at this step )
    if sel >= 6 :
        if user_inputs.user_name == '':
            user_inputs.user_name, abort = utils.validate_non_empty_input('Enter 500px user name >', user_inputs)
            if abort:
                return

        if user_inputs.password == '' and sel != 97:
            user_inputs.password, abort =  utils.validate_non_empty_input('Enter password >', user_inputs)
            if abort:
                return
    
    user_inputs.choice = str(sel)        

#---------------------------------------------------------------
def show_galllery_selection_menu(user_inputs):
    """ Menu to select a photo gallery for slideshow. Allow the user to abort during the input reception.
        Return three values: the photo href, the gallery name, and a boolean of True if an abort is requested, False otherwise. """

    printC('--------- Select the desired photos gallery: ---------')
    printC('    1  Popular')
    printC('    2  Popular-Undiscovered photographers')
    printC('    3  Upcoming')
    printC('    4  Fresh')
    printC("    5  Editor's Choice")
    printC("    6  User-specified gallery ...")
    # option to play slideshow on user's photos if a user name was provided 
    if user_inputs.choice == '13' and  user_inputs.user_name: 
        printC("    7  My photos")

    printC('')
    printY('    r  Restart for different user', write_log=False)
    printY('    q  Quit', write_log=False)

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
        input_val, abort = utils.validate_non_empty_input('Enter the link to your desired photo gallery.\n\
                             It could be a public gallery with filters, or a private gallery >', user_inputs)
        if abort:
            return '', '', True
        else:
            return input_val, 'User-specified gallery', False

    elif sel == '7': return f'https://500px.com/{user_inputs.user_name}'                  , 'My photos', False

    else:
        show_galllery_selection_menu(user_inputs)

#---------------------------------------------------------------
def define_and_read_command_line_arguments(): 
    """ Define all optional user inputs and their default values. Then fill in with the actual values from command lines.
        Return a user_inputs objects filled with given arguments. 

    All command line arguments are optional (as opposed to postional).  If the argurment '--choice' is not set, all other arguments will be ignored whether 
    they are set or not, and the attribute "use_command_line_args" will be set to false 
    """
    
    user_inputs = apiless.UserInputs()
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
        if config.DEBUG:
            print(f'    {dict_name}: {args_dict[dict_name]}')
        setattr(user_inputs, dict_name, args_dict[dict_name])
    # if a choice is provided from the command line, we will switch to command line mode. 
    if user_inputs.choice != '0':
        user_inputs.use_command_line_args = True
    return user_inputs

#---------------------------------------------------------------
def get_additional_user_inputs(user_inputs):
    """ Ask the user for additional inputs based on the option previously selected in user_inputs.choice.  

    Allow the user to abort (quit or restart) anytime during the input reception. return false if aborting, true otherwise """

    if user_inputs.choice == 'q' or user_inputs.choice == 'r':
        return False

    # no additional input are required for options from 1 to 5
    choice = int(user_inputs.choice)
    if choice < 5:
        return True
 
    # 5. Get a list of users who liked a given photo: photo_href
    if choice == 5: 
        user_inputs.photo_href, abort = utils.validate_non_empty_input('Enter your photo href >', user_inputs)
        if abort:
            return False

    # 6. Get n last notifications (max 5000) and the unique users on it: number_of_notifications 
    if choice == 6 : 
        input_val, abort =  utils.validate_input(f'Enter the number of notifications you want to retrieve(1-{config.MAX_NOTIFICATION_REQUEST}) >', user_inputs)
        if abort: 
            return False
        else:
            num1 = int(input_val)
            user_inputs.number_of_notifications = num1 if num1 < config.MAX_NOTIFICATION_REQUEST else config.MAX_NOTIFICATION_REQUEST

        input_val, abort =  utils.validate_input(f'Enter the desired start index (1-{config.MAX_NOTIFICATION_REQUEST - num1}) >', user_inputs)
        if abort: 
            return False
        else:
            num2 = int(input_val)
            if num2 > 0:
                num2 -= 1   # assuming ordinary end user will enter 1-based number 
            user_inputs.index_of_start_notification = num2 if num2 < config.MAX_NOTIFICATION_REQUEST -  user_inputs.number_of_notifications else \
                                                      config.MAX_NOTIFICATION_REQUEST - user_inputs.number_of_notifications
  
    # 7. Check if a user is following you : target user name
    elif choice == 7:
        user_inputs.target_user_name , abort =  utils.validate_non_empty_input('Enter target user name >', user_inputs)
        if abort:
            return False  

    # common input for 8 to 11: number of photo to be auto-liked
    elif choice >= 8 and choice <= 11:
        input_val, abort =  utils.validate_input(f'Enter the number of photos you want to auto-like (1-{config.MAX_AUTO_LIKE_REQUEST})>', user_inputs)
        if abort:
            return False
        else: 
            num = int(input_val)
            user_inputs.number_of_photos_to_be_liked = num if num < config.MAX_AUTO_LIKE_REQUEST else config.MAX_AUTO_LIKE_REQUEST         

        # 8.  Like n photos from a given user: target_user_name
        if choice == 8: 
            user_inputs.target_user_name, abort = utils.validate_non_empty_input('Enter target user name >', user_inputs)
            if abort:
                return False  

        # 9.  Like n photos, starting at a given index, on various photo pages:  gallery_href, index_of_start_photo
        elif choice == 9:  
            # gallery selection
            user_inputs.gallery_href, user_inputs.gallery_name, abort = show_galllery_selection_menu(user_inputs)
            if abort:
                return False
            
            input_val, abort =  utils.validate_input('Enter the index of the start photo (1-500) >', user_inputs)
            if abort:
                return False  
            else: 
                user_inputs.index_of_start_photo = int(input_val)

        # 10.  Like n photos of each user who likes a given photo or yours:
        elif choice == 10: 
            #photo_href
            user_inputs.photo_href, abort =  utils.validate_non_empty_input('Enter your photo href >', user_inputs)
            if abort: 
                return False    
            # these additional options are for next version
            ## index_of_start_user
            #input_val, abort =  utils.Validate_input('Enter the start index of the user (default 1)>' , user_inputs)
            #if abort:
            #    return False  
            #else: 
            #    int_val = int(input_val)
            #    # the end user will use 1-based index, so we will convert the input to 0-based
            #    if int_val > 0: int_val -= 1
            #    user_inputs.index_of_start_user = int_val   
            
            ## number of users    
            #input_val, abort =  utils.Validate_input('Enter the number of users you want to process>' , user_inputs)
            #if abort:
            #    return False  
            #else: 
            #    int_val = int(input_val)
            #    user_inputs.number_of_users = int_val        
    
    # 12. Like n photos of each users in your last m notifications         
    elif choice == 12: 
        input_val, abort = utils.validate_input(f'Enter the number of notifications you want to process(max {config.MAX_NOTIFICATION_REQUEST}) >', user_inputs)
        if abort: 
            return False
        else: 
            num = int(input_val)
            user_inputs.number_of_notifications = num if num < config.MAX_NOTIFICATION_REQUEST else config.MAX_NOTIFICATION_REQUEST

        input_val, abort = utils.validate_input('Enter the number of photos you want to auto-like for each user >', user_inputs)
        if abort:
            return False
        else: 
            num = int(input_val)
            user_inputs.number_of_photos_to_be_liked = num if num < config.MAX_AUTO_LIKE_REQUEST else config.MAX_AUTO_LIKE_REQUEST

    # 13.  Play slideshow on a given gallery 
    elif choice == 13:
        # allow a login for showing NSFW (not suitable for work) contents
        if user_inputs.password == '':
            printY('If you want to show NSFW contents, please login.', write_log=False)
            if user_inputs.user_name == '':            
                printY(' Type in your user name or just press ENTER to ignore', write_log=False)
                expecting_user_name = input('User name >')
                if expecting_user_name  == 'q' or expecting_user_name  == 'r':
                    user_inputs.choice = expecting_user_name
                    return False               
                if len(expecting_user_name) > 0:
                    user_inputs.user_name = expecting_user_name

            # user name has been entered
            if user_inputs.user_name != '':  
                printY('Type in your password or just press ENTER to ignore', write_log=False)
                expecting_password = utils.win_getpass(prompt='Password >')
                if expecting_password == 'q' or expecting_password == 'r':
                    user_inputs.choice = expecting_password
                    return True 
                if len(expecting_password) > 0:
                    user_inputs.password = expecting_password

        user_inputs.gallery_href, user_inputs.gallery_name, abort = show_galllery_selection_menu(user_inputs)
        if abort:
            return False

        input_val, abort = utils.validate_input('Enter the interval time between photos, in second>', user_inputs)
        if abort:
            return False
        else:
            user_inputs.time_interval = int(input_val)

            printY('To pause, press p', write_log=False)
            printY('To continue, press c', write_log=False)
            printY('To stop, press any other keys.', write_log=False)
            printY('You can use Left/Right arrow keys to manually navigate backward/forward.', write_log=False)
            printY(f'Now press ENTER to start the slideshow {user_inputs.gallery_name}.', write_log=False)
            wait_for_enter_key = input() 
 
    # Options not yet available from the menu:
    # 99. (in progress) Get following statuses of users you are following ( user_name, start index, number_of_users)
    # 98. Like n photos from each of m users, starting at a given start index, from a given csv files
    # more to come ...
    elif choice >= 98 :
        # number of followers
        input_val, abort = utils.validate_input('Enter the number of followers you want to process >', user_inputs)
        if abort:
            return False  
        else: 
            user_inputs.number_of_users = int(input_val)

        # start index of the user
        input_val, abort = utils.validate_input('Enter the user start index (1-based)>' , user_inputs)
        if abort:
            return False  
        else: 
            int_val = int(input_val)
            # the end user will use 1-based index, so we will convert the input to 0-based
            if int_val > 0: int_val -= 1
            user_inputs.index_of_start_user = int_val 
        
        if choice == 98:
            #number of photos
            input_val, abort = utils.validate_input('Enter the number of photos you want to auto-like >', user_inputs)
            if abort:
                return False
            else: 
                num = int(input_val)
                user_inputs.number_of_photos_to_be_liked = num if num < config.MAX_AUTO_LIKE_REQUEST else config.MAX_AUTO_LIKE_REQUEST 
        
            # full file name of the cvs file 
            user_inputs.csv_file, abort =  utils.validate_non_empty_input('Enter the csv full file name>', user_inputs)
            if abort: 
                return False       
            else:
                user_inputs.csv_file =user_inputs.csv_file.replace("\"", "").replace("\'", "") 
        return True
 
#---------------------------------------------------------------
def handle_option_1(driver, user_inputs, output_lists):
    """ Get user status."""

    time_start = datetime.datetime.now().replace(microsecond=0)
    date_string = time_start.strftime(config.DATE_FORMAT)
    printG(f"1. Getting {user_inputs.user_name}'s statistics:")

    # do task   
    stats, error_message = get_stats(driver, user_inputs, output_lists) 
    if error_message:
        printR('   - ' + error_message)
        if user_inputs.use_command_line_args == False:
            show_menu(user_inputs, error_message)
            return
    
    # write result to html file, show it on browser
    html_file =  os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_stats_{date_string}.html')
    utils.write_string_to_text_file(utils.create_user_statistics_html(stats), html_file, 'utf-16')
    utils.show_html_result_file(html_file)

    # print summary report
    printG(f"   File saved at: {os.path.basename(html_file)}")
    printG(f"   Duration: {datetime.datetime.now().replace(microsecond=0) - time_start}s")
    
#---------------------------------------------------------------
def handle_option_2(driver, user_inputs, output_lists):
    """ Get user photos """

    time_start = datetime.datetime.now().replace(microsecond=0)
    date_string = time_start.strftime(config.DATE_FORMAT)

    printG(f"2. Getting {user_inputs.user_name.capitalize()}'s photos list:")
    # avoid to do the same thing twice: if list (in memory) has items AND output file (on disk) exists
    if output_lists.photos is not None and len(output_lists.photos) > 0:
        html_file = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_{len(output_lists.photos)}_photos_{date_string}.html')
        if  os.path.isfile(html_file):
            printY(f'Results exists in memory and on disk. Showing the existing file at:\n{os.path.abspath(html_file)} ...', write_log=False)
            utils.show_html_result_file(html_file)
            ans = input('This file will be overidden if you want to redo. Proceed ? (y/n)')
            if ans == 'n' : 
                return

    # do the action
    # if user provided password then login (logged-in users can see the galleries that feature theirs photos
    if user_inputs.password != '' and not logged_in(driver):
        if login(driver, user_inputs) == False :
            return

    hide_banners(driver)
    output_lists.photos, error_message = get_photos_list(driver, user_inputs, output_lists)
    if error_message:
        printR('   - ' + error_message)
        if len(output_lists.photos) == 0:
            return

    # write result to csv, convert it to html, show html in browser
    if output_lists.photos is not None and len(output_lists.photos) > 0:
        csv_file = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_{len(output_lists.photos)}_photos_{date_string}.csv')           
        if utils.write_photos_list_to_csv(user_inputs.user_name, output_lists.photos, csv_file) == True:
            html_file = utils.CSV_photos_list_to_HTML(csv_file, output_lists, use_local_thumbnails = config.USE_LOCAL_THUMBNAIL,  
                                                ignore_columns = ['ID', 'Author Name', 'Href', 'Thumbnail Href', 'Thumbnail Local', 'Rating'])
            utils.show_html_result_file(html_file)  
            printG(f"   Duration: {datetime.datetime.now().replace(microsecond=0) - time_start}s")
        else:
            printR(f'   Error writing the output file\n:{csv_file}')

#---------------------------------------------------------------
def handle_option_3(driver, user_inputs, output_lists):
    """ Get followers"""
    
    time_start = datetime.datetime.now().replace(microsecond=0)
    date_string = time_start.strftime(config.DATE_FORMAT)
    printG(f"3. Getting the list of users who follow {user_inputs.user_name}:")

    # avoid to do the same thing twice: when the list (in memory) has items and output file exists on disk
    if output_lists.followers_list is not None and len(output_lists.followers_list) > 0:
        html_file = f'{user_inputs.user_name}_{len(output_lists.followers_list)}_followers_{date_string}.html'
        if os.path.isfile(html_file):
            printY(f'Results exists in memory and on disk. Showing the existing file at:\n{os.path.abspath(html_file)} ...', write_log=False)
            utils.show_html_result_file(html_file) 
            return
   
    # do task
    # if user provided password then login
    if user_inputs.password != '' and not logged_in(driver):
        if login(driver, user_inputs) == False :
            return

    hide_banners(driver)
    output_lists.followers_list = get_followers_list(driver, user_inputs, output_lists)

    # write result to csv, convert it to html, show html in browser
    if output_lists.followers_list is not None and len(output_lists.followers_list) > 0:
        csv_file = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_{len(output_lists.followers_list)}_followers_{date_string}.csv')           
        if utils.write_users_list_to_csv(output_lists.followers_list, csv_file) == True:
            # show output and print summary report
            html_file = utils.CSV_to_HTML(csv_file, apiless.CSV_type.followers, output_lists, use_local_thumbnails = config.USE_LOCAL_THUMBNAIL, 
                                    ignore_columns=['Avatar Href', 'Avatar Local', 'User Name', 'ID', 'Status'])
            utils.show_html_result_file(html_file) 
            printG(f"   Duration: {datetime.datetime.now().replace(microsecond=0) - time_start}s")
        else:
            printR(f'   Error writing the output file\n:{csv_file}')

#---------------------------------------------------------------
def handle_option_4(driver, user_inputs, output_lists):
    """ Get followings (friends)"""
    
    time_start = datetime.datetime.now().replace(microsecond=0)
    date_string = time_start.strftime(config.DATE_FORMAT)
    printG(f"4. Getting the list of users that you are following:")

    # avoid to do the same thing twice: when the list (in memory) has items and output file exists on disk
    if output_lists.followings_list is not None and len(output_lists.followings_list) > 0:
        # find the latest html file on disk and show it
        files = [f for f in glob.glob(output_lists.output_dir + f"**/{user_inputs.user_name}*followings*.html")]
        files.sort(key=lambda x: os.path.getmtime(x))
        html_file = files[-1]
        printY(f'Results exists in memory and on disk. Showing the existing file at:\n{os.path.abspath(html_file)} ...', write_log=False)
        utils.show_html_result_file(html_file)
        ans = input('This file will be overidden if you want to redo. Proceed ? (y/n)')
        if ans == 'n' : 
            return

    # do task
    output_lists.followings_list = get_followings_list(driver, user_inputs, output_lists)
    
    # write result to csv, convert it to html, show html in browser
    if len(output_lists.followings_list) > 0:
        csv_file = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_{len(output_lists.followings_list)}_followings_{date_string}.csv')
        if utils.write_users_list_to_csv(output_lists.followings_list, csv_file) == True:
            # show output and print summary report
            html_file = utils.CSV_to_HTML(csv_file, apiless.CSV_type.followings, output_lists, use_local_thumbnails = config.USE_LOCAL_THUMBNAIL, 
                                    ignore_columns = ['Avatar Href', 'Avatar Local', 'User Name', 'ID', 'Status'])
            utils.show_html_result_file(html_file) 
            printG(f"   Duration: {datetime.datetime.now().replace(microsecond=0) - time_start}s")
        else:
            printR(f'   Error writing the output file\n:{csv_file}')

#---------------------------------------------------------------
def handle_option_5(driver, user_inputs, output_lists):
    """ Get a list of users who liked a given photo."""
    
    time_start = datetime.datetime.now().replace(microsecond=0) 
    printG(f"5. Getting the list of unique users who liked the given photo:")

    # if user provided password then login
    if user_inputs.password != '' and not logged_in(driver):
        if login(driver, user_inputs) == False :
            return
    try:
        driver.get(user_inputs.photo_href)
    except:
        printR(f'   Invalid href: {user_inputs.photo_href}. Please retry.')
        show_menu(user_inputs)        
        return

    # do task
    time.sleep(1)
    hide_banners(driver)
    output_lists.like_actioners_list, csv_file = get_like_actioners_list(driver, user_inputs, output_lists, get_name_only = False)

    # write result to csv, convert it to html, show html in browser
    if output_lists.like_actioners_list is not None and  len(output_lists.like_actioners_list) > 0 and \
                                            utils.write_users_list_to_csv(output_lists.like_actioners_list, csv_file) == True:
        html_file = utils.CSV_to_HTML(csv_file, apiless.CSV_type.like_actors, output_lists, use_local_thumbnails = config.USE_LOCAL_THUMBNAIL,  
                                ignore_columns = ['Avatar Href', 'Avatar Local', 'User Name', 'ID'])
        utils.show_html_result_file(html_file) 

    printG(f"   Duration: {datetime.datetime.now().replace(microsecond=0) - time_start}s")

#---------------------------------------------------------------
def handle_option_6(driver, user_inputs, output_lists):
    """ Get n last notifications details (max 5000). Show the detail list and the list of the unique users on it"""

    time_start = datetime.datetime.now().replace(microsecond=0)
    date_string = time_start.strftime(config.DATETIME_FORMAT)
    if user_inputs.number_of_notifications == -1:
        printG(f"6. Getting up to {config.MAX_NOTIFICATION_REQUEST} notifications and the unique users on that list ...")
    elif user_inputs.index_of_start_notification > 0:
        printG(f"6. Getting {user_inputs.number_of_notifications} notifications, starting from index {user_inputs.index_of_start_notification}, and the unique users on that list:")
    else: 
        printG(f"6. Getting the last {user_inputs.number_of_notifications} notifications and the unique users on that list ...")
    html_file = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_{user_inputs.number_of_notifications}_notifications_{date_string}.html')

    # avoid to do the same thing twice: when the list (in memory) has items and output file exists on disk
    if output_lists.notifications is not None and len(output_lists.notifications) > 0 and os.path.isfile(html_file):
        printY(f'   Results exists in memory and on disk. Showing the existing file at:\n{os.path.abspath(html_file)} ...', write_log=False)        
        utils.show_html_result_file(html_file)
        return
    
    if not logged_in(driver):
        if login(driver, user_inputs) == False :
            return

    driver.get('https://500px.com/notifications')
    time.sleep(1)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # abort the action if the target objects failed to load within a given timeout        
    if not webtools.finish_Javascript_rendered_body_content(driver, time_out=30, class_name_to_check='finished')[0]:
        return	

    hide_banners(driver)

    # do task   
    output_lists.notifications, output_lists.unique_notificators = get_notification_list(driver, user_inputs, output_lists, True)
    
    if len(output_lists.notifications) == 0 and len(output_lists.unique_notificators) == 0:
        show_menu(user_inputs)
        return
    
    csv_file = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_{len(output_lists.notifications)}_notifications_{date_string}.csv')
    html_file = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_{user_inputs.number_of_notifications}_notifications_{date_string}.html')

    # write unique users list to csv. Convert it to html, show it in browser
    csv_file_unique_users  = os.path.join(output_lists.output_dir, \
        f"{user_inputs.user_name}_{len(output_lists.unique_notificators)}_unique-users-in-{len(output_lists.notifications)}_notifications_{date_string}.csv")
    if len(output_lists.unique_notificators) > 0 and  utils.write_unique_notificators_list_to_csv(output_lists.unique_notificators, csv_file_unique_users) == True:
        html_file = utils.CSV_to_HTML(csv_file_unique_users, apiless.CSV_type.unique_users, output_lists, use_local_thumbnails = config.USE_LOCAL_THUMBNAIL,  
                                ignore_columns = ['Avatar Href', 'Avatar Local', 'User Name', 'ID'])
        utils.show_html_result_file(html_file)     
    
    # Write the notification list to csv. Convert it to html, show it in browser        
    if len(output_lists.notifications) > 0 and  utils.write_notifications_to_csvfile(output_lists.notifications, csv_file) == True:
        html_file = utils.CSV_to_HTML(csv_file, apiless.CSV_type.notifications , output_lists, use_local_thumbnails = config.USE_LOCAL_THUMBNAIL, 
                                ignore_columns = ['Avatar Href', 'Avatar Local', 'User Name', 'ID', 'Photo Thumbnail Href', 'Photo Thumbnail Local', 'Photo Link'])
        utils.show_html_result_file(html_file) 

    printG(f"   {user_inputs.number_of_notifications} notifications, starting at indes {user_inputs.index_of_start_notification}. Duration: {datetime.datetime.now().replace(microsecond=0) - time_start}s")
    
#---------------------------------------------------------------
def handle_option_7(driver, user_inputs, output_lists):
    """Check if a user is following you."""

    time_start = datetime.datetime.now().replace(microsecond=0)
    printG(f"7. Check if user {user_inputs.target_user_name} follows {user_inputs.user_name}:")

    # do task
    result, message = does_this_user_follow_me(driver, user_inputs)

    if result == True:
        printG('   - ' + message)
    else:
        printR('   - ' + message) if 'User name not found' in message else printR('   - ' + message)
    
    printG(f'   Duration: {datetime.datetime.now().replace(microsecond=0) - time_start}s') 

#---------------------------------------------------------------
def handle_option_8(driver, user_inputs, output_lists):
    """ Like n photos from a given user."""

    time_start = datetime.datetime.now().replace(microsecond=0)
    printG(f"8. Starting auto-like {user_inputs.number_of_photos_to_be_liked} photo(s) of user {user_inputs.target_user_name}:")
    if not logged_in(driver):
        if login(driver, user_inputs) == False :
            return
   
    # do task   
    like_n_photos_from_user(driver, user_inputs.target_user_name, user_inputs.number_of_photos_to_be_liked, include_already_liked_photo_in_count=True, close_browser_on_error = False) 

    printG(f"   Duration: {datetime.datetime.now().replace(microsecond=0) - time_start}s")

#---------------------------------------------------------------
def handle_option_9(driver, user_inputs, output_lists):
    """Like n photos, starting at a given index, on various photo pages ."""

    time_start = datetime.datetime.now().replace(microsecond=0)
    printG(f"9. Like {user_inputs.number_of_photos_to_be_liked} photo(s) from {user_inputs.gallery_name} gallery, start at index {user_inputs.index_of_start_photo}:")
    
    if not logged_in(driver): 
        if login(driver, user_inputs) == False :
            return
    
    driver.get(user_inputs.gallery_href)
    time.sleep(2)

    # abort the action if the target objects failed to load within a given timeout    
    #if not webtools.Finish_Javascript_rendered_body_content(driver, time_out=15, class_name_to_check = 'entry-visible')[0]:
    #    return None, None	
    innerHtml = driver.execute_script("return document.body.innerHTML")  
    time.sleep(2)

    hide_banners(driver)

    # do task
    like_n_photos_on_current_page(driver, user_inputs.number_of_photos_to_be_liked, user_inputs.index_of_start_photo)

    printG(f"   Duration: {datetime.datetime.now().replace(microsecond=0) - time_start}s")

#---------------------------------------------------------------
def handle_option_10(driver, user_inputs, output_lists):
    """Like n photos of each user who likes a given photo or yours."""

    time_start = datetime.datetime.now().replace(microsecond=0)
    printG(f"10. Like {user_inputs.number_of_photos_to_be_liked} photos of each user who liked the photo:")
    print(f'    Getting the list of users who liked the photo ...')
    if not logged_in(driver):
        if login(driver, user_inputs) == False :
            return
    try:
        driver.get(user_inputs.photo_href)
    except:
        printR(f'    Invalid href: {user_inputs.photo_href}. Please retry.')
        show_menu(user_inputs)         
        return

    time.sleep(1)
    hide_banners(driver)        

    # do preliminary task: get the list of users who liked your given photo
    output_lists.like_actioners_list, dummy_file_name = get_like_actioners_list(driver, user_inputs, output_lists)
    if len(output_lists.like_actioners_list) == 0: 
        printG(f'   - The photo {photo_tilte} has no affection')
        show_menu(user_inputs)
        return 
    actioners_count = len(output_lists.like_actioners_list)
    include_already_liked_photo_in_count = True  # meaning: if you want to autolike 3 first photos, and you found out two of them are already liked, then you need to like just one photo.
                                                    # if this is set to False, then you will find 3 available photos and Like them 

    # do main task
    # we may have option to process only part of the users list. 
    # Since the list may be quite large and we don't want to stress the server by sending too many requests. 
    #start_index = max(0, user_inputs.index_of_start_user)
    #end_index   = min(start_index + user_inputs.number_of_users, len(output_lists.like_actioners_list) - 1)
    #for i, actor in enumerate(output_lists.like_actioners_list[start_index : end_index]):  

    for i, actor in enumerate(output_lists.like_actioners_list):  
        print_and_log(f'    User {str(i+1)}/{actioners_count}: {actor.display_name}, {actor.user_name}')
        like_n_photos_from_user(driver, actor.user_name, user_inputs.number_of_photos_to_be_liked, include_already_liked_photo_in_count, close_browser_on_error=False)

    printG(f"   Duration: {datetime.datetime.now().replace(microsecond=0) - time_start}s")

#---------------------------------------------------------------
def handle_option_11(driver, user_inputs, output_lists):
    """Like n friend's photos in homefeed page."""
    
    time_start = datetime.datetime.now().replace(microsecond=0)
    printG(f"11. Like {user_inputs.number_of_photos_to_be_liked} photos from the {user_inputs.user_name}'s home feed page:")
    if not logged_in(driver):
        if login(driver, user_inputs) == False :
            return
    else:
        # make sure the current page is user's homefeed page 
        driver.get('https://500px.com')
        time.sleep(1)        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # abort the action if the target objects failed to load within a given timeout    
    if not webtools.finish_Javascript_rendered_body_content(driver, time_out=60, tag_name_to_check='img')[0]:
      return

    # after a success login, the user's the homefeed page will automatically open     
    # we may consider this: abort the action if the photos fail to load within a given timeout    
    #if not webtools.Finish_Javascript_rendered_body_content(driver, time_out=30, class_name_to_check='finished')[0]:
    #  return None, None	    
  
    hide_banners(driver) 
 
    # do task
    like_n_photos_on_homefeed_page(driver, user_inputs)     

    printG(f"   Duration: {datetime.datetime.now().replace(microsecond=0) - time_start}s")

#---------------------------------------------------------------
def handle_option_12(driver, user_inputs, output_lists):
    """Like n photos of each user in the last m notifications.  """

    time_start = datetime.datetime.now().replace(microsecond=0)
    printG(f"12. Like n photos of each user in the last m notifications:")
    print(f'    - Getting the list of unique users in the last {user_inputs.number_of_notifications} notifications ...')
    if not logged_in(driver):
        if login(driver, user_inputs) == False :
            return
    driver.get('https://500px.com/notifications')
    time.sleep(1)        

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    
    # abort the action if the target objects failed to load within a given timeout    
    if not webtools.finish_Javascript_rendered_body_content(driver, time_out=30, class_name_to_check='finished')[0]:
      return None, None	

    hide_banners(driver)  
       
    # do preliminary task
    output_lists.unique_notificators = get_notification_list(driver, user_inputs, output_lists, True)[1]

    # do main task
    users_count = len(output_lists.unique_notificators)
    print(f"    Starting auto-like {user_inputs.number_of_photos_to_be_liked} photos of each of {users_count} users on the list ...")
    
    for i, notification_element in enumerate(output_lists.unique_notificators):
        notif_items = notification_element.split(',')
        # unique notificator element:
        # 0   1            2             3             4          5   6         
        # No, Avatar Href, Avatar Local, Display Name, User Name, ID, Count       
        if len(notif_items) > 4: 
            print(f'    User {notif_items[0]}/{users_count}: {notif_items[3]}, {notif_items[4]}')
            like_n_photos_from_user(driver, notif_items[4], user_inputs.number_of_photos_to_be_liked, include_already_liked_photo_in_count=True, close_browser_on_error=False)

    printG(f"   Duration: {datetime.datetime.now().replace(microsecond=0) - time_start}s")

#---------------------------------------------------------------
def handle_option_13(driver, user_inputs, output_lists):
    """ Play slideshow on a given gallery. """

    time_start = datetime.datetime.now().replace(microsecond=0)
 
    printG("13. Playing the slideshow ...")
    print_and_log(f'    - Gallery: {user_inputs.gallery_name}, time interval: {user_inputs.time_interval}')
    # open a new Chrome Driver with specific options for playing the slideshow (we are not using the passed driver, which  may be in headless mode)
    chrome_options = Options()  
    chrome_options.add_argument('--kiosk')   
    chrome_options.add_argument('--hide-scrollbars')   
    chrome_options.add_argument('--disable-extensions')   
    # suppress popup 'Save Password'
    chrome_options.add_experimental_option("excludeSwitches", ['enable-automation', 'load-extension']);
    # suppress popup 'Disable Developer Mode Extension'
    chrome_options.add_experimental_option('prefs', {'credentials_enable_service': False, 'profile': {'password_manager_enabled': False}})
    
    driver_with_GUI = webdriver.Chrome(options=chrome_options)
    # login if credentials are provided
    if user_inputs.user_name != '' and user_inputs.password != '':
        if login(driver_with_GUI, user_inputs) == False :
            printR('   Error logging in. Slideshow will be played without a user login.')  
        
    driver_with_GUI.get(user_inputs.gallery_href)
    hide_banners(driver_with_GUI)

    # do task
    play_slideshow(driver_with_GUI, int(user_inputs.time_interval))
    
    printG(f"   Duration: {datetime.datetime.now().replace(microsecond=0) - time_start}s")
    webtools.close_chrome_browser(driver_with_GUI)

#---------------------------------------------------------------
# EXTRA OPTIONS, not yet available from the menu. Starting backward from 99
def handle_option_99(driver, user_inputs, output_lists):
    """Check/Update following statused of people you are following.
    
    This function checks all users that you are following, to see whether they are following you or not.
    If you already have a following list on  disk, this will offer you to update the file, instead of doing everything from scratch.
    Note: this is a time-cosumming process. Use it responsibly and respectfully 
    """

    time_start = datetime.datetime.now().replace(microsecond=0)
    date_string = time_start.replace(microsecond=0).strftime(config.DATE_FORMAT)
    if user_inputs.number_of_users == -1:
        message = f'99. Get the following statuses of all users that {user_inputs.user_name} is following:'
    else:
        message = f'99. Get the following statuses of {user_inputs.number_of_users} users, starting from index {user_inputs.index_of_start_user + 1}:'
    printG(message)
    
    csv_file = ''
    # Provide option whether to use the last Followings list on disk or to start from scratch
    following_file = utils.get_latest_cvs_file(output_lists.output_dir, user_inputs.user_name, apiless.CSV_type.followings)
    if following_file != '':
        print('    Existing Followings list on disk:')
        printY(f"{following_file}", write_log=False)
        sel = input("Using this file? (y/n) > ")
        # use the existing followings list
        if sel =='y':
            csv_file = following_file
        # redo the followings list:        
        else:
            printG(f"99. Getting {user_inputs.user_name}'s Followings list ...")
            output_lists.followings_list = get_followings_list(driver, user_inputs, output_lists)
            # write result to csv
            if len(output_lists.followings_list) == 0:
                printR(f'    User {user_inputs.user_name} does not follow anyone or error on getting the followings list')
                return ''
            csv_file = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_{len(output_lists.followings_list)}_followings_{date_string}.csv')
            if utils.write_users_list_to_csv(output_lists.followings_list, csv_file) == False:
                printR(f'    Error writing the output file\n:{csv_file}')
                return ''
    # do task
    get_following_statuses(driver, user_inputs, output_lists, csv_file )
    html_file = utils.CSV_to_HTML(csv_file, apiless.CSV_type.followings , output_lists, use_local_thumbnails = config.USE_LOCAL_THUMBNAIL, 
                            ignore_columns = ['Avatar Href', 'Avatar Local','User Name', 'ID'])
    utils.show_html_result_file(html_file) 
    printG(f"   Duration: {datetime.datetime.now().replace(microsecond=0) - time_start}s")

#---------------------------------------------------------------
def handle_option_98(driver, user_inputs, output_lists, sort_column_header='No', ascending=True):
    """Like n photos of m users from a given csv files. 

    - The given csv file is supposed to have a header row, with at least one column named 'User Name'.
      All the csv files produced by this program, except the photo list file, satisfy this requirement and can be used.
    - There is an option to process part of the list, by specifying the start index and the number of users   
    - There is also option to sort a selectable column in the csv file before processing 
    """
    time_start = datetime.datetime.now().replace(microsecond=0)
    date_string = time_start.replace(microsecond=0).strftime(config.DATE_FORMAT)
    printG("98. Like n photos of m users from a given csv files:")

    # do main task
    dframe = pd.read_csv(user_inputs.csv_file, encoding='utf-16')  
    # validate the given  csv file
    if len(list(dframe)) == 0 or not 'User Name' in list(dframe):
        printR(f'   The given csv file is not valid. It should  have a header row with  at leat one column named "User Name":.\n\t{user_inputs.csv_file}')
        return

    printG(f"98. Like {user_inputs.number_of_photos_to_be_liked} photos from {user_inputs.number_of_users} users, starting from index {user_inputs.index_of_start_user} from the file:")
    printG('   - ' + {user_inputs.csv_file}, write_log=False)    
    print(f'    There are {dframe.shape[1]} columns:')
    printG(list(dframe), write_log=False)
    sort_header = input('Enter the desired sort column >')
    if not sort_header:
        sort_header = "No" 
    sort_ascending = True
    ans = input('Sort descending ?(y/n) >')
    if ans == 'y':
        sort_ascending = False
    df = dframe.sort_values(sort_header, ascending = sort_ascending )   
    
    if not logged_in(driver):
        if login(driver, user_inputs) == False :
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
    
        # process each user in dataframe
        try:
            print(f'    User #{count}: {row["Display Name"]}  at row {row["No"]}   ({row[sort_header]} likes):')
        except:
            print(f'    User #{count}: {row["User Name"]}:')

        like_n_photos_from_user(driver, user_inputs.target_user_name, user_inputs.number_of_photos_to_be_liked, include_already_liked_photo_in_count=True, close_browser_on_error = False)

    printG(f"   Duration: {datetime.datetime.now().replace(microsecond=0) - time_start}s")

#---------------------------------------------------------------
def handle_option_15(driver, user_inputs, output_lists):
    """Create local database based on the latest csv files on disk
       - create a database for current user if it does not exist.
       - search the output directory for the latest relevant csv files: photos, followers, followings, notifications list
       - create the relevant tables and insert the contents, ignoring duplicated records
    """
    
    printG(f"15. Create local database based on the latest csv files on disk")
    conn = sqlite3.connect(user_inputs.db_path)  #(':memory:') #
    cc = conn.cursor()
    db.create_if_not_exists_photos_table(cc)
    db.create_if_not_exists_followers_and_followings_tables(cc)
    db.create_if_not_exists_notifications_tables(cc)

    rows_changed_count = 0
    # insert photos
    # find the latest photo csv file on disk
    csv_file = utils.get_latest_cvs_file(output_lists.output_dir, user_inputs.user_name, apiless.CSV_type.photos)
    if csv_file != '':
        df = utils.CSV_file_to_dataframe(csv_file)
        photos_list = df.values.tolist()
        for item in photos_list:
            db.insert_photo_to_photo_table(conn, tuple(item))
        conn.commit()
        rows_changed_count = conn.total_changes
        printG(f'   Record(s) changed: {rows_changed_count}')

    # insert followers
    # find the latest followers csv file on disk
    csv_file = utils.get_latest_cvs_file(output_lists.output_dir, user_inputs.user_name, apiless.CSV_type.followers)
    if csv_file != '':
        df = utils.CSV_file_to_dataframe(csv_file)
        followers_list = df.values.tolist()
        for item in followers_list:
            db.insert_user_to_table(conn, tuple(item), table_name='followers')
        conn.commit()
        printG(f'   Record(s) changed: {conn.total_changes - rows_changed_count}')
        rows_changed_count = conn.total_changes

    # insert followings
    # find the latest followings csv file on disk
    csv_file = utils.get_latest_cvs_file(output_lists.output_dir, user_inputs.user_name, apiless.CSV_type.followings)
    if csv_file != '':
        df = utils.CSV_file_to_dataframe(csv_file)
        followings_list = df.values.tolist()
        for item in followings_list:
            db.insert_user_to_table(conn, tuple(item), table_name='followings')
        conn.commit()
        printG(f'   Record(s) changed: {conn.total_changes - rows_changed_count}')
        rows_changed_count = conn.total_changes
   
    # insert notifications
    # find the latest notifications csv file on disk
    csv_file = utils.get_latest_cvs_file(output_lists.output_dir, user_inputs.user_name, apiless.CSV_type.notifications)
    if csv_file != '':
        df = utils.CSV_file_to_dataframe(csv_file)
        notifications_list = df.values.tolist()
        for item in notifications_list:
            db.insert_notification_to_table(conn, tuple(item))
        conn.commit()
        printG(f'   Record(s) changed: {conn.total_changes - rows_changed_count}')

    conn.close()

#--------------------------------------------------------------
def handle_option_14(driver, user_inputs, output_lists):
    """ Data analysis: caterorize users based on following statuses"""

    time_start = datetime.datetime.now().replace(microsecond=0)
    date_string = time_start.strftime(config.DATE_FORMAT)
    printG("14. We need to get the followers and followings lists ...")

    # Provide option whether to use the last followers csv file on disk or to start from scratch
    followers_file = utils.get_latest_cvs_file(output_lists.output_dir, user_inputs.user_name, apiless.CSV_type.followers)
    if followers_file != '':
        use_followers_file_on_disk = input("Using this file? (y/n) > ")

    # Provide option whether to use the last following csv file on disk or to start from scratch
    followings_file = utils.get_latest_cvs_file(output_lists.output_dir, user_inputs.user_name, apiless.CSV_type.followings)
    if followings_file != '':
        use_followings_file_on_disk = input("Using this file? (y/n) > ")
    
    # Extract followers list from 500px server in case the user does not want to use the existing files
    if use_followers_file_on_disk == 'n':
        print(f"    Getting {user_inputs.user_name}'s Followers list ...")
        output_lists.followers_list = get_followers_list(driver, user_inputs, output_lists)
        # write result to csv
        if len(output_lists.followers_list) == 0:
            printR(f'    User {user_inputs.user_name} does not follow anyone or error on getting the followings list')
            return ''
        followers_file = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_{len(output_lists.followers_list)}_followers_{date_string}.csv')
        if utils.write_users_list_to_csv(output_lists.followers_list, followers_file) == False:
            printR(f'    Error writing the output file\n:{followers_file}')
            return ''
        utils.CSV_to_HTML(followers_file, apiless.CSV_type.followers, output_lists, use_local_thumbnails = config.USE_LOCAL_THUMBNAIL, 
                                    ignore_columns=['Avatar Href', 'Avatar Local', 'User Name', 'ID', 'Status'])

    # close the popup windows, if they are opened from previous task
    webtools.close_popup_windows(driver, close_ele_class_names = ['close', 'ant-modal-close-x'])

    # Extract followings list from 500px server in case the user does not want to use the existing files
    if use_followings_file_on_disk == 'n':
        print(f"    Getting {user_inputs.user_name}'s Followings list ...")
        output_lists.followings_list = get_followings_list(driver, user_inputs, output_lists)
        # write result to csv
        if len(output_lists.followings_list) == 0:
            printR(f'    User {user_inputs.user_name} does not follow anyone or error on getting the followings list')
            return ''
        followings_file = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_{len(output_lists.followings_list)}_followings_{date_string}.csv')
        if utils.write_users_list_to_csv(output_lists.followings_list, followings_file) == False:
            printR(f'    Error writing the output file\n:{followings_file}')
            return ''
        utils.CSV_to_HTML(followings_file, apiless.CSV_type.followings, output_lists, use_local_thumbnails = config.USE_LOCAL_THUMBNAIL, 
                    ignore_columns = ['Avatar Href', 'Avatar Local', 'User Name', 'ID', 'Status'])
    
    # create followers dataframe
    df_followers= utils.CSV_file_to_dataframe(followers_file)

    # create followings dataframe
    df_followings = utils.CSV_file_to_dataframe(followings_file)

    # merge followers and followings dataframes, preserving all data 
    df_all_ = pd.merge(df_followers, df_followings, how='outer', indicator = True,  suffixes=('_follower_order', '_following_order'), 
                      on=['Avatar Href', 'Avatar Local', 'Display Name', 'ID', 'Followers Count', 'Status', 'User Name'] )   

    # removed the combined values in the overlap columns after merging
    # I'm using pandas 1.0.1 and yet to figure out how to avoid this: different values of the same column name are combined with a dot in between, eg 23.5, 
    # even they are already separate by two extra columns. If someone khows how to do that please shout
    df_all_['No_follower_order']   = df_all_['No_follower_order'].apply(lambda x: '' if math.isnan(x) else str(x).split('.')[0])
    df_all_['No_following_order'] = df_all_['No_following_order'].apply(lambda x: '' if math.isnan(x) else str(x).split('.')[0])

    # renamed some columns
    df_all = df_all_.rename(columns={'No_follower_order': 'Follower Order', 'No_following_order': 'Following Order', '_merge': 'Relationship'})
    
    # users who follow you and you follow them 
    df_reciprocal = df_all[df_all['Relationship'] == 'both']

    # users who follow you but you do not follow them
    df_not_follow =  df_all[df_all['Relationship'] == 'left_only']

    # users who you follow but they do not follow you
    df_right_only =  df_all[df_all['Relationship'] == 'right_only']                                              # getting the names
    df_not_follower = pd.merge(df_followings, df_right_only[['User Name']], how='inner', on='User Name')         # from names, getting the detail info (a whole row on other table) 
    df_not_follower = df_not_follower.rename(columns={'No': 'Following Order', 'Followers': 'Followers Count'})  # renaming some columns
    df_not_follower['Follower Order'] = ''                                                                       # add missing column with empty values
    df_not_follower['Relationship'] = 'right_only'                                                               # finally assigning the merged indicator info 

    # write dataframe to csv, html. Show html
    df_to_process = [df_reciprocal, df_not_follow, df_not_follower, df_all]
    csv_type_to_process= [apiless.CSV_type.reciprocal, apiless.CSV_type.not_following, apiless.CSV_type.not_follower, apiless.CSV_type.all]
    print_and_log(f'   - Analyzing users relationships')
    for df, csv_type in zip(df_to_process, csv_type_to_process):
        # add an index column, started at 1
        pd.options.mode.chained_assignment = None # this bypass the pandas' SettingWithCopyWarning, which we don't care because we are going to throw way 
                                                  # the copied and modified dataframe df after each loop iteration
        df['No'] = range(1, len(df) + 1)

        # Reorder columns to make it easier to generate html file . Original order:
        # Follower Order, Avatar Href, Avatar Local, Display Name, User Name, ID, Followers Count, Status, Following Order, Relationship, No
        new_columns_order = ['No', 'Avatar Href', 'Avatar Local', 'Display Name', 'User Name', 'ID', 'Followers Count', 'Status', 'Follower Order', 'Following Order', 'Relationship', ]
        df = df[new_columns_order]

        ignore_columns = ['Avatar Href', 'Avatar Local', 'User Name', 'ID', 'Status']
        if csv_type == apiless.CSV_type.not_following:
            ignore_columns.extend(['Following Order'])
        elif csv_type == apiless.CSV_type.not_follower:
            ignore_columns.extend(['Follower Order'])

        csv_file_name = os.path.join(output_lists.output_dir, f'{user_inputs.user_name}_{len(df)}_{csv_type.name}_{date_string}.csv')  
        printG(f'   - {csv_type.name.upper()}: ./Output/{os.path.basename(csv_file_name)}')
        df.to_csv(csv_file_name, encoding='utf-16', index = False)
        html_file = utils.CSV_to_HTML(csv_file_name, csv_type, output_lists, use_local_thumbnails = config.USE_LOCAL_THUMBNAIL,  ignore_columns = ignore_columns)
        utils.show_html_result_file(html_file) 

    printG(f'   Duration {datetime.datetime.now().replace(microsecond=0) - time_start}s') 

def main():
    os.system('color')
    driver = None
    logger.info('Started: =====================================')
    print_and_log(f'Script path: {os.path.dirname(sys.argv[0])}')
    print_and_log(f'Output path: {config.OUTPUT_PATH}')
    print_and_log(f'Log file:    {config.LOG_FILE}')

    # chrome driver takes a few seconds to load, so we let a thread to handle it while we go on with the menu and user inputs. 
    my_queue = queue.Queue()
    th = Thread(target = webtools.start_chrome_browser, args=([], config.HEADLESS_MODE, my_queue) )
    th.start()

    # check internet and 500px server connections, if needed  
    #if not webtools.has_server_connection(driver, r'https://500px.com'):
    #    return   

    #declare a dictionary so that functions can be referred to from a string of digit(s)
    Functions_dictionary = {   
            "1" : handle_option_1, 
            "2" : handle_option_2, 
            "3" : handle_option_3,
            "4" : handle_option_4, 
            "5" : handle_option_5, 
            "6" : handle_option_6, 
            "7" : handle_option_7, 
            "8" : handle_option_8, 
            "9" : handle_option_9, 
            "10": handle_option_10, 
            "11": handle_option_11,
            "12": handle_option_12, 
            "13": handle_option_13,  
            "14": handle_option_14,
            "15": handle_option_15,
            # options not yet available from the menu
            "99": handle_option_99,
            "98": handle_option_98,
            }

    output_lists = apiless.OutputData()
    
    user_inputs = define_and_read_command_line_arguments()
    if  user_inputs.use_command_line_args == False:
        show_menu(user_inputs)  
   
    while user_inputs.choice != 'q':
        #restart for different user
        if user_inputs.choice == 'r': 
            user_inputs.Reset()
            output_lists.Reset()
            webtools.close_chrome_browser(driver)
            driver = None
            
            my_queue = queue.Queue()
            th = Thread(target = webtools.start_chrome_browser, args=([], config.HEADLESS_MODE, my_queue) )
            th.start()
            
            user_inputs = define_and_read_command_line_arguments()
            show_menu(user_inputs, 'Restarted for a different user.')
            continue
        else:
        # add user to enter additional inputs according to the selected options
            if not user_inputs.use_command_line_args and int(user_inputs.choice) >= 5:
                if get_additional_user_inputs(user_inputs) == False:
                    continue
            # make sure the driver is ready 
            while driver == None:
                driver = my_queue.get()

            # dynamically call the function to perform the task 
            Functions_dictionary[user_inputs.choice](driver, user_inputs, output_lists)

            # close the popup windows, if they are opened from previous task
            webtools.close_popup_windows(driver, close_ele_class_names = ['close', 'ant-modal-close-x'])

        # after finishing a task, if we are in the command-line mode, we are done, since the specific task has finished 
        if  user_inputs.use_command_line_args:
            sys.exit()
             
        # if not, show the menu for another task selection  
        else:
            input("Press ENTER to continue")
            show_menu(user_inputs)
            continue

    webtools.close_chrome_browser(driver)

#---------------------------------------------------------------
if __name__== "__main__":
    main()

