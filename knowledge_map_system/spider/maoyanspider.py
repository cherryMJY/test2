import django
django.setup()
from model.models import TDataAcquisitionLog, TEntityExtractionLog
from spider.base.driver import Driver
from model.mongodb import Mongodb
from django.utils import timezone
import time
import datetime


class MaoyanSpider(Driver):
    def __init__(self, isheadless=False, ismobile=False, isvirtualdisplay=False, isloadimages=True, isproxy=False,
                 spider_id='2'):
        Driver.__init__(self, log_file_name=spider_id, ismobile=ismobile, isvirtualdisplay=isvirtualdisplay,
                        isheadless=isheadless, isloadimages=isloadimages, isproxy=isproxy)
        self.boxoffice_col = Mongodb(db='knowledge', collection='text').get_collection()
        self.news_col = Mongodb(db='movies1', collection='news').get_collection()

    @staticmethod
    def find_key_from_value(dict, value):
        key_list = dict.keys()
        for key in key_list:
            if value == dict[key]:
                return key
        return None

    def get_boxoffice_infos_from_one_page(self, url="", datetime="", user_id=-1, repo_id=-1):
        """
        获取猫眼此时刻票房数据
        :param repo_id:
        :param user_id:
        :param datetime:
        :param url:
        :return:
        """
        self.fast_new_page(url=url)
        time.sleep(1)
        if not self.judge_web_element_exist_by_css_selector(css_selector="div.dashboard-content"):
            self.close_curr_page()
            return True
        theads = self.until_presence_of_all_elements_located_by_css_selector(css_selector="div.dashboard-list > table.dashboard-table.table-header > thead > tr > th")[1:]
        theads = [item.text for item in theads]
        if not self.judge_web_element_exist_by_css_selector(css_selector="div.movielist-container > div.movielist > table.dashboard-table > tbody > tr"):
            self.close_curr_page()
            return False
        boxoffice_infos = self.until_presence_of_all_elements_located_by_css_selector(css_selector="div.movielist-container > div.movielist > table.dashboard-table > tbody > tr")
        crwal_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        boxoffice_data_from_the_page = []
        for item in boxoffice_infos:
            one_boxoffice_data = {}
            boxoffice_info = self.until_presence_of_all_elements_located_by_css_selector(css_selector="td", ele=item)
            movie_name = self.until_presence_of_element_located_by_css_selector(css_selector="div > div.moviename-desc > p.moviename-name", ele=boxoffice_info[0])
            movie_info = self.until_presence_of_all_elements_located_by_css_selector(css_selector="div > div.moviename-desc > p.moviename-info > span", ele=boxoffice_info[0])
            one_boxoffice_data.setdefault("日期", datetime)
            one_boxoffice_data.setdefault("电影名", movie_name.text)
            one_boxoffice_data.setdefault("上映时间", movie_info[0].text)
            one_boxoffice_data.setdefault("总票房", movie_info[1].text)
            boxoffice_info = boxoffice_info[1:]
            for i in range(len(boxoffice_info)):
                one_boxoffice_data.setdefault(theads[i], boxoffice_info[i].text)
            one_boxoffice_data.setdefault("crawl_time", crwal_time)
            one_boxoffice_data.setdefault("crawl_from", "猫眼专业版")
            # self.piaofang_col.insert_one(one_piaofang_data)
            judge_result = self.judge_data_exist_by_keys(collection=self.boxoffice_col,
                                                         keys={"user_id": user_id, "repo_id": repo_id,
                                                               "value.日期": one_boxoffice_data["日期"],
                                                               "value.电影名": one_boxoffice_data["电影名"],
                                                               "value.crawl_from": one_boxoffice_data["crawl_from"]})
            if judge_result is True:
                boxoffice_data_from_the_page.append(one_boxoffice_data)
            else:
                return boxoffice_data_from_the_page, False

        self.close_curr_page()
        return boxoffice_data_from_the_page, True

    def get_boxoffice_infos(self, spider_id, user_id, repo_id, spider_name):
        date = datetime.datetime.strptime("2020-01-23", '%Y-%m-%d')
        # date = datetime.datetime.now()
        final_result = []
        while True:
            data_list, result = self.get_boxoffice_infos_from_one_page(
                url="http://piaofang.maoyan.com/dashboard/movie?date=" + str(date)[:10], datetime=str(date)[:10],
                user_id=int(user_id), repo_id=int(repo_id))
            final_result.extend(data_list)
            if result is False:
                break
            date = date + datetime.timedelta(days=-1)
        if len(final_result) == 0:
            return
        one_data_acquisition_log = TDataAcquisitionLog.objects.create(create_time=timezone.now(),
                                                                      data_source_name=spider_name,
                                                                      data_access="爬虫",
                                                                      repo_id=int(repo_id),
                                                                      create_id=int(user_id),
                                                                      data_path="")
        TEntityExtractionLog.objects.create(data_acquisition_id=one_data_acquisition_log.id, is_extract=0,
                                            entity_number=0, extract_time=timezone.now(), create_id=int(user_id),
                                            repo_id=int(repo_id))

        for item in final_result:
            self.boxoffice_col.insert_one(
                {"file_id": one_data_acquisition_log.id, "category_id": -1, "spider_id": int(spider_id),
                 "user_id": int(user_id), "repo_id": int(repo_id), "value": item})

    def run_spider(self, url=""):
        lastest_info = self.boxoffice_col.find().sort("datetime", -1).limit(1)
        date = datetime.datetime.strptime(lastest_info[0]["datetime"], '%Y-%m-%d')
        date = date + datetime.timedelta(days=1)
        now = datetime.datetime.now()
        while date < now:
            self.get_boxoffice_infos_from_one_page("http://piaofang.maoyan.com/dashboard/movie?date=" + str(date)[:10], str(date)[:10])
            date = date + datetime.timedelta(days=1)
