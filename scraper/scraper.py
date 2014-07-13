from bs4 import BeautifulSoup
import lxml
import urllib
import sys
import os
import shelve
import time

path = 'templates/Reports'
default='http://selenium.qa.mtv2.mozilla.com:8080/view/B2G/'

#cache for build_dicts
def memo_build(f):
    cache = shelve.open('data/build_cache')

    def memoized(x, y, z=True):
        temp = x[:]
        temp += str(y)
        temp = str(temp)
        if temp not in cache:
            cache[temp] = f(x, y, z)
        else:
            return cache[temp]
    return memoized


# Helper method to make a dict out of a 3-item tuple.
def _make_test_dict(test):
    test_dict = {}
    identifiers = ['test_name', 'result', 'duration']
    for index, identifier in enumerate(identifiers):
        test_dict[identifier] = test[index]
    return test_dict

# Fetch number of builds for a given job
def _get_number_of_builds(job, legacy=False):
    if legacy:
        return os.listdir('%s/%s' % (job, path))[-1]
    else:
        base_url = default+'job/'
        opener = urllib.FancyURLopener()
        handle = opener.open(base_url+job+'/')
        report = handle.read()
        soup = BeautifulSoup(report, 'lxml')
        if not soup.select('#buildHistory .build-row')[0].text.split()[0][1:].isdigit():
            return 0
        return int(soup.select('#buildHistory .build-row')[0].text.split()[0][1:])

def _fetch_skip_check(job):
    if not os.path.exists('%s/%s' % (path, job)):
        os.mkdir('%s/%s' % (path, job))

    if not os.path.exists('%s/%s/skip.txt' % (path, job)):
        open('%s/%s/skip.txt' % (path, job), 'a').close()

# Fetch the HTML Report of a Job build
def fetch_build_html(job, build, legacy=False):

    _fetch_skip_check(job)

    skip = open('%s/%s/skip.txt' % (path, job), 'r+')
    skipped = skip.read().split('\n')
    fetch = open('%s/%s/fetch.txt' % (path, job), 'r+')
    fetched = fetch.read().split('\n')

    if build in skipped:
        print 'No HTML Report for %s:%s! Skipping...' % (job, str(build))
        return False
    if str(build)+'.html' in os.listdir('%s/%s' % (path, job)):
        print '%s:%s Already Fetched!' % (job, build) 
        return True
    if legacy:
        return build in os.listdir('%s/%s' % (job, path))
    else:
        base_url = default+'job/'
        base_suffix = '/HTML_Report/index.html'
        opener = urllib.FancyURLopener()
        handle = opener.open(base_url+job+'/'+str(build)+base_suffix)
        report = handle.read()
        soup = BeautifulSoup(report, 'lxml')

        if soup.body == None or 'Not found' in soup.body.text or soup.title.text != 'Test Report': 
            print 'No HTML Report for %s:%s! Skipping...' % (job, str(build))
            skip.write(str(build)+'\n')
            return False

        f = open('%s/%s/%s.html' % (path, job, build), 'w')
        f.write(report)
        print '%s:%s Fetched!' % (job, build) 
        return True

#Create a dict with relevant build info if available
@memo_build
def make_build_dict(job, build,check_exists=True):
    if check_exists:
        if not fetch_build_html(job, build):
            return
    build_dict = {}
    build_dict['build'] = build
    build_dict['job'] = job

    f = open('%s/%s/%s.html' % (path, job, build), 'r')
    report = f.read()
    soup = BeautifulSoup(report, 'lxml')

    # soup = BeautifulSoup(open('Test Report.html').read(), 'lxml')

    time_text = soup.p.text.split()
    #Convert to time since epoch in milliseconds for js
    build_dict['date'] = time.mktime(time.strptime(time_text[3]+" "+time_text[5]+" PST", "%d-%b-%Y %H:%M:%S %Z"))

    test_table_rows = soup.select('#results-table > #results-table-body > .results-table-row')
    fields = ['col-name', 'col-result', 'col-duration']

    # Generate a list for each test containing test name, result, and duration.
    test_info = [[test.find(attrs={'class':field}).text for field in fields] for test in test_table_rows]

    tests = {}
    for test in [_make_test_dict(test) for test in test_info]:
        test_name = test['test_name']
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
    new_keys = ['firmware_date', 'firmware_incremenal', 'firmware_release', 'identifier',
                'gaia_date', 'gaia_revision','gecko_build', 'gecko_revision', 'gecko_version']
    for idx, item in enumerate(config_keys):
        build_dict[new_keys[idx]]= build_dict.pop(item, None)

    return build_dict

