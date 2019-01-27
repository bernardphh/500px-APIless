# 500px-APIless: Scraping and automation
A personal project created by curiosity and for fun, to extract information from 500px web site fordata analyzing, and to perform some automated processes.


**A BIT OF HISTORY:**

500px is a famous photo sharing site who recently shutdown its API access (June 15 2018), leaving numerous applications relied on its API, useless.

Without the API, data is harder to get, and it takes longer time to collect.
But gone the API, came the challenges!


As a 500px user who does not want to be manipulated by bots, I initially just wanted to gather data from the site, manually analyze them and figure it out the users who: 
 - Trigger me into following them, then ignore me, or un-follow me not long after.
 - Like every photo I posted, give un-mistaken robot comments, and like my photo back every time I liked theirs
 - Get unbelievable number of followers
 - ...
 
And as a programmer, I got curious. I wondered how things can be done. I ended up creating some bots myself.
Not wanting to involve in the virtual fame, I created a new account one for testing. 

I don't want to fool myself by the "artificial" number of affections that I know could be manipulated if one chooses to do so.

I believe that using bots to promote popularity will do you harm. It kills all the fun interacting with fellow photographers.

Unless, you are in it not for fun, or your fun is getting ahead, no matter what...



**WHAT IT CAN DO SO FAR:**

![Main menu](/MainMenu.JPG)

The first 7 options are for data collection, for which you need to provide a 500px username.

Results are saved on disk as CSV files. You will be offered to view the data in the web browser when the process finished. 

The next 5 options, from 8 to 12, are the automated processes, for which you need to enter a password for actions.

For sample output, please refer to [500px-Apiless.docx](/500px-Apiless.docx)   



**ENVIRONMENT:**

This was developed using Visual Studio Code, testing and run on Windows 10, for Python version 3.6





**DEPENDENCIES:**

Python 3.6 or later (freely distributed on the web)

Selenium 





**USAGE:**

If Python and Selenium were installed properly, you should be able to double-click the file 500px-APIless.py in Window Explorer to run it.

If not, make sure the location of python executable is in the PATH, open the Windows Terminal (cmd.exe), navigate to the location of the python script and type:
 pythom.exe 500px-APIless.py




**LIMITATIONS, ISSUES, TODO :**

-	Not all exceptions are handled, especially with Selenium’s find_element… methods
-	For the requests involved more than 1000 items (list of notifications, photos, users…), processing time takes longer time than I’d like it to. 
- TODO: putting thumbnails on the result files, create a GUI, run the slideshow ... 

Prior to this project, I have zero knowledge on python and web scraping. I'm sure there are rooms for improvements. 
I left abundant comments in the code to make the intention clear, just in case someone wants to chip in.

Feedback, bug report, contributions are all welcomed.




**DISCLAIMER:**  

As in any web scraping, a change in page structure may break one or more options. Hopefully we can adapt when it happens. 
(500px certainly did not make it easy by already randomizing class names and by limiting the use of fixed tag id )

This project is created for fun and for gaining personal experience with python and web scraping. The owner assumes no responsibility.
Even though some limits have been set, some processes have been intentionally slowed down to make it look more human, 
abusing or over-usage may result in your account being banned. Use this at your own risk.



