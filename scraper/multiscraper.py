from scraper import JenkinsScraper
import itertools

class MultiScraper(object):
    def __init__(self, *arg):
        assert(reduce(lambda x, y: type(x) == JenkinsScraper, arg))
        self.scrapers = arg

    def which_scraper(self, job, offline=False):
        for scraper in self.scrapers:
            jobs = scraper.fetch_jobs(offline)
            if job in jobs['current'] or job in jobs['legacy']:
                return scraper

    def get_local_builds(self, job):
        for scraper in self.scrapers:
            builds = scraper.get_local_builds(job)
            if builds > 0:
                return builds
        return []

    def fetch_jobs(self, offline=False):
        jobs = [scraper.fetch_jobs(offline) for scraper in self.scrapers]
        return reduce(lambda x, y: {'current': x['current']+y['current'], 'legacy': x['legacy']+y['legacy']}, jobs)

    def fetch_build_html(self, job, build, offline=False):
        scraper = self.which_scraper(job, offline)
        if not scraper:
            return False
        return scraper.fetch_build_html(job, build, offline)

    def fetch_test_data(self, job, test_name, offline=False):
        scraper = self.which_scraper(job, offline)
        return scraper.fetch_test_data(job, test_name, offline)

    def generate_build_cache(self, offline=False):
        for scraper in self.scrapers:
            scraper.generate_build_cache(offline)

    def fetch_all_job_reports(self):
        for scraper in self.scrapers:
            scraper.fetch_all_job_reports()

    def list_tests(self, job, offline=False):
        scraper = self.which_scraper(job, offline)
        return scraper.list_tests(job, offline)


