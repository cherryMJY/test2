import requests
import re
from spider.base.driver import Driver
from model.mongodb import Mongodb


class BaikeSpider(Driver):
    urls = []
    # tags = ["电影", "演员", "导演", "编剧", "制片人"]
    count = 0

    def __init__(self, isheadless=False, ismobile=False, isvirtualdisplay=False, isloadimages=True, isproxy=False,
                 proxy_ip_from="", spider_id='2'):
        Driver.__init__(self, log_file_name=spider_id, ismobile=ismobile, isvirtualdisplay=isvirtualdisplay,
                        isheadless=isheadless, isloadimages=isloadimages, isproxy=isproxy,
                        proxy_ip_from=proxy_ip_from)
        # self.baike_col = Mongodb(db='movies1', collection="baike_member").get_collection()
        self.baike_col = Mongodb(db='baike', collection="test1").get_collection()

    def get_infos(self, url="", extensive_properties=None):
        if extensive_properties is None:
            extensive_properties = {}
        self.fast_new_page(url=url)
        relationship_urls = []
        relationship_tags = []
        if self.judge_web_element_exist_by_css_selector(css_selector="div.polysemantList-header-title > div.toggle.expand"):
            synonym = self.until_presence_of_element_located_by_css_selector(css_selector="div.polysemantList-header-title > div.toggle.expand > a")
            self.scroll_to_center(synonym)
            synonym.click()
            member_urls = self.until_presence_of_all_elements_located_by_css_selector(css_selector="ul.polysemantList-wrapper.cmn-clearfix > li.item > a")
            for item in member_urls:
                # for tag in self.tags:
                #     if tag in item.text:
                relationship_urls.append(item.get_attribute("href"))
                relationship_tags.append(item.text)
                        # break
        if self.driver.current_url not in self.urls:
            data = self.get_base_info_from_baike()
            if data is not None:
                current_tag = self.until_presence_of_element_located_by_css_selector(css_selector="ul.polysemantList-wrapper.cmn-clearfix > li.item > span.selected")
                data.setdefault("tag", current_tag.text)
                data.update(extensive_properties)
                print(data)
                self.baike_col.insert_one(data)
                self.urls.append(self.driver.current_url)
            self.close_curr_page()

        for item in relationship_urls:
            if item not in self.urls:
                self.fast_new_page(url=item)
                data = self.get_base_info_from_baike()
                if data is not None:
                    data.setdefault("tag", relationship_tags[relationship_urls.index(item)])
                    data.update(extensive_properties)
                    print(data)
                    self.baike_col.insert_one(data)
                    self.urls.append(item)
                self.close_curr_page()
        if self.count == 10:
            return False
        return True

    def get_base_info_from_baike(self):
        try:
            if not self.judge_web_element_exist_by_css_selector(css_selector="div.content > div.main-content div.basic-info.cmn-clearfix"):
                return
            basic_info_div = self.until_presence_of_element_located_by_css_selector(
                css_selector="div.content > div.main-content div.basic-info.cmn-clearfix")

            if self.judge_web_element_exist_by_css_selector(ele=basic_info_div, css_selector="a.toggle.toExpand"):
                btn = self.until_presence_of_element_located_by_css_selector(ele=basic_info_div, css_selector="a.toggle.toExpand")
                self.scroll_to_center(btn)
                btn.click()

            basic_info_name = self.until_presence_of_all_elements_located_by_css_selector(
                css_selector="dl > dt.basicInfo-item.name", ele=basic_info_div)
            basic_info_value = self.until_presence_of_all_elements_located_by_css_selector(
                css_selector="dl > dd.basicInfo-item.value", ele=basic_info_div)
            data = {}
            for i in range(len(basic_info_name)):
                name = basic_info_name[i].text.replace(" ", "")
                value = basic_info_value[i].text
                if name == "" or value.replace(" ", "") == "":
                    continue
                data.setdefault(name, value)
            data.setdefault("url", self.driver.current_url)
            if self.judge_web_element_exist_by_css_selector(css_selector="div.lemma-summary"):
                base_infos = self.until_presence_of_element_located_by_css_selector(
                    css_selector="div.lemma-summary").text
                data.setdefault("基础信息", base_infos)
            self.count = 0
            return data
        except Exception:
            self.count += 1
