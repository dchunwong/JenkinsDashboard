import flask as f
from flask import Flask, render_template, request, redirect, abort, flash
from scraper import scraper as scrape
from time import strptime

app = Flask(__name__)

@app.route('/<job>/<build>/')
def display_build(job, build):
    if(scrape.fetch_build_html(job, build)):
        return render_template('Reports/%s/%s.html' % (job, build))
    else:
        return "HTML Report doesn't exist for this build :("

@app.route('/<job>/tests/<test>/<year>/<month>/<day>/')
def display_test_day_stats(job, test, year, month, day):
    test_info = scrape.fetch_test_data(job,test)
    tests =[]
    for test in test_info:
        date = strptime(test['date'], '%d-%b-%Y')
        if date.tm_year == int(year) and date.tm_mon == int(month) and date.tm_mday == int(day):
            tests.append(test)
    return render_template('test_stats.html', tests = tests)

@app.route('/<job>/tests/<test>/')
def display_test_stats(job, test):
    test_info = scrape.fetch_test_data(job, test)
    return render_template('test_stats.html', tests = test_info)

@app.route('/<job>/tests/')
def display_tests(job):
    return render_template('list_tests.html', tests ={'job':job, 'tests':scrape.list_tests(job)})

@app.route('/')
def display_search():
    return render_template('search.html')

@app.route('/search/', methods=['POST'])
def fetch():
    job = request.form['job']
    build = request.form['build']
    test = request.form['test']
    if test == '':
        return redirect('/%s/%s' % (job, build))
    elif build == '' and test != '':
        return redirect('/%s/tests/%s' % (job, test))
    else: 
        return redirect('/')

if __name__ == '__main__':
    scrape.generate_build_cache()
    app.run(host='0.0.0.0', port=3030, debug=True, use_reloader=False)