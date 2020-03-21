# database.py
# module used in 500px_apiless.py to interact with sqlite database

import sqlite3

def create_if_not_exists_photos_table(connection_cursor):
    """Create the photos table if it does not exist
       Photo table has 15 columns, with photo id being the primary key
       0   1            2   3      4     5               6                7            8            9               10         11             12      13           14        15
       no  author_name  id  title  href  thumbnail_href  thumbnail_local  views_count  votes_count  comments_count  galleries  highest_pulse  rating  upload_date  category, tag
       """
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
                                    galleries       text, 
                                    highest_pulse   real, 
                                    rating          real, 
                                    upload_date     text, 
                                    category        text, 
                                    tag text )""")

#---------------------------------------------------------------
def create_if_not_exists_followers_and_followings_tables(connection_cursor):
    """Create the followers and followings table if they do not exist
       Followers and Followings table has 7 columns, with user id being the primary key
       0   1             2            3             4          5   6          7  
       no  avatar_href  avatar_local  display_name  user_name  id  followers  status  
       """
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

#---------------------------------------------------------------
def create_if_not_exists_notifications_tables(connection_cursor):
    """Create the notifications table if it does not exist
       Notification table has 13 columns
       0   1             2            3             4          5   6        7                     8                      9      10          11      12
       no  avatar_href  avatar_local  display_name  user_name  id  content  photo_thumbnail_href  photo_thumbnail_local  title  time_stamp  status, photo_link  
       """
    if connection_cursor is not None: 
        connection_cursor.execute("""CREATE TABLE IF NOT EXISTS notifications(
                                     no integer, 
                                     avatar_href text, 
                                     avatar_local text, 
                                     display_name text, 
                                     user_name text,
                                     id integer, 
                                     content text, 
                                     photo_thumbnail_href text, 
                                     photo_thumbnail_local text, 
                                     title text, 
                                     time_stamp text, 
                                     status text, 
                                     photo_link text,
                                     PRIMARY KEY (user_name, content, photo_link))""")
   #note: time_stamp is taken out from primary key set due to it unreliability. After 450 notifications or so, the 500px server stops updating it.
#---------------------------------------------------------------
def insert_photo_to_photo_table(conn, photo_info):
    """
    """
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
                                            galleries, 
                                            highest_pulse, 
                                            rating, 
                                            upload_date, 
                                            category, tag)
              VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) '''
    cur = conn.cursor()
    cur.execute(sql, photo_info)
    return cur.lastrowid


#---------------------------------------------------------------
def insert_user_to_table(conn, user_info, table_name):
    """
    """
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
    cur = conn.cursor()
    cur.execute(sql, user_info)
    return cur.lastrowid
#---------------------------------------------------------------
def insert_notification_to_table(conn, notification_info):
    """
    """
    sql = '''INSERT OR IGNORE INTO notifications(
                                            no, 
                                            avatar_href, 
                                            avatar_local, 
                                            display_name, 
                                            user_name, 
                                            id, 
                                            content, 
                                            photo_thumbnail_href, 
                                            photo_thumbnail_local, 
                                            title, 
                                            time_stamp, 
                                            status, 
                                            photo_link)
              VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) '''
    cur = conn.cursor()
    cur.execute(sql, notification_info)
    return cur.lastrowid
