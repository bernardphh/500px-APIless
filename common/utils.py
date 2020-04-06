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
def show_html_result_file(file_name):
    """Offer the given html file with the default system app. """

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
def CSV_photos_list_to_HTML(csv_file_name, output_lists, use_local_thumbnails = True, ignore_columns = None):
    """Create a html file from a given photos list csv  file. Save it to disk and return the file name.

    Save the html file using the same name but with extension '.html'
    Expecting the first line to be the column headers, which are  no, page, id, title, link, src
    Hide the columns specified in the given IGNORE_COLUMNS LIST. The data in these columns are still being used to form the web link tag <a href=...>
    """
    if ignore_columns is None:
        ignore_columns = []

    CUSTOMED_COLUMN_WIDTHS = """
    <colgroup>
		<col style="width:4%">
		<col style="width:18%">
		<col span= "3" style="width:5%" >
		<col style="width:14%">	
		<col style="width:7%" >
		<col style="width:6%" >
		<col style="width:8%" >				
		<col style="width:28%" >				
	</colgroup>
    """
    HEADER_STRING ="""
<head>
	<script charset="UTF-8" type = "text/javascript" src="javascripts/scripts.js"></script>
	<link   charset="UTF-8" type = "text/css" rel  = "stylesheet"  href = "css/styles.css" />
</head>""" 

# file name and extension check
    file_path, file_extension = os.path.splitext(csv_file_name)
    if file_extension != ".csv":
        return None

    html_file = file_path + '.html'
    avatars_folder    = os.path.basename(os.path.normpath(output_lists.avatars_dir))
    thumbnails_folder = os.path.basename(os.path.normpath(output_lists.thumbnails_dir))

    # Create the document description based on the given file name.
    # Ref: Photo list filename:  [path]\_[user name]\_[count]\_[types of document]\_[date].html
    # Example of filename: C:\ProgramData\500px_Apiless\Output\johndoe_16_photos_2019-06-17.html
    file_name = file_path.split('\\')[-1]
    splits = file_name.split('_')
    title_string = ''
    if len(splits) >=4:
        title_string = f'\
    <h2>Photo lists ({splits[1]})</h2>\n\
    <div><span>User:</span> <span><b>{splits[0]}</b></span></div>\n\
    <div><span>Date recorded:</span> <span><b>{splits[-1]}</b></span></div>\n\
	<div>\
    <span> File: {os.path.dirname(html_file)}\</span><br/>\n\
	<span><b>{file_name}.html</b> </span>\n\
	</div>\n'

    with open(csv_file_name, newline='', encoding='utf-16') as csvfile:
        reader = csv.DictReader(row.replace('\0', '') for row in csvfile)
        headers = reader.fieldnames

        row_string = '\t<tr>\n'
        # Ref:
        # Columns    : 0   1            2   3            4     5               6                7      8      9         10                     11             12      13    14        15
        # Photo List : No, Author Name, ID, Photo Title, Href, Thumbnail Href, Thumbnail Local, Views, Likes, Comments, Featured In Galleries, Highest Pulse, Rating, Date, Category, Tags

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
                # the No column is initially in ascending order, so we do not show the down arrow
                ascending_arrow_only = f"""
                <div class="hdr_arrows">
				    <div id ="arrow-up-{i-ignore_columns_count}">&#x25B2;</div>
				    <div id ="arrow-down-{i-ignore_columns_count}" hidden>&#x25BC;</div></div>"""
                row_string += f'\t\t<th onclick="sortTable({i-ignore_columns_count})">\n{first_left_div}{ascending_arrow_only}</th>\n'
            
            # special sort for title cell: we want to sort the displayed photo titles, not the photo link
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
                    if use_local_thumbnails:
                        photo_thumbnail = f"{thumbnails_folder}/{row['Thumbnail Local']}"
                    else:
                        photo_thumbnail = row['Thumbnail Href']
                    
                    # if photo thumbnail is empty, write an empty div to keep the same layout 
                    if (use_local_thumbnails and not row['Thumbnail Local']) or (not use_local_thumbnails and not row['Thumbnail Href']) :
                        row_string += f'\t\t<td><div"><div>{text}</div></div></td> \n' 
                    else:
                        photo_link =  row['Href']                 
                        row_string += f'\t\t<td>\n\t\t\t<div>\n\t\t\t\t<a href="{photo_link}" target="_blank">\n'
                        row_string += f'\t\t\t\t<img class="photo" src={photo_thumbnail}></a>\n'
                        row_string += f'\t\t\t\t<div><a href="{photo_link}" target="_blank">{text}</a></div></div></td>\n'
 
                elif  col_header == 'Category':
                    row_string += f'\t\t<td class="alignLeft">{text}</td> \n' 

                elif  col_header == 'Tags':
                    row_string += f'\t\t<td class="alignLeft">{text}</td> \n' 
                
                elif  col_header == 'Featured In Galleries' and text != '':
                    # a gallery link has this format: https://500px.com/[photographer_name]/galleries/[gallery_name]
                    galleries = text.split(',')
                    if len(galleries) == 0:
                           row_string += f'\t\t<td></td>\n'
                    else:
                        row_string += f'\t\t<td>({len(galleries)}) \n'
                        for j, gallery in enumerate(galleries):
                            gallery_name = gallery[gallery.rfind('/') + 1:]    
                            row_string += f'\t\t\t<a href="{gallery}" target="_blank">{gallery_name}</a>'
                            if j < len(galleries) -1:
                                row_string += ',\n'                    
                        row_string += f'\t\t</td> \n'
                                
                else: 
                    row_string += f'\t\t<td>{text}</td> \n' 
            row_string += '\t</tr>\n'

        html_string = f'<html>\n{HEADER_STRING}\n\n<body> \n{title_string}<table> {CUSTOMED_COLUMN_WIDTHS}\n{row_string} </table>\n</body> </html>'

        #write html file 
        with open(html_file, 'wb') as htmlfile:
            htmlfile.write(html_string.encode('utf-16'))

    return html_file

