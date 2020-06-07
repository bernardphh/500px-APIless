# python 3.6
# htmltools.py : Helper functions related to writing html components and files, used specifically for 500px_APIless.py module

import common.apiless as apiless
import common.config as config
import common.utils as utils
import os, time, datetime, csv

HEAD_STRING = ('<head>'
                   '\n\t<script charset="UTF-8" type = "text/javascript" src="javascripts/scripts.js"></script>'
	               '\n\t<link   charset="UTF-8" type = "text/css" rel  = "stylesheet"  href = "css/styles.css" />'
               '</head>' )

# associate table width with csv file type
TABLE_WIDTHS = {'photos':       '100%',
                'notifications':'1000px',
                'unique_users': '1100px',
                'like_actors':  '700px',
                'followers':    '500px',
                'followings':   '500px',
                'all_users':    '800px',
                'reciprocal':   '800px',
                'not_follow':   '700px',
                'following':    '700px'}

# associate table caption with csv file type
TABLE_CAPTION = {'photos':      'All Photos',
                'notifications':'Notifications',
                'unique_users': 'Unique users',
                'like_actors':  'Users',
                'followers':    'Users',
                'followings':   'Users',
                'all_users':    'Users',
                'reciprocal':   'Users',
                'not_follow':   'Users',
                'following':    'Users'}

# associate column width with column header text
COL_WIDTHS = {'Actions Count':          '100px',
              'Added To Gallery':       '100px',
              'Category':               '130px',
              'Commented':              '100px',
              'Comments':               '110px',
              'Content':                '100px',
              'Date':                   '110px',
              'Display Name':           'auto',
              'Featured In Galleries':  '240px',
              'Followed':               '100px',
              'Followers Count':        '100px',
              'Follower Order':         '100px',
              'Following Order':        '100px',
              'Galleries':              '110px',
              'Highest Pulse':          '110px',
              'Last Action Date':       '100px',
              'Liked':                  '100px',
              'Likes':                  '110px',
              'No':                     '50px',
              'Photo Title':            '300px',
              'Relationship':           '100px',
              'Tags':                   'auto',
              'Time Stamp':             '100px',
              'Views':                  '130px'
              }
# associate a table data cell text with a color
TD_BACKGROUND_COLOR = {'Recoprocal': 'lightgreen',
                       'Not Follow': 'lemonchiffon',
                       'Following' : 'lightpink'}
#--------------------------------------------------------------- 
def dict_to_html_table (dict, table_id = '', table_width = '', table_caption='Description', csv_file_type = apiless.CSV_type.not_defined, start_indent=1):
    """ Write a given dictionay to a html table, with option to assign a named class to the key cell, when key in dict matches with key_classes"""
        
    tab1 = '\n' + '\t'* start_indent
    tab2 = tab1 + '\t'

    # we want to be able to change a cell background color according to its text, so we use a dictinonary to associate a text with a CSS class name 
    bgcolor_classes = {}
    if csv_file_type == apiless.CSV_type.notifications or \
       csv_file_type == apiless.CSV_type.like_actors: bgcolor_classes = {'Following': 'following_raw'}
    elif csv_file_type == apiless.CSV_type.reciprocal:  bgcolor_classes = {'Reciprocal Following': 'reciprocal'}
    elif csv_file_type == apiless.CSV_type.not_follow:  bgcolor_classes = {'Not Follow': 'not_follow'}
    elif csv_file_type == apiless.CSV_type.following:   bgcolor_classes = {'Following': 'following'}

    id = f'id="{table_id}"' if table_id else ''
    width = f'style="width:{table_width}"' if table_width else ''
    caption = f'<caption>{table_caption}</caption>' if table_caption else ''

    table_string = f'{tab1}<table {id} {width}>{tab2}{caption}'
    
    for key,value in dict.items():
        optional_class_name = f'class="{bgcolor_classes[key]}"' if key in bgcolor_classes else ''
        table_string += f'{tab2}<tr><td {optional_class_name} >{key}</td><td>{value}</td></tr>'
    table_string += f'</table>'
    return table_string

