from bs4 import BeautifulSoup
import lxml
import urllib
import sys
import os
import shelve
import time

class JenkinsScraper(object):
    def __init__(self, default, path):
        self.default = default
        self.path = path

    #cache for build_dicts
    def memo_build(f):
        cache = shelve.open('data/build_cache')
        def memoized(x, y, z, a=False, b=True):
            temp = y[:]
            temp += str(z)
            temp = str(temp)
            if temp not in cache:
                cache[temp] = f(x, y, z, a, b)
            else:
                print 'CACHE HIT!'
                return cache[temp]
        return memoized

    def check_offline(self):
        opener = urllib.FancyURLopener()
        try:
            opener.open(self.default)
        except IOError:
            return True
        return False

    # return the jobs that have been already fetched and are stored locally
    def get_local_builds(self, job):
        if not os.path.exists('%s/%s' % (self.path, job)):
            print '%s/%s' %(self.path, job)
            return []
        return sorted([int(job.split('.')[0]) for job in os.listdir('%s/%s' % (self.path, job)) if job.split('.')[0].isdigit()])

    # Fetch number of builds for a given job
    def _get_number_of_builds(self, job, offline=False):
        if offline:
            if not len(self.get_local_builds(job)):
                return 0
            return self.get_local_builds(job)[-1]
        else:
            base_url = self.default+'job/'
            opener = urllib.FancyURLopener()
            handle = opener.open(base_url+job+'/')
            report = handle.read()
            soup = BeautifulSoup(report, 'lxml')
            if not soup.select('#buildHistory .build-row')[0].text.split()[0][1:].isdigit():
                return 0
            return int(soup.select('#buildHistory .build-row')[0].text.split()[0][1:])

    # create the necessary directories
    def _fetch_skip_check(self, job):
        if not os.path.exists('%s/%s' % (self.path, job)):
            os.mkdir('%s/%s' % (self.path, job))

        if not os.path.exists('%s/%s/skip.txt' % (self.path, job)):
            open('%s/%s/skip.txt' % (self.path, job), 'a').close()

    # Fetch the HTML Report of a Job build
    def fetch_build_html(self, job, build, offline=False):

        self._fetch_skip_check(job)

        skip = open('%s/%s/skip.txt' % (self.path, job), 'r+')
        skipped = skip.read().split('\n')
        fetched = self.get_local_builds(job)
        if build in skipped:
            print 'No HTML Report for %s:%s! Skipping...' % (job, str(build))
            return False
        elif int(build) in fetched:
            print '%s:%s Already Fetched!' % (job, build) 
            return True
        elif offline:
            print 'No HTML Report for %s:%s! Skipping...' % (job, str(build))
            skip.write(str(build)+'\n')
            return False
        else:
            base_url = self.default+'job/'
            base_suffix = '/HTML_Report/index.html'
            opener = urllib.FancyURLopener()
            handle = opener.open(base_url+job+'/'+str(build)+base_suffix)
            report = handle.read()
            soup = BeautifulSoup(report, 'lxml')

            if soup.body == None or 'Not found' in soup.body.text or soup.title.text != 'Test Report': 
                print 'No HTML Report for %s:%s! Skipping...' % (job, str(build))
                skip.write(str(build)+'\n')
                return False

            f = open('%s/%s/%s.html' % (self.path, job, build), 'w')
            f.write(report)
            print '%s:%s Fetched!' % (job, build) 
            return True

    #Create a dict with relevant build info if available
    @memo_build
    def make_build_dict(self, job, build, offline=False, check_exists=True):
        if check_exists:
            if not self.fetch_build_html(job, build, offline):
                return
        build_dict = {}
        build_dict['build'] = build
        build_dict['job'] = job

        f = open('%s/%s/%s.html' % (self.path, job, build), 'r')
        report = f.read()
        soup = BeautifulSoup(report, 'lxml')

        # soup = BeautifulSoup(open('Test Report.html').read(), 'lxml')

        time_text = soup.p.text.split()
        #Convert to time since epoch in milliseconds for js
        build_dict['date'] = time.mktime(time.strptime(time_text[3]+" "+time_text[5]+" PST", "%d-%b-%Y %H:%M:%S %Z"))

        test_table_rows = soup.select('#results-table > #results-table-body > .results-table-row')
        debug_rows = soup.select('td.debug')
        fields = ['col-name', 'col-result', 'col-duration']

        # Generate a list for each test containing test name, result, and duration.
        test_info = [[test.find(attrs={'class':field}).text for field in fields] for test in test_table_rows]

        tests = {}
        for index, test in enumerate([dict(zip(['test_name', 'result', 'duration'], test)) for test in test_info]):
            test_name = test['test_name']
            if test['result'] not in ['Passed', 'Skipped', 'Unexpected Pass']:
                test['log'] = debug_rows[index].find(attrs={'class':'log'}).text
            if test_name in tests.keys():
                tests[test_name].append(test)
            else:
                tests[test_name] = [test]

        build_dict['tests'] = tests

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
                    'gaia_date', 'gaia_revision','gecko_build', 'gecko_revision', 'gecko_version']
        for idx, item in enumerate(config_keys):
            build_dict[new_keys[idx]]= build_dict.pop(item, None)

        return build_dict

    # Fetch all build HTML Reports for a given job.
    def fetch_all_build_reports(self, job):
        self._fetch_skip_check(job)
        latest = self._get_number_of_builds(job)
        skip = open('%s/%s/skip.txt' % (self.path, job), 'r+')
        skipped = skip.read().split('\n')
        fetched = self.get_local_builds()
        for i in xrange(1, latest+1):
            if str(i) in skipped:
                print 'No HTML Report for %s:%s! Skipping...' % (job, str(i))
                continue
            if i in fetched:
                print '%s:%s Already Fetched!' % (job, i) 
                continue
            self.fetch_build_html(job, i)

    # For a given job, generate a build_dict for each build
    # Tries to take advantage of caching to reduce number of file reads
    def _create_all_build_dicts(self, job, offline=False):
        self._fetch_skip_check(job)
        latest = self._get_number_of_builds(job, offline)
        if latest < 1:
            return False
        skip = open('%s/%s/skip.txt' % (self.path, job), 'r+')
        skipped = skip.read().split('\n')
        fetched = self.get_local_builds(job)
        for i in xrange(1, latest+1):
            if str(i) in skipped or (offline and i not in fetched):
                print 'No HTML Report for %s:%s! Skipping...' % (job, str(i))
                continue
            if i in fetched:
                print '%s:%s Already Fetched!' % (job, i) 
                self.make_build_dict(job, i, offline, False)
            else:
                self.make_build_dict(job, i, offline, True)

    # Filter a build_dict to return only relevant test
    def _extract_test_info(self, build_dict, test_name):
        test_info = build_dict.copy()
        tests = test_info.pop('tests', None)
        if test_name not in tests.keys():
            return None
        test_info.update({'test_list':tests[test_name]})
        return test_info

    # Retrieve all releveant test_dicts for a job
    def fetch_test_data(self, job, test_name, offline=False):
        latest = self._get_number_of_builds(job, offline)
        builds = [self.make_build_dict(job, x,offline) for x in xrange(1,latest+1)]
        builds = [self._extract_test_info(build, test_name) for build in builds if build != None]
        builds = [build for build in builds if build != None]
        return builds 

    # Return all jobs available online and locally. If offline mode all local jobs are 'Legacy'
    def fetch_jobs(self, offline=False):
        if offline:
            return {'current': [], 'legacy': [job for job in os.listdir(self.path) if job[0] != '.' or '.txt' in job]}
        all_jobs = []
        url = self.default+''
        opener = urllib.FancyURLopener()
        print url
        handle = opener.open(url)
        report = handle.read()
        jobs_page = BeautifulSoup(report, 'lxml')
        jobs = jobs_page.select('#projectstatus .model-link.inside')
        for i in range(1,len(jobs)):
            all_jobs.append(jobs[i].attrs['href'].split('/')[1])
        return {'current': list(set(all_jobs)),
                    'legacy': [job for job in list(set(all_jobs) ^ set(os.listdir(self.path))) if job not in all_jobs and (job[0] != '.' or '.txt' in job)]
                }

    # Prebuild the cache by checking all available jobs.
    def generate_build_cache(self, offline=False):
        jobs = self.fetch_jobs(offline)
        for job in jobs['current']:
            if "download" in job or "perf" in job:
                continue
            self._create_all_build_dicts(job, offline)
        for job in jobs['legacy']:
            if "download" in job or "perf" in job:
                continue
            self._create_all_build_dicts(job, True)
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
            if 'perf' in job or 'download' in job:
                continue
            else:
                self.fetch_all_build_reports(job)

    #List all the tests for a given job.
    def list_tests(self, job, offline):
        build = None
        if len(self.get_local_builds(job)) > 0:
            build = self.get_local_builds(job)[-1]
        else:
            for i in range(self._get_number_of_builds(job,offline)):
                if self.fetch_build_html(job, i, offline):
                    build = i
                    break
        if not build:
            return []
        return self.make_build_dict(job, build,offline)['tests'].keys()
