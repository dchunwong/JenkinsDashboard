from scraper.scraper import JenkinsScraper
from scraper.multiscraper import MultiScraper

scrape = MultiScraper(JenkinsScraper('http://selenium.qa.mtv2.mozilla.com:8080/view/B2G/',
                                             'static/Reports/selenium',
                                             ['download', 'perf']),
                      JenkinsScraper('http://jenkins1.qa.scl3.mozilla.com/',
                                             'static/Reports/jenkins1',
                                             ['download', 'perf']))
scrape.generate_build_cache()