#--------------------------------------------------------------- 
def CSV_top_photos_list_to_HTML_table(csv_file_name, output_lists, use_local_thumbnails = True, ignore_columns = None, start_indent = 1):
    """Create a html table from a given csv photos list file.

    NOTE: This is a short, modified version of the function CSV_to_HTML(), so expect to see some duplicated code. 
    Expecting the first line to be the column headers
    Hide the columns specified in the given IGNORE_COLUMNS LIST. The data in these columns are still being used to form the web link tag <a href=...>
    """
    tab1 = '\t'* start_indent
    tab2 = '\n' + tab1 + '\t'
    tab3 = tab2 + '\t'
    tab4 = tab3 + '\t'
    tab5 = tab4 + '\t'
    tab6 = tab5 + '\t'
    tab7 = tab6 + '\t'

    if ignore_columns is None:
        ignore_columns = []

    table_id = 'top_photos'
    CUSTOMED_COLUMN_WIDTHS = (f'{tab2}<colgroup>'
		                        f'{tab3}<col style="width:15%">'
		                        f'{tab3}<col style="width:4%">'
		                        f'{tab3}<col style="width:20%">'
		                        f'{tab3}<col span= "5" style="width:6%">'
		                        f'{tab3}<col style="width:auto">'							
	                          f'{tab2}</colgroup>')
    
    thumbnails_folder = os.path.basename(os.path.normpath(output_lists.thumbnails_dir))

    with open(csv_file_name, newline='', encoding='utf-16') as csvfile:
        reader = csv.DictReader(row.replace('\0', '') for row in csvfile)
        headers = reader.fieldnames
        header_string = f'{tab2}<tr>'
        ignore_columns_count = 0

        # write headers
        for i, header in enumerate(reader.fieldnames):
            if header in ignore_columns:
                ignore_columns_count += 1
                continue  
            # break long word(s) so that we can minimize columns widths
            if   header == 'Highest Pulse': header = 'Highest<br>Pulse'    
            elif header == 'Comments':      header = 'Com-<br>ments'    
            elif header == 'Galleries':     header = 'Gal-<br>leries'    
           
            sort_direction_arrows = f"""
                    <div class="hdr_arrows">
		                <div id ="arrow-up-{table_id}-{i-ignore_columns_count}">&#x25B2;</div>
		                <div id ="arrow-down-{table_id}-{i-ignore_columns_count}">&#x25BC;</div></div>"""
            if header == 'Top Photos':
                left_div = f'''
                    <div class="hdr_text"></div>'''
            else:
                left_div = f'''
                    <div class="hdr_text">{header}</div>'''

            if header == "No":
                first_left_div = f'{tab4}<div class="hdr_text">{header}</div>'
                # the No column is initially in ascending order, so we do not show the down arrow
                ascending_arrow_only = f"""
                    <div class="hdr_arrows">
				        <div id ="arrow-up-{i-ignore_columns_count}">&#x25B2;</div>
				        <div id ="arrow-down-{i-ignore_columns_count}" hidden>&#x25BC;</div></div>"""
                header_string += f'''{tab3}<th onclick="sortTable('{table_id}', {i-ignore_columns_count})">{tab4}{first_left_div}{ascending_arrow_only}</th>'''
            
            # special sort for title cell: we want to sort the displayed photo titles, not the photo link
            elif header == "Photo Title":
                header_string += f'''{tab3}<th onclick="sortTable('{table_id}', {i-ignore_columns_count}, true)">{left_div}{sort_direction_arrows}</th>'''
            else:
                header_string += f'''{tab3}<th onclick="sortTable('{table_id}', {i-ignore_columns_count})">{left_div}{sort_direction_arrows}</th>'''
        header_string += f'{tab2}</tr>'

        # write each row 
        row_string = '\n'  
        for row in reader:
            row_string += f'{tab2}<tr>'
            hp_style, views_style, likes_style, comments_style, galleries_style = ('' for i in range(5))
            for i in range(len(headers) ):
                col_header = headers[i]
                if col_header in ignore_columns:
                    continue  
                text = row[headers[i]]     
                if col_header == 'Top Photos':
                    row_string += f'{tab3}<td>{text}</td>' 
                    # prepare the background colors for hightlighting the related column cells in the same row
                    if 'Highest Pulse'  in text: hp_style        =  'bgcolor="lightgreen" style="font-weight: bold"'
                    if 'Most Viewed'    in text: views_style     =  'bgcolor="lightgreen" style="font-weight: bold"' 
                    if 'Most Liked'     in text: likes_style     =  'bgcolor="lightgreen" style="font-weight: bold"'
                    if 'Most Commented' in text: comments_style  =  'bgcolor="lightgreen" style="font-weight: bold"'
                    if 'Most Featured'  in text: galleries_style =  'bgcolor="lightgreen" style="font-weight: bold"'

                # In Photo Tile column, show photo thumbnail and photo title with <a href> link
                elif  col_header == 'Photo Title': 
                    photo_thumbnail = f"{thumbnails_folder}/{row['Thumbnail Local']}" if use_local_thumbnails  else row['Thumbnail Href']
                    
                    # if photo thumbnail is empty, write an empty div to keep the same layout 
                    if (use_local_thumbnails and not row['Thumbnail Local']) or (not use_local_thumbnails and not row['Thumbnail Href']) :
                        row_string += f'{tab3}<td><div"><div>{text}</div></div></td>' 
                    else:
                        photo_link =  row['Href']                 
                        row_string += f'{tab3}<td><div><div style="width: 35%; float:left;">{tab6}<a href="{photo_link}" target="_blank">'
                        row_string += f'{tab7}<img class="photo" src={photo_thumbnail}></a></div>'
                        row_string += f'{tab6}<div><a href="{photo_link}" target="_blank">{text}</a></div></div></td>'
                 
                elif  col_header == 'Featured In Galleries' and text != '':
                    # a gallery link has this format: https://500px.com/[photographer_name]/galleries/[gallery_name]
                    galleries = text.split(',')
                    if len(galleries) == 0:
                           row_string += f'{tab3}<td></td>'
                    else:
                        row_string += f'{tab3}<td>'
                        for j, gallery in enumerate(galleries):
                            gallery_name = gallery[gallery.rfind('/') + 1:]    
                            row_string += f'{tab3}<a href="{gallery}" target="_blank">{gallery_name}</a>'
                            if j < len(galleries) -1:
                                row_string += ',\n'                    
                        row_string += f'\t\t</td>'                                
                elif  col_header == 'Highest Pulse':
                    row_string += f'{tab3}<td {hp_style}>{text}</td>' 
                elif  col_header == 'Views':
                    row_string += f'{tab3}<td {views_style}>{text}</td>' 
                elif  col_header == 'Likes':
                    row_string += f'{tab3}<td {likes_style}>{text}</td>' 
                elif  col_header == 'Comments':
                    row_string += f'{tab3}<td {comments_style}>{text}</td>' 
                elif  col_header == 'Galleries':
                    row_string += f'{tab3}<td {galleries_style}>{text}</td>' 
                else: 
                    row_string += f'{tab3}<td>{text}</td>' 
            row_string += '\t</tr>\n'

        top_photos_html_table_string = (f'{tab1}<table id="{table_id}">'
                                           f'{tab2}<caption>Top Photos</caption>'
                                           f'{CUSTOMED_COLUMN_WIDTHS}'
                                           f'{header_string}'
                                           f'{tab2}{row_string}'
                                        f'{tab1}</table>' )
        return top_photos_html_table_string

