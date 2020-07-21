import django
django.setup()
from model.models import TDataAcquisitionLog, TEntityExtractionLog
from spider.base.driver import Driver
from model.mongodb import Mongodb
from django.utils import timezone
import time
import datetime
import re


class MtimeSpider(Driver):
    def __init__(self, isheadless=False, ismobile=False, isvirtualdisplay=False, isloadimages=True, isproxy=False,
                 spider_id='2'):
        Driver.__init__(self, log_file_name=spider_id, ismobile=ismobile, isvirtualdisplay=isvirtualdisplay,
                        isheadless=isheadless, isloadimages=isloadimages, isproxy=isproxy)
        self.collection = Mongodb(db='knowledge', collection='text').get_collection()

    def get_news_from_one_page(self, ele=None):
        if ele is None:
            return None
        self.fast_click_page_by_elem(ele=ele)
        # self.fast_new_page(url)
        time.sleep(1)
        if self.judge_web_element_exist_by_css_selector(css_selector="p.newsinnerpageall > span > a"):
            show_all_page_btn = self.until_presence_of_element_located_by_css_selector(css_selector="p.newsinnerpageall > span > a")
            show_all_page_btn.click()
        try:
            news_title = self.until_presence_of_element_located_by_css_selector(
                css_selector="div.newsheader > div.newsheadtit").text
            news_time = re.findall(r"(\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{1,2}:\d{1,2})",
                                   self.until_presence_of_element_located_by_css_selector(
                                       css_selector="div.newsheader > p.newstime").text)[0]
            news_source = self.until_presence_of_element_located_by_css_selector(
                css_selector="div.newsheader > p.newstime > span.ml15").text.split("：")[1]
            news_content = self.until_presence_of_element_located_by_css_selector(
                css_selector="div.newsnote").get_attribute(
                'innerHTML') + self.until_presence_of_element_located_by_css_selector(
                css_selector="div#newsContent").get_attribute("innerHTML")
            news_author = \
            self.until_presence_of_element_located_by_css_selector(css_selector="p.newsediter").text.split(
                "：")[1]
        except Exception:
            return None
        crwal_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        one_news = {}
        one_news.setdefault("标题", news_title)
        one_news.setdefault("时间", news_time)
        one_news.setdefault("来源", news_source)
        one_news.setdefault("内容", news_content)
        one_news.setdefault("作者", news_author)
        one_news.setdefault("crawl_from", self.get_current_url())
        one_news.setdefault("crwal_time", crwal_time)
        self.close_curr_page()
        return one_news

    def get_news_infos(self, spider_id, user_id, repo_id, spider_name):
        url = "http://news.mtime.com/movie/1/"
        self.fast_new_page(url=url)
        time.sleep(1)
        final_result = []
        flag = 0
        while True:
            while self.judge_web_element_exist_by_css_selector(css_selector="div.newscontent > div#leftNews > a#viewmore"):
                more_info_btn = self.until_presence_of_element_located_by_css_selector(css_selector="div.newscontent > div#leftNews > a#viewmore")
                self.scroll_to_center(more_info_btn)
                more_info_btn.click()
                time.sleep(1)
            news_list = self.until_presence_of_all_elements_located_by_css_selector(css_selector="ul#newslist > li")
            for item in news_list:
                one_news = self.get_news_from_one_page(ele=item)
                if one_news is None:
                    continue
                print(one_news)
                judge_result = self.judge_data_exist_by_keys(collection=self.collection,
                                                             keys={"user_id": user_id, "repo_id": repo_id,
                                                                   "value.crawl_from": one_news["crawl_from"]})
                if judge_result:
                    final_result.append(one_news)
                else:
                    flag = 1
                    break
            if flag == 1 or not self.judge_web_element_exist_by_css_selector(css_selector="div#pages > a.cur + a"):
                break
            else:
                next_page_btn = self.until_presence_of_element_located_by_css_selector(css_selector="div#pages > a.cur + a")
                self.fast_click_page_by_elem(ele=next_page_btn)
                time.sleep(1)
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
            self.collection.insert_one(
                {"file_id": one_data_acquisition_log.id, "category_id": -1, "spider_id": int(spider_id),
                 "user_id": int(user_id), "repo_id": int(repo_id), "value": item})

