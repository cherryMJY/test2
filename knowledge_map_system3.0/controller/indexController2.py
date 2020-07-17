from django.core.serializers import json
from django.http import response, JsonResponse, HttpResponse

from controller.baseController import BaseController
from model.models import *
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import HttpResponseRedirect, render
from django.utils import timezone
from django.forms.models import model_to_dict
import json
from django.http import HttpResponse

class IndexController(BaseController):
    def login(self, request):
        username = request.POST['username']
        password = request.POST['password']
        try:
            user = TUser.objects.get(c_account=username)
            if password == user.c_password:
                request.session.set_expiry(0)
                request.session['user_account'] = user.c_account
                request.session['user_id'] = user.c_id
                return self.success("登录成功")
            else:
                return self.error("密码错误")
        except ObjectDoesNotExist:
            return self.error("账户不存在")

    #通过用户信息查询个人的数据库
    def homepage(self,request):

        json_list = []
        try:
            user_id = request.session['user_id']
            #user_id=1
            result= TRepository.objects.filter(c_user_id=user_id)
        except ObjectDoesNotExist:
            return self.error("账户不存在")
        for i in result:
            ret_result = model_to_dict(i)
            json_list.append(ret_result)
        return HttpResponse(json.dumps(json_list),content_type="application/json")

    #更新知识图谱的名字和描述
    def update_repo(self,request):

        repo_id = request.POST['repo_id']
        repo_name = request.POST['repo_name']
        repo_describe = request.POST['repo_describe']

        obj = TRepository.objects.get(c_id=repo_id , c_name=repo_name)
        obj.c_description = repo_describe
        obj.save();

        return HttpResponse(json.dumps({'result':'success'}),content_type="application/json")

    #删除知识图谱
    def delete_repo(self,request):

        repo_id = request.POST['repo_id']
        TRepository.objects.filter(c_id=repo_id).delete()

        return HttpResponse(json.dumps({'result': 'success'}), content_type="application/json")

    #增加知识图谱
    def add_repo(self,request):

        repo_name = request.POST['repo_name']
        repo_describe = request.POST['repo_describe']
        user_id = request.session['user_id']

        #repo_name = '3'
        #repo_describe = 'i am a pig'
        #user_id = 1

        TRepository.objects.create(c_name=repo_name,c_description=repo_describe,c_user_id=user_id)

        return HttpResponse(json.dumps({'result': 'success'}), content_type="application/json")