#--------------------------------------------------------------- 

def CSV_photos_list_to_HTML(csv_file_name, output_lists, use_local_thumbnails = True, ignore_columns = None, desc_dict = {}, stats_dict = {}, top_photos_html_table = '', start_indent=1):
    """Create a html file from a given photos list csv  file. Save it to disk and return the file name.

    Save the html file using the same name but with extension '.html'
    Expecting the first line to be the column headers, which are  no, page, id, title, link, src
    Hide the columns specified in the given IGNORE_COLUMNS LIST. The data in these columns are still being used to form the web link tag <a href=...>
    """
    global HEAD_STRING, TABLE_WIDTHS, TABLE_CAPTION, COL_WIDTHS 

    tab1 = '\t'* start_indent
    tab2 = '\n' + tab1 + '\t'
    tab3 = tab2 + '\t'
    tab4 = tab3 + '\t'
    tab5 = tab4 + '\t'
    tab6 = tab5 + '\t'
    tab7 = tab6 + '\t'   

    if ignore_columns is None:
        ignore_columns = []

    table_id = 'main_table'

    CUSTOMED_COLUMN_WIDTHS = """
        <colgroup>
		    <col style="width:4%">    
		    <col style="width:15%">
		    <col span= "5" style="width:6%" >
		    <col style="width:5%" >
		    <col style="width:8%" >
		    <col style="width:14%">	
		    <col style="width:auto">				
	    </colgroup> """