# Fetch all build HTML Reports for a given job.
def fetch_all_builds(job):
    _fetch_skip_check(job)
    latest = _get_number_of_builds(job)
    skip = open('%s/%s/skip.txt' % (path, job), 'r+')
    skipped = skip.read()

    for i in xrange(1, latest+1):
        if str(i)+'\n' in skipped:
            print 'No HTML Report for %s:%s! Skipping...' % (job, str(i))
            continue
        if str(i)+'.html' in os.listdir('%s/%s' % (path, job)):
            print '%s:%s Already Fetched!' % (job, i) 
            continue
        fetch_build_html(job, i)

# For a given job, generate a build_dict for each build
def create_all_build_dicts(job):
    _fetch_skip_check(job)
    latest = _get_number_of_builds(job)
    if latest < 1:
        return False
    skip = open('%s/%s/skip.txt' % (path, job), 'r+')
    skipped = skip.read().split('\n')
    for i in xrange(1, latest+1):
        if str(i) in skipped:
            print 'No HTML Report for %s:%s! Skipping...' % (job, str(i))
            continue
        if str(i)+'.html' in os.listdir('%s/%s' % (path, job)):
            print '%s:%s Already Fetched!' % (job, i) 
            make_build_dict(job, i, False)
        else:
            make_build_dict(job, i, True)


def extract_test_info(build_dict, test_name):
    test_info = build_dict.copy()
    tests = test_info.pop('tests', None)
    if test_name not in tests.keys():
        return None
    test_info.update({'test_list':tests[test_name]})
    return test_info

def fetch_test_data(job, test_name):
    latest = _get_number_of_builds(job)
    builds = [make_build_dict(job, x) for x in xrange(1,latest+1)]
    builds = [extract_test_info(build, test_name) for build in builds if build != None]
    builds = [build for build in builds if build != None]
    return builds 

def fetch_jobs():
    all_jobs = []
    url = default+''
    opener = urllib.FancyURLopener()
    handle = opener.open(url)
    report = handle.read()
    jobs_page = BeautifulSoup(report, 'lxml')
    jobs = jobs_page.select('#projectstatus .model-link.inside')
    for i in range(1,len(jobs)):
        all_jobs.append(jobs[i].attrs['href'].split('/')[1])
    return = {'current': all_jobs,
                'legacy': [job for job in list(set(all_jobs) ^ os.listdir(path)) if job not in all_jobs]
            }

def generate_build_cache(remote=True):
    jobs = fetch_jobs()
    for job in jobs['current']:
        if "download" in job or "perf" in job:
            continue
        create_all_build_dicts(job)
    print "Cached:"
    for job in os.listdir(path):
        print job

def fetch_all_job_reports():
    jobs = fetch_jobs()
    for job in jobs:
        if 'perf' in job or 'download' in job:
            continue
        else:
            fetch_all_builds(job)

def list_tests(job):
    latest = _get_number_of_builds(job)
    build_dict = make_build_dict(job, latest)
    while build_dict == None:
        if latest < 1:
            return 'No tests exist'
        latest-=1
        build_dict = make_build_dict(job, latest)
    return build_dict['tests'].keys()
