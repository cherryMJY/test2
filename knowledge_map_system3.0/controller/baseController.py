# -*- coding:utf-8 -*-
from knowledge_map_system import view
from django.shortcuts import render
from django.http import JsonResponse
from django.forms.models import model_to_dict


class BaseController:
    def __init__(self):
        self.__context = {}

    def display(self, request):
        return render(request, view.modules+"/"+view.action+".html", self.__context)

    @staticmethod
    def success(msg):
        data = {'status': 'success', 'msg': msg}
        return JsonResponse(data)

    @staticmethod
    def error(msg):
        data = {'status': 'error', 'msg': msg}
        return JsonResponse(data)

    @staticmethod
    def dict_encode_within(models, selector):
        dict_list = []
        keys = selector.split(' ')
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

    def transtime(self, time):
        return (int(time[:2]) * 60 + int(time[3:5])) * 60 + int(time[6:8])


    @staticmethod
    def get_category_name(request, category_name):
        return category_name + "_" + str(request.session["user_id"]) + "_" + str(request.session["repo_id"])