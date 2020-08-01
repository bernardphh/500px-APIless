# database.py
# module used in 500px_apiless.py to interact with sqlite database

import sqlite3
import os
import common.apiless as apiless
import common.config as config
import common.utils as utils
from common.utils import print_and_log, printB, printC, printG, printR, printY

def create_if_not_exists_photos_table(db_connection):
    """Create the photos table if it does not exist
       Photo table has 15 columns, with photo id being the primary key
       0   1            2   3      4     5               6                7            8            9               10               11             12      13           14        15         16
       no  author_name  id  title  href  thumbnail_href  thumbnail_local  views_count  votes_count  comments_count  galleries_count  highest_pulse  rating  upload_date  category, galleries, tag
       """
    connection_cursor = db_connection.cursor()
    if connection_cursor is not None: 
        connection_cursor.execute("""CREATE TABLE IF NOT EXISTS photos(
                                    no integer, 
                                    author_name text,
                                    id integer PRIMARY KEY,
                                    title text, 
                                    href text, 
                                    thumbnail_href  text, 
                                    thumbnail_local text,
                                    views_count     integer, 
                                    votes_count     integer, 
                                    comments_count  integer,
                                    galleries_count integer, 
                                    highest_pulse   real, 
                                    rating          real, 
                                    upload_date     text, 
                                    category        text, 
                                    galleries       text, 
                                    tag text )""")
    db_connection.commit()
    
#---------------------------------------------------------------
def create_if_not_exists_followers_and_followings_tables(db_connection):
    """Create the followers and followings table if they do not exist
       Followers and Followings table has 7 columns, with user id being the primary key
       0   1             2            3             4          5   6          7  
       no  avatar_href  avatar_local  display_name  user_name  id  followers  status  
       """
    connection_cursor = db_connection.cursor() 
    table_names = ['followers', 'followings']
    if connection_cursor is not None: 
        for name in table_names:
            connection_cursor.execute(f"""CREATE TABLE IF NOT EXISTS {name}(
                                        no integer, 
                                        avatar_href text, 
                                        avatar_local text, 
                                        display_name text,
                                        user_name text PRIMARY KEY,
                                        id integer, 
                                        followers text, 
                                        status integer )""")
    db_connection.commit()
    
#---------------------------------------------------------------
def create_if_not_exists_notifications_tables(db_connection):
    """Create the notifications table if it does not exist
       Notification table has 13 columns
       0   1             2            3             4          5   6        7                     8                      9      10          11      12
       no  avatar_href  avatar_local  display_name  user_name  id  content  photo_thumbnail_href  photo_thumbnail_local  title  time_stamp  status, photo_link  
       """

    connection_cursor = db_connection.cursor()
    if connection_cursor is not None: 
        connection_cursor.execute('''CREATE TABLE IF NOT EXISTS notifications(
                                     "No" integer, 
                                     "Avatar Href" text, 
                                     "Avatar Local" text, 
                                     "Display Name" text, 
                                     "User Name" text,
                                     "ID" integer, 
                                     "Content" text, 
                                     "Photo Thumbnail Href" text, 
                                     "Photo Thumbnail Local" text, 
                                     "Photo Title" text, 
                                     "Time Stamp" text, 
                                     "Relationship" text, 
                                     "Photo Link" text,
                                     PRIMARY KEY ("User Name", "Content", "Photo Link"))''')
    db_connection.commit()
    # Jun 16 2020: 500px masks out the exact date. The absolute date that we are used to have now became relative (such as 'a year ago'). 
    # To keep the integrity of the database, we are force to take the Time stamp out of primary keys.

#---------------------------------------------------------------
def insert_photo_to_photo_table(db_connection, photo_info):
    """    """
    connection_cursor = db_connection.cursor()
    sql = f'''INSERT OR IGNORE INTO photos(
                                            no, 
                                            author_name, 
                                            id, 
                                            title, 
                                            href, 
                                            thumbnail_href, 
                                            thumbnail_local, 
                                            views_count, 
                                            votes_count,  
                                            comments_count, 
                                            galleries_count, 
                                            highest_pulse, 
                                            rating, 
                                            upload_date, 
                                            category, 
                                            galleries, 
                                            tag)
              VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?) '''
    connection_cursor.execute(sql, photo_info)
    db_connection.commit()
    return connection_cursor.lastrowid

