import flask as f
from flask import Flask, render_template, request, redirect, abort, flash
from scraper import scraper as scrape
import time

app = Flask(__name__, static_folder='static', static_url_path='')
offline = False


def get_filtered_jobs(offline):
    jobs = scrape.fetch_jobs(offline)
    current = sorted([job for job in jobs['current'] if 'download' not in job and 'perf' not in job])
    legacy = sorted([job for job in jobs['legacy'] if 'download' not in job and 'perf' not in job])
    return {"current":current, "legacy":legacy}

@app.route('/')
def display_search():

    return render_template('search.html', jobs = get_filtered_jobs(offline))

@app.route('/job/<job>/')
def redirect_job(job):
    return redirect('job/%s/tests' % job)

@app.route('/job/<job>/tests/')
def display_tests(job):
    return render_template('list_tests.html', jobs=get_filtered_jobs(offline), test_list = sorted(scrape.list_tests(job, offline)), job=job)
    
@app.route('/job/<job>/<build>/')
def display_build(job, build):
    if(scrape.fetch_build_html(job, build, offline)):
        return render_template('html_report.html',job=job, build=build, jobs = get_filtered_jobs(offline))
    else:
        return "HTML Report doesn't exist for this build :("

@app.route('/job/<job>/tests/<test>/')
def display_test_stats(job, test):
    test_info = scrape.fetch_test_data(job, test, job in scrape.fetch_jobs(offline)['legacy'])
    return render_template('test_stats.html', jobs=get_filtered_jobs(offline), tests = test_info, clearDate=1)

@app.route('/job/<job>/tests/<test>/<year>/<month>/<day>/')
def display_test_day_stats(job, test, year, month, day):
    test_info = scrape.fetch_test_data(job, test, job in scrape.fetch_jobs(offline)['legacy'])
    tests =[]
    for test in test_info:
        date = time.localtime(test['date'])
        if date.tm_year == int(year) and date.tm_mon == int(month) and date.tm_mday == int(day):
            tests.append(test)
    return render_template('test_stats.html', jobs=get_filtered_jobs(offline), tests = [test for test in tests], clearDate = 0)

@app.route('/search/', methods=['POST'])
def fetch():
    job = request.form['job']
    build = ''
    test = ''
    if 'build' in request.form.keys():
        build = request.form['build']
    if 'test' in request.form.keys():
        test = request.form['test']
    if build != '':
        return redirect('/job/%s/%s' % (job, build))
    elif test != '':
        return redirect('/job/%s/tests/%s' % (job, test))
    else:
        return redirect('/job/%s/tests' % job)

@app.route('/refreshing/', methods=['GET'])
def refresh():
    scrape.generate_build_cache(offline)
    return redirect('/')

@app.route('/api/job/<job>/tests')
def get_tests(job):
    q = request.args['q']
    return f.jsonify({"results":sorted([job for job in scrape.list_tests(job, offline) if q in job])})    

@app.route('/api/job/<job>/builds')
def get_builds(job):
    q = request.args['q']
    return f.jsonify({"results":[build for build in scrape.get_retrieved(job) if q in str(build)]})

if __name__ == '__main__':
    scrape.generate_build_cache(offline)
    app.run(host='0.0.0.0', port=3030, debug=True, use_reloader=False)
