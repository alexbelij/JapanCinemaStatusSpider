import unittest

from crawler.showingspiders.kinezo import KinezoSpider
from .spider_mixin import BaseSpiderRunCase


class CustomSpider(KinezoSpider):
    '''
    Overridden spider name for testing
    '''
    name = "test-spider"


class TestSpider(unittest.TestCase, BaseSpiderRunCase):
    def setUp(self):
        BaseSpiderRunCase.setUp(
            self, 'http://kinezo.jp/pc/', CustomSpider, 60)

    def is_message_count(self, the_dict):
        # item is Showing or ShowingBooking
        if the_dict:
            if ('showing' not in the_dict and 'title' in the_dict
                    and the_dict['title'] and 'seat_type' in the_dict
                    and the_dict['seat_type']):
                return True
            elif ('showing' in the_dict and 'book_status' in the_dict
                    and the_dict['book_status']):
                return True
        return False

    def tearDown(self):
        BaseSpiderRunCase.tearDown(self)


if __name__ == '__main__':
    unittest.main()
