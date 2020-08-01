# python 3.6
# htmltools.py : Helper functions related to writing html components and files, used specifically for 500px_APIless.py module

import common.apiless as apiless
import common.config as config
import common.utils as utils
import os, time, datetime, csv


HEAD_STRING = ('<head>'
               	   '\n\t<meta charset="utf-8">'
	               '\n\t<meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0">'
                   '\n\t<link rel="stylesheet" type="text/css" charset="UTF-8" href = "css/styles.css" />'
	               '\n\t<link rel="stylesheet" type="text/css" charset="UTF-8" href="DataTables/DataTables-1.10.21/css/jquery.dataTables.min.css"/>\n'
	               '\n\t<link rel="stylesheet" type="text/css" charset="UTF-8" href="DataTables/FixedHeader-3.1.7/css/fixedHeader.dataTables.min.css"/>'
                '</head>\n')

SCRIPT_STRING = (  '\n\t<script  type="text/javascript" charset="utf8" src="DataTables/jQuery-3.3.1/jquery-3.3.1.min.js"></script>'
	               '\n\t<script  type="text/javascript" charset="utf8" src="DataTables/datatables.js"></script>	'	
                   '\n\t<script  type="text/javascript" charset="utf8" src="javascripts/handle_tables.js"></script>'
                   '\n\t<script  type="text/javascript" charset="utf8" src="javascripts/go_to_top.js"></script>'
	               '\n\t<script>'
                   '\n\t    $(document).ready(function() {'
			       '\n\t    $("#main_table").DataTable( {"lengthMenu": [[10, 25, 50, 100, 500, -1], [10, 25, 50, 100, 500, "All"]], "pageLength": 10, fixedHeader: true} );'
			       '\n\t    $("#photos_public").DataTable( {"lengthMenu": [[10, 25, 50, 100, 500, -1], [10, 25, 50, 100, 500, "All"]], "pageLength": 10, fixedHeader: true} );'
			       '\n\t       } );'
                   '\n\t</script>')

FLOATING_BACK_2_TOP_BUTTON = '\n\t<a id="back2Top" title="Back to top" href="#">&#10148;</a>'

# associate table width with csv file type
TABLE_WIDTHS = {'photos_public'         : '100%',
                'photos_unlisted'       : '100%',
                'photos_limited_access' : '100%',
                'notifications'         : '1100px',
                'all_notifications'     : '1100px',
                'unique_users'          : '1200px',
                'all_unique_users'      : '1200px',
                'like_actors'           : '700px',
                'followers'             : '600px',
                'followings'            : '600px',
                'all_users'             : '800px',
                'reciprocal'            : '800px',
                'not_follow'            : '700px',
                'following'             : '700px'}

# associate a table description with its csv file type
TABLE_CAPTION = {'photos_public'        : 'Public Photos',
                 'photos_unlisted'      : 'Unlisted Photos',
                 'photos_limited_access': 'Limited Access Photos',
                 'notifications'        : 'Notifications',
                 'all_notifications'    : 'All Notifications',
                 'unique_users'         : 'Unique users',
                 'all_unique_users'     : 'All Unique users',
                 'like_actors'          : 'Like Actor',
                 'followers'            : 'Followers',
                 'followings'           : 'Followings',
                 'all_users'            : 'All Users',
                 'reciprocal'           : 'Reciprocal Following Users',
                 'not_follow'           : 'Not-Follow Users',
                 'following'            : 'Following Users'}

# associate column width with column header text
COL_WIDTHS = {'Actions Count':          '80px',
              'Added To Gallery':       '80px',
              'Category':               '130px',
              'Commented':              '80px',
              'Comments':               '110px',
              'Content':                '80px',
              'Date':                   '110px',
              'Display Name':           'auto',
              'Featured In Galleries':  '240px',
              'Followed':               '80px',
              'Followers Count':        '80px',
              'Follower Order':         '80px',
              'Following Order':        '80px',
              'Galleries':              '110px',
              'Highest Pulse':          '110px',
              'Last Action Date':       '80px',
              'Liked':                  '80px',
              'Likes':                  '110px',
              'No':                     '40px',
              'Photo Title':            '300px',
              'Relationship':           '80px',
              'Tags':                   'auto',
              'Time Stamp':             '100px',
              'Views':                  '130px'
              }
