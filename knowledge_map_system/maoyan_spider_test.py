from spider.maoyanspider import MaoyanSpider


if __name__ == '__main__':
    test = MaoyanSpider()
    test.get_boxoffice_infos_from_one_page(url="http://piaofang.maoyan.com/dashboard/movie?date=2020-04-01", datetime="2020-04-01")
