# -*- coding:utf-8 -*-
import sys

# CLASS_NAME = {"新闻": "news", "票房": "piaofang"}

if __name__ == '__main__':
    obj = __import__("spider." + sys.argv[2] + "spider", fromlist=True)
    if hasattr(obj, sys.argv[2].capitalize() + "Spider"):
        spider = getattr(obj, sys.argv[2].capitalize() + "Spider")(isheadless=False, ismobile=False,
                                                                                isvirtualdisplay=False,
                                                                                spider_id=sys.argv[1])
        getattr(spider, "get_" + sys.argv[3] + "_infos")(sys.argv[1], sys.argv[4], sys.argv[5], sys.argv[6])
