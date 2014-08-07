Scraping Jenkins
================

Requires BeautifulSoup4, and optionally lxml parser

Currrently on startup the app will scrape all B2G reports from Jenkins. Just run:

	python app.py

It will then generate a cache file with dictionaries with stripped down data (test names, passing, duration, config info)

On initial run it will take awhile, but afterwards it should be fairly fast.
All build html reports take a total of 2 GB.

