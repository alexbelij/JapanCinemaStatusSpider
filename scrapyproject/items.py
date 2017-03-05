# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import re
import unicodedata
import scrapy


special_cinema = {
    'TOHOシネマズシャンテ': {
        r'SCREEN': r'CHANTER-'
    },
    'TOHOシネマズスカラ座・みゆき座': {
        r'^スカラ座$': r'SCALAZA',
        r'^みゆき座$': r'MIYUKIZA'
    },
    'TOHOシネマズ日劇': {
        r'日劇': r'NICHIGEKI-'
    },
    'TOHOシネマズ高岡': {
        r'シネマ': r'SCREEN'
    },
    'TOHOシネマズなんば': {
        r'^\((\w+)\)(\w+)$': r'\1\2'
    },
    'TOHOシネマズ天神': {
        r'^(\w+)\((\w+)\)$': r'\2\1'
    }
}


def standardize_cinema_name(cinema_name):
    """
    standardize cinema name
    this function has to handle several special cases include:
    - name includes full width charaters
      example: "ＴＯＨＯシネマズなんば　本館・別館"
    - name may include or not include space depends on crawling site
      example: " ＴＯＨＯシネマズなんば　本館・別館 "
    - cinema may divide into several sub cinemas depends on crawling site
      example: "TOHOシネマズなんば本館" "TOHOシネマズなんば別館"
    - name may include or not include parenthesis depends on crawling site
      example: "TOHOシネマズなんば　(本館・別館)"
    """
    # first, make sure only half width charaters left
    cinema_name = unicodedata.normalize('NFKC', cinema_name)
    # TODO
    return cinema_name


def standardize_screen_name(screen_name, cinema_name):
    """
    standardize screen name, make sure screen can be queried in database
    this function has to handle several special cases include:
    - name includes full width charaters
      example: "NICHIGEKI－３"
    - name word order may be different
      example: "別館SCREEN10" "SCREEN10別館"
    - name may include or not include space depends on crawling site
      example: "別館SCREEN10" " 別館 SCREEN10 "
    - name may be english or katakana
      example: "本館SELECT" "セレクト"
    - name may include or not include parenthesis depends on crawling site
      example: "本館SELECT" "(本館)SELECT"
    """
    # first, make sure only half width charaters left
    cinema_name = unicodedata.normalize('NFKC', cinema_name)
    # TODO
    return screen_name


def is_screen_name_special(screen_name, cinema_name):
    """
    check if given screen name is not same with screen name on cinemas table
    """
    # example:
    # (本館)SELECT -> 本館SELECT
    # SCREEN1(本館) -> 本館SCREEN1
    # シネマ1 -> SCREEN1
    # みゆき座 -> MIYUKIZA
    # 日劇1 -> NICHIGEKI-1
    # (TOHOシネマズシャンテ) SCREEN1 -> CHANTER-1
    return cinema_name in special_cinema


def convert_special_screen_name(screen_name, cinema_name):
    """
    some cinema have different screen name in order page and institution page,
    so we need to keep them same for further use.
    convert should only happen in toho_cinema spider
    """
    # replace special cinema screens
    if cinema_name in special_cinema:
        for key in special_cinema[cinema_name]:
            screen_name = re.sub(
                key, special_cinema[cinema_name][key], screen_name)
    return screen_name


def standardize_name(name):
    """
    remove all spaces, normalize full width characters to double width
    """
    name = unicodedata.normalize('NFKC', name)
    name = name.replace(' ', '')
    return name


class Cinema(scrapy.Item):
    name = scrapy.Field()
    county = scrapy.Field()
    company = scrapy.Field()
    screens = scrapy.Field()


class Session(scrapy.Item):
    title = scrapy.Field()
    title_en = scrapy.Field()
    start_time = scrapy.Field()
    end_time = scrapy.Field()
    cinema_name = scrapy.Field()
    screen = scrapy.Field()
    book_status = scrapy.Field()
    book_seat_count = scrapy.Field()
    total_seat_count = scrapy.Field()
    record_time = scrapy.Field()
