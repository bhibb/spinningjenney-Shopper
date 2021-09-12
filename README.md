# spinningjenney-Shopper
Ever wondered why you can't get that new Rae Dunn or Johanna Parker mug/cookie jar/etc before someone else does? Well, this script will help you know as soon as a new item is released for your search term!

This is an email alert when new URLs get added to keyword searches on Marshall's and TJMaxx websites. Currently, they search for 'halloween.'

In order to change which search terms that this tool searches for, go to the TJMaxx and Marshall's websites and search the term you want in their search bar.
Then, take the URL from that search and paste it into the SEARCHES_TRACKER.CSV file in a new row. The script, when run, will iterate over that URL and email you (whatever email is placed in the script as the receiver email) from your gmail email (which you also set in the script) when a new item is available in your search term response.
