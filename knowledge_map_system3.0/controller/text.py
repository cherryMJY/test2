import re
from typing import Set

import  arrow
from jpype import JClass

import re
from django.utils import timezone as datetime
from jpype import JClass
from numpy import unicode

from pyhanlp import *
from jpype import shutdownJVM

from Time_NLP.hanlpUnit import HanlpUnit
import datetime
import time

from Time_NLP.time_deal import Time_deal

from model.hanlpUnit import  HanlpUnit



#print(HanlpUnit().cut("2020年3月20日我是一个人"))
content = "20日我是一个人"
timeBase ="2020-06-05 14:21:40"
timeformat=arrow.get(timeBase).format('YYYY-M-D-H-m-s')
timeList = timeformat.split('-')
for i in range(6):
    timeList[i]=int(timeList[i])
date_string = "今天我是一个人"
str_len = len(date_string)
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
        if(i == 1 or i ==2):
            timeStr+="-"
        elif(i==3):
            timeStr += " "
        elif(i == 4 or i == 5):
            timeStr += ":"
        timeStr+=str(timeList[i]);
    return  -1,timeStr
wordList = ['今天','明天','后天','昨天','前天']
valList  =  [0,1,2,-1,-2]
#这里会有问题
cutResult =HanlpUnit().cut(date_string)
cnt = 0
print(cutResult)
for val in cutResult:
    tmp = val.split('/')[0]
    print(tmp)
    if(tmp in wordList):
        timeList[2]+=valList[cnt]
        timeStr = ''
        for i in range(6):
            if (i == 1 or i == 2):
                timeStr += "-"
            elif (i == 3):
                timeStr += " "
            elif (i == 4 or i == 5):
                timeStr += ":"
            timeStr +=str(timeList[i])
        print(cnt,timeStr)
        return cnt,timeStr
    cnt += 1
