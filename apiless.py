# apiless.py
# module containing all the classes used in 500px_apiless.py

import config
#from enum import Enum
import os
from os import listdir
from os.path import isfile, join


class user:
    """ Represents a user. It could be the main user(ie. me, the logged in user), or a target user whose photos we want to auto-like, or a user who had interaction with me(liked, commented, followed)
       
        - AVATAR_LOCAL : The full file name of the avatar image file, if we decide to save it on disk
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
    
    def to_dict(self):
        return {
            'No': self.order,
            'Avatar Href': self.avatar_href,
            'Avatar Local': self.avatar_local,
            'Display Name': self.display_name,
            'User Name': self.user_name,
            'ID': self.id,
            'Followers': self.number_of_followers,
            'Status': self.following_status
        }
#--------------------------------------------------
class photoStats:
    """ Photo statistics info.
        - TAGS is the comma-separated strings containing all tags set on the photo    
    """
    def __init__(self,  upload_date = '', views_count=0, votes_count=0, collections_count=0, comments_count=0, highest_pulse=0, rating=0, tags='' ):
        self.upload_date  = upload_date 
        self.views_count = views_count
        self.votes_count = votes_count 
        self.collections_count = collections_count
        self.comments_count = comments_count 
        self.highest_pulse = highest_pulse
        self.rating = rating
        self.tags = tags
#--------------------------------------------------
class photo:
    """ Represent a photo info.

    - ORDER is the ascending number with the latest uploaded photo being 1
    - STATS is an object of type photoStats()
    - THUMBNAIL_HREF is the link to the photo thumbnail
    - THUMBNAIL_LOCAL is the full file name of the thumbnail image, dowmloaded from the link thumbnail_href and saved on disk 
    - GALLERIES is a list containing the links to all the galleries that featured the photo
    """
    def __init__(self, author_name= ' ', order= ' ', id= ' ', title= ' ', href= ' ', thumbnail_href= ' ', thumbnail_local= ' ', galleries= ' ', stats= photoStats()):
        self.author_name = author_name
        self.order = order  
        self.id = id
        self.title = title
        self.href = href
        self.thumbnail_href = thumbnail_href        
        self.thumbnail_local = thumbnail_local        
        self.galleries = galleries
        self.stats = stats

    def __iter__(self):
        yield (self.author_name, self.order, self.id, self.title, self.href, self.thumbnail_href, self.thumbnail_local, self.galleries, self.stats )
#--------------------------------------------------
class notification:
    """ Represent a notification object.
        
        - ACTOR is an object of type user(), on which we will make use only 3 members: avatar_href, display_name, username
        - THIS_PHOTO is object of type photo(), on which we will make use only 3 members: photo_thumb, photo_link, photo_title
        - CONTENT is the type of notifications. It is 'liked', 'comment' or 'add to gallery'
        - TIMESTAMP is the time when the notification happened
        - STATUS is the following status of the main user toward the actor, ie. 'Following'  or 'Not follow'
        """
    def __init__(self, order, actor = user(), the_photo = photo(),  content = '', timestamp = '', status = ''): 
        self.order = order
        self.actor = actor
        self.content = content
        self.the_photo = the_photo        
        self.timestamp = timestamp
        self.status = status
#--------------------------------------------------
class userStats:
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
#--------------------------------------------------
class userInputs():
    """ Represent the input entered by the user. 
    
    Choice is an character string representing available options: [1-13] or 'r','q' . The default value is zero which means commnand line arguments will not be used 
    """

    def __init__(self, use_command_line_args = False, choice='0', user_name='', password='', target_user_name='', photo_href='', gallery_href='', gallery_name='',
                 number_of_photos_to_be_liked=2 , index_of_start_photo=1, number_of_notifications=200, time_interval=3, index_of_start_user=1, number_of_users=100, csv_file='', db_path=''):
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
        self.db_path                        = config.OUTPUT_DIR + r'/500px_' + user_name + '.db'

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
        self.db_path                        = ''
#--------------------------------------------------
class outputData():
    """ Represent all the output lists and data"""

    def __init__(self, output_dir = '', avatars_dir = '', thumbnails_dir = '', 
                 json_data = None, photos = None,notifications = None, unique_notificators = None, followers_list = None, followings_list = None, like_actioners_list= None, avatars_list=None, thumbnails_list=None):
        self.json_data = [] if json_data is None else json_data      
        self.photos = [] if photos is None else photos      
        self.notifications = [] if notifications is None else notifications      
        self.unique_notificators = [] if unique_notificators is None else unique_notificators      
        self.followers_list = [] if followers_list is None else followers_list      
        self.followings_list = [] if followings_list is None else followings_list     
        self.like_actioners_list = [] if like_actioners_list is None else like_actioners_list     
        #self.avatars_list = [] if avatars_list is None else avatars_list     
        #self.thumbnails_list = [] if thumbnails_list is None else thumbnails_list     
        self.stats = userStats()  
        
        output_dir =  config.OUTPUT_DIR 
        os.makedirs(output_dir, exist_ok = True)
        self.output_dir = output_dir
        
        avatars_dir =  os.path.join(output_dir, 'avatars')
        os.makedirs(avatars_dir, exist_ok = True)
        self.avatars_dir = avatars_dir
        self.avatars_list = [f for f in os.listdir(avatars_dir) if isfile(join(avatars_dir, f))]
 
        thumbnails_dir =  os.path.join(output_dir, 'thumbnails')
        os.makedirs(thumbnails_dir, exist_ok = True)
        self.thumbnails_dir = thumbnails_dir
        self.thumbnails_list = [f for f in listdir(thumbnails_dir) if isfile(join(thumbnails_dir, f))]
 
    def Reset(self):
        self.json_data = None       
        self.photos =None        
        self.notifications = None   
        self.unique_notificators = None
        self.followers_list = None  
        self.followings_list = None 
        self.like_actioners_list= None
        self.stats = userStats() 
#--------------------------------------------------
        
# not used for now
#class Output_file_type(Enum):
#   """ Enum representing 5 types of output list"""
#   NOT_DEFINED          = 0
#   FOLLOWERS_LIST       = 1                   
#   FOLLOWINGS_LIST      = 2                  
#   PHOTOS_LIST          = 3              
#   NOTIFICATIONS_LIST   = 4
#   UNIQUE_USERS_LIST    = 5        # Unique users with appearance count, extracted from Notifications list
#   STATISTICS_HTML_FILE = 6