# associate a table data cell text with a color
TD_BACKGROUND_COLOR = {'Recoprocal': 'lightgreen',
                       'Not Follow': 'lemonchiffon',
                       'Following' : 'lightpink'}

#--------------------------------------------------------------- 
def dictionary_to_html_table (dict, 
                              table_id = '', 
                              table_width = '', 
                              headline_text='', 
                              csv_file_type = apiless.CSV_type.not_defined, 
                              start_indent=1, 
                              headline_tag='h4',
                              headline_id='table_description_id'):
    """ Convert a given dictionary to a html table, with following options:
        - table id, table width, 
        - a headline string, with given tag, id, containing the given table description and a down-arrow symbol 
        - the first table cell background can be configurable, via css, by assigning a class name according to the keys of the dictionary """
        
    if not dict  or len(dict) == 0: 
        return ''

    tab1 = '\n' + '\t'* start_indent
    tab2 = tab1 + '\t'

    # create the html headline string only if the headline_text is given
    headline_string =  ''  if headline_text == '' else f'{tab1}<{headline_tag} id="{headline_id}">{headline_text} &nbsp;&nbsp; &#8681; </{headline_tag}>'

    # we want to be able to change a cell background color according to its text, so we use a dictinonary to associate a text with a CSS class name 
    bgcolor_classes = {}
    if csv_file_type == apiless.CSV_type.notifications or \
       csv_file_type == apiless.CSV_type.like_actors: bgcolor_classes = {'Following': 'following_raw'}
    elif csv_file_type == apiless.CSV_type.reciprocal:  bgcolor_classes = {'Reciprocal Following': 'reciprocal'}
    elif csv_file_type == apiless.CSV_type.not_follow:  bgcolor_classes = {'Not Follow': 'not_follow'}
    elif csv_file_type == apiless.CSV_type.following:   bgcolor_classes = {'Following': 'following'}

    id = f'id="{table_id}"' if table_id else ''
    width = f'style="width:{table_width}"' if table_width else ''

    table_string = f'{tab1}<table {id} {width}>'
    
    for key,value in dict.items():
        optional_class_name = f'class="{bgcolor_classes[key]}"' if key in bgcolor_classes else ''
        table_string += f'{tab2}<tr><td {optional_class_name} >{key}</td><td>{value}</td></tr>'
    table_string += f'</table>'
    return headline_string + table_string

#--------------------------------------------------------------- 
def list_to_html_table(detail_list, table_id = '', headline_text = 'Overview', table_style='', start_indent = 1, headline_tag='h4', headline_id = 'table_description_id'):
    """ Convert  a nested list of strings to a html table of 2 or more columns, with following options:
        - table id, table width, 
        - a headline string, with given tag, id, containing the given table description and a down-arrow symbol 
        - the first table cell background can be configurable, via css, by assigning a class name according to the keys of the dictionary
    """
    
    if not detail_list  or len(detail_list) == 0: 
        return ''  

    tab1 = '\n' + '\t'* start_indent
    tab2 = tab1 + '\t'

   # create the html headline string only if the headline_text is given
    headline_string =  ''  if headline_text == '' else f'{tab1}<{headline_tag} id="{headline_id}">{headline_text} &nbsp;&nbsp; &#8681; </{headline_tag}>'

    id = f'id="{table_id}"' if table_id else ''
    style = f'style = "{table_style}"' if table_style else ''
    
    table_string = f'{tab1}<table {id} {style}>'
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
    return headline_string + table_string

#---------------------------------------------------------------  

def CSV_top_photos_list_to_HTML_table(csv_file_name, output_lists, use_local_thumbnails = True, ignore_columns = None, start_indent = 1, headline_tag = 'h4'):
    """ Given a csv file containing a list of top photos, return a html string containing a description headline and the photos html table.
        - headline string contains a down-arrow symbol. Ex: <h4 id="top_photos_header">Top Photos &nbsp;&nbsp; &#8681;</h4>
        - We hide the columns specified in the given IGNORE_COLUMNS LIST. (The data in these columns are still being used to form the web link tag <a href=...>
        NOTE: This is a short, modified version of the function CSV_to_HTML(), so expect to see some duplicated code. 
        """

    if not os.path.isfile(csv_file_name): 
        return ''

    tab1 = '\n' + '\t'* start_indent
    tab2 = tab1 + '\t'
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
            header_string += f'{tab3}<th>{header}</th>'
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

        # create the table headline with down-arrow symbol at the end: ex: 	<h4 id="unlisted_photos_header">Unlisted Photos (1) &nbsp;&nbsp; &#8681;</h4>	
        headline_text = 'Top Photos'
        headline_id = 'top_photos_headline'
        headline_html_string = f'{tab1}<{headline_tag} id="{headline_id}">{headline_text} &nbsp;&nbsp; &#8681;</{headline_tag}>'

        top_photos_html_table_string = (f'{tab1}<table id="{table_id}">'
                                           f'{CUSTOMED_COLUMN_WIDTHS}'
                                           f'{header_string}'
                                           f'{tab2}{row_string}'
                                        f'{tab1}</table>' )
        return headline_html_string + top_photos_html_table_string

