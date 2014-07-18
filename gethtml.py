from bs4 import BeautifulSoup
import urllib
import sys
import os

path = "templates/Reports"
default='http://selenium.qa.mtv2.mozilla.com:8080/view/B2G/'

# Fetch number of builds for a given job
def _get_number_of_builds(job):
    base_url = default+'job/'
    opener = urllib.FancyURLopener()
    handle = opener.open(base_url+job+'/')
    report = handle.read()
    soup = BeautifulSoup(report, 'lxml')
    if v:
        print "%s:%s" %(job, soup.select('#buildHistory .build-row')[0].text.split()[0][1:])
    return int(soup.select('#buildHistory .build-row')[0].text.split()[0][1:])

# Check whether or not the appropriate directories exist, and if they don't, make them.
def _fetch_skip_check(job):
    if not os.path.exists('%s' % (path)):
        os.mkdir('%s' % (path))

    if not os.path.exists('%s/%s' % (path, job)):
        os.mkdir('%s/%s' % (path, job))

    if not os.path.exists('%s/%s/fetch.txt' % (path, job)):
        open('%s/%s/fetch.txt' % (path, job), 'a').close()

    if not os.path.exists('%s/%s/skip.txt' % (path, job)):
        open('%s/%s/skip.txt' % (path, job), 'a').close()


# return all B2G jobs
def _fetch_jobs():
    all_jobs = []
    url = default+''
    opener = urllib.FancyURLopener()
    handle = opener.open(url)
    report = handle.read()
    jobs_page = BeautifulSoup(report, 'lxml')
    jobs = jobs_page.select('#projectstatus .model-link.inside')
    for i in range(1,len(jobs)):
        all_jobs.append(jobs[i].attrs['href'].split('/')[1])
    return all_jobs

# Fetch the HTML Report of a Job build
def fetch_build_html(job, build):

    _fetch_skip_check(job)

    skip = open('%s/%s/skip.txt' % (path, job), 'r+')
    skipped = skip.read().split('\n')
    fetch = open('%s/%s/fetch.txt' % (path, job), 'r+')
    fetched = fetch.read().split('\n')

    if build in skipped:
        if v:
            print 'No HTML Report for %s:%s! Skipping...' % (job, str(build))
        return False
    if build in fetched:
        if v:
            print '%s:%s Already Fetched!' % (job, build) 
        return True

    base_url = default+'job/'
    base_suffix = '/HTML_Report/index.html'
    opener = urllib.FancyURLopener()
    handle = opener.open(base_url+job+'/'+str(build)+base_suffix)
    report = handle.read()
    soup = BeautifulSoup(report)

    if soup.body == None or 'Not found' in soup.body.text or soup.title.text != 'Test Report':
        if v:
            print 'No HTML Report for %s:%s! Skipping...' % (job, str(build))
        skip.write(str(build)+'\n')
        return False

    f = open('%s/%s/%s.html' % (path, job, build), 'w')
    f.write(report)
    if v:
        print '%s:%s Fetched!' % (job, build) 
    fetch.write(str(build)+'\n')
    return True

def fetch_all_builds(job):
    _fetch_skip_check(job)
    latest = _get_number_of_builds(job)
    fetch = open('%s/%s/fetch.txt' % (path, job), 'r+')
    skip = open('%s/%s/skip.txt' % (path, job), 'r+')
    skipped = skip.read()
    fetched = fetch.read()

    for i in xrange(1, latest+1):
        if str(i)+'\n' in skipped:
            if v:
                print 'No HTML Report for %s:%s! Skipping...' % (job, str(i))
            continue
        if str(i)+'\n' in fetched:
            if v:
                print '%s:%s Already Fetched!' % (job, i) 
            continue
        print "Fetching %s:%s" % (job, i)
        fetch_build_html(job, i)

def fetch_all_job_reports():
    jobs = _fetch_jobs()
    for job in jobs:
        if 'perf' in job or 'download' in job:
            continue
        else:
            fetch_all_builds(job)

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == 'v':
        v = True
    else:
        v = False
    print 'Fetching all job build reports...'
    fetch_all_job_reports()
    print "Job's done!"

