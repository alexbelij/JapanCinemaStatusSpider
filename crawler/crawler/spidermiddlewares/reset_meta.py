from scrapy.http import Request
from crawler.utils import sc_log_setup


class ResetMetaMiddleware(object):

    def __init__(self, settings):
        self.setup(settings)

    def setup(self, settings):
        '''
        Does the actual setup of the middleware
        '''
        # set up the default sc logger
        self.logger = sc_log_setup(settings)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_spider_output(self, response, result, spider):
        '''
        reset some meta value to default if not setted in request
        '''
        self.logger.debug("processing reset meta spider middleware")
        for x in result:
            # only operate on requests
            if isinstance(x, Request):
                self.logger.debug("found request")
                if 'dont_merge_cookies' not in x.meta:
                    if 'dont_merge_cookies' in response.meta:
                        x.meta['dont_merge_cookies'] = False
            yield x