#--------------------------------------------------------------- 
def write_sections_to_html_page( html_file_name, 
                                 csv_type,
                                 title,
                                 description_section = '', 
                                 statistics_section = '',
                                 main_section = '',
                                 photos_section = '',                                 
                                 other_list_section = ''):
    """Create a html file from a given html sections. Save it to disk and return the file name.

    Save the html file using the same name but with extension '.html'
    Expecting the first line to be the column headers, which are  no, page, id, title, link, src
    Hide the columns specified in the given IGNORE_COLUMNS LIST. The data in these columns are still being used to form the web link tag <a href=...>
    """
    global HEAD_STRING

    title_string = f'<h2>{title}</h2>'     
    html_string = ('<html>\n'
                    f'{HEAD_STRING}\n'
                    '<body>'
                        f'\n\t{title_string}\n'
                        f'{description_section}\n\n'
                        f'{statistics_section}\n\n'
                        f'{main_section}\n\n'                      
                        f'{photos_section}\n\n'                      
                        f'{other_list_section}\n\n'
                        f'{FLOATING_BACK_2_TOP_BUTTON}\n\n'
                        f'{SCRIPT_STRING}\n'
                    f'\n\t</body> </html>')
        
    with open(html_file_name, 'wb') as htmlfile:
        htmlfile.write(html_string.encode('utf-16'))

#--------------------------------------------------------------- 
def write_html_page(csv_file_name, csv_file_type, output_lists, 
                    description_dict= {}, 
                    statistics_info = None, # this could be a dictionary or a multi-dim list
                    page_title = '', 
                    photos_html_string = '',  
                    use_local_thumbnails=True, 
                    ignore_columns=[], 
                    headline_tag='h4'):
    """ Write given ingredients to a html file, with this template:
        - a title in <h2>
        - a description table with a <h4> description headline
        - optional: a statistics table with a <h4> description headline 
        - a main table from the csv file
        - if csv type is of type photos_public, use the given photos_html_string instead of the csv file.
    """
    main_table_width = TABLE_WIDTHS[csv_file_type.name] 

    description_html_string, statistics_html_string, main_html_string = '', '', ''
    html_file_name = os.path.splitext(csv_file_name)[0] + '.html'

    #  convert description  dictionary  to html table with a description headline 
    if description_dict:
        description_html_string = dictionary_to_html_table(description_dict, table_id = 'description', headline_text = "Description", 
                                                        start_indent = 1, headline_tag = headline_tag, headline_id = 'desc_headline')
    statistics_html_string = ''
    if type(statistics_info) is dict:
        statistics_html_string = dictionary_to_html_table(statistics_info, table_id = 'overview', headline_text = "Overview", 
                                                            start_indent = 1, headline_tag = headline_tag, headline_id = 'overview_headline')
    elif type(statistics_info) is list: #  and len(statistics_info)> 0:
        statistics_html_string = list_to_html_table(statistics_info, table_id = 'overview', headline_text = 'Overview', 
                                                    table_style= f'width:{main_table_width}', start_indent = 1, headline_tag=headline_tag, headline_id = 'overview_headline')

    if csv_file_type == apiless.CSV_type.photos_public:
        # unlike other csv types, photo type has multiple photo tables, so we processed them beforehand and passed here the single, combined html string of all photos tables 
        main_html_string = photos_html_string
    else:
        # convert a csv file to a html table string and a description headline
        main_html_string = CSV_list_to_HTML_table(csv_file_name, csv_file_type, output_lists, use_local_thumbnails = use_local_thumbnails,  
                                                  ignore_columns = ignore_columns, headline_tag = headline_tag )

    # assemble all sections into the result html page
    write_sections_to_html_page( html_file_name, csv_file_type,
                                 title = page_title,
                                 description_section = description_html_string, 
                                 statistics_section = statistics_html_string,
                                 main_section = main_html_string)
    return html_file_name
 
