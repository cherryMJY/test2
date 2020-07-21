from bs4 import BeautifulSoup
from pyhanlp import *
import re


class HanlpUnit:
    def __init__(self):
        self.CustomDictionary = JClass("com.hankcs.hanlp.dictionary.CustomDictionary")
        self.added_word_list = list()

    def add_word_list(self, word_list):
        """
        添加自定义词
        :param word_list:词列表，格式[{"word": "", "mask": ""}] word为词名，mask为词性
        :return:
        """
        try:
            for item in word_list:
                result = self.CustomDictionary.add(item["word"], item["mask"])
                if result is False:
                    self.added_word_list.append(item)
            return True
        except Exception:
            return False

    def cut(self, sentence):
        """
        分词
        :param sentence: 要分词的句子
        :return:
        """
        cut_result = HanLP.segment(sentence)
        for i in range(len(cut_result)):
            cut_result[i] = str(cut_result[i])
            for item in self.added_word_list:
                if cut_result[i].split("/")[0] == item["word"]:
                    cut_result[i] = item["word"] + "/" + item["mask"]
                    break
        return list(cut_result)

    @staticmethod
    def get_text_subsection_from_html(content):
        """
        从html内容提取文本，同时分段
        :param news:
        :return:
        """
        # news = "<div>" + news + "</div>"
        soup = BeautifulSoup(content, "lxml")
        text = soup.find_all(text=True)
        # text = [i.replace(" ", "").replace("\xa0", "") for i in text if i.replace(" ", "").replace("\xa0", "") != '']
        text = [''.join(i.split()) for i in text if ''.join(i.split()) != '']
        result = [text[0]]
        for i in range(1, len(text)):
            if text[i-1][-1] != "。":
                result[-1] = result[-1] + text[i]
            else:
                result.append(text[i])
        return result

    @staticmethod
    def get_text_from_html(text):
        """
        从html内容中提取文本，主要是针对爬下来的带有html标签的新闻内容
        :param text:
        :return:
        """
        text = "<div>" + text + "</div>"
        soup = BeautifulSoup(text, "html.parser")
        return soup.get_text()

    @staticmethod
    def split_paragraph(para):
        """
        将段落拆成句子
        :param para:
        :return:
        """
        para = re.sub('([。！？\?])([^”’])', r"\1\n\2", para)  # 单字符断句符
        para = re.sub('(\.{6})([^”’])', r"\1\n\2", para)  # 英文省略号
        para = re.sub('(\…{2})([^”’])', r"\1\n\2", para)  # 中文省略号
        para = re.sub('([。！？\?][”’])([^，。！？\?])', r'\1\n\2', para)
        # 如果双引号前有终止符，那么双引号才是句子的终点，把分句符\n放到双引号后，注意前面的几句都小心保留了双引号
        para = para.rstrip()  # 段尾如果有多余的\n就去掉它
        # 很多规则中会考虑分号;，但是这里我把它忽略不计，破折号、英文双引号等同样忽略，需要的再做些简单调整即可。
        return para.split("\n")

    def __del__(self):
        """
        消除对象时撤销已添加词汇
        :return:
        """
        for item in self.added_word_list:
            self.CustomDictionary.remove(item["word"])
