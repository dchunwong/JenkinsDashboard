import flask as f
from flask import Flask, render_template, request, redirect, abort, flash
from scraper import scraper as scrape
from time import strptime
import json

app = Flask(__name__, static_folder='static', static_url_path='')

@app.route('/')
def display_search():
    jobs = list(set(scrape.fetch_jobs()))
    jobs = sorted([job for job in jobs if 'download' not in job and 'perf' not in job])
    return render_template('search.html', jobs = jobs)

@app.route('/job/<job>/')
def redirect_job(job):
    return redirect('job/%s/tests' % job)

@app.route('/job/<job>/tests/')
def display_tests(job):
    return render_template('list_tests.html', tests ={'job':job, 'tests':sorted(scrape.list_tests(job))})
    
@app.route('/job/<job>/<build>/')
def display_build(job, build):
    if(scrape.fetch_build_html(job, build)):
        return render_template('Reports/%s/%s.html' % (job, build))
    else:
        return "HTML Report doesn't exist for this build :("

@app.route('/job/<job>/tests/<test>/')
def display_test_stats(job, test):
    test_info = scrape.fetch_test_data(job, test)
    return render_template('test_stats.html', tests = test_info)

@app.route('/job/<job>/tests/<test>/<year>/<month>/<day>/')
def display_test_day_stats(job, test, year, month, day):
    test_info = scrape.fetch_test_data(job,test)
    tests =[]
    for test in test_info:
        date = strptime(test['date'], '%d-%b-%Y')
        if date.tm_year == int(year) and date.tm_mon == int(month) and date.tm_mday == int(day):
            tests.append(test)
    return render_template('test_stats.html', tests = [test for test in tests])

@app.route('/search/', methods=['POST'])
def fetch():
    job = request.form['job']
    build = request.form['build']
    test = request.form['test']
    if test == '':
        return redirect('job/%s/%s' % (job, build))
    elif build == '' and test != '':
        return redirect('job/%s/tests/%s' % (job, test))
    elif test != '':
        return redirect('job/%s/tests' % (job))
    else: 
        return redirect('/')

if __name__ == '__main__':
    scrape.generate_build_cache()
    app.run(host='0.0.0.0', port=3030, debug=True, use_reloader=False)