#--------------------------------------------------------------- 
def CSV_to_HTML(csv_file_name, csv_file_type, output_lists, use_local_thumbnails = True, ignore_columns = None):
    """ Convert csv file of various types into html file and write it to disk . Return the saved html filename.
    
    Expected 5 csv files types: notifications list , unique users list, followers list, followings list, list of users who like a photo.
    The saved html file has the same name but with extension '.html' 
    Expecting first line is column headers, which varies depending on the csv types
    The argument IGNORE_COLUMNS is a list of the column headers for which we want to hide the entire column
    """
    if csv_file_name == '':
        return ''
    # file extension check
    file_path, file_extension = os.path.splitext(csv_file_name)
    if file_extension != ".csv":
        return ''
    if ignore_columns is None:
        ignore_columns = []

    HEADER_STRING = '''
<head>
	<script charset="UTF-8" type = "text/javascript" src="javascripts/scripts.js"></script>
	<link   charset="UTF-8" type = "text/css" rel  = "stylesheet"  href = "css/styles.css" />
</head>''' 

    LEGEND_BOX_ALL = '''
   <div class="legend" style="width:670px; height:180px;" >
		<p><b>Legend:</b></p>
		<p><span class="box reciprocal">Reciprocal</span>You and this user follow each other </p>
		<p><span class="box not_following">Follower only</span>You do not follow your follower</p>
		<p><span class="box not_follower"> Following only</span>Your follower does not follow you</p>
		<p><span class="box transparent_white">Follower Order</span>The chronological order at which a user followed you (in reverse, with 1 being the latest)</p>
		<p><span class="box transparent_white">Following Order</span>The chronological order at which you followed a user (in reverse, with 1 being the latest)</p>
	</div>'''

    LEGEND_BOX_RECIPROCAL = '''
   <div class="legend" style="width:670px; height:130px;" >
		<p><b>Legend:</b></p>
		<p><span class="box reciprocal">Reciprocal</span>You and this user follow each other </p>
		<p><span class="box transparent_white">Follower Order</span>The chronological order at which a user followed you (in reverse, with 1 being the latest)</p>
		<p><span class="box transparent_white">Following Order</span>The chronological order at which you followed a user (in reverse, with 1 being the latest)</p>
	</div>'''
    LEGEND_BOX_NOT_FOLLOWING = '''
   <div class="legend" style="width:670px; height:130px;" >
		<p><b>Legend:</b></p>
		<p><span class="box not_following">Follower only</span>You do not follow your follower</p>
		<p><span class="box transparent_white">Follower Order</span>The chronological order at which a user followed you (in reverse, with 1 being the latest)</p>
		<p><span class="box transparent_white">Following Order</span>The chronological order at which you followed a user (in reverse, with 1 being the latest)</p>
	</div>'''
    LEGEND_BOX_NOT_FOLLOWER = '''
   <div class="legend" style="width:670px; height:130px;" >
		<p><b>Legend:</b></p>
		<p><span class="box not_follower"> Following only</span>Your follower does not follow you</p>
		<p><span class="box transparent_white">Follower Order</span>The chronological order at which a user followed you (in reverse, with 1 being the latest)</p>
		<p><span class="box transparent_white">Following Order</span>The chronological order at which you followed a user (in reverse, with 1 being the latest)</p>
	</div>'''

    html_full_file_name = file_path + '.html'

    avatars_folder    = os.path.basename(os.path.normpath(output_lists.avatars_dir))
    thumbnails_folder = os.path.basename(os.path.normpath(output_lists.thumbnails_dir))


    # Create document title and description based on these predefined file names, under the format:
    # 0             1               2                    3    
    # [user name] _ [items count] _ [type of document] _ [date string].html
    #
    # Type of documents are:
    #
    # Notifications   :   notifications                       
    # Unique users    :   unique-users-in-the-last-n-notifications
    # Followers List  :   followers                          
    # Followings List :   followings                         
    # Users like photo:   likes_[photo title]_                
    # all             :   all                                
    # reciprocal      :   reciprocal                         
    # not_following   :   not_following                      
    # not_follower    :   not_follower                       


    file_name = file_path.split('\\')[-1]
    splits = file_name.split('_')  
    title, title_string = '', ''
    legend_box = ""
    if len(splits) >=4:
        if csv_file_type == apiless.CSV_type.unique_users:
            parts = splits[2].split('-')
            title = f'{splits[1]} unique users in {parts[-1]} notifications'
            table_width =  'style="width:500"'
        elif csv_file_type == apiless.CSV_type.notifications:
            title = f'{splits[1]} notifications'
            table_width =  'style="width:960"'
        elif csv_file_type == apiless.CSV_type.followers:
            title = f'List of {splits[1]} followers'
            table_width =  'style="width:460"'
        elif csv_file_type == apiless.CSV_type.followings:
            title = f'List of {splits[1]} followings'            
            table_width =  'style="width:460"'
        elif csv_file_type == apiless.CSV_type.like_actors:
            title = f'List of {splits[1]} users who liked photo {splits[-2].replace("-", " ")}'
            table_width = 'style="width:600"'

        elif csv_file_type == apiless.CSV_type.reciprocal:
            title = f'List of {splits[1]} followers that you are following'
            table_width =  'style="width:900"'
            legend_box = LEGEND_BOX_RECIPROCAL
        elif csv_file_type == apiless.CSV_type.not_following:
            title = f'List of {splits[1]} followers that you are not following'
            table_width =  'style="width:760"'
            legend_box = LEGEND_BOX_NOT_FOLLOWING
        elif csv_file_type == apiless.CSV_type.not_follower:
            title = f'List of {splits[1]} users whom you follow but they do not follow you'
            table_width =  'style="width:760"'
            legend_box = LEGEND_BOX_NOT_FOLLOWER
        elif csv_file_type == apiless.CSV_type.all:
            title = f'List all {splits[1]} users (your followers and your followings)'
            table_width =  'style="width:900"'
            legend_box = LEGEND_BOX_ALL

        title_string = f'\
    <h2>{title}</h2>\n\
    <div><span>User:</span> <span><b>{splits[0]}</b></span></div>\n\
    <div><span>Date recorded:</span> <span><b>{splits[-1]}</b></span></div>\n\
	<div>\
    <span> File: {os.path.dirname(csv_file_name)}\</span><br/>\n\
	<span><b>{file_name}.html</b> </span>\n\
	</div>\n'

    with open(csv_file_name, newline='', encoding='utf-16') as csvfile:
        reader = csv.DictReader(row.replace('\0', '') for row in csvfile)
        headers = reader.fieldnames
        if len(headers) < 3:
            printR(f'   File {csv_file_name} is in wrong format!')
            return ''
        row_string = '\n\t<tr>\n'
  
        # write headers and assign sort method for appropriate columns   
        #['No', 'Avatar Href', 'Avatar Local', 'Display Name', 'User Name', 'ID', 'Followers Count', 'Status', 'Follower Order', 'Following Order', 'Relationship', ]       
        # # each header cell has 2 parts: the left div for the header name, the right div for sort direction arrows     
        ignore_columns_count = 0
        for i, header in enumerate(reader.fieldnames):
            if header in ignore_columns:
                ignore_columns_count += 1
                continue

            sort_direction_arrows = f"""
            <div class="hdr_arrows">
		        <div id ="arrow-up-{i-ignore_columns_count}">&#x25B2;</div>
		        <div id ="arrow-down-{i-ignore_columns_count}">&#x25BC;</div></div>"""

            left_div = f"""
            <div class="hdr_text">{header}</div>"""
        
            if header == "No":
                first_left_div = f'\t\t\t<div class="hdr_text">{header}</div>'
                # the No column is initially in ascending order, so we do not show the down arrow
                ascending_arrow_only = f"""
                <div class="hdr_arrows">
				    <div id ="arrow-up-{i-ignore_columns_count}">&#x25B2;</div>
				    <div id ="arrow-down-{i-ignore_columns_count}" hidden>&#x25BC;</div>
			    </div>"""
                row_string += f'\t\t<th class="w40" onclick="sortTable({i-ignore_columns_count})">\n{first_left_div}{ascending_arrow_only}</th>\n'

            elif header == "Follower Order" or header == "Following Order":
                row_string += f"""\t\t<th class="w140" onclick="sortTable({i-ignore_columns_count})">{left_div}{sort_direction_arrows}</th>\n"""
            
            elif header == "Display Name":
                row_string += f"""\t\t<th class="w240" onclick="sortTable({i-ignore_columns_count})">{left_div}{sort_direction_arrows}</th>\n"""
            
            elif header == "Photo Title":
                row_string += f"""\t\t<th class="w240" onclick="sortTable({i-ignore_columns_count}, 'sortByPhotoTitle')">{left_div}{sort_direction_arrows}</th>\n"""
 
            elif header == "Followers Count" or header == "Appearances Count":
                row_string += f'\t\t<th class="w140" onclick="sortTable({i-ignore_columns_count})">{left_div}{sort_direction_arrows}</th>\n'
            
            elif header == "Content":
                row_string += f'\t\t<th class="w140" onclick="sortTable({i-ignore_columns_count})">{left_div}{sort_direction_arrows}</th>\n'

            elif header == "Relationship":
                row_string += f'\t\t<th class="w140" onclick="sortTable({i-ignore_columns_count})">{left_div}{sort_direction_arrows}</th>\n'
         
            elif header == "Status":
                row_string += f'\t\t<th class="w140" onclick="sortTable({i-ignore_columns_count})">{left_div}{sort_direction_arrows}</th>\n'
            
            elif header == "Time Stamp":
                row_string += f'\t\t<th class="w120" onclick="sortTable({i-ignore_columns_count})">{left_div}{sort_direction_arrows}</th>\n'
            
            else:
                row_string += f'\t\t<th onclick="sortTable({i-ignore_columns_count})">{left_div}{sort_direction_arrows}</th>\n'

        # create rows for html table 
        row_string += '\t</tr>'       
        for row in reader:
            row_string += '\n\t<tr>\n'
            # Table columns vary depending on 4 different csv files:
            # Columns:         0   1            2             3             4          5   6          7                     8                      9            10          11      12 
            # Notifications  : No, Avatar Href, Avatar Local, Display Name, User Name, ID, Content,   Photo Thumbnail Href, Photo Thumbnail Local, Photo Title, Time Stamp, Status, Photo Link
      
            # Unique users   : No, Avatar Href, Avatar Local, Display Name, User Name, ID, Count,    
            # Followers List : No, Avatar Href, Avatar Local, Display Name, User Name, ID, Followers, Status
            # Followings List: No, Avatar Href, Avatar Local, Display Name, User Name, ID, Followers, Status
            #                  1              2             3             4             5          6   7                8       9                10   
            # new userformat   Follower Order, Avatar Href, Avatar Local, Display Name, User Name, ID, Followers Count, Status, Following Order, _merg

            for i in range(len(headers)): 
                col_header = headers[i]   
                # ignore unwanted columns
                if col_header in ignore_columns:
                    continue

                text = row[col_header]

                # In Display Name column, show user's avatar and the display name with link 
                if col_header == 'Display Name' : 
                    user_home_page = f'https://500px.com/{row["User Name"]}'        
                    user_name = row["Display Name"]

                    row_string += f'\t\t<td>\n\t\t\t<div>\n\t\t\t\t<a href="{user_home_page}" target="_blank">\n'
                    if use_local_thumbnails:
                        user_avatar =f"{avatars_folder}/{row['Avatar Local']}"
                    else:
                        user_avatar = row['Avatar Href']

                    row_string += f'\t\t\t\t<img src={user_avatar}></a>\n'
                    row_string += f'\t\t\t\t<div><a href="{user_home_page}" target="_blank">{user_name}</a></div></div></td>\n'

                elif col_header == 'Status':
                    if text.find('Following') != -1: 
                        row_string += f'\t\t<td class="alignLeft" bgcolor="#00FF00">{text}</td> \n'   # green cell for following users                    
                    else:  
                        if text and text != 'Unknown':
                            row_string += f'\t\t<td class="alignLeft">{text}</td> \n'                 # default background color (white)
                        else:
                            row_string += f'\t\t<td></td> \n'                                         # empty td cell                       
  
                # In Photo Tile column, show photo thumbnail and photo title with <a href> link
                elif  col_header == 'Photo Title': 
                    if use_local_thumbnails:
                        photo_thumbnail = f"{thumbnails_folder}/{row['Photo Thumbnail Local']}"
                    else:
                        photo_thumbnail = row['Photo Thumbnail Href']
                    # if photo thumbnail is empty, write an empty div to keep the same layout 
                    if (use_local_thumbnails and not row['Photo Thumbnail Local'].strip()) or (not use_local_thumbnails and not row['Photo Thumbnail Href'].strip()) :
                        row_string += f'\t\t<td><div><div></div></div></td> \n'
                    else:
                        photo_link =  row['Photo Link']                 
                        row_string += f'\t\t<td>\n\t\t\t<div>\n\t\t\t\t<a href="{photo_link}" target="_blank">\n'
                        row_string += f'\t\t\t\t<img class="photo" src={photo_thumbnail}></a>\n'
                        row_string += f'\t\t\t\t<div>{text}</div></div></td>\n'

                elif  col_header == 'Relationship':
                    if text == 'both':
                        row_string += f'\t\t<td class="alignLeft" bgcolor="lightgreen">Reciprocal</td> \n'   # green cell for following users   
                    if text == 'left_only':
                        row_string += f'\t\t<td class="alignLeft" bgcolor="lightskyblue">Follower only</td> \n'   # green cell for following users   
                    if text == 'right_only':
                        row_string += f'\t\t<td class="alignLeft" bgcolor="lightpink">Following only</td> \n'   # green cell for following users   
                # All other columns, write text as is
                else:                            
                     row_string += f'\t\t<td>{text}</td> \n'

            row_string += '\t</tr>'

        html_string = f'<html>\n{HEADER_STRING}\n\n<body>\n{title_string}\n{legend_box}<table {table_width}> {row_string} </table>\n</body> </html>'
        
        #write html file 
        with open(html_full_file_name, 'wb') as htmlfile:
            htmlfile.write(html_string.encode('utf-16'))

    return html_full_file_name

