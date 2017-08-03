import unittest
from mock import MagicMock, patch

from models.cinema import Cinema
from models.movie import Movie
from models.showing import Showing
from models.showing_booking import ShowingBooking
from plugins.dbmanage_handler import DbManageHandler
from plugins.crawled_movie_handler import CrawledMovieHandler


class TestPlugins(unittest.TestCase):
    @patch('plugins.dbmanage_handler.db_connect')
    @patch('plugins.dbmanage_handler.drop_table_if_exist')
    @patch('plugins.dbmanage_handler.create_table')
    def test_dbmanage_handler(self, create_table_mock,
                              drop_table_if_exist_mock,
                              db_connect_mock):
        handler = DbManageHandler()
        handler.logger = MagicMock()
        handler.setup(MagicMock())
        handler.table_map = {
            'all': [Cinema, Movie, ShowingBooking, Showing],
            'movie': [Movie],
            'cinema': [Cinema],
            'showing': [ShowingBooking, Showing]
        }
        data = {
            "action": "init",
            "target": "all"
        }
        handler.handle(data)
        self.assertEqual(drop_table_if_exist_mock.call_count, 4)
        drop_table_if_exist_mock.assert_any_call(handler.engine, Cinema)
        drop_table_if_exist_mock.assert_any_call(handler.engine, Movie)
        drop_table_if_exist_mock.assert_any_call(
            handler.engine, ShowingBooking)
        drop_table_if_exist_mock.assert_any_call(handler.engine, Showing)
        create_table_mock.assert_called_once_with(handler.engine)

    @patch('plugins.crawled_movie_handler.add_item_to_database')
    @patch('plugins.crawled_movie_handler.db_connect')
    def test_scraped_movie_handler(self, db_connect_mock,
                                   add_item_to_database_mock):
        handler = CrawledMovieHandler()
        handler.logger = MagicMock()
        handler.setup(MagicMock())
        data = {
            "title": "Your Name.",
            "current_cinema_count": 1
        }
        Movie.get_movie_if_exist = MagicMock(return_value=None)
        handler.handle(data)
        self.assertEqual(add_item_to_database_mock.call_count, 1)
        args, kwargs = add_item_to_database_mock.call_args_list[0]
        self.assertEqual(len(args), 2)
        self.assertEqual(args[1].current_cinema_count, 1)

        exist_data = {
            "title": "Your Name.",
            "current_cinema_count": 3
        }
        exist_movie = Movie(**exist_data)
        Movie.get_movie_if_exist = MagicMock(return_value=exist_movie)
        handler.handle(data)
        self.assertEqual(add_item_to_database_mock.call_count, 2)
        expected_count = \
            data["current_cinema_count"] + exist_data["current_cinema_count"]
        args, kwargs = add_item_to_database_mock.call_args_list[1]
        self.assertEqual(len(args), 2)
        self.assertEqual(args[1].current_cinema_count, expected_count)
