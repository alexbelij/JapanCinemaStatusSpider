# -*- coding: utf-8 -*-
import copy
import re
import arrow
import scrapy
from scrapyproject.showingspiders.showing_spider import ShowingSpider
from scrapyproject.items import (Showing, standardize_cinema_name,
                                 standardize_screen_name)
from scrapyproject.utils.site_utils import UnitedUtil
from scrapyproject.utils.test_utils import TestUtility


class UnitedSpider(ShowingSpider):
    """
    united site spider.
    """
    name = "united"
    allowed_domains = ["www.unitedcinemas.jp"]
    start_urls = [
        'http://www.unitedcinemas.jp/index.html'
    ]

    cinema_list = ['ユナイテッド・シネマとしまえん']

    custom_settings = {
        'COOKIES_DEBUG': True
    }

    def parse(self, response):
        """
        crawl theater list data first
        """
        # TODO proxy encode problem
        theater_list = response.xpath(
            '//section[@class="rcol searchTheater"]//li')
        for theater_element in theater_list:
            if theater_element.xpath('./@class').extract_first() == "area":
                continue
            curr_cinema_url = theater_element.xpath(
                './a/@href').extract_first()
            cinema_img = theater_element.xpath('./img/@src').extract_first()
            cinema_name = theater_element.xpath('./a/img/@alt').extract_first()
            if cinema_img is not None:
                if "icon_uc_ss.gif" in cinema_img:
                    cinema_name = "ユナイテッド・シネマ" + cinema_name
                elif "icon_cpx_ss.gif" in cinema_img:
                    cinema_name = "シネプレックス" + cinema_name
            standardize_cinema_name(cinema_name)
            if not self.is_cinema_crawl([cinema_name]):
                continue
            cinema_name_en = curr_cinema_url.split('/')[-2]
            schedule_url = self.generate_cinema_schedule_url(
                cinema_name_en, self.date)
            request = scrapy.Request(schedule_url, callback=self.parse_cinema)
            request.meta["cinema_site"] = response.urljoin(curr_cinema_url)
            request.meta["cinema_name"] = cinema_name
            yield request

    def generate_cinema_schedule_url(self, cinema_name_en, show_day):
        """
        json data url for single cinema, all movies of curr cinema
        """
        date = show_day[:4] + '-' + show_day[4:6] + '-' + show_day[6:]
        url = 'http://www.unitedcinemas.jp/{cinema_name_en}'\
              '/daily.php?date={date}'.format(
                  cinema_name_en=cinema_name_en, date=date)
        return url

    def parse_cinema(self, response):
        TestUtility.write_to_unique_html(response.text)
        data_proto = Showing()
        data_proto['cinema_name'] = response.meta['cinema_name']
        data_proto["cinema_site"] = response.meta['cinema_site']
        result_list = []
        movie_section_list = response.xpath('//ul[@id="dailyList"]/li')
        for curr_movie in movie_section_list:
            self.parse_movie(response, curr_movie, data_proto, result_list)
        for result in result_list:
            if result:
                yield result

    def parse_movie(self, response, curr_movie, data_proto, result_list):
        """
        parse movie showing data
        """
        title = curr_movie.xpath('./h3/span/a[1]/text()').extract_first()
        title_list = [title]
        if not self.is_movie_crawl(title_list):
            return
        movie_data_proto = copy.deepcopy(data_proto)
        movie_data_proto['title'] = title
        screen_section_list = curr_movie.xpath('./ul/li')
        for curr_screen in screen_section_list:
            self.parse_screen(response, curr_screen,
                              movie_data_proto, result_list)

    def parse_screen(self, response, curr_screen, data_proto, result_list):
        screen_data_proto = copy.deepcopy(data_proto)
        screen_name = curr_screen.xpath('./p/a/img/@alt').extract_first()
        screen_name = 'screen' + re.findall(r'\d+', screen_name)[0]
        screen_data_proto['screen'] = standardize_screen_name(
            screen_name, screen_data_proto['cinema_name'])
        show_section_list = curr_screen.xpath('./ol/li')
        for curr_showing in show_section_list:
            self.parse_showing(response, curr_showing,
                               screen_data_proto, result_list)

    def parse_showing(self, response, curr_showing, data_proto, result_list):
        def parse_time(time_str):
            time = time_str.split(":")
            return (int(time[0]), int(time[1]))

        showing_data_proto = copy.deepcopy(data_proto)
        start_time = curr_showing.xpath(
            './div/ol/li[@class="startTime"]/text()').extract_first()
        start_hour, start_minute = parse_time(start_time)
        showing_data_proto['start_time'] = self.get_time_from_text(
            start_hour, start_minute)
        end_time = curr_showing.xpath(
            './div/ol/li[@class="endTime"]/text()').extract_first()[1:]
        end_hour, end_minute = parse_time(end_time)
        showing_data_proto['end_time'] = self.get_time_from_text(
            end_hour, end_minute)
        # handle free order seat type showings
        seat_type = curr_showing.xpath(
            './div/ul/li[@class="seatIcon"]/img/@src').extract_first()
        showing_data_proto['seat_type'] = \
            UnitedUtil.standardize_seat_type(seat_type)
        book_status = curr_showing.xpath(
            './div/ul/li[@class="uolIcon"]//img[1]/@src').extract_first()
        showing_data_proto['book_status'] = \
            UnitedUtil.standardize_book_status(book_status)
        if (showing_data_proto['seat_type'] == 'FreeSeat' or
                showing_data_proto['book_status'] in ['SoldOut', 'NotSold']):
            # sold out or not sold, seat set to 0
            showing_data_proto['book_seat_count'] = 0
            showing_data_proto['total_seat_count'] = 0
            showing_data_proto['record_time'] = arrow.now()
            showing_data_proto['source'] = self.name
            result_list.append(showing_data_proto)
            return
        else:
            # normal, need to crawl book number on order page
            # we will visit schedule page again to generate independent cookie
            # as same cookie will lead to confirm page
            url = curr_showing.xpath(
                './div/ul/li[@class="uolIcon"]/a/@href').extract_first()
            # determine if next page is 4dx confirm page by title
            if '4DX' in showing_data_proto['title']:
                request = scrapy.Request(
                    url, callback=self.parse_4dx_confirm_page)
            else:
                request = scrapy.Request(
                    url, callback=self.parse_normal_showing)
            request.meta["data_proto"] = showing_data_proto
            # use independent cookie to avoid affecting each other
            request.meta["cookiejar"] = url
            result_list.append(request)

    def parse_4dx_confirm_page(self, response):
        url = response.xpath('//form/@action').extract_first()
        url = response.urljoin(url)
        request = scrapy.Request(url, method='POST',
                                 callback=self.parse_normal_showing)
        request.meta["data_proto"] = response.meta['data_proto']
        yield request

    def parse_normal_showing(self, response):
        result = response.meta["data_proto"]
        total_seat_count = int(response.xpath(
            '//span[@class="seat"]/text()').extract_first())
        result['book_seat_count'] = len(response.xpath(
            '//img[contains(@src,"lb_non_selected")]'))
        result['total_seat_count'] = total_seat_count
        result['record_time'] = arrow.now()
        result['source'] = self.name
        yield result
