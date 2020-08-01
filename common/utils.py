# python 3.6
# utils.py: helper functions used in 500px_APIless.py
import common.config as config 
import common.apiless as apiless

from common.config import LOG as logger

import pandas as pd
import os, sys, time, datetime, re, math, csv
import msvcrt, glob, random, requests #, sqlite3

from time import sleep
from os import listdir
from os.path import isfile, join
from time import sleep
from dateutil.relativedelta import relativedelta

#---------------------------------------------------------------
# print colors text on console with option to log the same text to file on disk
def printG(text, write_log=True):  print(f"\033[92m {text}\033[00m"); logger.info(text) if write_log else None 
def printY(text, write_log=True):  print(f"\033[93m {text}\033[00m"); logger.info(text) if write_log else None
def printR(text, write_log=True):  print(f"\033[91m {text}\033[00m"); logger.error(text)if write_log else None
def printC(text, write_log=False): print(f"\033[96m {text}\033[00m"); logger.info(text)if write_log else None 
def printB(text, write_log=False): print(f"\033[94m {text}\033[00m"); logger.info(text)if write_log else None 
def print_and_log(text): print(text); logger.info(text)

#---------------------------------------------------------------
def write_string_to_text_file(input_string, file_name, encode = ''):
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
def show_html_file(file_name):
    """Open the given html file using the default system app. """

    if not os.path.isfile(file_name):
         return

    file_path, file_extension = os.path.splitext(file_name)
    if file_extension == ".html":
        os.startfile(file_name)

#--------------------------------------------------------------- 
def find_encoding(file_name):
    """Return the encoding of a given text file """
    import chardet
    r_file = open(file_name, 'rb').read()
    result = chardet.detect(r_file)
    charenc = result['encoding']
    return charenc 

#--------------------------------------------------------------- 
def win_getpass(prompt='Password: ', stream=None):
    """Mask the passwork characters with * character, supporting the backspace key """

    # The getpass.win_getpass() does not work properly on Windows. We implement this for the desired effect.
    # Credit: atbagga from https://github.com/microsoft/knack
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
def validate_non_empty_input(prompt_message, user_inputs):
    """Prompt user for an input, make sure the input is not empty. Return True if Quit or Restart is requested. False otherwise """

    if 'password' in prompt_message:
        val = win_getpass(prompt=prompt_message)
    else:
        val = input(prompt_message)
    if val == 'q' or val == 'r':
        user_inputs.choice = val
        return val, True
    while len(val) == 0:        
        printR("   Input cannot be empty! Please re-enter. Type 'q' to end or 'r' to restart", write_log=False)
        val = input(prompt_message)

    return val, False

#--------------------------------------------------------------- 
def validate_input(prompt_message, user_inputs):
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
            printR("Invalid input! Please retry.", write_log=False)
            val = input(prompt_message)

#---------------------------------------------------------------  
def CSV_file_to_dataframe(csv_file_name, encoding='utf-16', sort_column_header='No', ascending=True):
    """ Wrapper function for pandas' read_csv(),  with some frequently-used default arguments ."""

    if not os.path.isfile(csv_file_name):
        return None
    dframe = pd.read_csv(csv_file_name, encoding = encoding)  
    ##option to sort a selected column
    #sort_header = input('Enter the desired sort column >')
    #if not sort_header:
    #    sort_header = "No" 
    #sort_ascending = True
    #ans = input('Sort descending ?(y/n) >')
    #if ans == 'y':
    #    sort_ascending = False
    if sort_column_header and sort_column_header in list(dframe):
        df = dframe.sort_values(sort_column_header, ascending=ascending )  
    return df

