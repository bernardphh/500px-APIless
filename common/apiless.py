# apiless.py
# module containing all the classes used in 500px_apiless.py

import common.config as config
from enum import Enum
import os
from os import listdir
from os.path import isfile, join
import pandas as pd

class User:
    """ Represents a user. It could be the main user(ie. me, the logged in user), or a target user whose photos we want to auto-like, or a user who had interaction with me(liked, commented, followed)
       
        - AVATAR_LOCAL : The file name of the avatar image file saved to disk
        - FOLLOWING_STATUS is n/a for the main user, if not, it could be either "following" or "not follow"
    """
    def __init__(self, order = '', avatar_href = '', avatar_local = '', display_name = '', user_name = '', id = '0', number_of_followers = '0', following_status = ''):
        self.order = order
        self.avatar_href = avatar_href
        self.avatar_local = avatar_local
        self.display_name = display_name
        self.user_name = user_name
        self.id = id
        self.number_of_followers = number_of_followers
        self.following_status = following_status

    def __repr__(self):
        return f'{self.order},{self.avatar_href},{self.avatar_local},{self.display_name},{self.user_name},{self.id},{self.number_of_followers},{self.following_status}'
      
#--------------------------------------------------
class PhotoStats:
    """ Photo statistics info.
        - TAGS is the comma-separated strings containing all tags set on the photo    
    """
    def __init__(self,  upload_date = '', views_count=0, votes_count=0, collections_count=0, comments_count=0, highest_pulse=0, rating=0, category='', tags='' ):
        self.upload_date  = upload_date 
        self.views_count = views_count
        self.votes_count = votes_count 
        self.collections_count = collections_count
        self.comments_count = comments_count 
        self.highest_pulse = highest_pulse
        self.rating = rating
        self.category = category
        self.tags = tags

    def __repr__(self):
        return f'{self.upload_date},{self.views_count},{self.votes_count},{self.collections_count},{self.comments_count},{self.highest_pulse},{self.rating},{self.category},{self.tags}'
  
#--------------------------------------------------
class Photo:
    """ Represent a photo info.

    - ORDER is the ascending number with the latest uploaded photo being 1
    - STATS is an object of type PhotoStats()
    - THUMBNAIL_HREF is the link to the photo thumbnail
    - THUMBNAIL_LOCAL is file name of the thumbnail image, dowmloaded from the link thumbnail_href and saved on disk 
    - GALLERIES is a comma separated string containing the links to all the galleries that featured the photo
    """
    def __init__(self, author_name= ' ', order= ' ', id= ' ', title= ' ', href= ' ', thumbnail_href= ' ', thumbnail_local= ' ', category= ' ', galleries= ' ', stats= PhotoStats()):
        self.author_name = author_name
        self.order = order  
        self.id = id
        self.title = title
        self.href = href
        self.thumbnail_href = thumbnail_href        
        self.thumbnail_local = thumbnail_local    
        self.category = category
        self.galleries = galleries
        self.stats = stats

    def __iter__(self):
        yield (self.author_name, self.order, self.id, self.title, self.href, self.thumbnail_href, self.thumbnail_local, delf.category, self.galleries, self.stats )
    def __repr__(self):
        return f'{self.author_name},{self.order},{self.id},{self.title},{self.href},{self.thumbnail_href},{self.thumbnail_local},{self.category},{self.galleries},{self.stats}'
    
    def to_dict(self):
        #No,Author Name,ID,Photo Title,Href,Thumbnail Href,Thumbnail Local,Views,Likes,Comments,Galleries,Highest Pulse,Rating,Date,Category,Featured In Galleries,Tags
        return {
            'No': self.order,
            'Author Name': self.author_name,
            'ID': self.id,
            'Photo Title':self.title,
            'Href':self.href,
            'Thumbnail Href':self.thumbnail_href,
            'Thumbnail Local': self.thumbnail_local,
            'Views': self.stats.views_count,
            'Likes': self.stats.votes_count,
            'Comments': self.stats.comments_count,
            'Galleries': self.stats.collections_count,
            'Highest Pulse': self.stats.highest_pulse,
            'Rating': self.stats.rating,
            'Date': self.stats.upload_date,
            'Category': self.category,
            'Featured In Galleries': self.galleries,
            'Tags': self.stats.tags
        }   


 
