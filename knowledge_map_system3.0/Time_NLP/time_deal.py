import ast

from Time_NLP.TimeNormalizer import TimeNormalizer # 引入包
from cocoNLP.extractor import extractor, arrow
from EventTriplesExtraction.triple_extraction import *
from Time_NLP.hanlpUnit import HanlpUnit


class Time_deal():
    def __init__(self):
        a=1

    def dealtime(self,content,timebase):
        timeformat = arrow.get(timebase).format('YYYY-M-D-H-m-s')
        timeList = timeformat.split('-')
        for i in range(6):
            timeList[i] = int(timeList[i])
        date_string = content
        str_len = len(date_string)
        print(111)
        if re.match(r'\d+年\d+月\d+日', date_string):
            ind = 0
            tmp_num = 0
            for i in range(0, str_len):
                if (date_string[i] == ' '):
                    continue
                elif (date_string[i] >= '0' and date_string[i] <= '9'):
                    tmp_num = tmp_num * 10 + ord(date_string[i]) - ord('0')
                elif (date_string[i] == '年'):
                    timeList[0] = str(tmp_num)
                    tmp_num = 0
                elif (date_string[i] == '月'):
                    timeList[1] = str(tmp_num)
                    tmp_num = 0
                elif (date_string[i] == '日'):
                    timeList[2] = str(tmp_num)
                    tmp_num = 0
            timeStr = ''
            for i in range(6):
                if (i == 1 or i == 2):
                    timeStr += "-"
                elif (i == 3):
                    timeStr += " "
                elif (i == 4 or i == 5):
                    timeStr += ":"
                timeStr += str(timeList[i]);
            return -1,"", timeStr
        print(222)
        wordList = ['今天', '明天', '后天', '昨天', '前天']
        valList = [0, 1, 2, -1, -2]
        # 这里会有问题
        print(555)
        cutResult = HanlpUnit().cut(date_string)
        print(666)
        cnt = 0
        print(cutResult)

        for val in cutResult:
            tmp = val.split('/')[0]
            print(tmp)
            if (tmp in wordList):
                timeList[2] += valList[cnt]
                timeStr = ''
                for i in range(6):
                    if (i == 1 or i == 2):
                        timeStr += "-"
                    elif (i == 3):
                        timeStr += " "
                    elif (i == 4 or i == 5):
                        timeStr += ":"
                    timeStr += str(timeList[i])
                #print(cnt, timeStr)
                return cnt,tmp, timeStr
            cnt += 1
        print(444)
        timeStr = ''
        for i in range(6):
            if (i == 1 or i == 2):
                timeStr += "-"
            elif (i == 3):
                timeStr += " "
            elif (i == 4 or i == 5):
                timeStr += ":"
            timeStr += str(timeList[i])
        print(333)
        return -1,"",timeStr

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