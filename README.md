Scraping Jenkins
================

Requires BeautifulSoup4, and optionally lxml parser

Currrently on startup the app will scrape all B2G reports from Jenkins. Just run:

	python app.py

It will then generate a cache file with dictionaries with stripped down data (test names, passing, duration, config info)

On initial run it will take awhile, but afterwards it should be fairly fast.
All build html reports take a total of 2 GB.

Optionally if you just want the HTML files downloaded with no flask app, or maybe just fetch several new files at once while flask is running run:

	python gethtml.py

To retrieve new reports. Add a 'v' at the end for it to print what it's fetching.
