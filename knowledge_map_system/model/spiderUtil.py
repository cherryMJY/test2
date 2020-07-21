from spider.base.params import *
import time
import signal
from model.mongodb import Mongodb
import os


class SpiderUtil:

    @staticmethod
    def start_project(project_id, data_website, data_type, user_id, repo_id, project_name):
        """
        开启爬虫
        :param repo_id:
        :param user_id:
        :param data_type:
        :param data_website:
        :param project_id:
        :return:
        """
        result = PROJECT_SUCCESS
        try:
            cmd = SPIDERPY_PROCESS_CMD % project_id
            int(os.popen(cmd).read()[:-1])
            print('项目已经在运行,不用重复开启!!!')
            result = 'error:项目已经在运行,不用重复开启!!!'
        except Exception as e:
            cmd = SPIDERPY_START_CMD % (project_id, data_website, data_type, user_id, repo_id, project_name)
            print(cmd)
            try:
                os.system(cmd)
            except Exception as e:
                print('%e,没有这个选项!!!' % e)
                result = 'error:没有这个选项!!!'
        return result

    @staticmethod
    def stop_project(project_id):
        """

        :param project_id:
        :return:
        """
        result = PROJECT_SUCCESS
        try:
            cmd = SPIDERPY_PROCESS_CMD % project_id
            print(cmd)
            process = int(os.popen(cmd).read()[:-1])  # 获取floodlight的进程号
            os.kill(process, signal.SIGTERM)
        except Exception:
            print('没有这个项目,无法停止!!!')
            result = 'error:没有这个项目,无法停止!!!'
        return result

    @staticmethod
    def GetStatistics(spider_id, repo_id):
        collection = Mongodb(db='knowledge', collection='text').get_collection()
        count = collection.find({"spider_id": spider_id, "repo_id": repo_id}).count()
        # comment_count = comments_collection.find({FieldName.DATA_WEBSITE: str(project.data_website), FieldName.DATA_REGION: str(project.data_region), FieldName.DATA_SOURCE: str(project.data_source)}).count()
        # try:
        #     predict_comment_count = shops_collection.aggregate([{'$match': {FieldName.DATA_WEBSITE: str(project.data_website), FieldName.DATA_REGION: str(project.data_region), FieldName.DATA_SOURCE: str(project.data_source), FieldName.SHOP_COMMENT_NUM: {"$gt": 0}}}, {'$group': {"_id": "$%s"%FieldName.SHOP_URL, "num": {"$first": "$%s" % FieldName.SHOP_COMMENT_NUM}}}, {'$group': {"_id": None, "sum": {"$sum": "$num"}}}]).next().get('sum')
        # except Exception:
        #     predict_comment_count = 0
        curr_date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        count_today = collection.find(
            {"spider_id": spider_id, "repo_id": repo_id, "value.crawl_time": {'$regex': curr_date}}).count()
        week_start = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() - 7 * 24 * 3600))
        count_week = collection.find(
            {"spider_id": spider_id, "repo_id": repo_id, "value.crawl_time": {'$gt': week_start}}).count()
        month_start = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() - 30 * 24 * 3600))
        count_month = collection.find(
            {"spider_id": spider_id, "repo_id": repo_id, "value.crawl_time": {'$gt': month_start}}).count()
        result = '数据:%6s条 今日:%6s条 本周:%6s条 本月:%s条' % (count, count_today, count_week, count_month)
        return result