#--------------------------------------------------
class Notification:
    """ Represent a notification object.
        
        - ACTOR is an object of type user(), on which we will make use only 3 attributes: avatar_href, display_name, username
        - THE_PHOTO is object of type photo(), on which we will make use only 3 attributes: photo_thumb, photo_link, photo_title
        - CONTENT is the type of notification, which is one of the following text 'liked', 'followed', 'comment' or 'add to gallery'
        - TIMESTAMP is the time when the notification happened 
        - STATUS is the following status of the main user toward the actor, ie. 'Following'  or 'Not follow'
        """
    def __init__(self, order, actor = None, the_photo = None,  content = '', timestamp = '', status = ''): 
        self.order = order      
        self.actor = User() if actor is None else actor       
        self.the_photo = Photo() if the_photo is None else the_photo 
        self.content = content
        self.timestamp = timestamp
        self.status = status

    def __repr__(self):
        return f'{self.order},{self.actor},{self.the_photo},{self.content},{self.the_photo},{self.timestamp},{self.status}'

    def to_dict(self):
        return {
            'No': self.order,
            'Avatar Href': self.actor.avatar_href,
            'Avatar Local': self.actor.avatar_local,
            'Display Name':self.actor.display_name,
            'User Name':self.actor.user_name,
            'ID':self.actor.id,
            'Content': self.content,
            'Photo Thumbnail Href': self.the_photo.thumbnail_href,
            'Photo Thumbnail Local': self.the_photo.thumbnail_local,
            'Photo Title': self.the_photo.title,
            'Time Stamp': self.timestamp,
            'Relationship': self.status,
            'Photo Link': self.the_photo.href
        }
 
    def to_notification_data(self):
        ## No, Avatar Href, Avatar Local, Display Name, User Name, ID, Content, Photo Thumbnail Href, Photo Thumbnail Local, Photo Title, Time Stamp, Relationship, Photo Link
        notif_array_item = [f'{self.order}', f'{self.the_photo.avatar_href}', f'{self.the_photo.avatar_local}', f'{self.actor.display_name}', f'{self.actor.user_name}', 
                            f'{self.actor.id}', f'{self.content}', f'{self.the_photo.thumbnail_href}', f'{self.the_photo.thumbnail_local}', f'{self.the_photo.title}', 
                            f'{self.timestamp}', f'{self.status}', f'{self.the_photo.href}']
        return notif_array_item

#--------------------------------------------------
class UserStats:
    """ Represent basic statistics of a user."""
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

    def to_dict(self):
        return {
            'Display name': self.display_name,
            'Username': self.user_name,
            'ID': self.id,
            'Location':self.location,
            'Activities':self.affection_note,
            'Following note': self.following_note,
            'Affecction':self.affections_count,
            'Views': self.views_count,
            'Followers': self.followers_count,
            'Followings': self.followings_count,
            'Photo count': self.photos_count,
            'Galleries count': self.galleries_count,
            'Registration date': self.registration_date,
            'Last upload date': self.last_upload_date,
            'Status': self.user_status
        }
#--------------------------------------------------
class UserInputs():
    """ Represent the input entered by the user. 
    
    Choice is an character string representing available options: [1-13] or 'r','q' . The default value is zero which means commnand line arguments will not be used 
    """

    def __init__(self, use_command_line_args = False, choice='0', user_name='', password='', target_user_name='', photo_href='', gallery_href='', gallery_name='',
                 number_of_photos_to_be_liked=2 , index_of_start_photo=1, number_of_notifications=200, time_interval=3, index_of_start_user=1, number_of_users=100, csv_file='', db_path='', index_of_start_notification=0):
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
        self.db_path                        = '' 
        self.index_of_start_notification    = index_of_start_notification
        self.main_html_page                 = '' 
        self.js_file_name                   = ''


    def Reset(self):
        self.use_command_line_args = False
        self.choice                         = '0'
        self.user_name                      = ''
        self.password                       = ''
        self.target_user_name               = ''
        self.photo_href                     = ''
        self.gallery_href                   = ''
        self.gallery_name                   = ''
        self.number_of_photos_to_be_liked   = 2
        self.index_of_start_photo           = 1
        self.number_of_notifications        = 200
        self.time_interval                  = 3
        self.index_of_start_user            = 1
        self.number_of_users                = 100
        self.csv_file                       = ''
        self.db_path                        = ''
        self.index_of_start_notification    = 0
        self.main_html_page                 = ''  
