#config.py
# define all the constants and configurable values to be used in apiless.py and 500px_APIless.py

import os

HEADLESS_MODE = True                                # Use the chrome browser without the graphical user interface (headless, recommended) 
USE_LOCAL_THUMBNAIL = True                          # Save the user avatars and photo thumbnails to disk for off-line viewing of html files
OUTPUT_DIR =  os.path.join(os.getcwd(), 'Output')   # at [current working directory]\Output
CREATE_LOCAL_DATABASE = True                       # to be implemented
USE_MULTIPROCESSING = False                         # to be implemented

# used mainly for a more realistic demonstration of progress on the console progress bar  
PHOTOS_PER_PAGE         = 50                         # 500px currently loads 50 photos per page
LOADED_ITEM_PER_PAGE    = 50                         # it also loads 50 followers, or friends, at a time in the popup window
NOTIFICATION_PER_LOAD   = 20                         # currently notifications are requested to display ( by scrolling the window) 20 items at a time

# self limitation to avoid abusing
MAX_NOTIFICATION_REQUEST = 5000  
MAX_AUTO_LIKE_REQUEST    = 100     

DEBUG = False

DATE_FORMAT = "%Y-%m-%d"                             # ex. 2019-06-15
DATETIME_FORMAT = "%Y-%b-%d--Time%H-%M-%S"           # ex. 2019-Jun-15--Time13-21-45


