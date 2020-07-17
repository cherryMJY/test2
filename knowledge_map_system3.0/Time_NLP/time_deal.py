import ast

from Time_NLP.TimeNormalizer import TimeNormalizer # 引入包
from cocoNLP.extractor import extractor
from EventTriplesExtraction.triple_extraction import *

class Time_deal():
    def __init__(self):
        a=1

    def deal_time(self,content,timebase):
        ret_val=timebase

        try:
            tn = TimeNormalizer()
            res = tn.parse(target=content, timeBase=timebase)
            # print(res)
            tmp = ast.literal_eval(res)
            ret_val = ''
            # print(tmp,type(tmp))
            ret_val=tmp['timestamp']
        except Exception:
            a=1
        return ret_val

    def deal_area(self,content):
        ex = extractor()
        text = content
        locations = ex.extract_locations(text)
        #这边location去同
        mp={}
        for val in locations:
            mp[val]=1
        ret_l = []
        for key in  mp.keys():
            ret_l.append(key)
        return  ret_l

    def deal_event(self,content):
        extractor = TripleExtractor()
        # content = '''视频中，周迅、董洁、陶虹、冯绍峰、张歆艺、董子健、崔永元、游本昌、贾樟柯、张一白、曹保平、伍仕贤、肖洋、杨庆、严艺丹等众星齐亮相支持《寻龙诀》，对电影大为称赞，如《烈日灼心》导演曹保平认为“视效上基本达到了中国电影现在最好的高度”，崔永元也表示很骄傲：“看完以后真觉得特别好，我们终于可以拿得出手了，可以跟好莱坞的大片争一争高下了'''
        # svos = extractor.triples_main(content)
        svos = extractor.triples_main(content)
        return svos