#--------------------------------------------------
class OutputData():
    """ Represent all the output lists and data"""

    def __init__(self, output_dir = '', avatars_dir = '', thumbnails_dir = '', 
                 json_data = None, photos = None, photos_unlisted = None, photos_limit_access = None,
                 notifications = None, unique_notificators = None, 
                 followers_list = None, followings_list = None, like_actioners_list= None,  thumbnails_list=None):
        self.json_data             = [] if json_data           is None else json_data      
        self.photos                = [] if photos              is None else photos      
        self.photos_unlisted       = [] if photos_unlisted     is None else photos_unlisted      
        self.photos_limited_access = [] if photos_limit_access is None else photos_limit_access     
        
        self.notifications         = [] if notifications       is None else notifications      
        self.unique_notificators   = [] if unique_notificators is None else unique_notificators      
        
        self.followers_list        = [] if followers_list      is None else followers_list      
        self.followings_list       = [] if followings_list     is None else followings_list     
        self.like_actioners_list   = [] if like_actioners_list is None else like_actioners_list     
        
        self.stats = UserStats()  
        
        output_dir =  config.OUTPUT_PATH 
        os.makedirs(output_dir, exist_ok = True)
        self.output_dir = output_dir
        
        avatars_dir =  os.path.join(output_dir, 'avatars')
        os.makedirs(avatars_dir, exist_ok = True)
        self.avatars_dir = avatars_dir
        #self.avatars_list = [f for f in os.listdir(avatars_dir) if isfile(join(avatars_dir, f))]
 
        thumbnails_dir =  os.path.join(output_dir, 'thumbnails')
        os.makedirs(thumbnails_dir, exist_ok = True)
        self.thumbnails_dir = thumbnails_dir
        self.thumbnails_list = [f for f in listdir(thumbnails_dir) if isfile(join(thumbnails_dir, f))]
 
    def Reset(self):
        self.json_data = None       
        self.photos = None        
        self.photos_unlisted = None        
        self.photos_limit_access = None        
        self.notifications = None   
        self.unique_notificators = None
        self.followers_list = None  
        self.followings_list = None 
        self.like_actioners_list= None
        self.stats = UserStats() 

#--------------------------------------------------
class CSV_type(Enum):
    """ Enum representing 10 types of output list"""
    not_defined              = 0
    user_summary             = 1
    photos_public            = 2         # accessible everywhere, including on Profile
    photos_unlisted          = 3         # accessible everywhere, except on Profile 
    photos_limited_access    = 4         # only visible to you, unless added to a Gallery

    notifications            = 5         # the last n notification of liked, comment, added to gallery
    all_notifications        = 6         # all recorded notification of liked, comment, added to gallery
    unique_users             = 7         # the last unique users in a notifications list, with the count of their appearances in the list 
    all_unique_users         = 8         # unique users in all recorded notifications, with the count of their appearances in the list 
    like_actors              = 9         # users that liked one specific photos of yours

    followers                = 10        # all your followers, regardless you are following them or not
    followings               = 11        # all your followings (friends), regardless they are following  or not

    all_users                = 12        # combined your followers and your followings
    reciprocal               = 13        # users who follow you and you follow them 
    not_follow               = 14        # list of users that you do not follow, but they are following you
    following                = 15        # list of users that you are following but they do not follow you
    interactor               = 16        # users who interact with you by liking, commenting, featuring your photo, but you and them are not following each other
    