# -*- coding:utf-8 -*-
from knowledge_map_system import view
from django.shortcuts import render
from django.http import JsonResponse
from django.forms.models import model_to_dict
from model.mongodb import Mongodb
from model.models import TAlgorithm


class BaseController:
    def __init__(self):
        self.__context = {}
        self.knowledge_col = Mongodb(db='knowledge', collection='text').get_collection()
        # self.spider_col = Mongodb(db='baike', collection='test1').get_collection()

    def display(self, request):
        self.get_base_info(request, self.__context)
        return render(request, view.modules+"/"+view.action+".html", self.__context)

    @staticmethod
    def get_base_info(request, context):
        context.setdefault("user_name", request.session['user_name'])
        context.setdefault("repo_id", request.session["repo_id"])
        context.setdefault("repo_name", request.session["repo_name"])
        return context

    @staticmethod
    def get_category_name(request, category_name):
        return category_name + "_" + str(request.session["user_id"]) + "_" + str(request.session["repo_id"])

    @staticmethod
    def success(msg):
        data = {'status': 'success', 'msg': msg}
        return JsonResponse(data)

    @staticmethod
    def error(msg):
        data = {'status': 'error', 'msg': msg}
        return JsonResponse(data)

    @staticmethod
    def dict_encode_within(models, keys=None):
        dict_list = []
        if keys is None:
            keys = []
        for model in models:
            dic = model_to_dict(model)
            for key in keys:
                try:
                    dic.pop(key)
                except KeyError:
                    pass
            dict_list.append(dic)
        return dict_list

    def assign(self, key, value):
        self.__context[key] = value

    @staticmethod
    def transtime(time):
        return (int(time[:2]) * 60 + int(time[3:5])) * 60 + int(time[6:8])

    @staticmethod
    def extract_info_from_text(algorithm_id, request, file_id):
        try:
            algorithm = TAlgorithm.objects.get(id=algorithm_id)
            if algorithm.id == 1:
                modules = "event"
            else:
                modules = "relationship"
            obj = __import__("model." + modules + "Unit", fromlist=True)
            if hasattr(obj, modules.capitalize() + "Controller"):
                controller = getattr(obj, modules.capitalize() + "Controller")()
                return getattr(controller, algorithm.algorithm_mask)(request, file_id)
        except Exception:
            return None
