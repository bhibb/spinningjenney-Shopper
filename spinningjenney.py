from bs4 import BeautifulSoup
import requests
from glob import glob
import pandas as pd
from datetime import datetime
from time import sleep
import os
import shutil
from requests.models import ReadTimeoutError
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urlsplit, urlunsplit
import pathlib


HEADERS = ({'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0',
            'Accept-Language': 'en-US, en;q=0.5'})

# Enter your gmail email here as the sender email, and your password as well. You may need to allow
# 3rd party software to use your gmail account in 'Security' settings.
# Must be a gmail account per line 195.
sender_email = ''
password = ''
# Enter the receiver's email, it does not have to be gmail.
receiver_email = ''

# Create a function to orient the script to all the necessary logs and files.
def get_path() -> pathlib.Path:
    return pathlib.Path(__file__).parent

# This is our main search function.
def search_url_list(interval_count = 1, interval_minutes = 15):
    """
    This function loads a csv file named SEARCHES.csv, with headers: [url]
    It looks for the file under in ./searches.
    
    It also requires a file called SEARCH_HISTORY.xslx under the folder ./search_history to start saving the results.
    An empty file can be used on the first time using the script.
    
    Both the old and the new results are then saved in a new file named SEARCH_HISTORY_{datetime}.xlsx

    Parameters
    ----------
    interval_count : TYPE, optional
        DESCRIPTION. The default is 1. The number of iterations you want the script to run a search on the full list.
    interval_minutes : TYPE, optional
        DESCRIPTION. The default is 15.

    Returns
    -------
    New .xlsx file with previous search history and CSV files with the results from current and old searches, 
    as well as an log of sent emails
    """
    # Set some variables and open the SEARCHES_TRACKER.csv file
    search_tracker = pd.read_csv((str(get_path().joinpath('searches/SEARCHES_TRACKER.csv'))), sep=',')
    search_tracker_URLS = search_tracker.url
    search_log = pd.DataFrame()
    now = datetime.now().strftime('%Y-%m-%d %Hh%Mm')
    interval = 0 # counter reset
    # This is our maine while loop
    while interval < interval_count:
        print('Beginning search.')
        # Set our email_needed variable to False
        email_needed = False
        # Archive the old list from a previous run.
        try:
            shutil.copy2((str(get_path().joinpath('MyList.csv'))), (str(get_path().joinpath('OLDMyList.csv'))))
            print('Old list copied to "OLDMyList.csv."')
        except Exception:
            pass
        # Start reading the URLs from the SEARCHES_TRSCKER.csv file
        for x, url in enumerate(search_tracker_URLS):
            page = requests.get(url, headers=HEADERS)
            soup = BeautifulSoup(page.text, 'lxml')
            # If the URL is a tjmaxx URL grab the relevant data
            if 'tjmaxx' in url:
                rooturl = 'https://tjmaxx.tjx.com/'
                try:
                    product_links = soup.find_all(class_='product-link')
                    links_list=[]
                    unique_links_list=[]
                    for link in product_links:
                        # we have to craft the link together for it to work, then we need to clean the query id off the URL
                        usable_link = rooturl + link.get('href')
                        parsed = urlsplit(usable_link)
                        clean_url = urlunsplit((parsed.scheme,parsed.netloc,parsed.path,'',''))
                        links_list.append(clean_url)
                    # we need to remove duplicate links
                    [unique_links_list.append(link) for link in links_list if link not in unique_links_list]
                except:
                    pass
                # Create a dataframe with a title URL and as many rows as there are items
                df = pd.DataFrame({'URL':unique_links_list})                
                df.to_csv((str(get_path().joinpath('MyList.csv'))), mode='a', index=False)
                search_log = search_log.append(df)  
            elif 'marshalls' in url:
            # If the URL is a marshalls URL grab the relevant data
                rooturl = 'https://www.marshalls.com/'
                try:
                    product_links = soup.find_all(class_='product-link')
                    links_list=[]
                    unique_links_list=[]
                    for link in product_links:
                        # we have to craft the link together for it to work, then we need to clean the query id off the URL
                        usable_link = rooturl + link.get('href')
                        parsed = urlsplit(usable_link)
                        clean_url = urlunsplit((parsed.scheme,parsed.netloc,parsed.path,'',''))
                        links_list.append(clean_url)
                    # we need to remove duplicate links
                    [unique_links_list.append(link) for link in links_list if link not in unique_links_list]
                except:
                    pass
                # Create a dataframe with a title URL and as many rows as there are items, and append them
                df = pd.DataFrame({'URL':unique_links_list})                
                df.to_csv((str(get_path().joinpath('MyList.csv'))), mode='a', index=False)
                search_log = search_log.append(df)                          
        # After the search, checks last search history record, and appends this run results to it, saving a new file
        search_history_list = []
        search_history_files = pathlib.Path(get_path().joinpath('search_history/')).glob('*.[xl]*')
        [search_history_list.append(str(item)) for item in search_history_files]
        last_search = search_history_list[-1] # path to file in the folder
        search_hist = pd.read_excel(last_search)
        final_df = search_hist.append(search_log, sort=False)
        final_df.to_excel(((str(get_path().joinpath('search_history'))) + '/' + 'SEARCH_HISTORY_{}.xlsx'.format(now)), index=False)
        print('End of search.')
        # Now we compare the two files we have from the old list and the new list and create a new temporary list
        try:
            # Check for new items by comparing the two search lists
            with open((str(get_path().joinpath('OLDMyList.csv'))), 'r', encoding='utf8') as t1, open((str(get_path().joinpath('MyList.csv'))), 'r', encoding='utf8') as t2:
                fileone = t1.readlines()
                filetwo = t2.readlines()
            # Create an email list csv file containing the different items
            with open('emailList.csv', 'w') as outFile:
                for line in filetwo:
                    if line not in fileone:
                        outFile.write(line)
                        # Set the email_needed variable to True because we have new URLs
                        email_needed = True
        except Exception:
            print('No old search history found, please search again, or wait for another search interval.')
            pass
        # Read the csv file and create a new html object with pandas
        try:
            fields = ['URL']
            email = pd.read_csv('emailList.csv', names=fields)
            # Assign the dataframe to an html object/string
            htmTable = email.to_html(index=False, render_links=True)
        except Exception:   
            pass
        # Check our email_needed variable to see if it is True
        if email_needed == True:
            if sender_email == '':
                print('No sender email was entered. Skipping the email.')
                pass
            elif receiver_email == '':
                print('No reciever email was entered. Skipping the email.')
                pass
            elif password == '':
                print('No password was entered. Skipping the email.')
                pass
            else:
                # Send an email with the updated URLs
                message = MIMEMultipart("alternative")
                message["Subject"] = 'Spinningjenney Shopper Update'
                message["From"] = sender_email
                message["To"] = receiver_email
                # Create the plain-text and HTML version of your message
                text = f"""\
                Hello!
                Here's a list of recent updates to your email searches:
                {htmTable}
                """
                html = f"""\
                <html>
                <body>
                    <p>Hello!<br>
                    Here's a list of recent updates to your email searches:<br>
                    <br>
                    {htmTable}
                    </p>
                </body>
                </html>
                """
                # Turn these into plain/html MIMEText objects
                part1 = MIMEText(text, "plain")
                part2 = MIMEText(html, "html")
                # Add HTML/plain-text parts to MIMEMultipart message
                # The email client will try to render the last part first
                message.attach(part1)
                message.attach(part2)
                # Create secure connection with server and send email
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                    server.login(sender_email, password)
                    server.sendmail(
                        sender_email, receiver_email, message.as_string()
                    )
                # Write to an email log so we can check and see what emails have been sent while the script is running
                with open('emailLog.txt', 'a') as output:
                    output.write(text + '\n' + 'END' + '\n\n')
                print('Email sent.')
        # Remove the emailList.csv file as we no longer need it
        try:
            os.remove('emailList.csv')
        except Exception:
            pass
        # Update the script to complete a run and sleep for an amount of minutes, or if it's just one run, complete
        interval += 1# counter update
        if interval_count != 1:
            sleep(interval_minutes * 60)
        print('End of interval '+ str(interval))

search_url_list()
