from bs4 import BeautifulSoup
from pyhanlp import *


class HanlpUnit:
    def __init__(self):
        self.CustomDictionary = JClass("com.hankcs.hanlp.dictionary.CustomDictionary")
        self.added_word_list = list()

    def add_word_list(self, word_list):
        #"""
        #添加自定义词
        #:param word_list:词列表，格式[{"word": "", "mask": ""}] word为词名，mask为词性
        #:return:
        #"""
        try:
            for item in word_list:
                result = self.CustomDictionary.add(item["word"], item["mask"])
                if result is False:
                    self.added_word_list.append(item)
            return True
        except Exception:
            return False


    def cut(self, sentence):
        #"""
        #分词
        #:param sentence: 要分词的句子
        #:return:
        #"""
        cut_result = HanLP.segment(sentence)
        for i in range(len(cut_result)):
            for item in self.added_word_list:
                if str(cut_result[i]).split(r"/")[0] == item["word"]:
                    cut_result[i] = item["word"] + "/" + item["mask"]
                    break
        #return HanLP.segment(sentence)
        return cut_result

    @staticmethod
    def get_text_from_html(text):
        #"""
        #从html内容中提取文本，主要是针对爬下来的带有html标签的新闻内容
        #:param text:
        #:return:
        #"""
        text = "<div>" + text + "</div>"
        soup = BeautifulSoup(text, "html.parser")
        return soup.get_text()

    def __del__(self):
        #"""
        #消除对象时撤销已添加词汇
        #:return:
        #"""
        for item in self.added_word_list:
            self.CustomDictionary.remove(item["word"])

