import re


class ScreenUtils(object):
    special_name_list = [
        ["PREMIER", "プレミア"],
        ["SELECT", "セレクト"],
        ["SCALAZA", "スカラ座"],  # special case for TOHOシネマズスカラ座・みゆき座
        ["MIYUKIZA", "みゆき座"],  # special case for TOHOシネマズスカラ座・みゆき座
        ["プラチナ"],  # special case for 新宿ピカデリー
        ["グランドEXE"],  # special case for 109シネマズ二子玉川
    ]

    @staticmethod
    def get_seat_count(screens, cinema_name, target_screen):
        """
        get screen seat count from given data.
        """
        # TODO use map reduce to rewrite
        remain_screens = ScreenUtils.query_by_number(
            screens, cinema_name, target_screen)
        if len(remain_screens) == 1:
            return list(remain_screens.values())[0]
        remain_screens = ScreenUtils.query_by_special_name(
            remain_screens, cinema_name, target_screen)
        if len(remain_screens) == 1:
            return list(remain_screens.values())[0]
        remain_screens = ScreenUtils.query_by_sub_cinema(
            remain_screens, cinema_name, target_screen)
        if len(remain_screens) == 1:
            return list(remain_screens.values())[0]
        return 0

    @staticmethod
    def query_by_regex(regex_str, screens):
        screen_name_list = screens.keys()
        match_screens = {}
        for curr_screen_name in screen_name_list:
            match = re.findall(regex_str, curr_screen_name)
            if match:
                match_screens[curr_screen_name] = screens[curr_screen_name]
        return match_screens

    @staticmethod
    def query_by_number(screens, cinema_name, target_screen):
        """
        get useful screens by its number,if no number in target screen name,
        function will fail and return all origin screens
        """
        # try to extract screen number
        screen_number = re.findall(r'.+?(\d+)', target_screen)
        if not screen_number:
            return screens
        screen_number = screen_number[-1]
        # convert to int once to remove pre 0 like "05"
        screen_number = str(int(screen_number))
        regex_str = r'^.+#[^0-9]+?' + screen_number + r'[^0-9]*?$'
        match_screens = ScreenUtils.query_by_regex(regex_str, screens)
        if not match_screens:
            return screens
        return match_screens

    @staticmethod
    def query_by_special_name(screens, cinema_name, target_screen):
        """
        get screen seat count by special name like:
        "PREMIER" "SELECT" "プレミア" "セレクト"
        """
        print("query_by_special_name")
        print(screens)
        print(cinema_name)
        print(target_screen)
        used_name_list = None
        for curr_name_list in ScreenUtils.special_name_list:
            for curr_name in curr_name_list:
                if curr_name in target_screen:
                    used_name_list = curr_name_list
                    break
        print(used_name_list)
        if used_name_list:
            # if find special name, use these screens
            for used_name in used_name_list:
                regex_str = r'^.+#.*?' + used_name + r'.*?$'
                match_screens = ScreenUtils.query_by_regex(regex_str, screens)
                if not match_screens:
                    continue
                else:
                    return match_screens
            return screens
        # if not have special name, filter all special screens
        result_screens = {}
        match_screens = []
        for curr_name_list in ScreenUtils.special_name_list:
            for used_name in curr_name_list:
                regex_str = r'^.+#.*?' + used_name + r'.*?$'
                match_screens += ScreenUtils.query_by_regex(regex_str, screens)
        print(match_screens)
        for key in screens:
            if key not in match_screens:
                result_screens[key] = screens[key]
        print(result_screens)
        if result_screens:
            return result_screens
        else:
            return screens

    @staticmethod
    def query_by_sub_cinema(screens, cinema_name, target_screen):
        """
        get screen seat count by sub cinema name ex:
        "アートフォーラム" and "フォーラム盛岡"
        """
        regex_str = r'^' + cinema_name + r'#.*?$'
        match_screens = ScreenUtils.query_by_regex(regex_str, screens)
        if not match_screens:
            return screens
        return match_screens