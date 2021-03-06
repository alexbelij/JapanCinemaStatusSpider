import copy
from optparse import OptionGroup
import arrow
from scrapy.commands.crawl import Command


class CrawlCommand(Command):
    def short_desc(self):
        return "Override default crawl command, support more options"

    def long_desc(self):
        return """Override default crawl command as we need to add some
                option for our spider and neeed to support run multiple
               spiders in single process"""

    def add_options(self, parser):
        Command.add_options(self, parser)
        # custom options
        group = OptionGroup(parser, "Custom Options")
        group.add_option("--all_showing", action="store_true", default=False,
                         help="run all showing spider")
        group.add_option("--use_proxy", action="store_true", default=False,
                         help="use setting's proxy when crawling")
        group.add_option("--require_js", action="store_true", default=False,
                         help="use phantomjs to process page")
        group.add_option("--keep_old_data", action="store_true",
                         default=False, help="keep old data when crawling")
        group.add_option("--crawl_all_cinemas", action="store_true",
                         default=False, help="crawl all cinemas")
        group.add_option("--crawl_all_movies", action="store_true",
                         default=False, help="crawl all movies")
        group.add_option("--crawl_booking_data", action="store_true",
                         default=False,
                         help="crawl booking data for each crawled showing")
        group.add_option("--movie_list",  action="append",
                         default=[], metavar="moviename",
                         help="crawl movie list, default is 君の名は。")
        group.add_option("--cinema_list",  action="append",
                         default=[], metavar="cinemaname",
                         help="crawl cinema list")
        tomorrow = arrow.now('UTC+9').shift(days=+1)
        group.add_option("--date", default=tomorrow.format('YYYYMMDD'),
                         help="crawl date, default is tomorrow")
        parser.add_option_group(group)

    def process_options(self, args, opts):
        Command.process_options(self, args, opts)

    def run(self, args, opts):
        # pass custom option to spiders
        opts.spargs = {}
        opts.spargs['use_proxy'] = opts.use_proxy
        opts.spargs['require_js'] = opts.require_js
        opts.spargs['keep_old_data'] = opts.keep_old_data
        opts.spargs['crawl_all_cinemas'] = opts.crawl_all_cinemas
        opts.spargs['crawl_all_movies'] = opts.crawl_all_movies
        opts.spargs['crawl_booking_data'] = opts.crawl_booking_data
        opts.spargs['movie_list'] = opts.movie_list
        opts.spargs['cinema_list'] = opts.cinema_list
        opts.spargs['date'] = opts.date
        if opts.all_showing:
            self.run_multiple_spiders(args, opts)
        else:
            Command.run(self, args, opts)

    def run_multiple_spiders(self, args, opts):
        # option passed to spider need deep copy
        self.crawler_process.crawl('aeon', **copy.deepcopy(opts.spargs))
        self.crawler_process.crawl('toho_v2', **copy.deepcopy(opts.spargs))
        self.crawler_process.crawl('united', **copy.deepcopy(opts.spargs))
        self.crawler_process.crawl('movix', **copy.deepcopy(opts.spargs))
        self.crawler_process.crawl('kinezo', **copy.deepcopy(opts.spargs))
        self.crawler_process.crawl('site109', **copy.deepcopy(opts.spargs))
        self.crawler_process.crawl('korona', **copy.deepcopy(opts.spargs))
        self.crawler_process.crawl('cinemasunshine',
                                   **copy.deepcopy(opts.spargs))
        self.crawler_process.crawl('forum', **copy.deepcopy(opts.spargs))
        self.crawler_process.start()
        return