#--------------------------------------------------------------- 


def CSV_photos_list_to_HTML_table(csv_file_name, csv_type, output_lists, use_local_thumbnails = True, ignore_columns = None, start_indent = 1, headline_tag = 'h4'):
    """ Given a csv file containing a list of photos, return a html string containing a description headline and the photos html table.

    - we use the csv_type.name as the base text to construct table id, headline id and headline text
      table id = csv_type.name
      headline id = csv_type.name_headline
      headline text = TABLE_CAPTION["csv_type.name"] (# of photo)
      sample of headline string: <h4 id="unlisted_photos_header">Unlisted Photos (1) &nbsp;&nbsp; &#8681;</h4>
    - We hide the columns specified in the given IGNORE_COLUMNS LIST. (The data in these columns are still being used to form the web link tag <a href=...>
    """
    global TABLE_WIDTHS, TABLE_CAPTION

    tab1 = '\t'* start_indent
    tab2 = '\n' + tab1 + '\t'
    tab3 = tab2 + '\t'
    tab4 = tab3 + '\t'
    tab5 = tab4 + '\t'
    tab6 = tab5 + '\t'
    tab7 = tab6 + '\t'   
    tab7 = tab6 + '\t'
    tab8 = tab7 + '\t'   

    if ignore_columns is None:
        ignore_columns = []

    CUSTOMED_COLUMN_WIDTHS = """
        <colgroup>
		    <col style="width:4%">    
		    <col style="width:15%">
		    <col span= "5" style="width:6%" >
		    <col style="width:5%" >
		    <col style="width:8%" >
		    <col style="width:15%">	
		    <col style="width:23%">				
	    </colgroup> """

# file name and extension check
    file_path, file_extension = os.path.splitext(csv_file_name)
    if file_extension != ".csv":
        return None

    html_file = file_path + '.html'
    avatars_folder    = os.path.basename(os.path.normpath(output_lists.avatars_dir))
    thumbnails_folder = os.path.basename(os.path.normpath(output_lists.thumbnails_dir))
    table_width = TABLE_WIDTHS[f'{csv_type.name}'] 

    with open(csv_file_name, newline='', encoding='utf-16') as csvfile:
        reader = csv.DictReader(row.replace('\0', '') for row in csvfile)
        headers = reader.fieldnames
        ignore_columns_count = 0
        header_string = f'{tab2}<thead>{tab3}<tr>'

        for i, header in enumerate(reader.fieldnames):
            if header in ignore_columns:
                ignore_columns_count += 1
                continue  
            # break long word(s) so that we can minimize columns widths
            if   header == 'Comments'       : header = 'Com-<br>ments'
            elif header == 'Highest Pulse'  : header = 'Highest<br>Pulse'    
            elif header == 'Galleries'      : header = 'Gal-<br>leries'    
            header_string += f'''{tab4}<th>{header}</th>'''
  
        header_string += f'{tab3}</tr>{tab2}</thead>'

       # create rows for html table 
        rows  = list(reader)
        rows_count = len(rows)
        row_string = f'{tab2}<tbody>'       
        for i, row in enumerate(rows):
            utils.update_progress(i / rows_count, f'    - Writing items to html {i}/{rows_count} ...')  
            row_string += f'{tab3}<tr>'

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
                        row_string += f'\t\t\t\t<td><div><div><a/></div><div></a></div></div></td> \n' 
                    else:
                        photo_link =  row['Href']                 
                        row_string += f'{tab4}<td><div><div style="width: 40%; float:left; margin-right:10px;">{tab7}<a href="{photo_link}" target="_blank">'
                        row_string += f'{tab8}<img class="photo" src={photo_thumbnail}></a></div>'
                        row_string += f'{tab6}<div><a href="{photo_link}" target="_blank">{text}</a></div></div></td>'
 
                elif  col_header == 'Category':
                    row_string += f'{tab4}<td class="alignLeft">{text}</td>' 

                elif  col_header == 'Tags':
                    row_string += f'{tab4}<td class="alignLeft">{text}</td>' 
                
                elif  col_header == 'Featured In Galleries' and text != '':
                    # a gallery link has this format: https://500px.com/[photographer_name]/galleries/[gallery_name]
                    galleries = text.split(',')
                    if len(galleries) == 0:
                           row_string += f'{tab4}<td></td>'
                    else:
                        row_string += f'{tab4}<td>'
                        for k, gallery in enumerate(galleries):
                            gallery_name = gallery[gallery.rfind('/') + 1:]    
                            row_string += f'{tab4}<a href="{gallery}" target="_blank">{gallery_name}</a>'
                            if k < len(galleries) -1:
                                row_string += ','                    
                        row_string += f'\t\t</td>'  
                        
                else: 
                    # write empty string if text == 0
                    alt_text = '' if text == '0' else text
                    row_string += f'{tab4}<td>{alt_text}</td>' 

            row_string += f'{tab3}</tr>\n'
        row_string += f'{tab2}</tbody>\n'

        # create the table headline with down-arrow symbol at the end: ex: 	<h4 id="unlisted_photos_header">Unlisted Photos (1) &nbsp;&nbsp; &#8681;</h4>	
        # we're gonna hide the un-important table on page load, so we won't need to show the down-arrow on the headlines of the main tables:
        direction_arrow = '' if csv_type.name is 'photos_public' else '&nbsp;&nbsp; &#8681;'
        headline_text = f'{TABLE_CAPTION[csv_type.name]}  ({rows_count})'
        headline_id = f'{csv_type.name}_headline'
        headline_html_string = f'{tab1}<{headline_tag} id="{headline_id}">{headline_text} {direction_arrow}</{headline_tag}>'
        
        # table_id_string = f'id="{table_id}"' if table_id != '' else ''
        table_string = ( f'{tab1}<table id="{csv_type.name}" class="main" style="width:{table_width}">'
                             #f'{tab2}<caption>{table_caption} ({rows_count})</caption>'
                             f'{tab3}{CUSTOMED_COLUMN_WIDTHS}'
                             f'{tab3}{header_string}' 
                             f'{tab3}{row_string}' 
                          f'{tab2}</table>' )
        
        utils.update_progress(1, f'    - Writing items to html {rows_count}/{rows_count} ...')  
    return  headline_html_string + '\n' + table_string