# file name and extension check
    file_path, file_extension = os.path.splitext(csv_file_name)
    if file_extension != ".csv":
        return None

    html_file = file_path + '.html'
    avatars_folder    = os.path.basename(os.path.normpath(output_lists.avatars_dir))
    thumbnails_folder = os.path.basename(os.path.normpath(output_lists.thumbnails_dir))
    main_table_width = TABLE_WIDTHS['photos'] 
    main_table_caption = TABLE_CAPTION['photos'] 

    # get the title out of the dictionary
    title_string =f'<h2>{desc_dict["Title"]}</h2>'
    desc_dict.pop('Title')

    # render summary html table
    description_html_table = ''
    if desc_dict and len(desc_dict)> 0:
        description_html_table = dict_to_html_table(desc_dict, table_id = 'description', table_width = main_table_width)

   # render statistic html table, the info could be a dict or a list
    stats_html_table = ''
    stats_html_table = dict_to_html_table(stats_dict, table_id = 'overview', table_caption='Overview' )  

    with open(csv_file_name, newline='', encoding='utf-16') as csvfile:
        reader = csv.DictReader(row.replace('\0', '') for row in csvfile)
        headers = reader.fieldnames

        # Ref:
        # Columns    : 0   1            2   3            4     5               6                7      8      9         10         11             12      13    14        15                     16
        # Photo List : No, Author Name, ID, Photo Title, Href, Thumbnail Href, Thumbnail Local, Views, Likes, Comments, Galleries, Highest Pulse, Rating, Date, Category, Featured In Galleries, Tags

        # write headers and assign sort method for appropriate columns   
        # each header cell has 2 DIVs: the left DIV for the header name, the right DIV for sort direction arrows     
        ignore_columns_count = 0
        header_string = f'{tab2}<tr>'

        for i, header in enumerate(reader.fieldnames):
            if header in ignore_columns:
                ignore_columns_count += 1
                continue  

            # break long word(s) so that we can minimize columns widths
            if   header == 'Comments':        header = 'Com-<br>ments'
            elif header == 'Highest Pulse': header = 'Highest<br>Pulse'    
            elif header == 'Galleries':       header = 'Gal-<br>leries'    
                
            sort_direction_arrows = f"""
                <div class="hdr_arrows">
		            <div id ="arrow-up-{i-ignore_columns_count}">&#x25B2;</div>
		            <div id ="arrow-down-{i-ignore_columns_count}">&#x25BC;</div></div>"""

            ascending_arrow_only = f"""
                <div class="hdr_arrows">
				    <div id ="arrow-up-{table_id}-{i-ignore_columns_count}">&#x25B2;</div>
				    <div id ="arrow-down-{table_id}-{i-ignore_columns_count}" hidden>&#x25BC;</div></div>"""
            left_div = f'''
                <div class="hdr_text">{header}</div>'''

            if header == "No":
                first_left_div = f'{tab3}<div class="hdr_text">{header}</div>'
                # the No column is initially in ascending order, so we do not show the down arrow
                header_string += f'''{tab3}<th onclick="sortTable('{table_id}', {i-ignore_columns_count})">{first_left_div}{ascending_arrow_only}</th>'''
            
            # special sort for title cell: we want to sort the displayed photo titles, not the photo link
            elif header == "Photo Title":
                header_string += f'''{tab3}<th onclick="sortTable('{table_id}', {i-ignore_columns_count}, 'sortByPhotoTitle')">{left_div}{sort_direction_arrows}</th>'''

            else:
                header_string += f'''{tab3}<th onclick="sortTable('{table_id}', {i-ignore_columns_count})">{left_div}{sort_direction_arrows}</th>'''
        
        header_string += f'{tab2}</tr>'

       # create rows for html table 
        rows  = list(reader)
        rows_count = len(rows)
        row_string = ''       
        for i, row in enumerate(rows):
            utils.update_progress(i / rows_count, f'    - Writing items to html {i}/{rows_count} ...')  
            row_string += f'{tab2}<tr>'

            for j in range(len(headers) ):
                col_header = headers[j]
                if col_header in ignore_columns:
                    continue  
                text = row[headers[j]]     
                # In Photo Tile column, show photo thumbnail and photo title with <a href> link
                if  col_header == 'Photo Title': 
                    photo_thumbnail = f"{thumbnails_folder}/{row['Thumbnail Local']}" if use_local_thumbnails  else row['Thumbnail Href']
                    
                    # if photo thumbnail is empty, write an empty div to keep the same layout 
                    if (use_local_thumbnails and not row['Thumbnail Local']) or (not use_local_thumbnails and not row['Thumbnail Href']) :
                        row_string += f'\t\t\t<td><div><div><a/></div><div></a></div></div></td> \n' 
                    else:
                        photo_link =  row['Href']                 
                        row_string += f'{tab3}<td><div><div style="width: 40%; float:left; margin-right:10px;">{tab6}<a href="{photo_link}" target="_blank">'
                        row_string += f'{tab7}<img class="photo" src={photo_thumbnail}></a></div>'
                        row_string += f'{tab5}<div><a href="{photo_link}" target="_blank">{text}</a></div></div></td>'
 
                elif  col_header == 'Category':
                    row_string += f'{tab3}<td class="alignLeft">{text}</td>' 

                elif  col_header == 'Tags':
                    row_string += f'{tab3}<td class="alignLeft">{text}</td>' 
                
                elif  col_header == 'Featured In Galleries' and text != '':
                    # a gallery link has this format: https://500px.com/[photographer_name]/galleries/[gallery_name]
                    galleries = text.split(',')
                    if len(galleries) == 0:
                           row_string += f'{tab3}<td></td>'
                    else:
                        row_string += f'{tab3}<td>'
                        for k, gallery in enumerate(galleries):
                            gallery_name = gallery[gallery.rfind('/') + 1:]    
                            row_string += f'{tab3}<a href="{gallery}" target="_blank">{gallery_name}</a>'
                            if k < len(galleries) -1:
                                row_string += ',\n'                    
                        row_string += f'\t\t</td>'  
                        
                else: 
                    # write empty string if text == 0
                    alt_text = '' if text == '0' else text
                    row_string += f'{tab3}<td>{alt_text}</td>' 

            row_string += f'{tab2}</tr>\n'

        html_string = ('<html>\n'
                       f'{HEAD_STRING}\n'
                       '<body>'
                          f'{tab1}{title_string}\n'

                          f'{tab1}<div class="float_left" style="width:60%">'
                          f'{description_html_table}</div>\n\n'
                          
                          f'{tab1}<div class="float_right">'
                          f'{stats_html_table}</div>\n\n'

                          f'{top_photos_html_table}\n'
                          f'{tab1}<table id="{table_id}"style="width:{main_table_width}">'
                             f'{tab2}<caption>Photos</caption>'
                             f'{tab3}{CUSTOMED_COLUMN_WIDTHS}'
                             f'{tab3}{header_string}' 
                             f'{tab3}{row_string}' 
                          f'{tab2}</table>'
                       f'{tab1}</body> </html>')
        
        utils.update_progress(1, f'    - Writing items to html {rows_count}/{rows_count} ...')  
        #write html file 
        with open(html_file, 'wb') as htmlfile:
            htmlfile.write(html_string.encode('utf-16'))

    return html_file