#---------------------------------------------------------------
def insert_user_to_table(db_connection, user_info, table_name):
    """     """
    
    connection_cursor = db_connection.cursor()
    sql = f'''INSERT OR IGNORE INTO {table_name}(
                                            no, 
                                            avatar_href, 
                                            avatar_local, 
                                            display_name, 
                                            user_name, 
                                            id, 
                                            followers, 
                                            status)
              VALUES(?, ?, ?, ?, ?, ?, ?, ?) '''
    connection_cursor.execute(sql, user_info)
    db_connection.commit()
    return connection_cursor.lastrowid
#---------------------------------------------------------------
def insert_notification_to_table(db_connection, notification_info):
    """     """    
    connection_cursor = db_connection.cursor()
    sql = '''INSERT OR IGNORE INTO notifications(
                                            No, 
                                            "Avatar Href", 
                                            "Avatar Local", 
                                            "Display Name", 
                                            "User Name", 
                                            "ID", 
                                            "Content", 
                                            "Photo Thumbnail Href", 
                                            "Photo Thumbnail Local", 
                                            "Photo Title", 
                                            "Time Stamp", 
                                            "Relationship", 
                                            "Photo Link")
              VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) '''
    connection_cursor.execute(sql, notification_info)
    db_connection.commit()
    return connection_cursor.lastrowid

#---------------------------------------------------------------
def insert_all_notification_csv_files_to_database(db_full_file_name, csv_dir, user_name):
    """ Find all notification csv files on disk, at the given folder. Read and insert them into notification table in the database.
        Duplications are avoided by the primary keys: same actor, same photo and same content of notification"""

    # connect to database (create it if it does not exist)
    if not os.path.isfile(db_full_file_name):
        file_name = db_full_file_name.split('\\')[-1]
        print_and_log(f"   Create local database {file_name} ...")
    db_connection = sqlite3.connect(db_full_file_name)
    total_changed_sofar = 0
    create_if_not_exists_notifications_tables(db_connection)
    csv_files = utils.get_all_notifications_csv_files(csv_dir, user_name)
    print_and_log(f"   Updating database with notifications files:")
    for file in csv_files:
        file_name = file.split('\\')[-1]
        print_and_log(f"   - {file_name}")
        df = utils.CSV_file_to_dataframe(file)
        data_list = df.values.tolist()
        for item in data_list:
            insert_notification_to_table(db_connection, tuple(item))
        db_connection.commit()
        recent_changes = db_connection.total_changes - total_changed_sofar
        printG(f'    Records changed: {str(recent_changes)}')
        total_changed_sofar = db_connection.total_changes
    db_connection.close()
    return total_changed_sofar

#---------------------------------------------------------------
def insert_latest_csv_data_to_database(db_connection, csv_dir, records_changed_sofar, user_name, csv_file_type):
    """ Update the local database with the latest csv file of the given type"""

    recent_changes, changes_sofar = 0, 0
    # find the latest csv file on disk
    csv_file = utils.get_latest_file(csv_dir, user_name, csv_file_type, file_extenstion = 'csv')
    if csv_file != '':
        df = utils.CSV_file_to_dataframe(csv_file)
        data_list = df.values.tolist()
        for item in data_list:
            if csv_file_type == apiless.CSV_type.photos_public:
                insert_photo_to_photo_table(db_connection, tuple(item))
            elif csv_file_type == apiless.CSV_type.followers or csv_file_type == apiless.CSV_type.followings:
                insert_user_to_table(db_connection, tuple(item), csv_file_type.name)
            elif csv_file_type == apiless.CSV_type.notifications:
                insert_notification_to_table(db_connection, tuple(item))
        db_connection.commit()
        recent_changes = db_connection.total_changes - records_changed_sofar
        printG(f'     Records changed: {str(recent_changes)}')
        changes_sofar = db_connection.total_changes
    return changes_sofar, recent_changes, csv_file

#---------------------------------------------------------------

