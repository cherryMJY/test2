from spider.mtimespider import MtimeSpider

if __name__ == '__main__':
    test = MtimeSpider()
    result = test.get_news_from_one_page("http://news.mtime.com/2020/03/12/1601689.html")
    print(result)
