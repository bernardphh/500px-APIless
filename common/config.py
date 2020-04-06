#config.py
# define all the constants and configurable values to be used in apiless.py and 500px_APIless.py

import os, sys, logging, datetime

script_path   = os.path.dirname(sys.argv[0])
output_folder = 'Output'
log_file_name = '500px_apiless_log.txt'

OUTPUT_PATH = os.path.join(script_path, output_folder)  # at [script location]\output_folder
LOG_FILE = os.path.join(OUTPUT_PATH, log_file_name )    # file will saved at [script location]\output_folder\log_file_name

HEADLESS_MODE = True                                    # Use the chrome browser without the graphical user interface (headless), recommended) 
USE_LOCAL_THUMBNAIL = True                              # Save the user avatars and photo thumbnails to disk for off-line viewing of html files
CREATE_LOCAL_DATABASE = True                            # for local SQLITE
USE_MULTIPROCESSING = False                             # to be implemented

# used mainly for a more realistic demonstration of progress on the console progress bar  
PHOTOS_PER_PAGE         = 50                            # 500px currently loads 50 photos per page
LOADED_ITEM_PER_PAGE    = 50                            # it also loads 50 followers, or friends, at a time in the popup window
NOTIFICATION_PER_LOAD   = 20                            # currently notifications are requested to display ( by scrolling the window) 20 items at a time

# self limitation to avoid abusing
MAX_NOTIFICATION_REQUEST = 5000  
MAX_AUTO_LIKE_REQUEST    = 100     

DEBUG = False

DATE_FORMAT = "%Y-%m-%d"                            # ex. 2019-06-15
DATETIME_FORMAT = "%Y-%b-%d--Time%H-%M-%S"          # ex. 2019-Jun-15--Time13-21-45 ( This will be used as part of a file name, so avoid using invalid characters such as :, >, *, etc..)

# logging
# setup log file, back it up when file gets to a certain size. 
if os.path.isfile(LOG_FILE) and os.path.getsize(LOG_FILE) > 10240000:
    os.rename(LOG_FILE, LOG_FILE + f'_bak_{datetime.datetime.now().strftime("%Y_%m_%d")}.txt')

LOG = logging.getLogger()
LOG.setLevel(logging.INFO) 
handler = logging.FileHandler(LOG_FILE, 'a', 'utf-16') 
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt='%Y-%m-%d %H:%M:%S')) 
LOG.addHandler(handler)



