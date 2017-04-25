# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from sqlalchemy.orm import sessionmaker
from scrapyproject.models import (Cinema, Showing, ShowingBooking, Movie,
                                  db_connect, drop_table_if_exist,
                                  create_table)
from scrapyproject.items import (CinemaItem, ShowingItem, ShowingBookingItem,
                                 MovieItem)
from scrapyproject.utils import (use_cinema_database,
                                 use_showing_database,
                                 use_movie_database)


class DataBasePipeline(object):
    """
    pipeline to add item to database
    will keep exist data if spider has attribute 'keep_old_data'
    """
    def __init__(self, database):
        self.database = database

    @classmethod
    def from_crawler(cls, crawler):
        return cls(database=crawler.settings.get('DATABASE'))

    def open_spider(self, spider):
        self.keep_old_data = (
            True if hasattr(spider, 'keep_old_data') else False)
        engine = db_connect()
        if not self.keep_old_data:
            # drop data
            if use_showing_database(spider):
                drop_table_if_exist(engine, ShowingBooking)
                drop_table_if_exist(engine, Showing)
            elif use_cinema_database(spider):
                drop_table_if_exist(engine, Cinema)
            elif use_movie_database(spider):
                drop_table_if_exist(engine, Movie)
        create_table(engine)
        self.Session = sessionmaker(bind=engine)

    def close_spider(self, spider):
        pass

    def process_item(self, item, spider):
        """
        use cinema table if spider has attribute "use_cinema_database"
        use showing table if spider has attribute "use_showing_database"
        a spider should not have both attributes
        """
        if isinstance(item, CinemaItem):
            return self.process_cinema_item(item, spider)
        elif isinstance(item, ShowingItem):
            return self.process_showing_item(item, spider)
        elif isinstance(item, ShowingBookingItem):
            return self.process_showing_booking_item(item, spider)
        elif isinstance(item, MovieItem):
            return self.process_movie_item(item, spider)

    def process_cinema_item(self, item, spider):
        cinema = Cinema(**item)
        exist_cinema = Cinema.get_cinema_if_exist(cinema)
        if not exist_cinema:
            # if data do not exist in database, add it
            self.add_item_to_database(cinema)
        else:
            # otherwise check if it should be merged to exist record
            # merge strategy:
            # - if exist data is crawled from other source, only add names
            # and screens to exist data;
            # - if cinema do not have site url, item is treated as duplicate
            # and dropped;
            # - otherwise, merge all data
            if cinema.source != exist_cinema.source:
                # replace when new cinema data crawled more screens
                if cinema.screen_count > exist_cinema.screen_count:
                    exist_cinema.merge(
                        cinema, merge_method=Cinema.MergeMethod.replace)
                else:
                    exist_cinema.merge(
                        cinema, merge_method=Cinema.MergeMethod.info_only)
                self.add_item_to_database(exist_cinema)
            elif cinema.site:
                exist_cinema.merge(
                    cinema, merge_method=Cinema.MergeMethod.update_count)
                self.add_item_to_database(exist_cinema)
        return item

    def process_showing_item(self, item, spider):
        showing = Showing(**item)
        # if data do not exist in database, add it
        if not Showing.get_showing_if_exist(showing):
            self.add_item_to_database(showing)
        return item

    def process_showing_booking_item(self, item, spider):
        showing_booking = ShowingBooking()
        showing_booking.from_item(item)

        # if showing exists use its id in database
        exist_showing = Showing.get_showing_if_exist(showing_booking.showing)
        if exist_showing:
            old_showing = showing_booking.showing
            showing_booking.showing = exist_showing
            showing_booking.showing.title = old_showing.title
            showing_booking.showing.title_en = old_showing.title_en
            showing_booking.showing.start_time = old_showing.start_time
            showing_booking.showing.end_time = old_showing.end_time
            showing_booking.showing.cinema_name = old_showing.cinema_name
            showing_booking.showing.cinema_site = old_showing.cinema_site
            showing_booking.showing.screen = old_showing.screen
            showing_booking.showing.seat_type = old_showing.seat_type
            showing_booking.showing.total_seat_count = \
                old_showing.total_seat_count
            showing_booking.showing.source = old_showing.source
        # then add self
        self.add_item_to_database(showing_booking)
        return item

    def process_movie_item(self, item, spider):
        movie = Movie(**item)
        # if data do not exist in database, add it
        if not Movie.get_movie_if_exist(movie):
            self.add_item_to_database(movie)
        return item

    def add_item_to_database(self, db_item):
        session = self.Session()
        try:
            db_item = session.merge(db_item)
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
