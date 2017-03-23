# -*- coding: utf-8 -*-
import unicodedata
import re
from scrapyproject.items import standardize_screen_name
from scrapyproject.spiders.cinema_spider import CinemaSpider
from scrapyproject.utils.site_utils import extract_seat_number


class WalkerplusCinemaSpider(CinemaSpider):
    """
    cinema info spider for http://movie.walkerplus.com/
    """
    name = "walkerplus_cinema"
    allowed_domains = ["movie.walkerplus.com"]
    start_urls = ['http://movie.walkerplus.com/theater/']

    # settings for cinema_spider, sone are not used as we will override
    # screen data extract function
    county_xpath = '//div[@id="rootAreaList"]//a'
    cinema_xpath = '//div[@id="theaterList_wrap"]//li/a'
    cinema_site_xpath = '//a[text()="映画館公式サイト"]/@href'

    def is_county_crawl(self, county):
        """
        filter useless county
        """
        county_name = county.xpath('.//text()').extract_first()
        if county_name in ['札幌', '道央', '道北', '道南', '道東']:
            return False
        else:
            return True

    def adjust_cinema_url(self, url):
        """
        adjust cinema page's url if needed
        """
        return url.replace('schedule.html', '')

    def parse_screen_data(self, response, cinema):
        """
        override as screen text on this site is a bit different
        """
        screen_raw_text = response.xpath(
            '//th[text()="座席数"]/../td/text()[2]').extract_first()
        screen_raw_text = unicodedata.normalize('NFKC', screen_raw_text)
        screen_raw_text = screen_raw_text.strip()
        screen = {}
        screen_count = 0
        total_seats = 0
        match = re.findall(r" ?(.+?)・(\d+)", screen_raw_text)
        # if no match found, use pattern for single screen
        if not match:
            match = re.findall(r"(\d+)", screen_raw_text)
            if match:
                match[0] = ("スクリーン", match[0])
        for screen_name, seat_str in match:
            screen_name = standardize_screen_name(screen_name, cinema)
            # add cinema name into screen name to avoid conflict for
            # sub cinemas
            screen_name = response.meta['cinema_name'] + "#" + screen_name
            seat_count = extract_seat_number(seat_str)
            screen_count += 1
            total_seats += seat_count
            screen[screen_name] = str(seat_count)
        return screen, screen_count, total_seats