#---------------------------------------------------------------  
def CSV_file_to_dataframe(csv_file_name, encoding='utf-16', sort_column_header='No', ascending=True):
    """Read a given csv file from disk and convert it to dataframe."""

    # do main task
    dframe = pd.read_csv(csv_file_name, encoding = encoding)  
    ## validate the given  csv file, if needed
    #if len(list(dframe)) == 0 or not 'User Name' in list(dframe):
    #    printR(f'   The given csv file is not valid. It should  have a header row with  at leat one column named "User Name":.\n\t{user_inputs.csv_file}')
    #    return

    #print(f'Table has {dframe.shape[0]} rows, {dframe.shape[1]} columns')
    
    ##option to sort a selected column
    #printG(list(dframe))
    #sort_header = input('Enter the desired sort column >')
    #if not sort_header:
    #    sort_header = "No" 
    #sort_ascending = True
    #ans = input('Sort descending ?(y/n) >')
    #if ans == 'y':
    #    sort_ascending = False
    df = dframe.sort_values(sort_column_header, ascending=ascending )  
    #df = df.drop(df[df.ID == 0].index)
    return df

def write_photos_list_to_csv(user_name, list_of_photos, csv_file_name):
    """ Write photos list to a csv file with the given  name. Return True if success.    
        If the file is currently open, give the user a chance to close it and come back to re-try.   
    """
    try:
        with open(csv_file_name, 'w', encoding = 'utf-16', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer = csv.DictWriter(csv_file, fieldnames = ['No', 'Author Name', 'ID', 'Photo Title', 'Href', 'Thumbnail Href', 'Thumbnail Local', 'Views', 'Likes', 'Comments', 'Featured In Galleries', 'Highest Pulse', 'Rating', 'Date', 'Category','Tags'])  
            writer.writeheader()
            for i, a_photo in enumerate(list_of_photos):
                writer.writerow({'No' : str(a_photo.order), 'Author Name': a_photo.author_name, 'ID': str(a_photo.id), 'Photo Title' : str(a_photo.title), 'Href' :a_photo.href, 'Thumbnail Href': a_photo.thumbnail_href, \
                                 'Thumbnail Local' : a_photo.thumbnail_local, 'Views': str(a_photo.stats.views_count), 'Likes': str(a_photo.stats.votes_count), 'Comments': str(a_photo.stats.comments_count), \
                                 'Featured In Galleries': str(a_photo.galleries), 'Highest Pulse': str(a_photo.stats.highest_pulse), 'Rating': str(a_photo.stats.rating), \
                                 'Date': str(a_photo.stats.upload_date), 'Category': a_photo.stats.category, 'Tags': a_photo.stats.tags}) 
            print(f"    List of {user_name}\'s {len(list_of_photos)} photo(s) is saved at:")
            printG(f"   ./Output/{os.path.basename(csv_file_name)}")
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
    """ Write the users list to a csv file with the given  name. Return True if success.h
    
    The users list could be one of the following: followers list, friends list or unique users list. 
    If the file is currently open, give the user a chance to close the file and retry
    """
    try:
        with open(csv_file_name, 'w', encoding = 'utf-16', newline='') as csv_file: 
            writer = csv.writer(csv_file)
            writer = csv.DictWriter(csv_file, fieldnames = ['No', 'Avatar Href', 'Avatar Local', 'Display Name', 'User Name', 'ID', 'Followers Count', 'Status'])  
            writer.writeheader()
            for a_user in users_list:
                writer.writerow({'No' : a_user.order, 'Avatar Href': a_user.avatar_href,'Avatar Local': a_user.avatar_local, 'Display Name' : a_user.display_name, \
                    'User Name': a_user.user_name, 'ID': a_user.id, 'Followers Count': a_user.number_of_followers, 'Status': a_user.following_status}) 
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
        If the file is currently open, give the user a chance to close it and come back to retry

    Headers: 1   2            3             4             5          6   7        8                     9                      10           11          12      13
             No, Avatar Href, Avatar Local, Display Name, User Name, ID, Content, Photo Thumbnail Href, Photo Thumbnail Local, Photo Title, Time Stamp, Status, Photo Link
    """

    try:
        with open(csv_file_name, 'w', encoding = 'utf-16', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer = csv.DictWriter(csv_file, fieldnames = ['No', 'Avatar Href', 'Avatar Local', 'Display Name', 'User Name', 'ID', 'Content', \
                'Photo Thumbnail Href', 'Photo Thumbnail Local', 'Photo Title', 'Time Stamp', 'Status', 'Photo Link'])    
            writer.writeheader()
            for notif in notifications_list:
                writer.writerow({'No': notif.order, 'Avatar Href' : notif.actor.avatar_href, 'Avatar Local': notif.actor.avatar_local, \
                                 'Display Name': notif.actor.display_name, 'User Name': notif.actor.user_name, 'ID' : notif.actor.id, \
                                 'Content': notif.content, 'Photo Thumbnail Href': notif.the_photo.thumbnail_href, 'Photo Thumbnail Local': notif.the_photo.thumbnail_local, \
                                 'Photo Title': notif.the_photo.title, 'Time Stamp': notif.timestamp, 'Status': notif.status, 'Photo Link': notif.the_photo.href}) 
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
    If the file is currently open, give the user a chance to close it and come back to retry
    
    Headers:    0   1            2             3             4          5   6
                No, Avatar Href, Avatar Local, Display Name, User Name, ID, Count
    """
    try:
        with open(csv_file_name, 'w', encoding = 'utf-16', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer = csv.DictWriter(csv_file, fieldnames = ['No', 'Avatar Href', 'Avatar Local', 'Display Name', 'User Name', 'ID', 'Appearances Count'])  
            writer.writeheader()

            for actor in unique_users_list:
                items = actor.split(',')
                if len(items) == 7:
                    writer.writerow({'No': items[0], 'Avatar Href': items[1], 'Avatar Local': items[2], 'Display Name': items[3], 'User Name': items[4], 'ID' : items[5], 'Appearances Count': items[6]}) 
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
     
    This function is meant to be called repeatedly in the loop, so for better performance, we don't chech the existance of the given path
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
def create_user_statistics_html(stats):
    """ write user statistic object stats to an html file. """
    if stats is None:
        return

    time_stamp = datetime.datetime.now().replace(microsecond=0).strftime(config.DATETIME_FORMAT)

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
def get_latest_cvs_file(file_path, user_name, csv_file_type):
    """ Find the latest csv file for the given csv_file_type, from the given user, at the given folder location"""
    files = [f for f in glob.glob(file_path + f"**/{user_name}*_{csv_file_type.name}_*.csv")]
    if len(files) > 0:
        if csv_file_type == apiless.CSV_type.notifications:
            files = [f for f in files if not 'unique' in f]

        files.sort(key=lambda x: os.path.getmtime(x))
        csv_file = files[-1]
        dated = os.path.splitext(csv_file)[0].split('_')[-1]
        print(f"    - The latest {user_name}'s {csv_file_type.name} csv file is on {dated}:")
        printG(f'   - {os.path.basename(csv_file)}')
        return csv_file
    else:
        return ""

#---------------------------------------------------------------
def count_And_Remove_Duplications(values):
    """Given a list containing the comma-separated strings of avatar href, avatar local, display name, user name and id( such as "http://...,  C://LocalAvatar, John Doe, johndoe, 1234567" ).
       Count the duplication of each item in the list then remove the duplicated entry(ies). Append the count to each entry's count column.
       An output list item has this form: Avatar Href, Avatar Local, Display Name, User Name, ID, Count"""

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
                if len(list_items) == 6:
                    new_count = int(list_items[5]) + 1
               # elif len(list_items) == 4: # just in crazy situation where display name has comma in it 
               #     new_count = int(list_items[3]) + 1
                output[index] = f'{list_items[0]},{list_items[1]},{list_items[2]},{list_items[3]},{list_items[4]},{new_count}'
            except:
                continue
    return output    

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
    text = f'\r{message:<46.45}[{"."*block + " "*(barLength-block)}] {int(round(progress*100)):<3}% {status}'
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
