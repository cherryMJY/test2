from bs4 import BeautifulSoup
from pyhanlp import *


class HanlpUnit:
    def __init__(self):
        self.CustomDictionary = JClass("com.hankcs.hanlp.dictionary.CustomDictionary")
        self.added_word_list = list()

    def add_word_list(self, word_list):
        #"""
        #����Զ����
        #:param word_list:���б���ʽ[{"word": "", "mask": ""}] wordΪ������maskΪ����
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
        #�ִ�
        #:param sentence: Ҫ�ִʵľ���
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
        #��html��������ȡ�ı�����Ҫ������������Ĵ���html��ǩ����������
        #:param text:
        #:return:
        #"""
        text = "<div>" + text + "</div>"
        soup = BeautifulSoup(text, "html.parser")
        return soup.get_text()

    def __del__(self):
        #"""
        #��������ʱ��������Ӵʻ�
        #:return:
        #"""
        for item in self.added_word_list:
            self.CustomDictionary.remove(item["word"])