#--------------------------------------------------------------- 
def CSV_list_to_HTML_table(csv_file_name, csv_file_type, output_lists, use_local_thumbnails = True, ignore_columns = None, 
                encoding = 'utf-16', column_to_sort = 'No', start_indent = 1, headline_tag='h4'):
    """Given a csv file containing a list of items, return a html string containing a description headline and a html table representing items.

     - we use the csv_type.name as the base text to construct table id, headline id and headline text
       table id = csv_type.name
       headline id = [csv_type.name]_headline
       headline text = TABLE_CAPTION["csv_type.name"] (# of photo)
       sample of headline string: <h4 id="followers_headline">Followers (1234)</h4>
     - We hide the columns specified in the given IGNORE_COLUMNS LIST. 
     - Support various types of csv files, which are lists of:
       notifications, unique_users, like_actors, followers, followings, all_users, reciprocal, not_follow, following
     - Return saved html file name (the same name as csv file but with extension '.html'   )
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
    tab8 = tab7 + '\t'
    tab9 = tab8 + '\t'
    
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

    with open(csv_file_name, newline='', encoding=encoding) as csvfile:
        reader = csv.DictReader(row.replace('\0', '') for row in csvfile)
        headers = reader.fieldnames
        if len(headers) < 3:
            printR(f'   File {csv_file_name} is in wrong format!')
            return ''
  
        # write headers and assign appropriate sort method for each columns   
        # # each header cell has 2 parts: the left div for the header name, the right div for sort direction arrows     
        ignore_columns_count = 0
        header_string = f'{tab3}<thead>{tab4}<tr>'
        for i, header in enumerate(reader.fieldnames):
            if header in ignore_columns:
                ignore_columns_count += 1
                continue
            
            col_width = f'width="{COL_WIDTHS[header]}"'
            header_string += f'''{tab5}<th {col_width}><div class="hdr_text">{header}</div></th>'''
        header_string += '</tr></thead>' 

        # create rows for html table 
        rows  = list(reader)
        rows_count = len(rows)
        row_string = f'{tab3}<tbody>'       
        for i, row in enumerate(rows):
            utils.update_progress(i / rows_count, f'    - Writing items to html {i}/{rows_count} ...')  
            row_string += f'{tab4}<tr>'
            
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
                    row_string += f'{tab5}<td><div><div style="width: 30%; float:left;">{tab8}<a href="{user_home_page}" target="_blank">'
                    if use_local_thumbnails:
                        user_avatar =f"{avatars_folder}/{row['Avatar Local']}"
                    else:
                        user_avatar = row['Avatar Href']

                    row_string += f'{tab9}<img src={user_avatar}></a></div>'
                    row_string += f'{tab7}<div><a href="{user_home_page}" target="_blank">{user_name}</a></div></div></td>'
 
                # In Photo Tile column, show photo thumbnail and photo title with <a href> link
                elif  col_header == 'Photo Title': 
                    photo_thumbnail = f"{thumbnails_folder}/{row['Photo Thumbnail Local']}"  if use_local_thumbnails else  row['Photo Thumbnail Href']
                    # if photo thumbnail is empty, write an empty divs to keep the same layout 
                    if (use_local_thumbnails and not row['Photo Thumbnail Local'].strip()) or (not use_local_thumbnails and not row['Photo Thumbnail Href'].strip()) :
                        row_string += f'{tab5}<td><div><div><a/></div><div><a/></div></div></td>'
                    else:
                        photo_link =  row['Photo Link']                 
                        row_string += f'{tab5}<td><div><div style="width: 30%; float:left;">{tab9}<a href="{photo_link}" target="_blank">'
                        row_string += f'{tab9}<img class="photo" src={photo_thumbnail}></a></div>'
                        row_string += f'{tab7}<div><a href="{photo_link}" target="_blank">{text}</a></div></div></td>'

                elif  col_header == 'Relationship':
                    color_class_name = text.lower().replace(' ', '_')
                    if csv_file_type.name == 'reciprocal' or csv_file_type.name == 'not_follow' or csv_file_type.name == 'following' or \
                       csv_file_type.name == 'all_users' or csv_file_type.name == 'unique_users' or csv_file_type.name == 'all_unique_users': 
                        row_string += f'{tab5}<td class="alignLeft {color_class_name}" >{text}</td>'    
                    elif csv_file_type.name == 'notifications' or csv_file_type.name == 'like_actors':
                        if text == 'Following': 
                            row_string += f'{tab5}<td class="alignLeft following_raw">{text}</td>'  # green cell for following users from notification                   
                        elif text == 'Not Follow':  
                            row_string += f'{tab5}<td class="alignLeft">{text}</td>'                # default background color (white)
                        else:
                            row_string += f'{tab5}<td></td>'                                        # empty td cell     
                    else:
                        row_string += f'{tab5}<td>{text}</td>'                                             
               
                elif  col_header == 'Content': 
                     row_string += f'{tab5}<td class="alignCenter">{text}</td>'

                else:                            
                     row_string += f'{tab5}<td class="alignRight">{text}</td>'

            row_string += '</tr>'
        row_string += f'{tab3}</tbody>'

        # create the main table headline ex: 	<h4 id="followers_headline">Followers (1234) </h4>	
        headline_text = f'{TABLE_CAPTION[csv_file_type.name]} ({rows_count})'
        headline_id = f'{csv_file_type.name}_headline'
        headline_html_string = f'{tab1}<{headline_tag} id="{headline_id}">{headline_text}</{headline_tag}>'

        table_string = (f'{tab1}<div class="float_left" style="width:{main_table_width}">'
                            f'{tab2}<table id="{table_id}">'
                                f'{tab3}{header_string}'
                                f'{tab3}{row_string}'
                            f'{tab2}</table>{tab1}</div>')
        
        utils.update_progress(1, f'    - Writing items to html {rows_count}/{rows_count} ...')  
    return  headline_html_string  + table_string

#---------------------------------------------------------------  
def dict_to_html(info_dict, table_id = '', title = ''):
    """ write user statistic object stats to an html file. """
    
    title_string = f'<h2>{title}</h2>\n'
    summary_html_string = dictionary_to_html_table(info_dict, table_id = table_id, start_indent = 1 )
 
    return f'''
<html>
    {HEAD_STRING}
    <body>
       {title_string}
       {summary_html_string} 
    </body>
</html>
'''
#---------------------------------------------------------------
def create_main_html_page(html_file_name, user_name):
    """ Generate a main html page that hosts all the result html pages"""

    html_string = f"""<!DOCTYPE html>
