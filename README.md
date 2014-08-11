# Scraping Jenkins

Requires BeautifulSoup4 and Flask.

Currrently on startup the app will scrape all B2G reports from Jenkins. Just run:

	python app.py

- On initial run it will take awhile, but afterwards it should be fairly fast.
- All build html reports take > 2 GB.
- As a cache it will save a JSON version of each HTML Report.

# JenkinsScraper and MultiScraper

The `JenkinsScraper` and `MultiScraper` classes found in the scraper module do the heavy lifting of scraping Jenkins by pulling in HTML Reports locally and scraping the data, storing them as JSON's used later for data visualizations.

The MultiScraper most of the methods of a `JenkinsScraper`. It takes in mulitple `JenkinsScraper`'s as its arguments. Its purpose is to abstract away multiple scrapers and act as a single scraper with its methods.

The JenkinsScraper takes in various parameters:

- `default`: This is the base URL that will be scraped from. It should be the list of jobs that are relevant to what you are interested in scraping.
- `path`: This will be the default path the scraper stores the HTML and JSON files.
- `filters`: A list of strings that will be used to filter out job names that do not have HTML reports. e.g. 'perf' or 'download'.

## JenkinsScraper Methods

- `_setup_job_dir(self, job)` :Takes in a job, and will check if the proper directory paths exist for the given job as well as a `skip.txt`
- `get_local_builds(self, job): Will return the build numbers of the given job that exist locally on the server.
- `_get_latest_build_number(self, job)`: Will ping the server, if connected, and get the latest build number for the given job, else return the latest build number stored locally.
- `fetch_build_html(self, job, build)`: This will get and store the html report of a given build.
- `make_build_dict(self, job, build, check_exists)`: if `check_exists` is true it will check if a HTML Report exists for a given job and build combo, else it will assume it exists. If a JSON of the given combo already exists it will simply return that. It will take the local HTML report and scrape it of relevant B2G configuration info, test results, and other useful information. Currently it does not store the screenshots. The resulting dictionary has the following structure:
```
{
    "build": buildno,
    "job": job_name,
    "date": daterun,
    "firmware_date": date,
    "firmware_incremental": incremental,
    "firmware_release": release,
    "identifier": device_identifier,
    "gaia_date": gaia_date,
    "gaia_revision": revision,
    "gecko_build": build,
    "gecko_revision": revision,
    "gecko_version": version,
    "tests": {
        "test_name": [{
            "test_name": name,
            "result": result,
            "log": traceback_if_fail_or_error,
            "duration": duration,
            "class": class_name
        }]
    }
}
```
It saves this as a JSON and returns the resulting dictionary as well.
- `fetch_all_build_reports(self, job)`: For a given job will try and retrieve all HTML reports from 1 to the latest build.
- `_create_all_build_dicts(self, job)`: Will rcreate all build dictionaries fora  given job and all its builds. Used for creating the JSON cache.
- `_extract_test_info`(self, build_dict, test_name): Used to pare down a build dictionary to only the relevant `test_name`. Replaces `tests` field with just `test_list`.
- `fetch_test_data(self, job, test_name)`: Will retrieve the relevant build dictionaries pared down to only the relevant tests.
- `fetch_jobs(self)`: Return a combination of all local and online jobs in a list.
- `generate_build_cache(self)`: Will generate the JSON's for all jobs and builds. 
- `refresh_jobs`: Will refresh `test.jobs`