#--------------------------------------------------------------- 
def CSV_to_HTML(csv_file_name, csv_file_type, output_lists, use_local_thumbnails = True, ignore_columns = None, 
                encoding = 'utf-16', column_to_sort = 'No', desc_dict={}, statistics_info = None, start_indent = 1):
    """ Convert csv file of various types into html file and write it to disk . Return the saved html filename.
    
    Support various types of csv files, which are lists of:
    notifications, unique_users, like_actors, followers, followings, all_users, reciprocal, not_follow, following
    The saved html file has the same name but with extension '.html' 
    Expecting the first line on the file is column headers, which are different from type to type
    Arguments:
    - IGNORE_COLUMNS :  a list of the column headers that we want to hide the entire column
    - DESC_DICT      :  a dictonary containing description info. It will be rendered as the first table, if passed
    - STATISTICS_INFO:  a statistics, or overview info, could be either a dictionary or a list, It will be rendered as the second table, if passed 
    """
    if csv_file_name == '':
        return ''

    global HEAD_STRING, TABLE_WIDTHS, TABLE_CAPTION, COL_WIDTHS  

    tab1 = '\n' + '\t'* start_indent
    tab2 = tab1 + '\t'
    tab3 = tab2 + '\t'
    tab4 = tab3 + '\t'
    tab5 = tab4 + '\t'
    tab6 = tab5 + '\t'
    tab7 = tab6 + '\t'   
    # file extension check
    file_path, file_extension = os.path.splitext(csv_file_name)
    if file_extension != ".csv":
        return ''
    html_full_file_name = file_path + '.html'

    if ignore_columns is None:
        ignore_columns = []

    table_id = 'main_table'

    avatars_folder    = os.path.basename(os.path.normpath(output_lists.avatars_dir))
    thumbnails_folder = os.path.basename(os.path.normpath(output_lists.thumbnails_dir))

    main_table_width = TABLE_WIDTHS[csv_file_type.name] 
    main_table_caption = TABLE_CAPTION[csv_file_type.name] 

    title_string =f'<h2>{desc_dict["Title"]}</h2>'
    desc_dict.pop('Title')

    # render description table
    description_html_table = ''
    if desc_dict and len(desc_dict)> 0:
        if csv_file_type.name == 'notifications':
            description_html_table = dict_to_html_table(desc_dict, table_id = 'description', csv_file_type = csv_file_type )
        else:
            description_html_table = dict_to_html_table(desc_dict, table_id = 'description', table_width = main_table_width, csv_file_type = csv_file_type )

    # render statistic html table, the info could be a dict or a list
    stats_html_table = ''
    if type(statistics_info) is dict:
        stats_html_table = dict_to_html_table(statistics_info, table_id = 'overview', table_caption='Overview', csv_file_type = csv_file_type )  
    elif type(statistics_info) is list  and len(statistics_info)> 0:
        stats_html_table = statistics_list_to_html_table(statistics_info, table_style= f'width:{main_table_width}')

    with open(csv_file_name, newline='', encoding=encoding) as csvfile:
        reader = csv.DictReader(row.replace('\0', '') for row in csvfile)
        headers = reader.fieldnames
        if len(headers) < 3:
            printR(f'   File {csv_file_name} is in wrong format!')
            return ''
  
        # write headers and assign appropriate sort method for each columns   
        # # each header cell has 2 parts: the left div for the header name, the right div for sort direction arrows     
        ignore_columns_count = 0
        header_string = f'{tab2}<tr>'
        for i, header in enumerate(reader.fieldnames):
            if header in ignore_columns:
                ignore_columns_count += 1
                continue
            
            col_width = f'width="{COL_WIDTHS[header]}"'
            
            up_down_arrows = (f'{tab5}<div class="hdr_arrows">'
		                        f'{tab6}<div id ="arrow-up-{i-ignore_columns_count}">&#x25B2;</div>'
		                        f'{tab6}<div id ="arrow-down-{i-ignore_columns_count}">&#x25BC;</div></div>')
            down_arrow_only = (f'{tab5}<div class="hdr_arrows">'
				                 f'{tab6}<div id ="arrow-up-{i-ignore_columns_count}">&#x25B2;</div>'
				                 f'{tab6}<div id ="arrow-down-{i-ignore_columns_count}" hidden>&#x25BC;</div></div>')
            
            # break the multi-words headers text into multiple lines
            if header == "Display Name" or header  == "Photo Title":
                left_div = f'<div class="hdr_text">{header}</div>'
            else:
                left_div = f"""<div class="hdr_text">{header.replace(' ','<br>')}</div>"""
        
            if header == "No":
                first_left_div = f'<div class="hdr_text">{header}</div>'
                # Initially, the No column is in ascending order, so we need to hide the up arrow
                sort_arrows = down_arrow_only if header == column_to_sort else up_down_arrows
                header_string += f'''{tab3}<th {col_width} onclick="sortTable('{table_id}', {i-ignore_columns_count})">{tab4}{first_left_div}{sort_arrows}</th>'''

            elif header == "Display Name":
                header_string += f"""{tab3}<th {col_width} onclick="sortTable('{table_id}', {i-ignore_columns_count}, 'sortByDisplayName')">{tab4}{left_div}{up_down_arrows}</th>"""
            
            elif header == "Photo Title":
                header_string += f"""{tab3}<th {col_width} onclick="sortTable('{table_id}', {i-ignore_columns_count}, 'sortByPhotoTitle')">{tab4}{left_div}{up_down_arrows}</th>"""
 
            elif (header == "Follower Order"  or header == "Following Order"   or header == "Content"  or header == "Last Action Date" or
                                                 header == "Followers Count" or header == "Relationship" or header == "Added To Gallery"):
                header_string += f'''{tab3}<th {col_width} onclick="sortTable('{table_id}', {i-ignore_columns_count})">{tab4}{left_div}{up_down_arrows}</th>'''
            
            elif ( header == "Actions Count" or  header == "Liked" or header == "Followed" or header == "Commented" ):
                header_string += f'''{tab3}<th {col_width}  onclick="sortTable('{table_id}', {i-ignore_columns_count})">{tab4}{left_div}{up_down_arrows}</th>'''

            elif header == "Time Stamp":
                header_string += f'''{tab3}<th {col_width}  onclick="sortTable('{table_id}', {i-ignore_columns_count})">{tab4}{left_div}{up_down_arrows}</th>\n'''
            
            else:
                header_string += f'''{tab3}<th {col_width} onclick="sortTable('{table_id}', {i-ignore_columns_count})">{tab4}{left_div}{up_down_arrows}</th>'''

        header_string += '</tr>' 

        # create rows for html table 
        rows  = list(reader)
        rows_count = len(rows)
        row_string = ''       
        for i, row in enumerate(rows):
            utils.update_progress(i / rows_count, f'    - Writing items to html {i}/{rows_count} ...')  
            row_string += f'{tab2}<tr>'
            
            for j in range(len(headers)): 
                col_header = headers[j]   
                # ignore unwanted columns
                if col_header in ignore_columns:
                    continue

                text = row[col_header]

                # In Display Name column, show user's avatar and the display name with link 
                if col_header == 'Display Name' : 
                    user_home_page = f'https://500px.com/{row["User Name"]}'        
                    user_name = row["Display Name"]
                    row_string += f'{tab3}<td><div><div style="width: 30%; float:left;">{tab6}<a href="{user_home_page}" target="_blank">'
                    if use_local_thumbnails:
                        user_avatar =f"{avatars_folder}/{row['Avatar Local']}"
                    else:
                        user_avatar = row['Avatar Href']

                    row_string += f'{tab7}<img src={user_avatar}></a></div>'
                    row_string += f'{tab5}<div><a href="{user_home_page}" target="_blank">{user_name}</a></div></div></td>'
 
                # In Photo Tile column, show photo thumbnail and photo title with <a href> link
                elif  col_header == 'Photo Title': 
                    photo_thumbnail = f"{thumbnails_folder}/{row['Photo Thumbnail Local']}"  if use_local_thumbnails else  row['Photo Thumbnail Href']
                    # if photo thumbnail is empty, write an empty divs to keep the same layout 
                    if (use_local_thumbnails and not row['Photo Thumbnail Local'].strip()) or (not use_local_thumbnails and not row['Photo Thumbnail Href'].strip()) :
                        row_string += f'{tab3}<td><div><div><a/></div><div><a/></div></div></td>'
                    else:
                        photo_link =  row['Photo Link']                 
                        row_string += f'{tab3}<td><div><div style="width: 30%; float:left;">{tab7}<a href="{photo_link}" target="_blank">'
                        row_string += f'{tab7}<img class="photo" src={photo_thumbnail}></a></div>'
                        row_string += f'{tab5}<div><a href="{photo_link}" target="_blank">{text}</a></div></div></td>'

                elif  col_header == 'Relationship':
                    color_class_name = text.lower().replace(' ', '_')
                    if csv_file_type.name == 'reciprocal' or csv_file_type.name == 'not_follow' or csv_file_type.name == 'following' or csv_file_type.name == 'all_users' or csv_file_type.name == 'unique_users': 
                        row_string += f'{tab3}<td class="alignLeft {color_class_name}" >{text}</td>'    
                    elif csv_file_type.name == 'notifications' or csv_file_type.name == 'like_actors':
                        if text == 'Following': 
                            row_string += f'{tab3}<td class="alignLeft following_raw">{text}</td>'  # green cell for following users from notification                   
                        elif text == 'Not Follow':  
                            row_string += f'{tab3}<td class="alignLeft">{text}</td>'                # default background color (white)
                        else:
                            row_string += f'{tab3}<td></td>'                                        # empty td cell     
                    else:
                        row_string += f'{tab3}<td>{text}</td>'                                             
               
                elif  col_header == 'Content': 
                     row_string += f'{tab3}<td class="alignCenter">{text}</td>'

                else:                            
                     row_string += f'{tab3}<td class="alignRight">{text}</td>'

            row_string += '\t</tr>'

        #special layout for notification type
        if csv_file_type == apiless.CSV_type.notifications:
            desc_and_stats_box = (f'{tab1}<div style="width:{main_table_width}">'
                                        f'{tab2}<div class="float_left" style="width:65%">' 
                                        f'{tab3}{description_html_table}</div>'
                                        f'{tab2}<div class="float_right">'
                                        f'{tab3}{stats_html_table}</div>\n')
        else:
            desc_and_stats_box = (f'{description_html_table}\n\n'                          
                                  f'{stats_html_table}\n\n')

        html_string = ('<html>\n'
                       f'{HEAD_STRING}\n'
                       f'<body>'
                          f'{tab1}{title_string}\n'
                          f'{desc_and_stats_box}'
                          f'{tab1}<table id="{table_id}" style="width:{main_table_width}">'
                              f'{tab2}<caption>{main_table_caption}</caption>'
                              f'{tab2}{header_string}'
                              f'{tab2}{row_string}'
                          f'{tab1}</table>'
                       '</body> </html>')
        utils.update_progress(1, f'    - Writing items to html {rows_count}/{rows_count} ...')  
        
        #write html file 
        with open(html_full_file_name, 'wb') as htmlfile:
            htmlfile.write(html_string.encode(encoding))

    return html_full_file_name

