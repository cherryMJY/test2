# -*- coding:utf-8 -*-
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from pyvirtualdisplay import Display
import random
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import traceback
import inspect
import requests
from spider.base.logger import get_logger


class Driver(object):
    desktop_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393'
    mobile_user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 9_2 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13C75 Safari/601.1'
    curr_user_agent = desktop_user_agent

    scroll_to_center_js_script = 'window.scrollBy(arguments[0].getClientRects()[0].x + arguments[0].clientWidth / 2 - window.innerWidth / 2, arguments[0].getClientRects()[0].y + arguments[0].clientHeight / 2 - window.innerHeight / 2)'
    logger = get_logger("10")

    def __init__(self, log_file_name='2', ismobile=False, isvirtualdisplay=False, isheadless=False, isloadimages=True,
                 isproxy=False, proxy_ip_from=""):
        """

        :param log_file_name:
        :param ismobile:
        :param isvirtualdisplay:
        :param isheadless:
        :param isloadimages:
        :param isproxy:
        :param initial_proxy_ip:
        """
        # self.logger = get_logger(log_file_name)
        self.log_file_name = "spider" + log_file_name
        self.ismobile = ismobile
        self.isvirtualdisplay = isvirtualdisplay
        self.isheadless = isheadless
        self.isloadimages = isloadimages
        self.data_key = {}
        self.isproxy = isproxy
        self.proxy_ip_from = proxy_ip_from
        self.initial_proxy_ip = self.get_ip(self.proxy_ip_from)  # 用户设定的初始化ip
        self.driver = self.get_driver()

    def __del__(self):
        """

        :return:
        """
        self.info_log(data=self.log_file_name + "结束！！！", name=self.log_file_name)
        self.driver.quit()

    def get_current_url(self):
        """
        获取当前页面url
        :return:
        """
        return self.driver.current_url

    def judge_web_element_exist_by_link_text(self, ele=None, link_text=""):
        if not ele:
            ele = self.driver
        try:
            ele.find_element_by_link_text(link_text=link_text)
            return True
        except Exception:
            return False

    def judge_web_element_exist_by_css_selector(self, ele=None, css_selector=""):
        """
        判断元素是否存在
        :param ele:WebElement
        :param css_select:
        :return:
        """
        if not ele:
            ele = self.driver
        try:
            ele.find_element_by_css_selector(css_selector=css_selector)
            return True
        except Exception:
            return False

    def until_presence_of_all_elements_located_by_css_selector(self, css_selector: str, ele=None, timeout=10):
        """
        判断是否至少有1个元素存在于dom树中，如果定位到就返回列表
        :param ele:WebElement
        :param timeout:
        :param css_selector:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector)))

    def until_presence_of_element_located_by_css_selector(self, css_selector: str, ele=None, timeout=10):
        """
        判断某个元素是否被加到了dom树里，并不代表该元素一定可见，如果定位到就返回WebElement
        :param ele:WebElement
        :param timeout:
        :param css_selector:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))

    def get_driver(self):
        """

        :return:
        """
        driver = webdriver.Chrome(chrome_options=self.get_options())
        driver.set_page_load_timeout(30)
        return driver

    def get_options(self):
        options = webdriver.ChromeOptions()
        prefs = {}
        if self.ismobile:
            options.add_argument(
                'user-agent=%s'%self.mobile_user_agent)
            self.curr_user_agent = self.mobile_user_agent
        else:
            options.add_argument(
            'user-agent=%s'%self.desktop_user_agent)
            self.curr_user_agent = self.desktop_user_agent
        options.add_argument('lang=zh_CN.UTF-8')
        if self.isvirtualdisplay:
            self.logger.debug('virtualdisplay is running')
            display = Display(visible=0, size=(1440, 900))
            display.start()
        if self.isvirtualdisplay == False and self.isheadless == True:
            self.logger.debug('headless is running')
            options.add_argument('--headless')
        if not self.isloadimages:
            self.logger.debug('load images is false')
            # 1允许所有图片；2阻止所有图片；3阻止第三方服务器图片
            prefs.setdefault('profile.default_content_setting.images', 2)
        if self.isproxy:
            options.add_argument("--proxy-server=" + self.initial_proxy_ip)
        prefs.setdefault('profile.default_content_setting.notifications', 2)
        prefs.setdefault('profile.default_content_setting.geolocation', 2)
        options.add_argument('--disk-cache=true')#允许缓存
        options.add_argument('disable-infobars')#隐藏自动化软件测试的提示
        options.add_experimental_option('prefs', prefs)
        return options

    def download_pic(self, url, path, file_name):
        """
        下载图片
        :param url:图片url
        :param file_name: 保存本地的图片名
        :return:
        """
        r = requests.get(url, verify=False)
        # with open("D:\\hdu\\爬虫\\huayu_picture\\" + file_name, "wb") as f:
        with open(path + file_name, "wb") as f:
            f.write(r.content)

    def new_window(self, url:str):
        """

        :param url:
        :return:
        """
        self.driver.execute_script('window.open("{}");'.format(url))

    def scroll_to_center(self, ele: WebElement):
        '''
        把页面元素滚动到页面中间
        :param ele:
        :return:
        '''
        try:
            self.driver.execute_script(self.scroll_to_center_js_script, ele)
        except Exception:
            self.error_log(e='由于元素不存在,滚动元素到页面中间出错!!!',istraceback=False)

    def vertical_scroll_to(self, offset=0):
        """
        下拉滚动加载, offset为0默认把页面下拉到最下端
        :param offset:
        :return:
        """
        self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight + %s)' % offset)

    def __get_running_func__(self, level=2):
        """

        :param level:
        :return:
        """
        inspect_stack = inspect.stack()
        if len(inspect_stack) < 2:
            pass
        elif len(inspect_stack) < level:
            inspect_stack = inspect_stack[:-2][::-1]
        elif len(inspect_stack) > level:
            inspect_stack = inspect.stack()[-level - 2:-2][::-1]
        return ' - '.join('%s.%s.[%s]'%(i[1].split('/')[-1].split('.')[0],i[3],i[2]) for i in inspect_stack)

    def debug_log(self, data:str, name='', level=2):
        """

        :param name:
        :param data:
        :param level:
        :return:
        """
        self.logger.debug('%s %s: %s' % (self.__get_running_func__(level=level),name, data))

    def warning_log(self, e:str, name='', level=2):
        """

        :param name:
        :param e:
        :param level:
        :return:
        """
        self.logger.warning('%s %s: %s' % (self.__get_running_func__(level=level),name, e))

    def info_log(self, data:str, name='', level=2):
        """

        :param name:
        :param data:
        :param level:
        :return:
        """
        self.logger.info('%s %s: %s' % (self.__get_running_func__(level=level),name, data))

    def error_log(self, e:str, name='', istraceback=True, level=2):
        """

        :param name:
        :param e:
        :param istraceback:
        :param level:
        :return:
        """
        traceback_e = ''
        if istraceback:
            traceback_e = traceback.format_exc()
        self.logger.error('%s %s: %s\n%s' % (self.__get_running_func__(level=level),name, traceback_e,e))

    def fast_new_page(self, url:str, try_times=15, min_time_to_wait=30, max_time_to_wait=60, is_scroll_to_bottom=True):
        """
        新建标签页码快速加载页面
        :param url:
        :param try_times:
        :param min_time_to_wait:
        :param max_time_to_wait:
        :return:
        """
        for i in range(1, try_times+1):
            try:
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.set_page_load_timeout(random.randint(min_time_to_wait, max_time_to_wait))
                self.new_window(url)
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.refresh()
                if is_scroll_to_bottom:
                    self.vertical_scroll_to()  # 滚动到页面底部
                self.debug_log(data='经过%s次创建标签页和%s次关闭标签页,成功加载页面!!!' % (i, i - 1), name=self.log_file_name)
                return True
            except Exception:
                self.error_log(e='第%s次加载页面失败!!!' % i, name=self.log_file_name, istraceback=False)
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[-1])
        self.error_log(e='由于网络原因,无法加载页面,直接跳过!!!', name=self.log_file_name, istraceback=False)
        return False

    def until_presence_of_all_elements_located_by_partial_link_text(self, link_text:str, ele=None, timeout=10):
        """
        判断是否至少有1个元素存在于dom树中，如果定位到就返回列表
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.presence_of_all_elements_located((By.PARTIAL_LINK_TEXT, link_text)))

    def until_presence_of_element_located_by_partial_link_text(self, link_text:str, ele=None, timeout=10):
        """
        判断某个元素是否被加到了dom树里，并不代表该元素一定可见，如果定位到就返回WebElement
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, link_text)))

    def close_curr_page(self):
        """
        关闭当前的页面
        :return:
        """
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[-1])

    @staticmethod
    def get_ip(url):
        try:
            res = requests.get(url)
            return res.text.split("\n")[0]
        except Exception:
            return "127.0.0.1:3000"

    def change_ip(self, ip="127.0.0.1:3000"):
        try:
            if self.isproxy is False:
                self.info_log(data="ip不允许变更！！！", name=self.log_file_name)
                return
            self.driver.quit()
            self.initial_proxy_ip = ip
            self.driver = self.get_driver()
            self.info_log(data="ip变更成功，新代理ip为" + ip, name=self.log_file_name)
        except Exception:
            self.debug_log(data="ip变更失败，未知原因！！！", name=self.log_file_name)

    def judge_data_exist_by_keys(self, collection=None, keys=None):
        if collection is None or keys is None:
            self.error_log(e='collection和keys不可以为空!!!')
            raise ValueError
        if len(list(collection.find(keys))) == 0:
            return True
        else:
            return False

    def fast_click_page_by_elem(self, ele=None, try_times=15, min_time_to_wait=30, max_time_to_wait=60, is_scroll_to_bottom=True):
        """
        yqs
        点击快速加载页面
        :param ele:
        :param try_times:
        :param min_time_to_wait:
        :param max_time_to_wait:
        :return:
        """
        if not ele:
            self.error_log(e='请传入正确的点击对象!!!', istraceback=False)
            return False
        for i in range(1, try_times+1):
            try:
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.set_page_load_timeout(random.randint(min_time_to_wait, max_time_to_wait))
                self.scroll_to_center(ele)
                ele.click()
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.refresh()
                if is_scroll_to_bottom:
                    self.vertical_scroll_to()  # 滚动到页面底部
                self.debug_log(data='经过%s次点击和%s次关闭标签页,成功加载页面!!!' % (i, i - 1))
                return True
            except Exception:
                self.error_log(e='第%s次加载页面失败!!!' % i, istraceback=False)
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[-1])
        self.error_log(e='由于网络原因,无法加载页面,直接跳过!!!', istraceback=False)
        return False