#---------------------------------------------------------------  
def write_photos_list_to_csv(user_name, list_of_photos, csv_file_name):
    """ Write photos list to a csv file with the given name. Return True if success.    
        If the file is currently open, give the user a chance to close it and re-try.   
    """
    try:
        with open(csv_file_name, 'w', encoding = 'utf-16', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer = csv.DictWriter(csv_file, fieldnames = ['No', 'Author Name', 'ID', 'Photo Title', 'Href', 'Thumbnail Href', 'Thumbnail Local', 'Views', 'Likes', 'Comments', 'Galleries', \
                                                            'Highest Pulse', 'Rating', 'Date', 'Category', 'Featured In Galleries','Tags'])  
            writer.writeheader()
            for i, a_photo in enumerate(list_of_photos):
                writer.writerow({'No' : str(a_photo.order), 'Author Name': a_photo.author_name, 'ID': str(a_photo.id), 'Photo Title' : str(a_photo.title), 'Href' :a_photo.href, \
                                'Thumbnail Href': a_photo.thumbnail_href, 'Thumbnail Local' : a_photo.thumbnail_local, 'Views': str(a_photo.stats.views_count), \
                                'Likes': str(a_photo.stats.votes_count), 'Comments': str(a_photo.stats.comments_count), 'Galleries': str(a_photo.stats.collections_count), \
                                'Highest Pulse': str(a_photo.stats.highest_pulse), 'Rating': str(a_photo.stats.rating), 'Date': str(a_photo.stats.upload_date), \
                                'Category': a_photo.stats.category, 'Featured In Galleries': str(a_photo.galleries), 'Tags': a_photo.stats.tags}) 
            print(f"    - File saved at:")
            printG(f"   - ./Output/{os.path.basename(csv_file_name)}")
        return True

    except PermissionError:
        printR(f'   Error writing file {os.path.abspath(csv_file_name)}.\nMake sure the file is not in use. Then type r for retry >')
        retry = input()
        if retry == 'r': 
            write_photos_list_to_csv(user_name, list_of_photos, csv_file_name)
        else:
            printR('   Error witing file' + os.path.abspath(csv_file_name))
            return False

#---------------------------------------------------------------
def write_users_list_to_csv(users_list, csv_file_name):
    """ Write the users list to a csv file with the given name. Return True if success
    
    The users list could be one of the following: followers list, following (friends) list or unique users list. 
    If the file is currently open, give the user a chance to close the file and retry
    """
    try:
        with open(csv_file_name, 'w', encoding = 'utf-16', newline='') as csv_file: 
            writer = csv.writer(csv_file)
            writer = csv.DictWriter(csv_file, fieldnames = ['No', 'Avatar Href', 'Avatar Local', 'Display Name', 'User Name', 'ID', 'Followers Count', 'Relationship'])  
            writer.writeheader()
            for a_user in users_list:
                writer.writerow({'No' : a_user.order, 'Avatar Href': a_user.avatar_href,'Avatar Local': a_user.avatar_local, 'Display Name' : a_user.display_name, \
                    'User Name': a_user.user_name, 'ID': a_user.id, 'Followers Count': a_user.number_of_followers, 'Relationship': a_user.following_status}) 
        print('    The users list is saved at:')
        printG(f'   ./Output/{os.path.basename(csv_file_name)}')
        return True
    except PermissionError:
        retry = input(f'   Error writing to file {csv_file_name}. Make sure the file is not in use. Then type r for retry >')
        if retry == 'r': 
            write_users_list_to_csv(users_list, csv_file_name)
        else:
            printR('   Error writing file\n' + os.path.abspath(csv_file_name))
            return False 

#---------------------------------------------------------------
def write_notifications_to_csvfile(notifications_list, csv_file_name):
    """ Write the  notifications list to a csv file with the given  name. Return True if success.
        If the file is currently open, give the user a chance to close it and retry

    Headers: 1   2            3             4             5          6   7        8                     9                      10           11          12            13
             No, Avatar Href, Avatar Local, Display Name, User Name, ID, Content, Photo Thumbnail Href, Photo Thumbnail Local, Photo Title, Time Stamp, Relationship, Photo Link
    """

    try:
        with open(csv_file_name, 'w', encoding = 'utf-16', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer = csv.DictWriter(csv_file, fieldnames = ['No', 'Avatar Href', 'Avatar Local', 'Display Name', 'User Name', 'ID', 'Content', \
                'Photo Thumbnail Href', 'Photo Thumbnail Local', 'Photo Title', 'Time Stamp', 'Relationship', 'Photo Link'])    
            writer.writeheader()
            for notif in notifications_list:
                writer.writerow({'No': notif.order, 'Avatar Href' : notif.actor.avatar_href, 'Avatar Local': notif.actor.avatar_local, \
                                 'Display Name': notif.actor.display_name, 'User Name': notif.actor.user_name, 'ID' : notif.actor.id, \
                                 'Content': notif.content, 'Photo Thumbnail Href': notif.the_photo.thumbnail_href, 'Photo Thumbnail Local': notif.the_photo.thumbnail_local, \
                                 'Photo Title': notif.the_photo.title, 'Time Stamp': notif.timestamp, 'Relationship': notif.status, 'Photo Link': notif.the_photo.href}) 
        print('    Notifications list is saved at:')
        printG(f'   {os.path.basename(csv_file_name)}')
        return True 
    except PermissionError:
        retry = input(f'Error writing to file {csv_file_name}.\n Make sure the file is not in use, then type r for retry >')
        if retry == 'r':  
            write_notifications_to_csvfile(notifications_list, csv_file_name)
        else: 
            printR(f'   Error writing file {csv_file_name}')
            return False

#---------------------------------------------------------------
def write_unique_notificators_list_to_csv(unique_users_list, csv_file_name):
    """ Write the unique notifications list to a csv file with the given  name. Return True if success.   
    If the file is currently open, give the user a chance to close it and retry
    
    Headers:    0   1            2             3             4          5   6,             7
                No, Avatar Href, Avatar Local, Display Name, User Name, ID, Actions Count, Last Action Date
    """
    try:
        with open(csv_file_name, 'w', encoding = 'utf-16', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer = csv.DictWriter(csv_file, fieldnames = ['No', 'Avatar Href', 'Avatar Local', 'Display Name', 'User Name', 'ID', \
                                                            'Actions Count', 'Last Action Date'])  
            writer.writeheader()

            for actor in unique_users_list:
                items = actor.split(',')
                if len(items) == 8:
                    writer.writerow({'No': items[0], 'Avatar Href': items[1], 'Avatar Local': items[2], 'Display Name': items[3], \
                                    'User Name': items[4], 'ID' : items[5], 'Actions Count': items[6], 'Last Action Date': items[7]}) 
            print('    Unique notificators is saved at:')
            printG(f'   {os.path.basename(csv_file_name)}')
            return True 

    except PermissionError:
        retry = input(f'Error writing to file {csv_file_name}. Make sure the file is not in use. Then type r for retry >')
        if retry == 'r': 
            write_unique_notificators_list_to_csv(unique_users_list, csv_file_name)
        else: 
            printR(f'   Error writing file {csv_file_name}')
            return False

#---------------------------------------------------------------   
def save_avatar(url, full_file_name):
    """ Save the image from the given url to disk, at the given full file name."""
     
    try:
        r = requests.get(url, allow_redirects=True )
        #time.sleep(random.randint(1, 5) / 10)         
    except requests.exceptions.RequestException as e:
        printR(f'   Error saving user avatar {full_file_name}')
    with open(full_file_name, 'wb+') as f:
        f.write(r.content)

#---------------------------------------------------------------
def save_photo_thumbnail(url, path):
    """ Save the photo thumbnail to the given path on disk. 500px thumbnail files has this format "stock-photo-[photo ID].jpg". 
        We will extracted the filename from the header, and use just the photo id for filename. 
        Existing file will be overwritten
        Return the file name
     
    This function is meant to be called repeatedly in a loop, so for better performance, we don't chech the existance of the given path
    We have to make sure the given path is valid prio to calling this. 
    """ 
    file_name = '' 
    try:
        r = requests.get(url, allow_redirects=True)
        time.sleep(random.randint(1, 5) / 10)         
        file_name =  r.headers.get('content-disposition').replace('filename=stock-photo-','')
    except:
        printR(f'   Error getting photo thumbnail url: {url}')
        return ''
    full_file_name = os.path.join(path + "\\", file_name)
    #if not os.path.isfile(full_file_name):
    with open(full_file_name, 'wb+') as f:
        f.write(r.content)
    return file_name

#---------------------------------------------------------------
def get_latest_file(file_path, user_name, csv_file_type, file_extenstion = 'csv', print_info = True):
    """ Find the latest file of the given csv_file_type, from the given user, at the given folder location"""

    files = [f for f in glob.glob(file_path + f"**/{user_name}*_{csv_file_type.name}_*.{file_extenstion}")]
    if len(files) > 0:
        if csv_file_type == apiless.CSV_type.notifications:
            files = [f for f in files if not 'unique' in f and not 'all' in f]

        files.sort(key=lambda x: os.path.getmtime(x))
        csv_file = files[-1]
        if print_info:
            #dated = os.path.splitext(csv_file)[0].split('_')[-1]
            print(f"    - Latest {csv_file_type.name.upper()} file: {os.path.basename(csv_file)}")
        return csv_file
    else:
        return ""

#---------------------------------------------------------------
def get_all_notifications_csv_files(file_path, user_name):
    """ Return all the notifications csv files previously extracted, at the given folder.
        Files are sorted on last mofification times"""

    files = [f for f in glob.glob(file_path + f"**/{user_name}*_notifications_*.csv")]
    if len(files) > 0:
        files = [f for f in files if (not 'unique' in f and not 'all' in f)]
        files.sort(key=lambda x: os.path.getmtime(x))
    return files


#---------------------------------------------------------------
def find_unique_names_and_count_duplication(names_and_contents):
    """Given a list of names and notification content (ex. [ ['johndoe','liked'], ['mariedo','commented'], ...]
        - Count the number of occurences of each unique name in the given list 
        - Get the index of the first occurence of unique name
        - Get the statistic on the notification of each unique user
        - Return a list of comma-separated strings containing
          name, first original index, number of action, liked count, followed count, commented count, and added to gallery count """

    output = []
    seen = set()
    count = 0 
    items_to_process = len(names_and_contents)
    for i, row in names_and_contents.iterrows():
        update_progress(i / items_to_process, f'    - Finding unique users {i}/{items_to_process} ...')  

        like_count, follow_count, comment_count, add_to_gallery_count = (0 for i in range(4) )
        name = row['User Name']
        content = row['Content']
        if 'liked' in content:
            like_count = 1
        elif 'followed' in content:
            follow_count = 1
        elif 'commented' in content:
            comment_count = 1
        elif 'added' in content:
            add_to_gallery_count = 1
        
        if name not in seen:           
            seen.add(name)
            output.append(f"{name},{str(i)},1,{str(like_count)},{str(follow_count)},{str(comment_count)},{str(add_to_gallery_count)}") # name, index in the full list, count
        else:
            # name is already seen: increase the count number by one
            for j, item in enumerate(output):
                if name in item:
                   list_items = item.split(',')
                   try:
                        if len(list_items) == 7:
                            new_count = int(list_items[2]) + 1

                        if 'liked' in content:
                            like_count = int(list_items[3]) + 1
                            output[j] = f'{name},{list_items[1]},{new_count},{str(like_count)},{list_items[4]},{list_items[5]},{list_items[6]}'
                        elif 'followed' in content:
                            follow_count = int(list_items[4]) + 1
                            output[j] = f'{name},{list_items[1]},{new_count},{list_items[3]},{str(follow_count)},{list_items[5]},{list_items[6]}'
                        elif 'commented' in content:
                            comment_count = int(list_items[5]) + 1
                            output[j] = f'{name},{list_items[1]},{new_count},{list_items[3]},{list_items[4]},{str(comment_count)},{list_items[6]}'
                        elif 'added' in content:
                            add_to_gallery_count = int(list_items[6]) + 1
                            output[j] = f'{name},{list_items[1]},{new_count},{list_items[3]},{list_items[4]},{list_items[5]},{str(add_to_gallery_count)}'
                   except:
                        continue
    update_progress(1, f'    - Finding unique users {items_to_process}/{items_to_process} ...')                      
    return output    

#---------------------------------------------------------------
def analyze_notifications(df):
    """Given a  dataframe containing notification items
        - Count the number of occurences of each unique name in the given list 
        - Return a new dataframe containing unique names, last action date, number of actions, liked count, followed count, commented count, and added to gallery count """

    all_users_count = df.shape[0]
    if all_users_count == 0:
        print_and_log(f'No notification item in the given dataframe ')
        return
    names_and_contents = df[['User Name', 'Content']]
    # get the first index of each  unique users, their occurences countsand the count of each notification type 
    indexes_and_counts_list = find_unique_names_and_count_duplication(names_and_contents) 
    unique_users_count = len(indexes_and_counts_list)
    if unique_users_count  == 0:
        print_and_log(f'No unique names item in notification table ')
        return
    unique_notificators = []
   
    # update the given dataframe at the indexes found on indexes_and_counts_list, and added new columns with all the counts 
    for i, item in enumerate(indexes_and_counts_list):    
        update_progress(i / unique_users_count, f'    - Processing notification item {i}/{unique_users_count} ...')  
        index_count_pair = item.split(',')
        index = int(index_count_pair[1])
        count = int(index_count_pair[2])
        like_count = int(index_count_pair[3])
        follow_count = int(index_count_pair[4])
        comment_count = int(index_count_pair[5])
        add_to_gallery_count = int(index_count_pair[6])
        df.loc[index,'No'] = str(i +1)
        df.loc[index,'Actions Count'] = count
        df.loc[index,'Liked'] = like_count
        df.loc[index,'Followed'] = follow_count
        df.loc[index,'Commented'] = comment_count
        df.loc[index,'Added To Gallery'] = add_to_gallery_count

    # drop the duplicated users
    df2 = df[df['Actions Count'].isnull()==False]

    # drop the unwanted columns
    df2.drop(['Content', 'Photo Thumbnail Href', 'Photo Thumbnail Local', 'Photo Title', 'Photo Link'], axis=1, inplace=True)

    # rename one colume name: Time Stamp --> Last Action Date
    df2.rename(columns={'Time Stamp':'Last Action Date'}, inplace=True)

    unique_users_count = df2.shape[0]

    # change the newly created columns data type from default float to int
    df3 = df2.astype({"Actions Count":int, "Liked":int, "Followed":int, "Commented":int, "Added To Gallery":int})
    
    # Change the columns order for better representing the output html 
    # No, Avatar Href, Avatar Local, Display Name, User Name,ID, Last Action, Relationship, Actions Count, Liked, Followed, Commented, Added To Gallery
    df4 = df3[['No', 'Avatar Href', 'Avatar Local', 'Display Name', 'User Name', 'ID', 'Relationship', 'Last Action Date', 'Actions Count', 'Liked', 'Followed', 'Commented', 'Added To Gallery']]
    update_progress(1, f'    - Processing notification item {unique_users_count}/{unique_users_count} ...')  
    return df4

#---------------------------------------------------------------
def convert_relative_datetime_string_to_absolute_date(relative_time_string, format = "%Y %m %d" ):
    """ Convert a string of relative time (e.g. "2 days ago") to a datetime object, strip the time part and return 
        the date string in the given format (e.g. YYYY-mm-dd )
        Possible inputs:
         in a few seconds
         in 1 minute, in 2 minutes, 3-59 minutes ago
         an hour ago, 2-23 hours ago
         a day ago,   yesterday,        2-31 days ago
         a month ago, 2-11 months ago
         a year ago,  last year,        xx years ago 
        """
    abs_date = None
    datetime_now = datetime.datetime.now()
    if not relative_time_string:
        return ''
    
    if 'an hour ago' in relative_time_string or 'minutes ago' in relative_time_string:
        abs_date = datetime_now + datetime.timedelta(hours = -1)
    elif 'minute' in relative_time_string or 'second' in relative_time_string :
        abs_date = datetime_now  #ignoring seconds amount and time less than 2 minutes           
    elif 'hours ago' in relative_time_string:
        delta = relative_time_string.replace('hours ago', '').strip()
        abs_date = datetime_now + datetime.timedelta(hours = -int(delta))
    elif 'a day ago' in relative_time_string or 'yesterday' in relative_time_string:
        abs_date = datetime_now + datetime.timedelta(days = -1)
    elif 'days ago' in relative_time_string:
        delta = relative_time_string.replace('days ago', '').strip()
        abs_date = datetime_now + datetime.timedelta(days = -int(delta))

    # We use dateutil.relativedelta to handle months and years because datetime.timedelta() support only hours, days, weeks
    elif 'a month ago' in relative_time_string:
        abs_date = datetime_now + relativedelta(months = -1)
    elif 'months ago' in relative_time_string:
        delta = relative_time_string.replace('months ago', '').strip()
        abs_date = datetime_now + relativedelta(months = -int(delta))

    elif 'a year ago' in relative_time_string or 'last year' in relative_time_string:
        abs_date = datetime_now + relativedelta(years = -1)
    # it seems 500px does not report the correct year if it is dated back more than 1 year. i.e. any date later than 12 months will be recorded as last year,
    # so, for now, this following case will unlikely happen:
    elif 'years ago' in relative_time_string:
        delta = relative_time_string.replace('years ago', '').strip()
        abs_date = datetime_now + relativedelta(years = -int(delta))       
    return  "" if abs_date is None else abs_date.strftime(format)

#---------------------------------------------------------------
def update_progress(progress, message = ''):
    """Updates a text-based progress bar on the console.

    Accepts a float between 0 and 1. any int will be converted to a float.
    A value under 0 represents a 'halt'.
    A value at 1 or bigger represents 100%
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
    text = f'\r{message:<52.51}[{"."*block + " "*(barLength-block)}] {int(round(progress*100)):<3}% {status}'
    sys.stdout.write(text)
    sys.stdout.flush()

#---------------------------------------------------------------
def profile(func):
    """A decoration that users cProfle to profile a function. Add the line '@profile' before a function to profile it"""
    import cProfile, pstats, io

    def inner(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        retval = func(*args, **kwargs)
        pr.disable()
        s = io.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())
        return retval
    return inner

#---------------------------------------------------------------
def merge_relationships(df_unique, df_all):
    """ Update the values on the Relationship column from the given dataframe df_unique, with the one from the given df_all 
        Both dataframe should contain, as a minimun, two columns: User Name and Relationship               
    """
    # rename Relationship values on df_unique to avoid confusion later when we merge with df_all 
    # on notification, 'Not Follow' means this is your new follower and you do not follow back
    # and 'Following' means this is your new follower and you also follow back
    #df_unique.loc[df_unique.Relationship == 'Not Follow', 'Relationship'] = 'New follower'
    df_unique.loc[df_unique.Relationship == 'Following', 'Relationship'] = 'Reciprocal'
    df_unique.loc[df_unique.Relationship.isnull(), 'Relationship'] = ''

    # merge Relationship from 2 dataframes, the left one, or Relationship_x, is the latest from notification page, the right one, or Relationship_y is the one from local database 
    # We will update the right side, Relationship_y, then delete the left side    
    df_merge = pd.merge(df_unique, df_all[['User Name', 'Relationship']], how='left', on='User Name')

    # We use the left side if it has value ( override the right side)
    df_merge.loc[df_merge.Relationship_x.notnull() , 'Relationship_y'] = df_merge.Relationship_x 
   
    # Delete column Relationship_x and rename Relationship_y to the orginin name before merging: Relationship 
    df_merge.drop("Relationship_x", axis=1, inplace=True)    
    df_merge.rename(columns={'Relationship_y': 'Relationship'}, inplace=True)
        
    # create an summary dictionary 
    followers_count   = df_merge.loc[df_merge.Relationship.str.contains('Not Follow', regex=False), :].shape[0]
    followings_count  = df_merge.loc[df_merge.Relationship.str.contains('Following',  regex=False), :].shape[0]
    reciprocals_count = df_merge.loc[df_merge.Relationship.str.contains('Reciprocal', regex=False), :].shape[0]
    no_relationship_counts = df_merge.shape[0] - (followers_count + followings_count + reciprocals_count )

    # create the statistics list in such a way that an html table (4 rows, 3 columns) can be easily constructed from it.
    # each row has 4 strings of the following usage:
    # First string is the class name to be used in CSS for column 1 background color, the next 3 strings are the texts for column 1, 2, 3  
    stats_list = [['reciprocal',      'Reciprocal Following',  reciprocals_count,      'You and this user follow each other'],
                  ['not_follow',      'Not Follow',            followers_count,        'You do not follow your follower'],
                  ['following',       'Following',             followings_count,       'You are following this user without being followed back'],
                  ['no_relationship', 'None',                  no_relationship_counts, 'Not following each other']]

    return df_merge, stats_list 

#---------------------------------------------------------------
def merge_duplicate_top_photos(df):
    """ Given a dataframe containing 5 photos of these 5 categories: Highest Pulse, Most Views, Likes, Comments and Galleries, in that order. 
        Some, if not all, are likely the same photo. The goal is to remove the duplicate photos, but the category of the removed photo is to be added to
        the existing category that the same photo already holds.  
        Return a non-duplicate photos dataframe, with the first column is a new column called 'Top Photos', holding the category or a combination of two or more categoies     
        """

    if df is None or df.shape[0] <=1:
        return df
    # add a new columns with 4 row of fixed text data representing top-photo categories
    df['Top Photos'] = ['Highest Pulse', 'Most Viewed', 'Most Liked', 'Most Commented', 'Most Featured']    # , 'Most Featured In Galleries']

    # add new index column with orderly numbers from 0 to 4
    df['OrderlyIndex'] = [0, 1, 2, 3, 4]
    
    # reorder columns
    new_columns_order = ['OrderlyIndex', 'Top Photos', 'No','Author Name','ID','Photo Title','Href','Thumbnail Href','Thumbnail Local','Views','Likes','Comments', 
                         'Galleries', 'Highest Pulse', 'Rating', 'Date', 'Category', 'Featured In Galleries', 'Tags']
    df_source = df[new_columns_order]
    df_source.set_index('OrderlyIndex', drop=False, inplace=True)
    
    #create an one-row dataframe to store the merges duplicates
    df_result = pd.DataFrame(index= [0], columns=list(df_source))

    #copy the first row from source to result
    df_result.loc[df_source.index[0]] = df_source.iloc[0]

    # mark the duplications, using the 'No' column, by a boolean serie. (True means duplicate row) 
    bool_series = df_source["No"].duplicated(keep = "first")

    for i, val in df_source.iloc[1:].iterrows():
        # copy over non-duplicate rows
        if not bool_series[i]:
            df_result.loc[df_source.index[i]] = df_source.iloc[i]
        # this is the duplicate row, we will not copy it to the result, but we will concatenate its top-photo category to the existing row 
        else:
            for j, item in df_result.iterrows():
                if val.No == item.No:                
                    current_data = df_result.loc[j, 'Top Photos']
                    df_result.loc[j, 'Top Photos'] = f'{current_data}<p></p>{ val["Top Photos"]}'  # Inserted <p></p> between categories to make sure each category shows in one line
                    break
    df_result.drop("OrderlyIndex", axis=1, inplace=True)     
    return df_result 

#---------------------------------------------------------------
def get_notifications_statistics(df):
    """Given a dataframe containing notifications, return a dictionary holding statistic data"""

    liked  = df.loc[df.Content =='liked', "Content"].shape[0]
    commented  = df.loc[df.Content =='commented', "Content"].shape[0]
    followed = df.loc[df.Content =='followed', "Content"].shape[0]
    gallery = df.loc[df.Content =='added to gallery', "Content"].shape[0]
    not_follow = df.loc[df.Relationship =='Not Follow', "Relationship"].shape[0]
    following = df.loc[df.Relationship =='Following', "Relationship"].shape[0]
    
    last_upload_date   = df['Time Stamp'].iloc[[0]].values[0]
    first_upload_date = df['Time Stamp'].iloc[[-1]].values[0]
    try:
        last_date_obj = datetime.datetime.strptime(last_upload_date, "%Y %m %d").date()
        first_date_obj = datetime.datetime.strptime(first_upload_date, "%Y %m %d").date()
        days = (last_date_obj -first_date_obj).days
        last_date  = last_date_obj.strftime("%b %d %Y")
        first_date = first_date_obj.strftime("%b %d %Y")
    except:
        printR(f'Error converting datetime string:{last_upload_date}, {first_upload_date}')
        last_date = last_upload_date
        first_date = first_upload_date
        days = ''

    stats_dict = {'Notifications':    df.shape[0], 
                  'From':             first_date, 
                  'To':               last_date, 
                  'Duration':         f'{days} days',
                  'Liked':            liked, 
                  'Commented':        commented,
                  'Added To Gallery': gallery,
                  'New Followers':    followed,
                  'Following':        following , 
                  'Not Follow':       not_follow } 
    return stats_dict

#---------------------------------------------------------------
def convert_string_num_to_int(string_num):
    """ convert a string of a floating number with a letter K representing 1000 (eg. 3.2K) to an integer (eg. 3200) """

    str_num = string_num.strip()
    if str_num.isnumeric():
        return int(str_num)
    if 'K' in str_num:
        int_num = 0
        str_num = str_num.replace('K', '')
        try:
            int_num = int(float(str_num) * 1000)
        except:
            printR(f'Error converting number {str_num}')
        return int_num
    
#---------------------------------------------------------------
def handle_local_avatar(avatar_href, save_to_disk, dir):
    """ Given a link to an avatar image file, save the image to disk if 'save_to_disk' is True.
        Expecting the link contains the user id, or the text 'userpic.png' if user uses the default avatar.
        The file name is either [user_id].jpg or 'userpic.png'
        Return the user id and saved file name."""

    if not avatar_href: return '', ''
    user_id, avatar_local = '', ''

    # if user has default avatar
    if 'userpic.png' in avatar_href:
        if save_to_disk:
            avatar_local = 'userpic.png'
    else:
        user_id  =  re.search('\/user_avatar\/(\d+)\/', avatar_href).group(1)
        avatar_local = user_id + '.jpg'
        # save avatar to disk if requested, and only if it does not exist
        # this means that if the users changed theirs avatars after we get it, we will not update it. 
        # To get the latest version of an avatar, we have to identify and delete the old file ([user_id].jpg) on disk before running the script
            
    avatar_full_file_name = os.path.join(dir, 'avatars', avatar_local)
    # save avatar to disk if requested, and only if it does not already exist
    if save_to_disk and not os.path.isfile(avatar_full_file_name):  
        save_avatar(avatar_href, avatar_full_file_name)
    return user_id, avatar_local

#---------------------------------------------------------------
def update_active_page_on_main_html_page_js(js_file_name, menu_item_name, new_html_page):
    """ - Open the given javascript file (menu.js), search for the given menu item, then update the associated file with the given html page  
        - Set the value of the global variable 'active_html_page' to the new html page
        
        This function is meant to be called whenever the user run a task that results in a new html file.
        The javascript file is used in the main 500px-APIless.html file, which provides instant access to all html results.

        Example:
          var active_html_file = ""                  <-- set value to the 'new_html_page'
          var active_menu_item = ""                  <-- set value to the 'menu_item_name'
          ...
          { "item" : "user_summary",                  <-- menu_item_name (used the csv_type.name)
           "file" : "johndoe_stats_2020-07-08.html"  <-- new_html_page
          },
     """
   
    # identify the variable 'active_html_file'
    var_patttern1 = r'(\s+var\s+active_html_file\s+=\s+")(.+)'

    # identify the variable 'active_menu_item'
    var_patttern2 = r'(\s+var\s+active_menu_item\s+=\s+")(.+)'

    # identify the given menu item (== csv_type.name)
    menu_pattern = rf'("{menu_item_name}",\s+"file"\s+:\s+")(.+)'

    # Read in the file
    with open(js_file_name, 'r') as file :
        filedata = file.read()
        new_filedata1 = re.sub(var_patttern1, rf'\1{new_html_page}"', filedata )
        new_filedata2 = re.sub(var_patttern2, rf'\1{menu_item_name}"', new_filedata1 )
        new_filedata3 = re.sub(menu_pattern, rf'\1{new_html_page}"', new_filedata2 )

    # Write the file out again
    with open(js_file_name, 'w') as file:
        file.write(new_filedata3)
    
#---------------------------------------------------------------
def create_menu_items(user_name, file_path, js_file_name = 'menu_items.js', active_html_file='', active_menu_item=''):
    """ Create a javascript file that handles the menu items with the latest html files on disk
        This function is called when a user_name is entered """
    csv_types_to_process = [apiless.CSV_type.user_summary, 
                            apiless.CSV_type.photos_public,
                            apiless.CSV_type.followers, 
                            apiless.CSV_type.followings,
                            apiless.CSV_type.reciprocal,
                            apiless.CSV_type.not_follow,
                            apiless.CSV_type.following,
                            apiless.CSV_type.all_users,
                            apiless.CSV_type.like_actors,
                            apiless.CSV_type.notifications, 
                            apiless.CSV_type.unique_users, 
                            apiless.CSV_type.all_notifications, 
                            apiless.CSV_type.all_unique_users]

 
    js_string = f"""jQuery(document).ready(function() {{
    var active_html_file = "{active_html_file}";
    var active_menu_item = "{active_menu_item}";
    var main_container_ele = document.getElementById("div_main_content")
    // associate menu items (csv_type.name) with html files by using an array of objects
    // this js file is generated when the user wants to update the main html file
    var menu_items =[\n"""

    for i, csv_type in enumerate(csv_types_to_process):                            
        csv_file = get_latest_file(file_path, user_name, csv_type, file_extenstion = 'html', print_info=False)
        js_string += (f'\t\t{{ "item" : "{csv_type.name}",\n' 
	                  f'\t\t  "file" : "{os.path.basename(csv_file)}"\n'  
	                   '\t\t}')
        if i < len(csv_types_to_process) -1: 
            js_string += ',\n'
    js_string += '\n\t]\n'

    # add functions
    js_string += """
	//for dynamic menu items
    menu_items.forEach(add_listeners);
	
	//--------------------------------------------------------------------------
	//for dynamic menu items: gray out text of un-available menu items, add click event listener
	function add_listeners(menu_item) {
		var ele = document.getElementById(menu_item.item)
		if (menu_item.file == ""){
			// add css class to change text color (gray out)
			ele.classList += " inactive_menu" ;
		}
		else{
			// remove class to restore the normal text color
			ele.classList.remove("inactive_menu");	
		    // add event listener 
		    ele.addEventListener("click", function(){
			    switch_page(menu_item.file, menu_item.item, main_container_ele)
		    });				
	    }				
    }
	//--------------------------------------------------------------------------   
	// assign class to elements (identified by tag names), depending on its indexes
	// this means to set background colors for different menu items depending on its group	
    function reset_default_menu_bg_colors(tag_name){
		var li_eles = document.getElementsByTagName(tag_name);
		var i;
		for (i = 0; i < li_eles.length; i++) {
			if (i >= 2 && i <= 7){
				li_eles[i].classList += ' users_group';				
			}
			else if ( i >= 9 && i <= 12 ){
				li_eles[i].classList += ' notifications_group';				
			}
			else{
				li_eles[i].classList += ' other_group';	
			}
		}	
	}	
	//--------------------------------------------------------------------------    
    // set main html object, handle menu items background colors and update global variables	
	function switch_page(active_html_file, active_menu_item, main_container_ele){
		// replace the main html object
        if (active_html_file != ""){ 
		    new_inner_HTML = `<object type="text/html" data="${active_html_file}" width="100%" height="100%" "></object>`
		    main_container_ele.innerHTML = new_inner_HTML;
        }		
		reset_default_menu_bg_colors('li');
		
		// set the background of the active item 
		var ele = document.getElementById(active_menu_item);		
		ele.className = '';		
		ele.classList += ' active_menu'
		
		// update the global variables
		window.active_html_file = active_html_file;
		window.active_menu_item = active_menu_item;
	};	
	//--------------------------------------------------------------------------
	// load the main object on page load or on refresh
    if (active_html_file != "" &&  active_menu_item != ""){
	    switch_page(active_html_file, active_menu_item, main_container_ele)	
    }	
}); 
"""
# Write 
    with open(js_file_name, 'w', encoding = 'utf-8') as file:
        file.write(js_string)