#---------------------------------------------------------------  
def dict_to_html(info_dict, table_id = ''):
    """ write user statistic object stats to an html file. """
    
    global HEAD_STRING
    title_string = ''
    if 'Title' in info_dict:
        title_string =f'<h2>{info_dict["Title"]}</h2>\n'
        info_dict.pop('Title')
    stats_html_table = dict_to_html_table(info_dict, table_id = table_id)
    return f'''
<html>
    {HEAD_STRING}
    <body>
       {title_string}
       {stats_html_table} 
    </body>
</html>
'''
#---------------------------------------------------------------  
def table_to_html(html_table, table_id = ''):
    """ write user statistic object stats to an html file. """
    
    global HEAD_STRING

    return f'''
<html>
    {HEAD_STRING}
    <body>
       {html_table} 
    </body>
</html>
'''

#---------------------------------------------------------------  
def statistics_list_to_html_table(detail_list, table_id = '', table_caption = 'Overview', table_style='', start_indent = 1):
    """ Hightly customized function to write a nested list of strings to a html table of 2 or more columns."""
    
    tab1 = '\t'* start_indent
    tab2 = '\n' + tab1 + '\t'

    id = f'id="{table_id}"' if table_id else ''
    style = f'style = "{table_style}"' if table_style else ''
    caption = f'<caption>{table_caption}</caption>' if table_caption else ''
    
    table_string = f'{tab1}<table {id} {style}>{tab2}{caption}'
    for i, row in enumerate(detail_list):
        table_string += f'{tab2}<tr>'
        # if a row has only 2 items, then span the first column to 2 cells
        if len(row) == 2:
            table_string += f'<td colspan="2">{row[0]}</td><td><i>{row[1]}</td> </tr>'
        # if a row has 3 items, write a simple table row with 3 columns  
        elif len(row) == 3:
            table_string += f'<td>{row[0]}</td> <td>{row[1]}</td> <td><i>{row[2]}</td> </tr>'       
        # if row has 4 items, then write the last 3 items as 3 columns. The first item is used as a assigned class for the first column.
        elif len(row) == 4:
            table_string += f'<td class="{row[0]}">{row[1]}</td><td style="text-align:right;">{row[2]}</td><td><i>{row[3]}</td></tr>'

    table_string += f'{tab1}</table>'
    return table_string
