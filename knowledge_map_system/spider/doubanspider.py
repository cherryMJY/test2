import django
django.setup()
from model.models import TDataAcquisitionLog, TEntityExtractionLog
from spider.base.driver import Driver
from model.mongodb import Mongodb
from django.utils import timezone
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import time
import re


class DoubanSpider(Driver):
    # 爬取电影人的豆瓣url集合，用以筛去所有重复的url
    member_set = set()

    def __init__(self, isheadless=False, ismobile=False, isvirtualdisplay=False, isloadimages=True, isproxy=False,
                 proxy_ip_from="", spider_id='2', data_queue=None):
        Driver.__init__(self, log_file_name=spider_id, ismobile=ismobile, isvirtualdisplay=isvirtualdisplay,
                        isheadless=isheadless, isloadimages=isloadimages, isproxy=isproxy,
                        proxy_ip_from=proxy_ip_from)
        self.movie_col = Mongodb(db='knowledge', collection='text').get_collection()
        # self.member_col = Mongodb(db='movies', collection='member').get_collection()
        # self.comment_col = Mongodb(db='movies', collection="comments").get_collection()

    def get_member_info(self, url=""):
        """
        获取一个电影人的具体个人信息
        :param url:
        :return:
        """
        self.fast_new_page(url=url)
        if "条目不存在" in self.driver.title or "页面不存在" in self.driver.title:
            self.close_curr_page()
            return None
        name = self.driver.title[:-4].strip()
        member_data = {}
        member_data.setdefault("member_name", name)
        member_data.setdefault("douban_url", url)
        member_div_infos = self.until_presence_of_all_elements_located_by_css_selector("div.info > ul > li")
        for item in member_div_infos:
            item = item.text.split(":")
            key = item[0].strip()
            if len(item) > 2:
                value = ":".join(item[1:])
            else:
                value = item[1]
            if key == "性别" or key == "星座" or key == "出生日期" or key == "出生地" or key == "官方网站":
                member_data.setdefault(key, value.strip())
            else:
                member_data.setdefault(key, [item.strip() for item in value.split("/")])
        self.close_curr_page()
        return member_data
        # self.member_col.insert_one(member_data)
        # self.info_log(data="取得个人资料数据----" + member_data["member_name"])
        # return True

    def get_member_awards(self, url=""):
        """
        获取一个电影人曾经获得的所有荣誉
        :param url:
        :return:
        """
        self.fast_new_page(url=url)
        awards_div = self.until_presence_of_element_located_by_css_selector("div.grid-16-8.clearfix > div.article")
        result = []
        try:
            awards_info = self.until_presence_of_all_elements_located_by_css_selector(css_selector="div.awards", ele=awards_div, timeout=5)
        except Exception:
            self.close_curr_page()
            return result
        for temp in awards_info:
            awards_time = self.until_presence_of_element_located_by_css_selector(css_selector="div.hd > h2", ele=temp)
            awards = self.until_presence_of_all_elements_located_by_css_selector(css_selector="ul.award", ele=temp)
            for award in awards:
                data = {}
                award_info = self.until_presence_of_all_elements_located_by_css_selector(css_selector="li", ele=award)
                data.setdefault("time", awards_time.text)
                data.setdefault("award_from", award_info[0].text)
                data.setdefault("award", award_info[1].text)
                data.setdefault("relevant_movie", award_info[2].text)
                result.append(data)
        self.close_curr_page()
        return result

    def get_member_movies(self, url=""):
        """
        获取一个电影人参与过的所有电影列表
        :param url:
        :return:
        """
        movies = []
        self.fast_new_page(url=url)
        while True:
            movies_a = self.until_presence_of_all_elements_located_by_css_selector("div.article > div.grid_view > ul > li > dl > dd > h6 > a")
            for temp in movies_a:
                movies.append(temp.text)
            try:
                self.vertical_scroll_to()
                next_page = self.until_presence_of_element_located_by_css_selector("div.article > div.paginator > span.next > a", timeout=5)
                next_page.click()
                time.sleep(1)
            except Exception:
                self.close_curr_page()
                return movies

    def get_comments(self, url="", movie_name="", movie_id=None):
        """
        获取单页的20条评论信息
        :param url:
        :param movie_name:
        :return:
        """
        self.fast_new_page(url=url)
        if "页面不存在" in self.driver.title or "条目不存在" in self.driver.title:
            self.close_curr_page()
            return
        comments_list = self.until_presence_of_all_elements_located_by_css_selector("div.article > div#comments.mod-bd > div.comment-item")
        if not self.judge_web_element_exist_by_css_selector(ele=comments_list[0], css_selector="div.comment"):
            self.close_curr_page()
            return
        for temp in comments_list:
            self.scroll_to_center(temp)
            data = {}
            commenter_name = self.until_presence_of_element_located_by_css_selector(css_selector="div.comment > h3 > span.comment-info > a", ele=temp)
            commenter_useful = self.until_presence_of_element_located_by_css_selector(css_selector="div.comment > h3 > span.comment-vote > span.votes", ele=temp)
            comment_content = self.until_presence_of_element_located_by_css_selector(css_selector="div.comment > p > span.short", ele=temp)
            comment_time = self.until_presence_of_element_located_by_css_selector(css_selector="div.comment > h3 > span.comment-info > span.comment-time", ele=temp)
            data.setdefault("movie_name", movie_name)
            data.setdefault("nickname", commenter_name.text)
            data.setdefault("useful", commenter_useful.text)
            data.setdefault("time", comment_time.text)
            data.setdefault("content", comment_content.text)
            data.setdefault("comment_from", "douban.com")
            if movie_id is not None:
                data.setdefault("movie_id", movie_id)
            if self.judge_web_element_exist_by_css_selector(ele=temp, css_selector="div.comment > h3 > span.comment-info > span.rating"):
                commenter_evaluate = self.until_presence_of_element_located_by_css_selector(
                    css_selector="div.comment > h3 > span.comment-info > span.rating", ele=temp)
                data.setdefault("evaluate", commenter_evaluate.get_attribute("title"))
            else:
                data.setdefault("evaluate", "")
            # self.comment_col.insert_one(data)
        self.close_curr_page()

    def get_one_movie_info(self, ele=None):
        """
        获取电影详细数据
        :param url:
        :return:
        """
        self.fast_click_page_by_elem(ele=ele)
        time.sleep(1)
        # self.fast_new_page(url=url)
        if "页面不存在" in self.driver.title or "条目不存在" in self.driver.title:
            self.close_curr_page()
            return None
        try:
            actor_more = self.driver.find_element_by_css_selector("div#info > span.actor > span.attrs > a.more-actor")
            actor_more.click()
            mask = 1
        except Exception:
            mask = 0
        div_info = self.until_presence_of_element_located_by_css_selector(css_selector="div#info")
        infos = div_info.text
        info_list = infos.split("\n")
        movie_info = {}
        for info in info_list:
            info = info.split(":")
            key = info[0].strip()
            if len(info) == 1 or (len(info) == 2 and info[1] == ""):
                continue
            elif len(info) > 2:
                value = ":".join(info[1:])
            else:
                value = info[1]
            if key == "官方网站":
                movie_info.setdefault(key, value.strip())
            else:
                movie_info.setdefault(key, [item.strip() for item in value.split("/")])
        # member_link = self.until_presence_of_all_elements_located_by_css_selector(css_selector="span span.attrs a",
        #                                                                     ele=div_info)
        # if mask == 1:
        #     member_link = member_link[:-1]
        # for item in member_link:
        #     item_link = item.get_attribute("href")
        #     if item_link in self.member_set:
        #         continue
        #     self.member_set.add(item_link)
        #     actor_info = {"member_name": item.text, "douban_url": item_link}
        #     self.dataQueue.put(actor_info)
        # self.close_curr_page()
        comment1 = self.until_presence_of_element_located_by_css_selector(
            "div#comments-section > div.mod-hd > h2 > span.pl > a")
        comment2 = self.until_presence_of_element_located_by_css_selector(
            "section#reviews-wrapper > header > h2 > span.pl > a")
        comment_number = int(re.findall(r'\d+', comment1.text)[0]) + int(re.findall(r'\d+', comment2.text)[0])
        movie_info.setdefault("豆瓣评论数量", comment_number)
        self.close_curr_page()
        return movie_info

    def get_movie_infos(self, spider_id, user_id, repo_id, spider_name):
        self.fast_new_page(
            url="https://movie.douban.com/explore#!type=movie&tag=%E7%83%AD%E9%97%A8&sort=recommend&page_limit=20&page_start=0")
        self.driver.refresh()
        if "页面不存在" in self.driver.title or "条目不存在" in self.driver.title:
            self.close_curr_page()
            return None
        # category_ul = self.until_presence_of_element_located_by_css_selector("ul.category")
        # category = self.until_presence_of_all_elements_located_by_css_selector(css_selector="li", ele=category_ul)[5:]
        # cur = 0
        # description = category[cur].text
        # category[cur].click()
        time.sleep(1)
        css_selector = "div.list-wp a.item"
        elements_list = self.until_presence_of_all_elements_located_by_css_selector(css_selector=css_selector)
        final_result = []
        for each in elements_list:
            data = {}
            self.vertical_scroll_to()
            time.sleep(1)
            self.scroll_to_center(ele=each)
            movie_link = each.get_attribute("href")
            movie_name = self.until_presence_of_element_located_by_css_selector(ele=each,
                                                                                css_selector="div.cover-wp > img")
            movie_score = self.until_presence_of_element_located_by_css_selector(ele=each,
                                                                                 css_selector="p > strong")
            data.setdefault("电影名", movie_name.get_attribute("alt"))
            data.setdefault("豆瓣评分", movie_score.text)
            crwal_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            data.setdefault("crawl_from", movie_link)
            data.setdefault("crawl_time", crwal_time)
            movie_info = self.get_one_movie_info(ele=each)
            movie_info.update(data)
            print(movie_info)
            final_result.append(movie_info)

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
            judge_result = self.judge_data_exist_by_keys(collection=self.movie_col,
                                                         keys={"user_id": user_id, "repo_id": repo_id,
                                                               "value.电影名": item["电影名"],
                                                               "value.crawl_from": item["crawl_from"]})
            if judge_result is True:
                self.movie_col.insert_one(
                    {"file_id": one_data_acquisition_log.id, "category_id": -1, "spider_id": int(spider_id),
                     "user_id": int(user_id), "repo_id": int(repo_id), "value": item})

    # def run(self):
    #     """
    #     单个线程启动方法，对每一个队列中的数据的url进行解析，找到对应的方法进行爬取对应数据
    #     :return:
    #     """
    #     self.info_log(data="线程启动", name=self.name)
    #     count = 0
    #     while not self.dataQueue.empty() and count == 0:
    #         temp = self.dataQueue.get(False)
    #         url_path = urlparse(temp["douban_url"]).path
    #         while True:
    #             try:
    #                 if "/celebrity" in url_path:
    #                     # 获取一条电影人详细数据
    #                     member_info = self.get_member_info(temp["douban_url"])
    #                     if member_info is None:
    #                         print("人物数据不存在")
    #                         break
    #                     member_awards = self.get_member_awards(temp["douban_url"] + "awards")
    #                     member_movies = self.get_member_movies(temp["douban_url"] + "movies")
    #                     member_info.setdefault("awards", member_awards)
    #                     member_info.setdefault("acting_movies", member_movies)
    #                     self.member_col.insert_one(member_info)
    #                     self.info_log(data="成功获取并存储一条人物数据-----" + member_info["member_name"], name=self.threadName)
    #                 elif "/subject" in url_path and "/subject_search" not in url_path and "/comments" not in url_path:
    #                     # 获取一条电影数据，成功获取电影数据后将他的影评url数据压入队列
    #                     movie_info = self.get_movie_info(temp["douban_url"])
    #                     if movie_info is None:
    #                         print("电影数据不存在")
    #                         break
    #                     movie_info.update(temp)
    #                     self.movie_col.insert_one(movie_info)
    #                     self.info_log(data="成功获取并存储一条电影数据-----" + movie_info["movie_name"], name=self.threadName)
    #                     print(movie_info)
    #                     comments_url = temp["douban_url"] + "comments?start=0&limit=20&sort=new_score&status=P"
    #                     self.dataQueue.put({"movie_name": temp["movie_name"], "douban_url": comments_url, "movie_id": movie_info["_id"]})
    #                 elif "/subject" in url_path and "/comments" in url_path:
    #                     # 对url解析，爬取200条影评数据
    #                     bits = list(urlparse(temp["douban_url"]))
    #                     qs = parse_qs(bits[4])
    #                     start = int(qs["start"][0])
    #                     while start <= 200:
    #                         qs["start"][0] = start
    #                         bits[4] = urlencode(qs, True)
    #                         temp["douban_url"] = urlunparse(bits)
    #                         self.get_comments(temp["douban_url"], temp["movie_name"], temp["movie_id"])
    #                         start += 20
    #                 count = 0
    #                 break
    #             except Exception:
    #                 # 累计失败次数，每次失败后更换换代理ip，若连续失败5次则线程结束
    #                 count += 1
    #                 if count > 5:
    #                     self.dataQueue.put(temp)
    #                     break
    #                 self.change_ip(self.get_ip(self.proxy_ip_from))

    @staticmethod
    def get_data_source():
        """
        获取已获取的电影人url
        :return:
        """
        member_col = Mongodb(db='movies', collection='member').get_collection()
        url_set = set()
        for item in member_col.find():
            url_set.add(item["douban_url"])
        return url_set
