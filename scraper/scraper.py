from bs4 import BeautifulSoup
import urllib
import os
import time
import json

# A scraper for the given Jenkins URL
# It will download HTML reports and store them in the given relative path
# Scraping info from the reports it creates a dict with nearly all information from the report
# These dicts are memoized and stored locally for quick access without the need to constantly remake tests
# offline dictates whether it will only check locally or ping the given default


class JenkinsScraper(object):
    def __init__(self, baseurl, path, filters=None):
        self.baseurl = baseurl
        self.path = path
        if filters is None:
            self.filters = []
        else:
            self.filters = filters
        self.offline = self.is_offline
        self.jobs = self.fetch_jobs()

    # check if scraper can access default
    @property
    def is_offline(self):
        try:
            urllib.urlopen(self.baseurl)
        except IOError:
            return True
        return False

    # create the necessary directories
    def _setup_job_dir(self, job):
        if not os.path.exists('%s/%s/HTML' % (self.path, job)):
            os.mkdir('%s/%s/HTML' % (self.path, job))
        if not os.path.exists('%s/%s/skip.txt' % (self.path, job)):
            open('%s/%s/skip.txt' % (self.path, job), 'a').close()
        if not os.path.exists('%s/%s/JSON' % (self.path, job)):
            os.mkdir('%s/%s/JSON' % (self.path, job))

    # return the jobs that have been already fetched and are stored locally
    def get_local_builds(self, job):
        if not os.path.exists('%s/%s' % (self.path, job)):
            print '%s/%s' % (self.path, job)
            return []
        return sorted([int(job.split('.')[0]) for job in os.listdir('%s/%s/HTML' % (self.path, job))
                       if job.split('.')[0].isdigit()])

    # Fetch number of builds for a given job
    def _get_latest_build_number(self, job):
        if self.offline or job in self.jobs['legacy']:
            if not len(self.get_local_builds(job)):
                return 0
            return self.get_local_builds(job)[-1]
        else:
            base_url = self.baseurl+'job/'
            opener = urllib.FancyURLopener()
            handle = opener.open(base_url+job+'/')
            report = handle.read()
            soup = BeautifulSoup(report)
            build_num = soup.select('#buildHistory .build-row')[0].text.split()[0][1:]
            if not build_num.isdigit():
                return 0
            return int(build_num)

    # Fetch the HTML Report of a Job build
    def fetch_build_html(self, job, build):
        legacy = job in self.jobs['legacy']
        self._setup_job_dir(job)
        skip = open('%s/%s/skip.txt' % (self.path, job), 'r+')
        skipped = skip.read().split('\n')
        if str(build) in skipped:
            # print 'No HTML Report for %s:%s! Skipping...' % (job, str(build))
            return False
        elif os.path.exists('%s/%s/HTML/%s.html' % (self.path, job, build)):
            # print '%s:%s Already Fetched!' % (job, build)
            return True
        elif self.offline or legacy:
            # print 'No HTML Report for %s:%s! Skipping...' % (job, str(build))
            skip.write(str(build)+'\n')
            return False
        else:
            base_url = self.baseurl+'job/'
            base_suffix = '/HTML_Report/index.html'
            opener = urllib.FancyURLopener()
            handle = opener.open(base_url+job+'/'+str(build)+base_suffix)
            report = handle.read()
            soup = BeautifulSoup(report)

            if soup.body is not None or 'Not found' in soup.body.text or soup.title.text != 'Test Report':
                # print 'No HTML Report for %s:%s! Skipping...' % (job, str(build))
                skip.write(str(build)+'\n')
                return False

            f = open('%s/%s/HTML/%s.html' % (self.path, job, build), 'w')
            f.write(report)
            # print '%s:%s Fetched!' % (job, build)
            return True

    #Create a dict with relevant build info if available
    def make_build_dict(self, job, build, check_exists=True):
        html_path = self.path + '/' + job + '/HTML/' + str(build) + '.html'
        json_path = self.path + '/' + job + '/JSON/' + str(build) + '.json'
        if check_exists:
            if not self.fetch_build_html(job, build):
                return

        if os.path.exists(json_path):
            return json.load(open(json_path))

        build_dict = {'build': build, 'job': job}

        f = open(html_path, 'r')
        report = f.read()
        soup = BeautifulSoup(report)
        time_text = soup.p.text.split()
        build_dict['date'] = time.mktime(time.strptime(time_text[3]+" "+time_text[5]+" PST", "%d-%b-%Y %H:%M:%S %Z"))

        test_table_rows = soup.select('#results-table > #results-table-body > .results-table-row')
        debug_rows = soup.select('td.debug')
        fields = ['col-name', 'col-result', 'col-duration', 'col-class']

        # Generate a list for each test containing test name, result, class, and duration.
        test_info = [[test.find(attrs={'class': field}).text for field in fields] for test in test_table_rows]

        tests = {}
        for index, test in enumerate([dict(zip(['test_name', 'result', 'duration', 'class'], test))
                                      for test in test_info]):
            test_name = test['test_name']
            if test['result'] not in ['Passed', 'Skipped', 'Unexpected Pass']:
                test['log'] = debug_rows[index].find(attrs={'class': 'log'}).text
            if test_name in tests.keys():
                tests[test_name].append(test)
            else:
                tests[test_name] = [test]

        build_dict['tests'] = tests

        # Brittle, if order changes or new options are added.
        config_table = soup.select('#configuration tr')
        config_keys = []
        for index, row in enumerate(config_table):
            temp = row.select('td')
            if index == 5 or index == 7:
                build_dict[temp[0].text] = {'revision': temp[1].text, 'link': temp[1].a['href']}
            else:
                build_dict[temp[0].text] = temp[1].text
            config_keys.append(temp[0].text)
        new_keys = ['firmware_date', 'firmware_incremental', 'firmware_release', 'identifier',
                    'gaia_date', 'gaia_revision', 'gecko_build', 'gecko_revision', 'gecko_version']
        for idx, item in enumerate(config_keys):
            build_dict[new_keys[idx]] = build_dict.pop(item, None)

        with open(json_path, 'wb') as fp:
            json.dump(build_dict, fp)

        return build_dict

    # Fetch all build HTML Reports for a given job.
    def _fetch_all_build_reports(self, job):
        self._setup_job_dir(job)
        latest = self._get_latest_build_number(job)
        skip = open('%s/%s/skip.txt' % (self.path, job), 'r+')
        skipped = skip.read().split('\n')
        fetched = self.get_local_builds(job)
        for i in xrange(1, latest+1):
            if str(i) in skipped:
            #    print 'No HTML Report for %s:%s! Skipping...' % (job, str(i))
                continue
            if i in fetched:
            #    print '%s:%s Already Fetched!' % (job, i)
                continue
            self.fetch_build_html(job, i)

    # For a given job, generate a build_dict for each build
    # Tries to take advantage of caching to reduce number of file reads
    def _create_all_build_dicts(self, job):
        self._setup_job_dir(job)
        latest = self._get_latest_build_number(job)
        if latest < 1:
            return False
        skip = open('%s/%s/skip.txt' % (self.path, job), 'r+')
        skipped = skip.read().split('\n')
        fetched = self.get_local_builds(job)
        for i in xrange(1, latest+1):
            if str(i) in skipped or (self.offline and i not in fetched):
            #    print 'No HTML Report for %s:%s! Skipping...' % (job, str(i))
                continue
            if i in fetched:
            #    print '%s:%s Already Fetched!' % (job, i)
                self.make_build_dict(job, i, False)
            else:
                self.make_build_dict(job, i, True)

    # Filter a build_dict to return only relevant test
    def _extract_test_info(self, build_dict, test_name):
        test_info = build_dict.copy()
        tests = test_info.pop('tests', None)
        if test_name not in tests.keys():
            return None
        test_info.update({'test_list': tests[test_name]})
        return test_info

    # Retrieve all relevant test_dicts for a job
    def fetch_test_data(self, job, test_name):
        latest = self._get_latest_build_number(job)
        builds = [self.make_build_dict(job, x) for x in xrange(1, latest + 1)]
        builds = [self._extract_test_info(build, test_name) for build in builds
                  if build is not None and test_name in build['tests'].keys()]
        return builds 

    # Return all jobs available online and locally. If offline mode all local jobs are 'Legacy'
    def fetch_jobs(self):
        if self.offline:
            return {'current': [], 'legacy': [job for job in os.listdir(self.path) if job[0] != '.' or '.txt' in job]}
        all_jobs = []
        url = self.baseurl + ''
        opener = urllib.FancyURLopener()
        handle = opener.open(url)
        report = handle.read()
        jobs_page = BeautifulSoup(report)
        jobs = jobs_page.select('#projectstatus .model-link.inside')
        for i in range(1, len(jobs)):
            all_jobs.append(jobs[i].attrs['href'].split('/')[1])
        return {'current': list(set(all_jobs)),
                'legacy': [job for job in list(set(all_jobs) ^ set(os.listdir(self.path)))
                           if job not in all_jobs and (job[0] != '.' or '.txt' in job)]
                }

    # Prebuild the cache by checking all available jobs.
    def generate_build_cache(self):
        jobs = self.fetch_jobs()
        for job in jobs['current']:
            if any(filter in job for filter in self.filters):
                continue
            print job
            self._create_all_build_dicts(job)
        for job in jobs['legacy']:
            if any(filter in job for filter in self.filters):
                continue
            print job
            self._create_all_build_dicts(job)
        print "Cached:"
        print 'Current:'
        for job in jobs['current']:
            print job
        print "Legacy:"
        for job in jobs['legacy']:
            print job

    #Assumes connection to server.
    def fetch_all_job_reports(self):
        jobs = self.fetch_jobs()
        for job in jobs:
            if any(filter in job for filter in self.filters):
                continue
            else:
                self._fetch_all_build_reports(job)

    #List all the tests for a given job.
    def list_tests(self, job):
        build = None
        if len(self.get_local_builds(job)) > 0:
            build = self.get_local_builds(job)[-1]
        else:
            for i in range(self._get_latest_build_number(job)):
                if self.fetch_build_html(job, i):
                    build = i
                    break
        if not build:
            return []
        return self.make_build_dict(job, build)['tests'].keys()

    def refresh_jobs(self):
        self.jobs = self.fetch_jobs()