<html lang="en">
<head>
	<title>500pxAPI-less_{user_name}'s snapshot</title>                  
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0">	
	<link rel="stylesheet" media="screen, projection" href="css/menu.css">		
	<link rel="stylesheet" type="text/css" charset="UTF-8" href = "css/styles.css" />
	<link rel="stylesheet" type="text/css" charset="UTF-8" href="DataTables/DataTables-1.10.21/css/jquery.dataTables.min.css"/>
	<link rel="stylesheet" type="text/css" charset="UTF-8" href="DataTables/FixedHeader-3.1.7/css/fixedHeader.dataTables.min.css"/>	
</head>

<body>
	<!-- container -->
	<div class="container">
		
		<!-- page-header -->
		<div class="page-header">
			<h1>500pxAPI-less - {user_name}'s snapshot</h1>
		</div>
		
		<span class="menu-trigger">MENU</span>
		
		<!-- nav-menu -->
		<div class="nav-menu">
			<ul class="clearfix">
			    <li id="user_summary" >
					<a class="tooltip"  href="#">Summary 
						<span class="tooltiptext">User summary</span> </a></li>
				<li id="photos_public">
					<a class="tooltip"  href="#">Photos
						<span class="tooltiptext">Photos and statistics</span> </a></li>				
				<li id="followers" class="users_group">
					<a  class="tooltip" href="#">Followers  
						<span class="tooltiptext">Users who follow you</span> </a></li>				
				<li id="followings" class="users_group">
					<a class="tooltip" href="#">Followings
						<span class="tooltiptext">Users whom you are following</span> </a></li>
				<li id="reciprocal" class="users_group">
					<a class="tooltip"  href="#">Reciporcal
						<span class="tooltiptext">Reciprocal Following: you and these users follow each other</span> </a></li>						
				<li id="not_follow" class="users_group">
					<a class="tooltip"  href="#">Not Follow					 
						<span class="tooltiptext">Your followers whom you do not follow back</span> </a></li>						
				<li id="following" class="users_group">
					<a class="tooltip"  href="#">Following
						<span class="tooltiptext">You are following these users without being followed back</span> </a></li>	
				<li id="all_users" class="users_group">
					<a class="tooltip"  href="#">All Users
						<span class="tooltiptext">Followers and Followings with following statuses</span> </a></li>	
				<li id="like_actors">
					<a class="tooltip"  href="#">Likers
						<span class="tooltiptext">Users who liked a photo of yours</span> </a></li>	
				<li id="notifications" class="notifications_group">
					<a class="tooltip"  href="#">Last Notifications
						<span class="tooltiptext">Last n notifications</span> </a></li>				
				<li id="unique_users" class="notifications_group">
					<a class="tooltip"  href="#">Last Active Users
						<span class="tooltiptext">Unique users in n last notifications</span> </a></li>
				<li id="all_notifications" class="notifications_group">
					<a class="tooltip"  href="#">All Notifications
						<span class="tooltiptext">All notifications that you have extracted over times</span> </a></li>				
				<li id="all_unique_users" class="notifications_group">
					<a class="tooltip"  href="#">All Active Users
						<span class="tooltiptext">Unique users in all recorded notifications</span> </a></li>						
			</ul>
		</div>
		<!-- main-content -->
		<div id= "div_main_content" class="main-content">
		</div>		
	</div>	
	<script type="text/javascript" charset="utf8" src="javascripts/jquery-3.3.1.min.js"></script>
	<script type="text/javascript" charset="utf8" src="javascripts/dynamic_menu_{user_name}.js"></script>
	<script type="text/javascript" charset="utf8" src="DataTables/datatables.js"></script>		
	<script type="text/javascript" charset="utf8" src="DataTables/DataTables-1.10.21/js/jquery.dataTables.min.js"></script>		
	<!--script type="text/javascript" charset="utf8" src="DataTables/FixedHeader-3.1.7/js/dataTables.fixedHeader.min.js"></script-->				
</body></html>
    """
    with open(html_file_name, 'wb') as htmlfile:
        htmlfile.write(html_string.encode('utf-8'))
