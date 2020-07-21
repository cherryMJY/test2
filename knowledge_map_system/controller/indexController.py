import arrow
import re
import ast
import functools
from controller.baseController import BaseController
from model.extractUnit import ExtractUnit
from model.models import *
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.shortcuts import HttpResponseRedirect
from django.utils import timezone
from django.forms.models import model_to_dict
# from django.views.decorators.csrf import csrf_exempt
from model.some_data_deal_func import some_data_deal_func
from model.spiderUtil import SpiderUtil
from model.neo4j import Neo4j
from model.mongodb import Mongodb
from spider.baikespider import BaikeSpider
from bson import ObjectId, json_util
from model.spiderUtil import SpiderUtil
from model.hanlpUnit import HanlpUnit
import simplejson
import pandas
import json
import xlrd
import os


class IndexController(BaseController):
    def login(self, request):
        username = request.POST['username']
        password = request.POST['password']
        try:
            user = TUser.objects.get(user_account=username)
            if password == user.user_password:
                request.session.set_expiry(0)
                request.session['user_account'] = user.user_account
                request.session['user_id'] = user.id
                request.session['user_name'] = user.user_name
                return self.success("登录成功")
            else:
                return self.error("密码错误")
        except ObjectDoesNotExist:
            return self.error("账户不存在")

    def homepage(self, request):
        json_list = []
        try:
            user_id = request.session['user_id']
            result = TRepository.objects.filter(create_id=user_id)
        except ObjectDoesNotExist:
            return self.error("账户不存在")
        for i in result:
            ret_result = model_to_dict(i)
            if ret_result["repo_description"] is None:
                ret_result["repo_description"] = ""
            if ret_result["create_time"] is None:
                ret_result["create_time"] = ""
            else:
                ret_result["create_time"] = str(ret_result["create_time"])[:19]
            print(ret_result["create_time"])
            json_list.append(ret_result)
        return render(request, 'index/homepage.html', context={"user_name": request.session['user_name'], "repo_list":json_list})

        # 更新知识图谱的名字和描述
    def update_repo(self, request):

        repo_id = request.POST['repo_id']
        repo_name = request.POST['repo_name']
        repo_describe = request.POST['repo_describe']

        obj = TRepository.objects.get(id=repo_id)
        obj.repo_name = repo_name
        obj.repo_description = repo_describe
        obj.save()
        return self.success("更新成功！")

    # 增加知识图谱
    def add_repo(self, request):
        repo_name = request.POST['repo_name']
        repo_describe = request.POST['repo_describe']
        user_id = request.session['user_id']
        TRepository.objects.create(repo_name=repo_name, repo_description=repo_describe, create_id=user_id, create_time=timezone.now())
        return self.success("添加成功！")

    # 删除知识图谱
    def delete_repo(self, request):
        repo_id = request.POST['repo_id']
        TRepository.objects.filter(id=repo_id).delete()
        return self.success("删除成功！")

    def get_repo_id(self, request):
        repo_id = request.POST["repo_id"]
        try:
            repo = TRepository.objects.get(id=repo_id, create_id=request.session["user_id"])
        except Exception:
            return self.error("不存在该知识库")
        request.session["repo_name"] = repo.repo_name
        request.session['repo_id'] = int(repo_id)
        return self.success("")

    # 输入repo_id返回类目树level1_child :{ id ,category,attribute,level_2child{ id, }}
    # 这边事物的attribute要返回其他的不用
    def knowledge_definition(self, request):
        #输入一个id 返回他的所有孩子节点
        try:
            repo_id = request.session['repo_id']
        except Exception:
            return self.error("没有得到repo_id")
        try:
            create_id = request.session['user_id']
        except Exception:
            return self.error("没有得到create_id")
        #repo_id = 1
        #create_id = 1
        ret_l={}
        ret_l['first_tree'] = some_data_deal_func().find_children(repo_id, create_id, 1)
        ret_l['second_tree'] = some_data_deal_func().find_children(repo_id, create_id, 2)
        print(ret_l)
        return render(request, 'index/knowledge_definition.html', context=self.get_base_info(request, ret_l))

    def category_query(self, request):
        """
        功能
        返回这个类目和他的组选类目的信息以及他们的属性
        :param request:
        category_id    数据类型str  类目id
        :return:
        ret_l          数据类型字典
        例子ret_l={'category':{'id': 4, 'category_name': '演员' 'attribute': [{'id': 24, 'attribute_name': '电影' },
        'father_category':[{},{}],'data_type':[{'datatype_name': '1211', 'datatype_id': 14, "category_id": 1},{}]}
        category        数据类型字典 这个类目信息
        father_category 数据类型列表 这个类目的祖先节点的信息
        data_type       数据类型列表  所有数据类型
        """
        _category_id = request.POST['category_id']
        repo_id = request.session['repo_id']
        create_id = request.session['user_id']
        # _category_id = 5
        ret_l = {}

        _category_now = TCategory.objects.get(id=_category_id)
        if _category_now.category_type == 2:
            event_rule = {}
            category_inherit_from_object = TCategory.objects.filter(category_type=1, repo_id=repo_id)
            object_category_list = [{"category_id": item.id, "category_name": item.category_name} for item in
                                    category_inherit_from_object]
            event_rule.setdefault("object_category_list", object_category_list)
            cur_rule_info = {}
            try:
                cur_rule = TEventRule.objects.get(category_id=_category_now.id)
                cur_rule_info.setdefault("event_subject_id", cur_rule.event_subject_id)
                cur_rule_info.setdefault("event_object_id", cur_rule.event_object_id)
                cur_rule_info.setdefault("algorithm_id", cur_rule.algorithm_id)
                trigger_words = TTriggerWord.objects.filter(event_rule_id=cur_rule.id)
                trigger_word_list = ";".join([item.trigger_word for item in trigger_words])
                cur_rule_info.setdefault("trigger_word_list", trigger_word_list)
            except ObjectDoesNotExist:
                cur_rule_info.setdefault("event_subject_id", -1)
                cur_rule_info.setdefault("event_object_id", -1)
                cur_rule_info.setdefault("trigger_word_list", "")
                cur_rule_info.setdefault("algorithm_id", -1)
            algorithm_list = TAlgorithm.objects.filter(algorithm_type=1)
            event_rule.setdefault("algorithm_list", self.dict_encode_within(algorithm_list))
            event_rule.setdefault("rule_detail", cur_rule_info)
            ret_l.setdefault("event_rule", event_rule)

        _category_now_dict = model_to_dict(_category_now)
        # _category_now_dict  要增加attribute
        _category_now_attribute = []

        tmp_res = TAttribute.objects.filter(category_id=_category_id)
        for val in tmp_res:
            tem_res_dict = model_to_dict(val)
            tem_res_dict.setdefault("attribute_datatype", TDataType.objects.get(id=tem_res_dict["data_type_id"]).datatype_name)
            attribute_id = tem_res_dict['id']
            attribute_alias_val = TAttrbuteAlias.objects.filter(attribute_id=attribute_id)
            num = 0
            attribute_alias = ''
            for attribute_val in attribute_alias_val:
                attribute_val_dict = model_to_dict(attribute_val)
                if (num != 0):
                    attribute_alias += ','
                attribute_alias += attribute_val_dict['attribute_alias']
                num += 1
            tem_res_dict['attribute_alias'] = attribute_alias
            tem_res_dict["create_time"] = str(tem_res_dict["create_time"])[:19]
            _category_now_attribute.append(tem_res_dict)

        _category_now_dict['attribute'] = _category_now_attribute

        # print(_category_now_dict)
        ret_l['category'] = _category_now_dict

        father_list = []
        _catgegory_father_id = _category_now.father_category_id

        if (str(-1) == _catgegory_father_id):
            return self.success(ret_l)

        _category_father = TCategory.objects.get(id=_catgegory_father_id)
        _category_father_dict = model_to_dict(_category_father)
        tmp_res = TAttribute.objects.filter(category_id=_catgegory_father_id)
        _category_father_attribute = []

        for val in tmp_res:
            tem_res_dict = model_to_dict(val)
            attribute_alias = ''
            num = 0
            attribute_id = tem_res_dict['id']
            attribute_alias_val = TAttrbuteAlias.objects.filter(attribute_id=attribute_id)
            for attribute_val in attribute_alias_val:
                attribute_val_dict = model_to_dict(attribute_val)
                if (num != 0):
                    attribute_alias += ','
                attribute_alias += attribute_val_dict['attribute_alias']
                num += 1
            tem_res_dict.setdefault("attribute_datatype",
                                    TDataType.objects.get(id=tem_res_dict["data_type_id"]).datatype_name)
            tem_res_dict['attribute_alias'] = attribute_alias
            tem_res_dict["create_time"] = str(tem_res_dict["create_time"])[:19]
            _category_father_attribute.append(tem_res_dict)
        _category_father_dict['attribute'] = _category_father_attribute

        father_list.append(_category_father_dict)

        if str(-1) != _catgegory_father_id and str(-1) != _category_father_dict['father_category_id']:
            _category_father_father_id = _category_father_dict['father_category_id']
            _category_father_father = TCategory.objects.get(id=_category_father_father_id)
            _category_father_father_dict = model_to_dict(_category_father_father)
            tmp_res = TAttribute.objects.filter(category_id=_category_father_father_id)
            _category_father_father_attribute = []

            for val in tmp_res:
                tem_res_dict = model_to_dict(val)
                tem_res_dict.setdefault("attribute_datatype",
                                        TDataType.objects.get(id=tem_res_dict["data_type_id"]).datatype_name)
                attribute_alias = ''
                num = 0
                attribute_id = tem_res_dict['id']
                attribute_alias_val = TAttrbuteAlias.objects.filter(attribute_id=attribute_id)
                for attribute_val in attribute_alias_val:
                    attribute_val_dict = model_to_dict(attribute_val)
                    if num != 0:
                        attribute_alias += ','
                    attribute_alias += attribute_val_dict['attribute_alias']
                    num += 1
                tem_res_dict['attribute_alias'] = attribute_alias
                tem_res_dict["create_time"] = str(tem_res_dict["create_time"])[:19]
                _category_father_father_attribute.append(tem_res_dict)

            _category_father_father_dict['attribute'] = _category_father_father_attribute
            father_list.append(_category_father_father_dict)
        ret_l['father_category'] = father_list

        res_data_type = TDataType.objects.filter(repo_id__in=[-1, repo_id])
        now_category_name = _category_now_dict['category_name']
        tmp_list = []
        for val in res_data_type:
            if val.datatype_name != now_category_name:
                tmp_list.append({"datatype_name": val.datatype_name, "datatype_id": val.id, "category_id": val.category_id})

        ret_l['data_type'] = tmp_list

        relationship_extract_algorithm = TAlgorithm.objects.filter(algorithm_type=2)
        ret_l["relationship_extract_algorithm"] = self.dict_encode_within(relationship_extract_algorithm)
        return self.success(ret_l)

    def update_event_rule(self, request):
        """
        更新保存事件规则
        :param request:
        :return:
        """
        trigger_word = request.POST["trigger_word"]
        event_subject_id = request.POST["event_subject_id"]
        event_object_id = request.POST["event_object_id"]
        category_id = request.POST["category_id"]
        event_algorithm_id = request.POST["event_algorithm_id"]
        trigger_word_list = [item for item in trigger_word.split(";") if item != ""]
        try:
            cur_rule = TEventRule.objects.get(category_id=category_id)
            cur_rule.event_subject_id = event_subject_id
            cur_rule.event_object_id = event_object_id
            cur_rule.algorithm_id = event_algorithm_id
            cur_rule.save()
            TTriggerWord.objects.filter(event_rule_id=cur_rule.id).delete()
        except ObjectDoesNotExist:
            cur_rule = TEventRule.objects.create(event_subject_id=event_subject_id, event_object_id=event_object_id,
                                                 category_id=category_id, repo_id=request.session["repo_id"], algorithm_id=event_algorithm_id)
        for item in trigger_word_list:
            TTriggerWord.objects.create(trigger_word=item, event_rule_id=cur_rule.id, repo_id=request.session["repo_id"])
        return self.success("保存成功！")

    def add_category(self, request):
        """
        功能
        新建一个类目 把新的类目添加到mysql数据库中
        为每个属性(包括祖先节点的属性)创建一条清洗规则
        为自己创建一条归一规则 创建一条详细的归一规则
        :param request
        category_name     数据类型str 类目名字
        category_describe 数据类型str 类目描述
        inherit_category  数据类型str 父亲节点的类目id
        :return:
        ret_l             数据类型字典 生成这个类目的属性
        例子
        ret_l={'id': 28, 'category_name': '456', 'father_category_id': '3', 'is_temporary': 0, 'category_description': '',
        'repo_id': 1, 'create_id': 1, 'create_time': '2020-06-30 07:33:31', 'category_level': 3, 'category_type': '1'}
        """
        print('这个接口是add_category')
        _category_name = request.POST['category_name']
        _category_describe = request.POST['category_describe']
        _father_category_id = request.POST['inherit_category']

        _repo_id = request.session['repo_id']
        _create_id = request.session['user_id']

        obj = TCategory.objects.get(id=_father_category_id)
        now_level = obj.category_level + 1
        if now_level == 2:
            category_type = obj.id
        else:
            category_type = obj.father_category_id
        dt = timezone.now()
        one_category = TCategory.objects.create(category_name=_category_name, father_category_id=_father_category_id,
                                 is_temporary=0,
                                 category_description=_category_describe, repo_id=_repo_id, create_id=_create_id,
                                 create_time=dt, category_level=now_level, category_type=category_type)

        TDataType.objects.create(datatype_name=one_category.category_name, category_id=one_category.id,
                                 repo_id=_repo_id, create_id=_create_id, create_time=timezone.now())
        ret_l = model_to_dict(one_category)
        ret_l['create_time'] = str(ret_l['create_time'])[:19]

        if int(_father_category_id) > 2:
            father_category = TCategory.objects.get(id=_father_category_id)
            ret_l["category_type"] = model_to_dict(father_category)["father_category_id"]
        else:
            ret_l["category_type"] = _father_category_id
        #print(ret_l)
        # 给继承自所有父类目的属性(除事物)创建一条清洗规则
        if one_category.category_level == 3:
            father_category_attribute = TAttribute.objects.filter(category_id=one_category.father_category_id)
            for item in father_category_attribute:
                TCleaningRule.objects.create(attribute_id=item.id, is_cleaning=0, cleaning_rule="",
                                             create_time=timezone.now(), create_id=_create_id,
                                             category_id=one_category.id, is_custom=0)
        dNormalizedRule=TNormalizedRule.objects.create(category_id = one_category.id,rule_number=0,update_time=dt,overall_threshold=0,repo_id=_repo_id)
        print(_create_id)
        print(555,dNormalizedRule.id)
        TNormalizedRuleDetail.objects.create(normalized_rule_id=dNormalizedRule.id, attribute_id=1, update_time=dt, similarity_threshold=0,
                                       create_id=_create_id)
        return self.success(ret_l)

    def add_attribute(self, request):
        """
        添加属性
        :param request:
        :return:
        """
        _attribute_name = request.POST['attribute_name']
        _attribute_datatype_id = request.POST['attribute_type_id']
        _is_single_value = request.POST['attribute_is_single_value']
        _attribute_description = request.POST['attribute_describe']
        _category_id = request.POST['category_id']
        # 属性别名要用逗号分开
        _attribute_alias = request.POST['attribute_alias']
        _algorithm_id = request.POST["algorithm_id"]
        _create_id = request.session['user_id']

        dt = timezone.now()
        attribute_obj = TAttribute.objects.create(attribute_name=_attribute_name,
                                                  data_type_id=_attribute_datatype_id,
                                                  is_single_value=_is_single_value,
                                                  attribute_description=_attribute_description,
                                                  category_id=_category_id, create_time=dt,
                                                  algorithm_id=_algorithm_id)
        attribute_obj_dict = model_to_dict(attribute_obj)
        li = _attribute_alias.split(',')
        _attribute_id = attribute_obj.id
        for val in li:
            if val != "":
                TAttrbuteAlias.objects.create(attribute_id=_attribute_id, attribute_alias=val, create_id=_create_id,
                                              create_time=dt)
        attribute_obj_dict['create_time'] = str(attribute_obj_dict['create_time'])[:19]
        attribute_obj_dict['attribute_alias'] = _attribute_alias
        attribute_obj_dict["attribute_datatype"] = TDataType.objects.get(id=attribute_obj_dict["data_type_id"]).datatype_name
        # 给每条属性添加一条初始的清洗规则
        TCleaningRule.objects.create(attribute_id=_attribute_id, is_cleaning=0, cleaning_rule="",
                                     create_time=timezone.now(), create_id=_create_id, category_id=_category_id,
                                     is_custom=0)

        # 检查mongodb现有结点数据,将拥有这条属性的数据更新到neo4j
        update_nodes = self.knowledge_col.find({"category_id": int(_category_id), "value." + _attribute_name: {"$exists": True}})
        category = TCategory.objects.get(id=_category_id)
        category_name = self.get_category_name(request=request, category_name=category.category_name)
        neo4j = Neo4j()
        for node in update_nodes:
            # print({_attribute_name: node["value"][_attribute_name]})
            neo4j.update_one_node(label_name=category_name, query_info={"_id": node["_id"]}, update_info={_attribute_name: node["value"][_attribute_name]})
        some_data_deal_func().update_t_mapping_rule(request.session["repo_id"], request.session["user_id"])
        return self.success(attribute_obj_dict)

    # 修改属性
    def update_attribute(self, request):
        _attribute_id = request.POST['attribute_id']
        _attribute_name = request.POST['attribute_name']
        _attribute_alias = request.POST['attribute_alias']
        _attribute_datatype_id = request.POST['attribute_type_id']
        _is_single_value = request.POST['attribute_is_single_value']
        _attribute_algorithm_id = request.POST["attribute_algorithm_id"]
        _attribute_description = request.POST['attribute_describe']
        _create_id = request.session['user_id']

        _attribute = TAttribute.objects.get(id=_attribute_id)

        _attribute.attribute_name = _attribute_name
        _attribute.data_type_id = _attribute_datatype_id
        _attribute.is_single_value = _is_single_value
        _attribute.algorithm_id = _attribute_algorithm_id
        _attribute.attribute_description = _attribute_description
        _attribute.save()
        _attribute_alias_delete = TAttrbuteAlias.objects.filter(attribute_id=_attribute_id)
        _attribute_alias_delete.delete()
        # 删除属性别名
        # 添加属性别名
        li = _attribute_alias.split(',')
        dt = timezone.now()
        for val in li:
            TAttrbuteAlias.objects.create(attribute_id=_attribute_id, attribute_alias=val, create_id=_create_id,
                                          create_time=dt)
        return self.success("修改成功！")

    # 删除
    def delete_attribute(self, request):
        _attribute_id = request.POST['attribute_id']
        create_id = request.session['user_id']
        repo_id = request.session['repo_id']
        # _attribute_id = 1
        # create_id = 1
        # repo_id   = 1
        _attribute_alias_delete = TAttrbuteAlias.objects.filter(attribute_id=_attribute_id)

        try:
            _attribute_delete = TAttribute.objects.get(id=_attribute_id)
        except ObjectDoesNotExist:
            return self.error("不存在该属性数据！")
        cleaning_rule = TCleaningRule.objects.filter(attribute_id=_attribute_delete.id)
        _attribute_delete_dict = model_to_dict(_attribute_delete)
        category_id = _attribute_delete_dict['category_id']

        # 还需要修改，删除操作后会对清洗和映射内容造成影响
        return_map_rule = TMappingRule.objects.filter(map_attribute_id=_attribute_id, category_id=category_id,
                                                      create_id=create_id)
        for val in return_map_rule:
            val_dict = model_to_dict(val)
            print(val_dict)
            old_map_attribute_id = val_dict['map_attribute_id']
            t_mapping_rule_id = val_dict['id']
            map_attribute_id = -1
            # 这边要改的东西
            # 假如说已经是-1 那么直接continue
            # 不是-1 上面有日志
            # 然后那 attribute_map_log
            if (old_map_attribute_id == -1):
                continue

            old_att_name = val_dict['attribute_name']
            old_name_show_in_database = old_att_name
            ret_attribute_log = TAttributeMapLog.objects.filter(map_rule_id=t_mapping_rule_id, create_id=create_id,
                                                                repo_id=repo_id)
            for val_log in ret_attribute_log:
                val_log_dict = model_to_dict(val_log)
                print(val_log_dict)
                return_attribtue_log = TAttribute.objects.get(id=val_log_dict['map_attribute_id'],
                                                              category_id=category_id)
                return_attribtue_log_dict = model_to_dict(return_attribtue_log)
                print(return_attribtue_log_dict)
                old_att_name = return_attribtue_log_dict['attribute_name']
                # 就一直更新就行 那最下面的那个
            new_att_name = val_dict['attribute_name']
            ret_category = TCategory.objects.get(id=category_id, repo_id=repo_id, create_id=create_id)
            category_name = model_to_dict(ret_category)['category_name']
            print(old_att_name, new_att_name)
            neo4j = Neo4j().update_attribute_key(category_id, t_mapping_rule_id, category_name, old_att_name,
                                             new_att_name,
                                             map_attribute_id, old_name_show_in_database, create_id, repo_id)
            val.map_attribute_id = -1
            val.save()

        _attribute_alias_delete.delete()
        _attribute_delete.delete()
        cleaning_rule.delete()
        # 在这个之后那个覆盖也要修改
        some_data_deal_func().update_t_mapping_rule(repo_id, create_id)
        return self.success("删除成功！")
        # return render(request, 'test1.html', context={1: 'success'})

    def knowledge_acquire(self, request):
        ret_l = {}
        repo_id = request.session['repo_id']
        create_id = request.session['user_id']

        ret_log = TDataAcquisitionLog.objects.filter(repo_id=repo_id, create_id=create_id)
        repo_list = []
        for val in ret_log:
            ret_log_list = model_to_dict(val)
            ret_log_list["create_time"] = str(ret_log_list["create_time"])[:19]
            repo_list.append(ret_log_list)
        ret_l['ret_log'] = repo_list
        return render(request, 'index/knowledge_acquire.html', context=self.get_base_info(request, ret_l))

    # 把文件从前端传递到后台
    # 把文件从前端传递到后台
    # 更新t_entity_extraction_log
    # 更新t_data_acquisition_log
    def upload_file(self, request):
        # d / 名字ID / 知识库名字ID
        repo_id = request.session['repo_id']
        # repo_id = 1
        create_id = request.session['user_id']
        # create_id = 1
        # data_access = request.POST['data_access']
        data_access = '文件'

        repo = TRepository.objects.get(id=repo_id)
        repo_dict = model_to_dict(repo)
        repo_name = repo_dict['repo_name']

        user = TUser.objects.get(id=create_id)
        user_dict = model_to_dict(user)
        user_name = user_dict['user_name']

        if request.method == "POST":  # 请求方法为POST时，进行处理
            myFile = request.FILES.get("file", None)  # 获取上传的文件，如果没有文件，则默认为None
            if not myFile:
                return self.error("no files for upload!")
            # 建文件夹
            path = "D:\\upload\\" + user_name + str(create_id) + "\\" + repo_name + str(repo_id)
            # 其实这边可以封装一个类来装这个函数
            if (os.path.exists('D:\\upload')):
                a = 1
            else:
                os.makedirs('D:\\upload')

            if (os.path.exists('D:\\upload\\' + user_name + str(create_id))):
                a = 1
            else:
                os.makedirs('D:\\upload\\' + user_name + str(create_id))

            if (os.path.exists('D:\\upload\\' + user_name + str(create_id) + '\\' + repo_name + str(repo_id))):
                a = 1
            else:
                os.makedirs('D:\\upload\\' + user_name + str(create_id) + '\\' + repo_name + str(repo_id))

            # 这个文件名字
            dt = timezone.now()
            true_file_name = myFile.name
            suffix = true_file_name.split(".")[-1]

            file_name_1 = str(dt)[:19] + "." + suffix
            file_name = file_name_1.replace(":", "")

            destination = open(os.path.join(path, file_name), 'wb+')  # 打开特定的文件进行二进制的写操作

            for chunk in myFile.chunks():  # 分块写入文件
                destination.write(chunk)
            destination.close()

            # 先存t_data_acquisition_log
            # id
            # crete_time
            # data_source_name
            # data_access
            # repo_id
            # create_id
            # data_path
            _create_time = dt
            _data_source_name = true_file_name
            _data_access = data_access
            _repo_id = repo_id
            _create_id = create_id
            _data_path = path + "\\" + file_name
            # data_path  包括新的文件名字
            return_data_acquisition_log = TDataAcquisitionLog.objects.create(create_time=_create_time,
                                                                             data_source_name=_data_source_name,
                                                                             data_access=_data_access,
                                                                             repo_id=_repo_id,
                                                                             create_id=_create_id,
                                                                             data_path=_data_path)
            return_data_acquisition_log_dict = model_to_dict(return_data_acquisition_log)

            # data = xlrd.open_workbook(path + '\\' + file_name)
            # table_name = data.sheet_names()[0]
            # 这边是第几个工作表
            # table = data.sheet_by_name(table_name)
            # list_attribute = list(table.row_values(0))
            # list_json = []

            data_acqisition_id = return_data_acquisition_log_dict['id']
            entity_number = 0
            is_extract = 0
            dt = timezone.now()
            TEntityExtractionLog.objects.create(data_acquisition_id=data_acqisition_id,
                                                is_extract=is_extract,
                                                entity_number=entity_number,
                                                create_id=create_id,
                                                repo_id=repo_id,
                                                extract_time=dt)
        return self.success("添加成功")

    # def view_file_content(self, request):
    #     file_id = request.GET["file_id"]
    #     #file_name = TDataAcquisitionLog.objects.get(id=file_id).data_source_name
    #
    #     # 通过pandas.ExcelFie函数，将excel文件转成html
    #     #path_obj = "D:\\\\upload\\" + file_name
    #     path_obj = TDataAcquisitionLog.objects.get(id=file_id).data_path
    #     new_file_name = "templates\\view_file_content.html"
    #     html_path = new_file_name.split('\\')[1]
    #
    #     xd = pandas.ExcelFile(path_obj)
    #     df = xd.parse()
    #     html = df.to_html(header=True, index=True)
    #     # 将转换后的html写入，一定要加编码方式utf-8，要不页面中打开会乱码
    #     with open(new_file_name, 'w', encoding='utf-8') as file:
    #         file.writelines('<meta charset="UTF-8">\n')
    #         file.write(html)
    #
    #     return render(request, html_path)

    def view_file_content(self, request):
        file_id = request.GET["file_id"]
        repoId = request.session['repo_id']
        createId = request.session['user_id']
        # file_id =12
        # repoId = 1
        # createId = 1
        data_access = TDataAcquisitionLog.objects.get(id=file_id, repo_id=repoId, create_id=createId).data_access
        ret_l = []
        if (data_access == "文件"):
            # 文件分词excel 和json
            path_obj = TDataAcquisitionLog.objects.get(id=file_id).data_path
            suffix = path_obj.split('.')[1]
            print(suffix)
            if (suffix == "xlsx"):
                data = xlrd.open_workbook(path_obj)
                table = data.sheets()[0]  # 通过索引顺序获取
                print(table.row_values(1))
                rowlen = table.nrows
                collen = table.ncols
                # 0-34  总共35个
                attributeNameList = table.row_values(0)
                print(attributeNameList)
                for i in range(1, rowlen):
                    tmpDict = {}
                    tmpList = table.row_values(i)
                    for j in range(0, collen):
                        tmpDict[attributeNameList[j]] = tmpList[j]
                    ret_l.append(tmpDict)
                # print(ret_l)
                # 行数
                # print(table.col_values(1))
                # print(df)
                # for val in df :
                #    print(111,val)
                # 将转换后的html写入，一定要加编码方式utf-8，要不页面中打开会乱码
            else:
                # 从文件里面一行一行读
                # print(1231)
                # print(path_obj)
                with open(path_obj, 'rb') as fp:
                    contents = fp.readlines()
                    for val in contents:
                        # print(l,type(l))
                        # tmpDict = ast.literal_eval(val)
                        try:
                            tmpDict = val.decode()
                        except Exception:
                            tmpDict = val.decode("GBK")
                        ret_l.append(tmpDict)

        elif (data_access == "爬虫"):
            # 爬虫相关
            tmp_info = {'file_id': int(file_id), 'user_id': createId, 'repo_id': repoId}
            try:
                news_col = Mongodb(db='knowledge', collection='text').get_collection()
            except Exception:
                return self.error("mongodb没有数据库或者表")
            cnt = 1
            ret_entity_map = news_col.find(tmp_info)
            for val in ret_entity_map:
                ret_l.append(val['value'])
        # return render(request, "test.html", context=ret)
        print(ret_l)
        return render(request, 'view_file_content.html', context={"running_results": ret_l})

    # 删除数据获取日志(需要添加一个删除文件内容)
    def delete_acquisition_log(self, request):
        _acquisition_log_id = request.POST['log_id']
        # _attribute_id = 28
        try:
            _acquisition_log_delete = TDataAcquisitionLog.objects.get(id=_acquisition_log_id)
            _acquisition_log_delete.delete()
            return self.success("删除成功！")
        except Exception:
            return self.error("删除失败！")

        # 返回四个日志表里面的内容要求一个方法
        # t_normalized_log
        # t_entity_extraction_log
        # ret_t_data_acquisition_log
        # t_attribute_map_log
        # 进行修改 TEntityExtractionLog这个表有变化

    def build_map(self, request):
        repo_id = request.session['repo_id']
        # repo_id =1
        create_id = request.session['user_id']
        # create_id=1
        ret_list = {}
        # TAttributeMapLog
        ret_log = TAttributeMapLog.objects.filter(create_id=create_id, repo_id=repo_id)
        log_list = []
        for val in ret_log:
            val_dict = model_to_dict(val)
            tmp_map = {}
            tmp_map['id'] = val_dict['id']
            tmp_map['attribute_name'] = val_dict['attribute_name']
            tmp_map['is_map'] = val_dict['is_map']
            tmp_map['entity_id'] = val_dict['entity_id']
            # tmp_map['map_attribute_id']
            map_attribute_id = val_dict['map_attribute_id']
            res_attribute = TAttribute.objects.get(id=map_attribute_id)
            res_attribute_dict = model_to_dict(res_attribute)
            tmp_map['map_attribute_name'] = res_attribute_dict['attribute_name']
            tmp_map['map_rule_id'] = val_dict['map_rule_id']
            # tmp_map['category_id']
            res_category = TCategory.objects.get(id=val_dict['category_id'])
            res_category_dict = model_to_dict(res_category)
            tmp_map['category_name'] = res_category_dict['category_name']
            log_list.append(tmp_map)
        ret_list.setdefault('t_attribute_map_log', log_list)

        ret_log = TCleaningLog.objects.filter(repo_id=repo_id, user_id=create_id)
        log_list = []
        for val in ret_log:
            val_dict = model_to_dict(val)
            tmp_map = {}
            # id
            # entity_id
            # cleaning_rule_id
            # cleaning_content
            # cleaning_result
            # category_id

            tmp_map['id'] = val_dict['id']
            tmp_map['entity_id'] = val_dict['entity_id']
            # tmp_map['cleaning_rule_id'] = val_dict['cleaning_rule_id']
            cleaning_rule_id = val_dict['cleaning_rule_id']
            cleaning_rule = TCleaningRule.objects.get(id=cleaning_rule_id)
            cleaning_rule_dict = model_to_dict(cleaning_rule)
            attribute_id = cleaning_rule_dict['attribute_id']
            return_attribute = TAttribute.objects.get(id=attribute_id)
            return_attribute_dict = model_to_dict(return_attribute)
            tmp_map['attribute_name'] = return_attribute_dict['attribute_name']
            #这个datatype后来改了
            tmpAttributeDatatypeID = return_attribute_dict['data_type_id']
            attribute_datatype=''
            if(tmpAttributeDatatypeID <= 3 ):
                attribute_datatype=TDataType.objects.get(id=tmpAttributeDatatypeID).datatype_name
            else:
                attribute_datatype=TDataType.objects.get(id=tmpAttributeDatatypeID,repo_id=repo_id,create_id=create_id).datatype_name
            tmp_map['attribute_datatype'] = attribute_datatype
            tmp_map['cleaning_content'] = val_dict['cleaning_content']
            tmp_map['cleaning_result'] = val_dict['cleaning_result']
            category_id = val_dict['category_id']
            ret_category = TCategory.objects.get(id=category_id)
            ret_category_dict = model_to_dict(ret_category)
            tmp_map['category_name'] = ret_category_dict['category_name']
            log_list.append(tmp_map)

        ret_list.setdefault('t_cleaning_log', log_list)

        # 这边这个表也有修改
        ret_log = TEntityExtractionLog.objects.filter(repo_id=repo_id, create_id=create_id)
        log_list = []
        for val in ret_log:
            val_dict = model_to_dict(val)
            tmp_map = {}
            tmp_map['id'] = val_dict['id']
            # tmp_map['data_source'] = val_dict['data_source']
            data_acquisition_id = val_dict['data_acquisition_id']
            ret_t_data_acquisition_log = TDataAcquisitionLog.objects.get(id=data_acquisition_id)
            ret_t_data_acquisition_log_dict = model_to_dict(ret_t_data_acquisition_log)
            tmp_map['data_source_name'] = ret_t_data_acquisition_log_dict['data_source_name']
            tmp_map['is_extract'] = val_dict['is_extract']
            tmp_map['entity_number'] = val_dict['entity_number']
            tmp_map['extract_time'] = str(val_dict['extract_time'])[:19]
            log_list.append(tmp_map)

        ret_list.setdefault('t_entity_extraction_log', log_list)

        ret_log = TNormalizedLog.objects.filter(repo_id=repo_id, create_id=create_id)
        log_list = []
        for val in ret_log:
            val_dict = model_to_dict(val)
            tmp_map = {}
            tmp_map['id'] = val_dict['id']
            tmp_map['merge_entity_id'] = val_dict['merge_entity_id']
            tmp_map['original_entity_id'] = val_dict['original_entity_id']
            tmp_map['normalized_rule_id'] = val_dict['normalized_rule_id']
            log_list.append(tmp_map)

        ret_list.setdefault('t_normalized_log', log_list)
        print(ret_list)
        # return render(request,"test1.html",ret_list)
        return render(request, 'index/build_map.html', self.get_base_info(request, ret_list))

    # 返回所有的类目 第一个用户定义的类目的属性以及他的父亲节点的属性
    def map_rule(self, request):

        repo_id = request.session["repo_id"]
        create_id = request.session["user_id"]
        # repo_id = 1
        # create_id = 1
        res_cate = TCategory.objects.filter(repo_id=repo_id, create_id=create_id)
        ret_l = {}
        cate_list = []
        for val in res_cate:
            cate_dict = model_to_dict(val)
            cate_id = cate_dict['id']
            cate_name = cate_dict['category_name']
            now_dict = {}
            now_dict['id'] = cate_id
            now_dict['category_name'] = cate_name
            cate_list.append(now_dict)
        ret_l['category'] = cate_list
        att_list = []

        try:
            cate_id = cate_list[0]["id"]
        except IndexError:
            return self.error("暂无类目！")

        # for val in cate_list:
        #     cate_id = val['id']
        print(cate_id)
        att_list = some_data_deal_func().input_category_id_return_attribute_list(cate_id, att_list)
        father_category_id = TCategory.objects.get(id=cate_id).father_category_id
        if (str(-1) != father_category_id):
            father_father_category_id = TCategory.objects.get(id=father_category_id).father_category_id
            att_list = some_data_deal_func().input_category_id_return_attribute_list(father_category_id, att_list)

            if (str(-1) != father_father_category_id):
                att_list = some_data_deal_func().input_category_id_return_attribute_list(father_father_category_id,
                                                                                         att_list)

        ret_l['attribute'] = att_list

        att_map_list = []
        # for val in cate_list:
        #     cate_id = val['id']
        res = TMappingRule.objects.filter(category_id=cate_id, create_id=create_id)
        for att in res:
            att_dict = model_to_dict(att)
            att_dict['create_time'] = str(att_dict['create_time'])
            att_map_list.append(att_dict)
        ret_l['attribute_mapping'] = att_map_list
        print(ret_l)
        # return render(request,"test1.html",context=ret_l)
        return render(request, "index/map_rule.html", context=self.get_base_info(request, ret_l))

    # 根据类目ID获取映射规则
    # 返回自己还有所有父亲节点的属性
    def get_map_rule(self, request):
        create_id = request.session["user_id"]
        # create_id = 1
        category_id = request.POST["category_id"]
        # category_id = 1

        ret_l = {}
        att_list = []
        father_category_id = TCategory.objects.get(id=category_id).father_category_id
        # print(father_category_id,type(father_category_id))
        att_list = some_data_deal_func().input_category_id_return_attribute_list(category_id, att_list)

        if (str(-1) != father_category_id):

            father_father_category_id = TCategory.objects.get(id=father_category_id).father_category_id
            att_list = some_data_deal_func().input_category_id_return_attribute_list(father_category_id, att_list)

            if (str(-1) != father_father_category_id):
                att_list = some_data_deal_func().input_category_id_return_attribute_list(father_father_category_id,
                                                                                         att_list)
            # python {} 默认不排序 按顺序输入 就和List一样

        ret_l['attribute'] = att_list
        # father

        att_map_list = []
        # for val in cate_list:
        #     cate_id = val['id']
        res = TMappingRule.objects.filter(category_id=category_id, create_id=create_id)

        for att in res:
            att_dict = model_to_dict(att)
            att_dict['create_time'] = str(att_dict['create_time'])
            att_map_list.append(att_dict)
        ret_l['attribute_mapping'] = att_map_list

        print(ret_l)
        return self.success(ret_l)

    # 根据id更新属性id
    # 更新neo4j数据库的属性名
    # 就是把第一个换成第二个
    # 这个属性映射了以后
    # 连续2次map_attribute_id = -1 那么就返回错误信息
    # 1 -1 变成 正常数字
    # 2 正常数字变成-1
    # 3正常数字 变成 正常数字
    def update_mapping_rule(self, request):
        t_mapping_rule_id = request.POST['map_rule_id']
        map_attribute_id = int(request.POST['map_attribute_id'])
        # t_mapping_rule_id = 13
        # map_attribute_id = 1
        repo_id = request.session["repo_id"]
        create_id = request.session["user_id"]
        # repo_id = 1
        # create_id = 1

        # 修改映射id
        obj = TMappingRule.objects.get(id=t_mapping_rule_id)
        old_map_attribute_id = obj.map_attribute_id
        obj.map_attribute_id = map_attribute_id
        obj.save()
        # print(type(old_map_attribute_id),type(map_attribute_id))
        # -1 变成 -1
        if (old_map_attribute_id == -1 and map_attribute_id == -1):
            return self.error("错误信息")
        # 获得旧的属性名字
        # 这个旧的属性名字可能不是这个因为可能已经映射过一次
        # 根据map_rule_id 来查询 如果没有映射日志 那么就是这个
        # 不然就是最近的那个
        # 这个初始化为本身
        print(old_map_attribute_id)
        category_id = model_to_dict(obj)['category_id']

        old_att_name = model_to_dict(TMappingRule.objects.get(id=t_mapping_rule_id))['attribute_name']
        ret_attribute_log = TAttributeMapLog.objects.filter(map_rule_id=t_mapping_rule_id, create_id=create_id,
                                                            repo_id=repo_id)
        old_name_show_in_database = old_att_name
        for val in ret_attribute_log:
            val_dict = model_to_dict(val)
            print(val_dict)
            print(val_dict['map_attribute_id'],category_id)
            return_attribtue_log = TAttribute.objects.get(id=val_dict['map_attribute_id'])
            return_attribtue_log_dict = model_to_dict(return_attribtue_log)
            print(return_attribtue_log_dict)
            old_att_name = return_attribtue_log_dict['attribute_name']
            # 就一直更新就行 那最下面的那个

        # 假如说他是-1 那么上面的都要删掉

        # 获得新的属性名字
        # 这个新的属性也可能没有因为可能是不映射 那么新的名字是原来的属性名字
        if (-1 != map_attribute_id):
            obj_att = TAttribute.objects.get(id=map_attribute_id)
            new_att_name = model_to_dict(obj_att)['attribute_name']
        else:
            # 这个应该是一开始的名字
            return_new_att = TMappingRule.objects.get(id=t_mapping_rule_id, category_id=category_id)
            new_att_name = model_to_dict(return_new_att)['attribute_name']
        print(new_att_name)
        # 获得要更新的类目名字
        # 只要更新这个类目的这个attribute就好了
        print(old_att_name, new_att_name)
        #假如属性表中不存在old_att_name 那么从mongodb里面把所有存在这个属性的节点都拿的来
        #更新到neo4j中
        #获得所有的attributename

        categoryName = TCategory.objects.get(id=category_id, create_id=create_id, repo_id=repo_id).category_name
        categoryLabel = self.get_category_name(request, categoryName)

        attList=some_data_deal_func().get_all_attribute_by_category_id(category_id)
        if(old_att_name not in attList):
            try:
                news_col = Mongodb(db='knowledge', collection='text').get_collection()
            except Exception:
                return self.error("mongodb没有数据库或者表")
            attribute="value."+old_att_name
            retcollect=news_col.find({attribute:{"$exists":True}})
            nodeList=[]
            for val in retcollect:
                tmpDict ={}
                _id = val['_id']
                #_id要变成5ef6e30c7765440d7a6c2616
                #而不是ObjectId('5ef6e30c7765440d7a6c2616')
                #print(str(_id))
                tmp=val['value']
                attributeVal=tmp[old_att_name]
                tmpDict['_id']=str(_id)
                tmpDict[old_att_name] = attributeVal
                nodeList.append(tmpDict)
            #945行 写到这里了
            #print(nodeList)
            for val in nodeList:
                Neo4j().update_one_node(categoryLabel,Neo4j().dictToQuesDict({'_id':val['_id']}),Neo4j().dictToQuesDict({old_att_name:val[old_att_name]}))
        ret_category = TCategory.objects.get(id=category_id, repo_id=repo_id, create_id=create_id)
        category_name = model_to_dict(ret_category)['category_name']
        neo4j = Neo4j().update_attribute_key(category_id, t_mapping_rule_id, categoryLabel, old_att_name, new_att_name,
                                         map_attribute_id, old_name_show_in_database, create_id, repo_id)
        ret_l = {}

        return self.success("更新成功！")

    def cleaning_rule(self, request):
        repo_id = request.session["repo_id"]
        create_id = request.session["user_id"]
        res_cate = TCategory.objects.filter(repo_id=repo_id, create_id=create_id)
        ret_l = {}
        cate_list = []
        for val in res_cate:
            cate_dict = model_to_dict(val)
            cate_id = cate_dict['id']
            cate_name = cate_dict['category_name']
            now_dict = {}
            now_dict['id'] = cate_id
            now_dict['category_name'] = cate_name
            cate_list.append(now_dict)
        ret_l['category'] = cate_list
        category_id = cate_list[0]["id"]

        res_cate = TCleaningRule.objects.filter(create_id=create_id, category_id=category_id)
        cate_list = []
        for val in res_cate:
            cate_dict = model_to_dict(val)
            attribute_id = cate_dict['attribute_id']
            res_attribute = TAttribute.objects.get(id=attribute_id)
            res_attribute_dict = model_to_dict(res_attribute)

            data_type_id = res_attribute_dict['data_type_id']
            if (data_type_id <= 3):
                dataTypeName = TDataType.objects.get(id=data_type_id).datatype_name
            else:
                dataTypeName = TDataType.objects.get(id=data_type_id, repo_id=repo_id,
                                                     create_id=create_id).datatype_name
            res_attribute_dict['attribute_datatype'] = dataTypeName

            cate_dict['attribute'] = res_attribute_dict
            cate_list.append(cate_dict)
        ret_l['cleaning_rule'] = cate_list
        print(ret_l)
        return render(request, "index/cleaning_rule.html", context=self.get_base_info(request, ret_l))

    # 已知create_id category_id 返回他的所有cleaning rule 和 attribute
    def get_cleaning_rule(self, request):
        category_id = request.POST['select_category_id']
        create_id = request.session['user_id']
        repo_id = request.session['repo_id']

        res_cate = TCleaningRule.objects.filter(create_id=create_id, category_id=category_id)
        ret_l = {}
        cate_list = []
        for val in res_cate:
            cate_dict = model_to_dict(val)
            attribute_id = cate_dict['attribute_id']
            res_attribute = TAttribute.objects.get(id=attribute_id)
            res_attribute_dict = model_to_dict(res_attribute)
            data_type_id = res_attribute_dict['data_type_id']
            dataTypeName = ''
            if (data_type_id <= 3):
                dataTypeName = TDataType.objects.get(id=data_type_id).datatype_name
            else:
                dataTypeName = TDataType.objects.get(id=data_type_id, repo_id=repo_id,
                                                     create_id=create_id).datatype_name
            res_attribute_dict['attribute_datatype'] = dataTypeName
            cate_dict['attribute'] = res_attribute_dict
            cate_list.append(cate_dict)
        ret_l['cleaning_rule'] = cate_list

        print(ret_l)
        return self.success(ret_l)

    # 输入规则id  是否自定义  规则内容
    def update_cleaning_rule(self, request):
        category_id = request.POST['category_id']
        rule_id = request.POST['rule_id']
        is_custom = request.POST['is_custom']
        rule_content = request.POST['rule_content']
        rule_number = int(request.POST["rule_number"])
        repo_id = request.session["repo_id"]
        create_id = request.session["user_id"]

        # request.session['repo_id'] = 1
        # request.session['user_id'] = 1
        # category_id = 2
        # rule_id = 2
        # 假如说这个是0 那么就是自定义正则表达式 否则是按固定的
        # is_custom = 0
        # rule_number  0 - 6  分别是清洗的 0 - 3 是小数点 4 - 6 是日期 7 是自定义
        # rule_content = 123
        # repo_id = 1
        # create_id = 1
        # rule_number = 4

        # 上面都是初始化
        obj = TCleaningRule.objects.get(id=rule_id, create_id=create_id)
        obj.cleaning_rule = rule_content
        obj.is_custom = is_custom
        attribute_id = obj.attribute_id
        obj.save()
        # 进行表的修改
        att = TAttribute.objects.get(id=attribute_id)
        att_dict = model_to_dict(att)
        attribute_name = att_dict['attribute_name']
        res = TCategory.objects.filter(id=category_id, repo_id=repo_id, create_id=create_id)
        all_list = []
        all_list_cate_id = []
        for val in res:
            val_dict = model_to_dict(val)
            category_name = val_dict['category_name']
            categoryLabel = self.get_category_name(request, category_name)
            all_list.append(categoryLabel)
            all_list_cate_id.append(val_dict['id'])
        print(all_list)
        Neo4j().update_attribute_value(all_list, attribute_name, rule_number, rule_content, create_id,
                                       rule_id, all_list_cate_id, repo_id)
        return self.success("更新成功！")

    def merging_rule(self, request):
        # repo_id = request.session['category_id']
        repo_id = request.session["repo_id"]
        ret_date_from_t_normalize_rule = TNormalizedRule.objects.filter(repo_id=repo_id)
        ret_list = []
        cnt = 1
        for val in ret_date_from_t_normalize_rule:
            val_dict = model_to_dict(val)
            category_id = val_dict['category_id']
            tmp_dict = {}
            tmp_dict['id'] = cnt
            tmp_dict['rule_number'] = val_dict['rule_number']
            tmp_dict['update_time'] = str(val_dict['update_time'])[:19]
            tmp_dict['overall_threshold'] = val_dict['overall_threshold']
            category_ques = TCategory.objects.get(id=category_id)
            category_ques_dict = model_to_dict(category_ques)
            tmp_dict['category_name'] = category_ques_dict['category_name']
            cnt += 1
            ret_list.append(tmp_dict)

        ret_l = {}
        ret_l['context'] = ret_list
        print(ret_l)
        return render(request, "index/merging_rule.html", context=self.get_base_info(request, ret_l))

    # 输入是normalized_rule_id 返回t_normalize_rule_detail中内容
    def get_normalize_rule_detail(self, request):
        """
        :param request:
        normalized_rule_id      数据类型str
        :return:
        """
        normalized_rule_id = request.POST['merging_rule_id']
        create_id = request.session['user_id']
        # normalized_rule_id=1
        # create_id=1
        # 查询到category_id
        try:
            ret_normalized_rule = TNormalizedRule.objects.get(id=normalized_rule_id)
        except Exception:
            return self.error("数据库中没有这条规则")
        ret_normalized_rule_dict = model_to_dict(ret_normalized_rule)
        category_id = ret_normalized_rule_dict['category_id']

        ret_normalized_rule = TNormalizedRuleDetail.objects.filter(normalized_rule_id=normalized_rule_id,
                                                                   create_id=create_id)
        ret_list = []
        ret_attribute_list = []
        for val in ret_normalized_rule:
            val_dict = model_to_dict(val)
            tmp_dict = {}
            tmp_dict['id'] = val_dict['id']
            # attribute_id = val_dict['attribute_id']
            tmp_dict['attribute_id'] = val_dict['attribute_id']
            # attribute = TAttribute.objects.get(id=attribute_id)
            # attribute_dict = model_to_dict(attribute)
            # tmp_dict['attribute_name'] = attribute_dict['attribute_name']
            tmp_dict['similarity_threshold'] = val_dict['similarity_threshold']
            ret_list.append(tmp_dict)

        # 返回这条规则类目下面的attribute
        print(category_id)
        ret_attribute_list=some_data_deal_func().get_all_attribute_by_category_id(category_id,['id','attribute_name'])
        # ret_val = TAttribute.objects.filter(category_id=category_id)
        # for att in ret_val:
        #     att_dict = model_to_dict(att)
        #     tmp_attribute_dict = {}
        #     tmp_attribute_dict['id'] = att_dict['id']
        #     tmp_attribute_dict['attribute_name'] = att_dict['attribute_name']
        #     ret_attribute_list.append(tmp_attribute_dict)
        ret_l = {}
        ret_l['context'] = ret_list
        ret_l['attribute'] = ret_attribute_list
        return self.success(ret_l)

    # 输入一些详细的规则 实体归一规则详细 如果id是-1那么添加数据  如果不是-1那么更新数据库 然后更新归一规则表
    def update_merging_rule(self, request):
        data_body = simplejson.loads(request.body)
        overall_threshold = data_body['overall_threshold']
        normalized_rule_id = data_body['rule_id']
        normalized_rule_detail_list = data_body['rule_list']
        create_id = request.session['user_id']
        repo_id = request.session["repo_id"]
        # category_id = request.session['category_id']
        # repo_id = request.session['repo_id']
        # overall_threshold = 1
        # normalized_rule_id = 1
        # normalized_rule_detail_list = [{'id': 1, 'attribute_id': 1, 'similarity_threshold': 0.5},
        #                                {'id': 2, 'attribute_id': 2, 'similarity_threshold': 0.5}]
        # create_id = 1
        try:
            normalized_rule = TNormalizedRule.objects.get(id=normalized_rule_id)
        except ObjectDoesNotExist:
            return self.error("该规则不存在！")
        try:
            news_col = Mongodb(db='knowledge', collection='text').get_collection()
        except Exception:
            return self.error("mongodb没有数据库或者表")

        category_id = normalized_rule.category_id

        num = 0
        key_attribute_list = []
        key_attribute_list_similarity_threshold = []
        for val in normalized_rule_detail_list:
            type = val['id']
            dt = timezone.now()
            # 通过val['attribute_id']得到attribute_name
            #这边有点问题
            ret_attribute = TAttribute.objects.get(id=val['attribute_id'])
            ret_attribute_dict = model_to_dict(ret_attribute)
            key_attribute_list.append(ret_attribute_dict['attribute_name'])
            key_attribute_list_similarity_threshold.append(val['similarity_threshold'])

            if -1 == type:
                TNormalizedRuleDetail.objects.create(normalized_rule_id=normalized_rule_id,
                                                     attribute_id=val['attribute_id'],
                                                     similarity_threshold=val['similarity_threshold'],
                                                     update_time=dt, create_id=create_id)
            else:
                obj = TNormalizedRuleDetail.objects.get(id=type)
                obj.normalized_rule_id = normalized_rule_id
                obj.attribute_id = val['attribute_id']
                obj.similarity_threshold = val['similarity_threshold']
                obj.update_time = dt
                obj.create_id = create_id
                obj.save()
            num += 1
        obj = TNormalizedRule.objects.get(id=normalized_rule_id, category_id=category_id, repo_id=repo_id)
        obj.rule_number = num
        obj.update_time = timezone.now()
        obj.overall_threshold = overall_threshold
        obj.save()

        # 进行同名实体  有类目名字 把所有的数据都拿出来 然后比较名字是否相同
        # 把id和名字拿出 然后n^2去找一样的
        # 找到以后相似度计算 可以用文本的那个
        category_val = TCategory.objects.get(id=category_id)
        category_val_dict = model_to_dict(category_val)
        category_name = category_val_dict['category_name']
        # 获得到名字的那个属性名 就是category_id为1的那个属性
        attribute_val = TAttribute.objects.get(category_id=1)
        attribute_val_dict = model_to_dict(attribute_val)
        attribute_name = attribute_val_dict['attribute_name']
        # 进行neo4j的查询
        while True:
            attributeLabel =self.get_category_name(request,category_name)
            ret_list_id, ret_list_val = Neo4j().ques_id_val(attributeLabel, attribute_name)
            vis = [0 for i in range(0, 100)]
            ret_list_id_len = len(ret_list_id)
            #print("重要",ret_list_id)
            #print("重要",key_attribute_list)
            cnt = 0
            for i in range(0, ret_list_id_len):
                if vis[i] == 0:
                    for j in range(i + 1, ret_list_id_len):
                        if vis[j] != 0:
                            continue
                        if ret_list_val[i] == ret_list_val[j]:
                            # 先写一个neo4j中的处理 把里面关键属性的名字和值拿出来
                            attribute_name_one, attribute_val_one = Neo4j().find_key_value(attributeLabel,
                                                                                           ret_list_id[i],
                                                                                           key_attribute_list)
                            attribute_name_two, attribute_val_two = Neo4j().find_key_value(attributeLabel,
                                                                                           ret_list_id[j],
                                                                                           key_attribute_list)
                            # 这边传入的是2个neo4j中的map 把他们关键属性拿出来就好了
                            # 直接计算val_one和val_two他们之间的相似度就好了
                            similarity = some_data_deal_func().calculate_similarity(attribute_val_one,
                                                                                    attribute_val_two,
                                                                                    key_attribute_list_similarity_threshold)
                            print(similarity)
                            if similarity >= float(overall_threshold):
                                vis[i]=1
                                vis[j]=1
                                cnt=cnt +1
                                #根据id查询整个node的内容
                                #ret_list_id[i] ret_list_id[j]
                                #根据id查询属性
                                firstNode=Neo4j().quesNodeDictUseIdAndLabel(attributeLabel,ret_list_id[i])
                                secondNode=Neo4j().quesNodeDictUseIdAndLabel(attributeLabel,ret_list_id[j])
                                print(firstNode)
                                print(secondNode)
                                ansNode = firstNode
                                for first  in  firstNode.keys():
                                    if(firstNode[first] == None and first in secondNode.keys()):
                                        ansNode[first] = secondNode[first]
                                for second in secondNode.keys():
                                    if(second not in firstNode.keys()):
                                        ansNode[second]=secondNode[second]
                                #在neo4j中新建节点
                                #categoryName  neo4jId
                                #先插入到mongodb
                                #print(ansNode)
                                if('_id' in ansNode.keys()):
                                    del  ansNode['_id']
                                ret=news_col.insert_one(ansNode)
                                #print(ret.inserted_id)
                                ansNode['_id']=ret.inserted_id
                                #然后插入到neo4j
                                retNode=Neo4j().create_node_mjy_edition(attributeLabel,ansNode)
                                #print(retNode.data()[0]['n'])
                                nodeId=0
                                for node in retNode:
                                    nodeId = node['id(n)']
                                #删除原有节点
                                firstNodeDict={'id':ret_list_id[i]}
                                secondNodeDict={'id':ret_list_id[j]}

                                Neo4j().deleteNode(attributeLabel,Neo4j().dictToQuesDict(firstNodeDict))
                                Neo4j().deleteNode(attributeLabel, Neo4j().dictToQuesDict(secondNodeDict))
                                # 大于这个阈值可以写入到数据库日志
                                TNormalizedLog.objects.create(merge_entity_id=nodeId,original_entity_id1=ret_list_id[i],original_entity_id2=ret_list_id[j],normalized_rule_id=normalized_rule_id,create_id=create_id,repo_id=repo_id)
                                break

            if(cnt == 0):
                break
            #这边没测试
        return self.success("修改成功！")

    # 把文件中的内容存入到mongodb 然后更新2个表 计算最近category 更新neo4j
    def knowledge_extract(self, request):
        """
        知识抽取
        :param request:
        :return:
        """
        log_id = request.POST['log_id']
        repo_id = request.session['repo_id']
        create_id = request.session['user_id']

        obj = TEntityExtractionLog.objects.get(id=log_id)
        file_id = obj.data_acquisition_id

        # ExtractUnit().eventExtraction(request=request, file_id=file_id)
        # return self.success("抽取成功！")

        category_attribute_mask = {}
        try:
            ret_file_data = TDataAcquisitionLog.objects.get(id=file_id)
        except Exception:
            return self.error("id没有对应文件")

        ret_file_data_dict = model_to_dict(ret_file_data)

        if ret_file_data_dict["data_access"] == "爬虫":
            entity_infos = self.knowledge_col.find({"file_id": file_id})
            for info in entity_infos:
                list_attribute = list(info["value"].keys())
                # list_attribute.remove("file_id")
                # list_attribute.remove("_id")
                # list_attribute.remove("tag")
                category_id = some_data_deal_func().calculate_nearest_category(list_attribute, repo_id)
                info.setdefault("category_id", category_id)
                self.knowledge_col.update_one({'_id': info["_id"]}, {"$set": {'category_id': int(category_id)}})
                if category_id != -1:
                    if category_id not in category_attribute_mask:
                        category_attribute_mask.setdefault(category_id,
                                                           some_data_deal_func.get_all_attribute_by_category_id(
                                                               category_id=category_id))
                    return_category_name = TCategory.objects.get(id=category_id).category_name
                    temp = category_attribute_mask[category_id].copy()
                    temp.append("_id")
                    content = info["value"]
                    content["_id"] = info["_id"]
                    Neo4j().create_node_mjy_edition(
                        label_name=self.get_category_name(request, return_category_name), property=content,
                        retain_field=temp)
                    ExtractUnit.extract_relationship_from_structured_data(request=request, category_id=category_id, json_data=content)
            obj.is_extract = 1
            obj.entity_number = entity_infos.count()
            obj.extract_time = str(timezone.now())[:19]
            obj.save()
            some_data_deal_func().update_t_mapping_rule(repo_id, create_id)
            # return self.success("抽取成功！")
        elif ret_file_data_dict['data_path'].split(".")[-1] != "xlsx":
            # try:
            with open(ret_file_data_dict['data_path'], 'rb') as fp:
                contents = fp.readlines()
                for content in contents:
                    # if content.startswith(u'/ufeff'):
                    #     content = content.encode('utf8')[3:].decode('utf8')
                    try:
                        content = content.decode("GBK")
                    except Exception:
                        # content = content.decode("GBK")
                        pass
                    content = json.loads(content, object_hook=json_util.object_hook)

                    if "_id" in content:
                        del content["_id"]
                    list_attribute = list(content.keys())
                    category_id = some_data_deal_func().calculate_nearest_category(list_attribute, repo_id)
                    one_new_data = {'file_id': file_id, 'category_id': category_id, "spider_id": -1,
                                    "user_id": request.session["user_id"], "repo_id": request.session["repo_id"],
                                    "value": content}

                    self.knowledge_col.insert_one(one_new_data)
                    if category_id != -1:
                        if category_id not in category_attribute_mask:
                            category_attribute_mask.setdefault(category_id,
                                                               some_data_deal_func.get_all_attribute_by_category_id(
                                                                   category_id=category_id))
                        return_category_name = TCategory.objects.get(id=category_id).category_name
                        temp = category_attribute_mask[category_id].copy()
                        temp.append("_id")
                        content["_id"] = one_new_data["_id"]
                        Neo4j().create_node_mjy_edition(
                            label_name=self.get_category_name(request, return_category_name), property=content,
                            retain_field=temp)
                        ExtractUnit.extract_relationship_from_structured_data(request=request, category_id=category_id, json_data=content)
                some_data_deal_func().update_t_mapping_rule(repo_id, create_id)
                obj.is_extract = 1
                obj.entity_number = len(contents)
                obj.extract_time = str(timezone.now())[:19]
                obj.save()
                # return self.success("抽取成功！")
            # except Exception as e:
            #     print(e)
            #     return self.error("错误！")
        else:
            try:
                data = xlrd.open_workbook(ret_file_data_dict['data_path'])
            except Exception:
                return self.error("没有找到对应文件")

            table_name = data.sheet_names()[0]
            table = data.sheet_by_name(table_name)
            row = table.nrows
            col = table.ncols
            dt = timezone.now()
            entity_number = table.nrows - 1
            is_extract = 1
            # obj = TEntityExtractionLog.objects.get(data_acquisition_id=file_id)
            obj.is_extract = is_extract
            obj.entity_number = entity_number
            obj.extract_time = str(dt)[:19]
            obj.save()

            # 这边还要计算这个的类目
            list_attribute = list(table.row_values(0))
            category_id = some_data_deal_func().calculate_nearest_category(list_attribute, repo_id)
            return_category_name = ''
            if category_id != -1:
                return_category_name = TCategory.objects.get(id=category_id).category_name
            print("相似的category", return_category_name)

            for i in range(1, row):
                dict_data = {}
                for j in range(0, col):
                    dict_data[list_attribute[j]] = table.row_values(i)[j]
                    # print(list_attribute[j],table.row_values(i)[j])
                dict_data['file_id'] = file_id
                dict_data['category_id'] = category_id
                self.knowledge_col.insert_one(dict_data)
                # print(dict_data)

                # 这个insert_one好像会自动帮你的字典里加_id
                # 这边如果category_!=-1
                if category_id != -1:
                    Neo4j().create_node_mjy_edition(return_category_name, dict_data)
            # 所有数据插入完了以后可以更新这个表
            some_data_deal_func().update_t_mapping_rule(repo_id, create_id)
        ExtractUnit().extract_relationship_from_unstructured_data(request=request, file_id=file_id)
        ExtractUnit().eventExtraction(request=request, file_id=file_id)
        return self.success("抽取成功！")

    def extract_result(self, request):
        """
        返回知识抽取结果
        :param request:log_id是t_entity_extraction_log的id，page是页数
        :return:
        """
        data_number_from_one_page = 20
        repo_id = request.session['repo_id']
        # repo_id =1
        log_id = request.GET['log_id']
        # file_id=1
        try:
            page = int(request.GET["page"])
        except Exception:
            page = 1
        file_id = TEntityExtractionLog.objects.get(id=log_id).data_acquisition_id
        tmp_info = {'file_id': file_id}
        try:
            news_col = Mongodb(db='knowledge', collection='text').get_collection()
        except Exception:
            return self.error("mongodb没有数据库或者表")

        ret_entity_map = news_col.find(tmp_info)
        ret_list = []
        for val in ret_entity_map:
            one_data = {"id": val["_id"], "value": val["value"], "category_id": val["category_id"]}
            if "relationship_extract_result" in val and len(val["relationship_extract_result"]) != 0:
                one_data["relationship_extract_result"] = val["relationship_extract_result"]
            if "event_extract_result" in val and len(val["event_extract_result"]) != 0:
                one_data["event_extract_result"] = val["event_extract_result"]
            ret_list.append(one_data)
        category_name_list = []
        ret_category = TCategory.objects.filter(repo_id=repo_id)
        for val in ret_category:
            val_dict = model_to_dict(val)
            tmp_map = {}
            tmp_map['category_name'] = val_dict['category_name']
            tmp_map['category_id'] = val_dict['id']
            category_name_list.append(tmp_map)

        total_num = ret_entity_map.count()
        if total_num % data_number_from_one_page == 0:
            total_page = int(total_num / data_number_from_one_page)
        else:
            total_page = int(total_num / data_number_from_one_page) + 1
        if page < 1:
            page = 1
        elif page > total_page:
            page = total_page
        ret_list = ret_list[(page-1)*data_number_from_one_page: page*data_number_from_one_page]
        ret_l = {'category': category_name_list, 'context': ret_list, 'page_info': json.dumps({'log_id': int(log_id), 'cur_page': page, 'total_page': total_page})}

        # return self.success("成功")
        print(ret_list)
        return render(request, 'index/extract_result.html', context=self.get_base_info(request, ret_l))

    # 点击确认后 输入_id和类目id 然后我要更新mongodb中的这个类目的id 和neo4j中的数据
    def update_entity_info(self, request):
        repo_id = request.session['repo_id']
        # repo_id=1
        create_id = request.session['user_id']
        # create_id=1
        neo4j_entity_id = request.POST['entity_id']
        mongodb_entity_id = ObjectId(neo4j_entity_id)
        # neo4j_entity_id = '5ec1dd47d2cbe96d835db79b'
        # mongodb_entity_id = ObjectId("5ec1dd47d2cbe96d835db79b")
        category_id = request.POST['category_id']
        # category_id=-1
        # category_id = 3
        # 更新Mongodb
        news_col = Mongodb(db='knowledge', collection='text').get_collection()
        # 这边要找到原来那个category_id
        try:
            last_category_id = news_col.find_one({"_id": mongodb_entity_id})['category_id']
        except Exception:
            return self.error("mongodb里面没有这个id对应的实体")
        try:
            news_col.update_one({'_id': mongodb_entity_id}, {"$set": {'category_id': int(category_id)}})
        except Exception:
            return self.error("mongodb中没有这个实体id")

        if (int(last_category_id) != -1):
            # 前面已经插入到数据库假如说不是-1那么酒正常写入
            if (-1 != int(category_id)):
                last_category_name = TCategory.objects.get(id=last_category_id).category_name
                category_name = TCategory.objects.get(id=category_id).category_name
                Neo4j().update_one_node_label(self.get_category_name(request, last_category_name), '_id', neo4j_entity_id, self.get_category_name(request, category_name))
            else:
                # 删除这个节点的数据
                print("删除")
                last_category_name = TCategory.objects.get(id=last_category_id).category_name
                Neo4j().delete_one_node(self.get_category_name(request, last_category_name), neo4j_entity_id)
        else:
            # 这边要从mongodb里面插入到数据库
            ret = news_col.find_one({"_id": mongodb_entity_id})
            # print(ret)
            category_name = TCategory.objects.get(id=category_id).category_name
            field = some_data_deal_func.get_all_attribute_by_category_id(category_id=int(category_id))
            content = ret["value"]
            content["_id"] = ret["_id"]
            field.append("_id")
            Neo4j().create_node_mjy_edition(
                label_name=self.get_category_name(request, category_name), property=content,
                retain_field=field)
            # Neo4j().create_node_mjy_edition(category_name, ret)

        # 这边完了可以更新表
        some_data_deal_func().update_t_mapping_rule(repo_id, create_id)
        return self.success("修改成功！")

    def test(self, request):
        test = {
            "nodes": [{"name": 'node01', "des": 'nodedes01', "symbolSize": 70,"category": 0, "id": "1"},
                      {"name": 'node02', "des": 'nodedes02', "symbolSize": 50, "category": 1, "id": "2"},
                      {"name": 'node03',  "des": 'nodedes3', "symbolSize": 50, "category": 1, "id": "3"},
                      {"name": 'node04', "des": 'nodedes04', "symbolSize": 50, "category": 1, "id": "4"},
                      {"name": 'node05', "des": 'nodedes05', "symbolSize": 50, "category": 1, "id": "5"}],
            "links": [{"source": '1', "target": '2', "name": 'link01', "des": 'link01des'},
                      {"source": '1', "target": '3', "name": 'link02', "des": 'link02des'},
                      {"source": '1', "target": '4', "name": 'link03', "des": 'link03des'},
                      {"source": '1',  "target": '5', "name": 'link04', "des": 'link05des'}]
        }
        return render(request, "index/test.html", context={"data": json.dumps(test)})

    def show_entity(self, request):
        try:
            repo_id = request.session["repo_id"]
        except Exception:
            return self.error("没有repo_id")
        try:
            create_id = request.session["user_id"]
        except Exception:
            return self.error("没有create_id")

        ret_category = TCategory.objects.filter(repo_id=repo_id, create_id=create_id)
        category_list = []
        first_category_name = ''
        first_category_id = 0
        num = 0
        for val in ret_category:
            val_dict = model_to_dict(val)
            tmp_map = {}
            tmp_map['id'] = val_dict['id']
            tmp_map['category_name'] = val_dict['category_name']
            category_list.append(tmp_map)
            if num == 0:
                first_category_name = val_dict['category_name']
                first_category_id = val_dict['id']
            num += 1
        # 查询事物的第一个attribute_name  其实就是名字
        affair_attribute = TAttribute.objects.get(category_id=1)
        affair_attribute_dict = model_to_dict(affair_attribute)
        first_category_attribute_name = affair_attribute_dict['attribute_name']

        #print(first_category_name+"123")
        #print(first_category_attribute_name)
        #print(first_category_id)
        #print(self.get_category_name(request,first_category_name))
        ret_Node = Neo4j().ret_node_list_get_one_category_node_name_id(self.get_category_name(request,first_category_name),
                                                                       first_category_attribute_name, first_category_id)
        ret_l = {}
        ret_l['category'] = json.dumps(category_list)
        ret_l['nodes'] = json.dumps(ret_Node)
        ret_l['links'] = json.dumps([])

        #print(ret_l)

        # test1 = {
        #     "nodes": [{"name": 'node01', "des": 'nodedes01', "symbolSize": 70, "category": 0, "id": "1"},
        #               {"name": 'node02', "des": 'nodedes02', "symbolSize": 50, "category": 1, "id": "2"},
        #               {"name": 'node03',  "des": 'nodedes3', "symbolSize": 50, "category": 1, "id": "3"},
        #               {"name": 'node04', "des": 'nodedes04', "symbolSize": 50, "category": 1, "id": "4"},
        #               {"name": 'node05', "des": 'nodedes05', "symbolSize": 50, "category": 1, "id": "5"}],
        #     "links": [{"source": '1', "target": '2', "name": 'link01', "des": 'link01des'},
        #               {"source": '1', "target": '3', "name": 'link02', "des": 'link02des'},
        #               {"source": '1', "target": '4', "name": 'link03', "des": 'link03des'},
        #               {"source": '1',  "target": '5', "name": 'link04', "des": 'link05des'}]
        # }
        return render(request, "index/show_entity.html", context=self.get_base_info(request, ret_l))

    def ret_category_all_node(self, request):
        """
        返回这个类目的所有节点
        :param request:
        :return:
        """
        try:
            category_id = request.POST['category_id']
        except Exception:
            return self.error("没有category_id")
        ret_category = TCategory.objects.get(id=category_id)
        ret_category_dict = model_to_dict(ret_category)
        category_name = ret_category_dict['category_name']
        affair_attribute = TAttribute.objects.get(category_id=1)
        affair_attribute_dict = model_to_dict(affair_attribute)
        first_category_attribute_name = affair_attribute_dict['attribute_name']
        ret_Node = Neo4j().ret_node_list_get_one_category_node_name_id(
            self.get_category_name(request, category_name),
            first_category_attribute_name, category_id)

        ret_l = {}
        ret_l['nodes'] = ret_Node
        ret_l['links'] = []
        print(ret_l)
        return self.success(ret_l)

    def spider_submit(self, request):
        key_word = request.POST["spider_key_word"]
        new_acq_info = TDataAcquisitionLog.objects.create(create_time=timezone.now(), data_source_name=key_word,
                                                          data_access="爬虫",
                                                          repo_id=request.session["repo_id"],
                                                          create_id=request.session["user_id"])
        new_ext_info = TEntityExtractionLog.objects.create(data_acquisition_id=new_acq_info.id, is_extract=0,
                                                           entity_number=0, extract_time=timezone.now(),
                                                           create_id=request.session["user_id"],
                                                           repo_id=request.session["repo_id"])

        baike_spider_object = BaikeSpider()
        if not baike_spider_object.get_infos(url="https://baike.baidu.com/item/" + key_word,
                                             extensive_properties={"file_id": new_acq_info.id}):
            # 如果爬虫失败删除所有前面建立的所有内容
            baike_col = Mongodb(db='baike', collection="test1").get_collection()
            baike_col.delete_many({"file_id", new_acq_info.id})
            new_acq_info.delete()
            new_ext_info.delete()
            return self.error("爬取失败！")
        return self.success("爬取成功！")

    def spider(self, request):
        """
        爬虫页面
        :param request:
        :return:
        """
        create_id = request.session["user_id"]
        repo_id = request.session["repo_id"]
        spider_project = TSpiderProject.objects.filter(create_id=create_id, repo_id=repo_id)
        project_list = []
        for item in spider_project:
            temp = model_to_dict(item)
            data_website = TSpiderDatawebsite.objects.get(id=temp["data_website_id"])
            data_type = TSpiderDatatype.objects.get(id=temp["data_type_id"])
            temp.setdefault("data_website", data_website.website_name)
            temp.setdefault("spider_datatype", data_type.data_type_name)
            temp.setdefault("spider_statistics", SpiderUtil.GetStatistics(spider_id=item.id, repo_id=request.session["repo_id"]))
            print(SpiderUtil.GetStatistics(spider_id=item.id, repo_id=request.session["repo_id"]))
            del temp["data_website_id"]
            del temp["data_type_id"]
            project_list.append(temp)

        data_website_list = TSpiderDatawebsite.objects.all()
        data_type_list = TSpiderDatatype.objects.all()

        self.assign("project_list", project_list)
        self.assign("data_type_list", self.dict_encode_within(data_type_list, keys=["data_type_mask"]))
        self.assign("data_website_list", self.dict_encode_within(data_website_list, keys=["website_mask"]))
        return self.display(request)

    def add_project(self, request):
        """
        添加爬虫项目
        :param request:
        :return:
        """
        spider_data_website_id = request.POST["spider_data_website_id"]
        spider_data_type_id = request.POST["spider_data_type_id"]
        try:
            TSpiderDatawebsite.objects.get(id=spider_data_website_id)
            TSpiderDatatype.objects.get(id=spider_data_type_id)
            TSpiderProject.objects.create(data_website_id=spider_data_website_id, data_type_id=spider_data_type_id,
                                          status=0, create_id=request.session["user_id"],
                                          repo_id=request.session["repo_id"], create_time=timezone.now())
            return self.success("创建成功！")
        except ObjectDoesNotExist:
            return self.error("爬虫网站或类型不存在！")

    def refresh_statistics(self, request):
        spider_id = request.POST["spider_id"]
        return self.success(SpiderUtil.GetStatistics(spider_id=int(spider_id), repo_id=request.session["repo_id"]))

    def change_status(self, request):
        """
        改变项目状态
        :param request:
        :return:
        """
        project_id = request.POST["project_id"]
        project_status = request.POST["project_status"]
        project = TSpiderProject.objects.get(id=project_id)
        project.status = project_status
        project.save()
        data_website = TSpiderDatawebsite.objects.get(id=project.data_website_id)
        data_type = TSpiderDatatype.objects.get(id=project.data_type_id)
        if int(project_status) == 1:
            # one_data_acquisition_log = TDataAcquisitionLog.objects.create(create_time=timezone.now(),
            #                                                               data_source_name=data_website + data_type,
            #                                                               data_access="爬虫",
            #                                                               repo_id=request.session["repo_id"],
            #                                                               create_id=request.session["user_id"],
            #                                                               data_path="")
            result = SpiderUtil.start_project(project.id, data_website.website_mask, data_type.data_type_mask,
                                              request.session["user_id"], request.session["repo_id"],
                                              data_website.website_name + data_type.data_type_name)
            return self.success(result)
        else:
            result = SpiderUtil.stop_project(project.id)
            return self.error(result)

    # 从后台传输事件数据到前端
    def knowledge_test(self, request):
        li = []
        for i in range(1, 20):
            tmp_map = {}
            tmp_map['date'] = i
            tmp_map['event'] = '本地硬盘自定义RAID等功能1111111111111111111111'
            li.append(tmp_map)
        ret_l = {'category': li}
        return self.success(ret_l)
        # return render(request, 'index.html', context=ret_l)    def acquire_movie_piaofang(self,request):
        movie_id = request.POST['movie_id']
        print(movie_id)
        list_date = []
        list_data = []
        for i in range(1, 50):
            list_date.append('开始' + str(i) + '天');
            if (i <= 10):
                list_data.append(i * 10000);
            else:
                list_data.append(i * 100000000)
        ret_l = {'date': list_date, 'data': list_data}
        return self.success(ret_l)
        # return render(request, 'index.html', context=ret_l)

    def acquire_movie_piaofang(self, request):
        movie_id = request.POST['movie_id']
        print(movie_id)
        list_date = []
        list_data = []
        for i in range(1, 50):
            list_date.append('开始' + str(i) + '天')
            if (i <= 10):
                list_data.append(i * 10000)
            else:
                list_data.append(i * 100000000)
        ret_l = {'date': list_date, 'data': list_data}
        return self.success(ret_l)
        # return render(request, 'index.html', context=ret_l)

    def searchEntity(self,request):
        """

        :param request:
        :param categoryId  类目id
        :param keyWord   关键字
        :return:{'nodes':[{},{}],'links':[{},{}]}
        {'nodes': [{'name': '孟佳营', 'category': 4, 'id': 2962843}, {'name': '孟佳营营', 'category':
         4, 'id': 2962949}, {'name': '孟佳营主演快手枪手快枪手', 'id': 2962948, 'category': 6}, {'name':
        2962924, 'id': 2962924, 'category': 15}], 'links': [{'source': 2962843, 'target': 2962948, 'name'
        : '主谓关系'}, {'source': 2962843, 'target': 2962924, 'name': '主谓关系'}, {'source': 2962843, 't
        arget': 2962924, 'name': '主谓关系'}, {'source': 2962843, 'target': 2962924, 'name': '主谓关系'},
         {'source': 2962843, 'target': 2962924, 'name': '主谓关系'}]}

        """
        #使用neo4jId

        categoryId = request.POST['category_id']
        keyWord = request.POST['entity_search_text']
        repoId=request.session['repo_id']
        createId=request.session['user_id']


        #only for debug
        # request.session['repo_id']=1
        # request.session['user_id']=1
        # categoryId = 4
        # keyWord = "孟佳营"
        # repoId=1
        # createId=1
        # only for debug

        retCategory=TCategory.objects.get(id=categoryId,repo_id=repoId,create_id=createId)
        retCategoryDict=model_to_dict(retCategory)
        categoryName=retCategoryDict['category_name']
        NameLabel=self.get_category_name(request,categoryName)

        #事物的attributeName  = 名字
        retAttribute=TAttribute.objects.get(category_id=1)
        retAttributeName = model_to_dict(retAttribute)['attribute_name']

        #事件的attributeName = 名字
        #事件的attributeTime = 发生时间
        #事件的attributeTriggerWord = 触发词
        #事件的attributePlace = 地点
        retAttributeTwo = TAttribute.objects.get(id=2)
        retAttributeEventName=model_to_dict(retAttributeTwo)['attribute_name']

        #retAttributeThree = TAttribute.objects.get(id=3)
        #retAttributeEventTime=model_to_dict(retAttributeThree)['attribute_name']

        #retAttributeFour = TAttribute.objects.get(id=4)
        #retAttributeEventTriggerWord=model_to_dict(retAttributeFour)['attribute_name']

        #retAttributeFive = TAttribute.objects.get(id=5)
        #retAttributeEventPlace=model_to_dict(retAttributeFive)['attribute_name']


        retNodeList=Neo4j().ret_node_list_get_one_category_node_name_id(NameLabel,retAttributeName,categoryId)

        nodeList =[]
        linkList=[]
        retIdList = []

        #用来节点去同
        nodeIdSet=set()

        for item in retNodeList:
            tmpName = item['name']
            tmpId   =item['id']
            #print(item)
            if(keyWord in tmpName):
                retIdList.append(item)
                nodeIdSet.add(item['id'])
                nodeList.append(item)
                #id name categoryId

        #根据id返回内容
        #对于里面的每一个节点要去同
        #查询所有的关系
        #把指到的节点拿的来
        #把谁指到的节点也拿过来然后去同

        for item in retIdList:
            #print(111111,item)
            retList=Neo4j().getNearRelationshipNode(NameLabel, retAttributeName, item['name'])
            for val in retList:
                #print(val)
                startId = val['id(n)']
                #startId没什么用
                #
                #这一句会有问题关系没有_id
                #
                relationShipId=val['id(r)']
                #relationShipName = Neo4j().getLabelByid(relationShipId)
                #print("relationShip",relationShipId)
                relationShipType=Neo4j().returnRelationShip(relationShipId)
                #Match ()-[r]-() Where ID(r)=2904563 return type(r)
                #print(relationShipType['type(r)'])
                tmpRelationShip={}
                tmpRelationShip['target']=str(startId)

                tmpDict ={}
                tmpDict['id']=relationShipId
                endId = val['id(m)']

                tmpRelationShip['source'] =str(endId)
                tmpRelationShip['name'] = relationShipType['type(r)']
                tmpRelationShip['des'] = relationShipType['type(r)']
                linkList.append(tmpRelationShip)
                #print("endId",endId)
                if( endId not in nodeIdSet):
                    #print("endId111",endId)
                    nodeIdSet.add(endId)
                    endCategoryName = Neo4j().getLabelByNeo4jId(endId)
                    #_id  name category_id
                    #endId
                    #print(endId)
                    retNodeList=Neo4j().returnIdAndNode({'id':endId})
                    #print(retNodeList)
                    if(retNodeList != False):
                        for node in retNodeList:
                            #这边不是很清晰了 明天调整
                            #对node进行解析拿到_id
                            #mongodbid  category_name category_id
                            nodeId = node['id(n)']
                            retNode=Neo4j().analysisNode(node['n'])
                            tmpNode = {}
                            #修改event变成
                            #print(retNode)
                            if(retAttributeEventName in retNode.keys()):
                                tmpNode['name']=retNode[retAttributeEventName]
                            else:
                                tmpNode['name'] = nodeId
                            tmpNode['id'] = str(nodeId)
                            nodeLabel=Neo4j().getLabelByNeo4jId(nodeId)
                            nodeName = nodeLabel['labels(n)'][0].split('_')[0]
                            nodeCategoryId = TCategory.objects.get(category_name=nodeName,repo_id=repoId,create_id=createId).id
                            tmpNode['category']=nodeCategoryId
                            nodeList.append(tmpNode)
                            #事件存入的时候也有cateogory_id
                            #实际上只会有一个节点
                            #all node  attribute from table


        #match(n) where id(n) =  return labels(n)
        ret_l = {}
        ret_l['nodes'] = nodeList
        ret_l['links'] = linkList
        #match(n: 演员_1_1)-[r] - (m)whereid(n) = 2962947return r
        #print(ret_l)
        #match(n: 演员_1_1)-[r] - (m) where id(n) = 2962947 return id(n), id(r), id(m)
        #返回关系和节点好了
        #match(n: 演员_1_1{名字: '林更新'})-[r] - (m) return id(n), id(r), id(m)
        return self.success(ret_l)
        # test1 = {
        #     "nodes": [{"name": 'node01', "des": 'nodedes01', "symbolSize": 70, "category": 0, "id": "1"},
        #               {"name": 'node02', "des": 'nodedes02', "symbolSize": 50, "category": 1, "id": "2"},
        #               {"name": 'node03',  "des": 'nodedes3', "symbolSize": 50, "category": 1, "id": "3"},
        #               {"name": 'node04', "des": 'nodedes04', "symbolSize": 50, "category": 1, "id": "4"},
        #               {"name": 'node05', "des": 'nodedes05', "symbolSize": 50, "category": 1, "id": "5"}],
        #     "links": [{"source": '1', "target": '2', "name": 'link01', "des": 'link01des'},
        #               {"source": '1', "target": '3', "name": 'link02', "des": 'link02des'},
        #               {"source": '1', "target": '4', "name": 'link03', "des": 'link03des'},
        #               {"source": '1',  "target": '5', "name": 'link04', "des": 'link05des'}]
        # }

    # 输入是实体id 返回这个实体的所有信息
    def query_entity_info(self, request):
        try:
            entity_id = request.POST['entity_id']
            # entity_id = 2962783
        except Exception:
            return self.error("没有实体id")
        # 把名字id 和类目跳出来
        # attribute name
        res_attribute = TAttribute.objects.get(category_id=1)
        res_attribute_dict = model_to_dict(res_attribute)
        attribute_name = res_attribute_dict['attribute_name']
        ret_node = Neo4j().ques_node_by_id(entity_id, attribute_name)
        ret_result = self.searchEvent(request=request, _id=entity_id)
        ret_node.update(ret_result)
        print(ret_node)
        print(ret_result)
        return self.success(ret_node)

    def searchEvent(self, request, _id):
        """
        :param _id: 一个节点的neo4jId
        :return: 排好序的事件node {'event':[{'名字': '孟佳营主演快手枪手快枪手', 'time': 1, 'place': '', '_id': 1}]
                                'category':[{"category_id": 类目id, "category_name": "", "attribute": []}]}
        """
        #_id = request.POST['_id']
        repoId = request.session['repo_id']
        createId = request.session['user_id']

        #only for debug
        #_id = 444
        #repoId = 1
        #createId = 1
        #only for debug

        # retNode = Neo4j().returnNode({'id':_id})
        # print(id)

        nodeLabel = Neo4j().getLabelByNeo4jId(_id)
        #print(retNode)
        #print(111,nodeLabel)
        #print(nodeLabel['labels(n)'][0])
        ansNode = None

        #n节点的查询结果变成dict
        # print(123,nodeLabel)
        #print(type(retNode))
        # for val in retNode:
        #     ansNode=Neo4j().analysisNode(val['n'])
        #     ansNode=Neo4j().dictToQuesDict(ansNode)
        #查询之前数字不用变 str要变成\' +str+ \'
        # print(nodeLabel)
        # print(nodeLabel['labels(n)'][0])
        # print(ansNode)
        endNodeList=Neo4j().getEndNode(nodeLabel['labels(n)'][0],"主谓关系", {"id": _id},None)
        nodeList =[]
        categorySet = set()
        endNodeSet = set()
        categoryList=[]
        for val in endNodeList:
            nodeNeo4jId = val['id(m)']
            tmpNode = val['m']
            tmpNode = Neo4j().analysisNode(tmpNode)
            nodeList.append(tmpNode)
            #tmpNode 是节点 根据节点查询label  set 去同
            #最终节点也要去同
            #print(1111,tmpNode)
            tmpNodeId = nodeNeo4jId
            if(tmpNodeId in endNodeSet):
                continue
            endNodeSet.add(tmpNodeId)
            #tmpNodeLabel = Neo4j().getLabelByNeo4jId(tmpNodeId)
            #print(tmpNodeLabel)
            #nodeDict ={}
            #nodeCategory=tmpNodeLabel['labels(n)'][0].split('_')[0]
            #print(nodeCategory)
            #print(nodeCategory)
            #retCategory=TCategory.objects.get(category_name =nodeCategory,repo_id=repoId,create_id=createId)
            #retCategoryDict = model_to_dict(retCategory)
            #nodeCategoryId = retCategoryDict['id']
            #nodeDict['category_id'] = nodeCategoryId
            #nodeDict['category_name'] = nodeCategory
            #nodeDict['attribute']=[]
            #if(nodeCategoryId not in categorySet):
            #    categorySet.add(nodeCategoryId)
            #    print(nodeCategoryId)
            #    print(categorySet)
            #    #获得attribute
            #    att_list = []
            #    father_category_id = TCategory.objects.get(id=nodeCategoryId,repo_id=repoId,create_id=createId).father_category_id
                # print(father_category_id,type(father_category_id))
            #    att_list = some_data_deal_func().input_category_id_return_attribute_list(nodeCategoryId, att_list)

            #    if (str(-1) != father_category_id):

            #        father_father_category_id = TCategory.objects.get(id=father_category_id,repo_id=repoId,create_id=createId).father_category_id
            #        att_list = some_data_deal_func().input_category_id_return_attribute_list(father_category_id,
            #                                                                                 att_list)

            #        if (str(-1) != father_father_category_id):
            #            att_list = some_data_deal_func().input_category_id_return_attribute_list(
            #                father_father_category_id, att_list)
            #    nodeDict['attribute'] =att_list
            #categoryList.append(nodeDict)
        #print(categoryList)
        #ret_l['attribute'] = att_list
            #Neo4j().getLabelByid(_id)
        nodeList = sorted(nodeList, key=functools.cmp_to_key(some_data_deal_func().nodeCmp))
        #for val in retNode:
            #print(val)
        #    id=Neo4j().quesIdByLabelAttribute(nodeLabel['labels(n)'][0],'_id',str(_id))
            #print(id)

        #根据这个Nodelabel 查询所有的有关系的类目 返回
        #nodeLabel 指的是电影

        categoryList=[]
        # print(nodeLabel)
        startCategoryLabel = nodeLabel['labels(n)'][0]
        startCategoryName = startCategoryLabel.split('_')[0]
        category_data_type = TDataType.objects.get(datatype_name=startCategoryName, repo_id=request.session["repo_id"],
                                                   create_id=request.session["user_id"])
        retAttributeList=TAttribute.objects.filter(data_type_id=category_data_type.id)
        for val in retAttributeList:
            valDict =model_to_dict(val)
            categoryId = valDict['category_id']
            nodeDict={}
            tmpCategory=TCategory.objects.get(id=categoryId,repo_id=repoId,create_id=createId)
            tmpCategoryDict = model_to_dict(tmpCategory)
            categoryName = tmpCategoryDict['category_name']
            nodeDict['category_id']=categoryId
            nodeDict['category_name'] = categoryName
            att_list = []
            father_category_id = TCategory.objects.get(id=categoryId, repo_id=repoId,
                                                       create_id=createId).father_category_id
            # print(father_category_id,type(father_category_id))
            att_list = some_data_deal_func.get_all_attribute_by_category_id(category_id=categoryId, return_field_list=["id", "attribute_name"])
            # att_list = some_data_deal_func().input_category_id_return_attribute_list(categoryId, att_list)
            #
            # if (str(-1) != father_category_id):
            #
            #     father_father_category_id = TCategory.objects.get(id=father_category_id, repo_id=repoId,
            #                                                       create_id=createId).father_category_id
            #     att_list = some_data_deal_func().input_category_id_return_attribute_list(father_category_id,
            #                                                                              att_list)
            #
            #     if (str(-1) != father_father_category_id):
            #         att_list = some_data_deal_func().input_category_id_return_attribute_list(
            #             father_father_category_id, att_list)
            nodeDict['attribute'] = att_list
            #那就要票房的类目id，类目名和所有属性
            categoryList.append(nodeDict)
        # print(categoryList)
        #查出自己本身的所有属性然后对着Tcategory表进行查询把所有一样的都查出来
        #根基label查出他的id
        nodeId=TCategory.objects.get(category_name=startCategoryName,repo_id=repoId,create_id=createId).id
        nodeAttribute=TAttribute.objects.filter(category_id =nodeId)
        #用一个list把所有的category id 和category_name 都存起来
        allCategoryList =[]
        allCategory = TCategory.objects.filter(repo_id=repoId,create_id=createId)
        for category in allCategory:
            categoryDcit = model_to_dict(category)
            categoryIdLoop = categoryDcit['id']
            categoryNameLoop = categoryDcit['category_name']
            dictLoop = {}
            dictLoop['id']=categoryIdLoop
            dictLoop['category_name']=categoryNameLoop
            allCategoryList.append(dictLoop)

        for attribute in nodeAttribute:
            #写到这里了
            attributeDict = model_to_dict(attribute)
            attributeName = attributeDict['attribute_name']
            for categoryItem in allCategoryList:
                #这个属性名字和其他的类目名字相同
                if(attributeName == categoryItem['category_name']):
                    nodeDict={}
                    categoryId = categoryItem['id']
                    nodeDict['category_id'] = categoryId
                    nodeDict['category_name'] = categoryItem['category_name']
                    # att_list = []
                    # father_category_id = TCategory.objects.get(id=categoryId, repo_id=repoId,
                    #                                            create_id=createId).father_category_id
                    # print(father_category_id,type(father_category_id))
                    att_list = some_data_deal_func.get_all_attribute_by_category_id(category_id=categoryId,
                                                                                    return_field_list=["id",
                                                                                                       "attribute_name"])
                    # att_list = some_data_deal_func().input_category_id_return_attribute_list(categoryId, att_list)
                    #
                    # if (str(-1) != father_category_id):
                    #
                    #     father_father_category_id = TCategory.objects.get(id=father_category_id, repo_id=repoId,
                    #                                                       create_id=createId).father_category_id
                    #     att_list = some_data_deal_func().input_category_id_return_attribute_list(father_category_id,
                    #                                                                              att_list)
                    #
                    #     if (str(-1) != father_father_category_id):
                    #         att_list = some_data_deal_func().input_category_id_return_attribute_list(
                    #             father_father_category_id, att_list)
                    nodeDict['attribute'] = att_list
                    categoryList.append(nodeDict)
        ret_l = {'event': nodeList, 'category': categoryList}
        return ret_l

    def extract_test(self, request):
        from model.extractUnit import ExtractUnit
        test = ExtractUnit().extract_relationship_from_structured_data(request=request, category_id=11,
                                                                       json_data={"关系测试": "霸王别姬", "_id": "zxcvbnmasdf", "名字": "测试"})

    def acquireGraphInf(self,request):
        """
        :param  id  neo4j中的某个要查询节点的Neo4jId
        :param  category_id 查询的末端节点的category_id
        :param  attributeHorizontalId  横坐标attribute_id
        :param  attributeVerticalId  纵坐标attribute_id
        :return: dict  横的 纵的 数值{'horizontal':[1,2,3],'vertical':[4,5,6]}
        """
        repoId = request.session['repo_id']
        createId = request.session['user_id']
        id = request.POST['id']
        categoryId = request.POST['link_category_id']
        attributeHorizontalId = request.POST['abscissa_id']
        attributeVerticalId =request.POST['ordinate_id']


        #only for debug
        #id =3046302
        #categoryId = 16
        #repoId =createId=1
        #横坐标id
        #attributeHorizontalId=15
        #纵坐标id
        #attributeVerticalId =14
        # only for debug

        attributeHorizontal   = TAttribute.objects.get(id=attributeHorizontalId)
        attributeHorizontalIdDict = model_to_dict(attributeHorizontal)
        attributeHorizontalName = attributeHorizontalIdDict['attribute_name']

        attributeVertical = TAttribute.objects.get(id=attributeVerticalId)
        attributeVerticalDict = model_to_dict(attributeVertical)
        attributeVerticalName = attributeVerticalDict['attribute_name']

        category=TCategory.objects.get(id=categoryId,repo_id=repoId,create_id=createId)
        categoryDict = model_to_dict(category)
        categoryName=categoryDict['category_name']
        labelName =self.get_category_name(request,categoryName)
        #
        attributeDict = {'id':id}
        # attributeDictTrans =Neo4j().dictToQuesDict(attributeDict)
        # print(attributeDictTrans)
        ret = Neo4j().getEndNode(attribute=attributeDict, category_name=labelName)
        # ret=Neo4j().getEndNode(None,None,attributeDict,labelName)
        #print(ret)
        vertical = []
        horizontal = []
        lowestUnit = 3
        # 0 1  2  3
        # % 1 万 亿

        for node in ret:

            nodeId = node['id(m)']
            nodeTrans = Neo4j().analysisNode(node['m'])
            retVertical = nodeTrans[attributeVerticalName]
            # print(retVertical)
            tmpUnit = 3
            if (retVertical.find("%") != -1):
                tmpUnit = 0
            elif (retVertical.find("亿") != -1):
                tmpUnit = 3
            elif (retVertical.find("万") != -1):
                tmpUnit = 2
            else:
                tmpUnit = 1
            if (tmpUnit < lowestUnit):
                lowestUnit = tmpUnit
        # print(lowestUnit)
        ret = Neo4j().getEndNode(attribute=attributeDict, category_name=labelName)
        for node in ret:
            # print(111111)
            nodeId = node['id(m)']
            nodeTrans = Neo4j().analysisNode(node['m'])
            # print(nodeTrans,attributeVerticalName,attributeHorizontalName)
            retHorizontal = nodeTrans[attributeHorizontalName]
            retVertical = nodeTrans[attributeVerticalName]
            num = 0
            try:
                num = float(re.search("\d+(\.\d+)?", retVertical).group())
                if (retVertical.find("万") != -1):
                    if (lowestUnit == 1):
                        num = num * 10000
                if (retVertical.find("亿") != -1):
                    if (lowestUnit == 1):
                        num = num * 100000000
                    elif (lowestUnit == 2):
                        num = num * 10000
                if (retVertical.find("%") != -1):
                    num = num / 100
            except:
                num = 0

            #print(retVertical,resultNumFloat)

            #print(retVertical, resultNumFloat)
            horizontal.append(retHorizontal)
            vertical.append(num)
            #print(resultNumFloat)
            #print(retVertical)
            #print(retHorizontal)

        #这边目前没有数据可以先等着
        #写一个排序
        idList=[]
        lens =len(vertical)
        for i in range(0,lens):
            idList.append(i)
        idList,horizontal=some_data_deal_func().bubbleSort(idList,horizontal)
        newVertical = [0 for i in range(lens)]
        for i in range(0,lens):
            newVertical[i]=vertical[idList[i]]
        ret_l={'horizontal':horizontal,'vertical':newVertical}
        print(ret_l)
        return self.success(ret_l)

    def insertTerm(self,request):
        """
        功能
        新增一个术语 修改分词的结果
        修改原来分词结果在现在结果中的下标
        :param request:
        term        数据类型str     要添加的术语
        categoryId  数据类型int     要添加的术语的类目
        _id         数据类型str     要修改的段落在mongodb里面的id
        :return:
        """
        term=request.POST["word"]
        categoryId=request.POST["word_type"]
        page_id = str(request.POST['id'])
        #only for debug start
        #page_id="5ef6e30c7765440d7a6c2616"
        #term = "相关部门"
        #categoryId=17
        #request.session['repo_id']=1
        #request.session['user_id'] = 1
        # only for debug end

        repoId = request.session['repo_id']
        createId = request.session['user_id']

        try:
            news_col = Mongodb(db='knowledge', collection='text').get_collection()
        except Exception:
            return self.error("mongodb没有数据库或者表")
        retDocument=news_col.insert_one({'名字':term})
        #print(ret)
        _id=retDocument.inserted_id
        mongodb_id =ObjectId(_id)
        ret=news_col.find_one({'_id':mongodb_id})
        #print(ret)
        try:
            categoryName = TCategory.objects.get(id=categoryId,repo_id=repoId,create_id=createId).category_name
        except:
            return self.error("没有类目id或者没有id对应类目")
        categoryLabel = self.get_category_name(request,categoryName)
        Neo4j().create_node_mjy_edition(categoryLabel,ret)
        mongodbPage_id = ObjectId(page_id)
        retPageDocument=news_col.find_one({'_id':mongodbPage_id})
        wordSegmentationResults=retPageDocument['wordSegmentationResults']
        #print(wordSegmentationResults)
        updatewordSegmentationResults=[[]]
        #首先是术语合并更新num tag = 0
        #完成以后对于每一个触发词进行寻找最近的
        #更新事件和关系
        #

        wordSegmentationResultsLen=len(wordSegmentationResults)
        allWordLen = 0;
        for ind in  range(wordSegmentationResultsLen):
            tmpList = wordSegmentationResults[ind]
            allWordLen+= len(tmpList)
        wordListTag =[]
        for ind in range(allWordLen):
            wordListTag.append(0)
        for ind in range(wordSegmentationResultsLen):
            tmpList=wordSegmentationResults[ind]
            tmpAddList=[]
            tmpListTranslate=[]
            tmpListLen = len(tmpList)
            #在统计完成以后进行重新赋值
            for i in  range(tmpListLen):
                tmpStr = ''
                for j in range(i,tmpListLen):
                    tmpStr += tmpList[j]['word']
                    #print(tmpStr,term)
                    if(tmpStr == term):
                        tmpDict={'start':i,'end':j}
                        tmpAddList.append(tmpDict)
                        i=j
                        break
            tmpAddListLen  =len(tmpAddList)
            #print(tmpAddList)

            if(tmpAddListLen !=0):
                #tmpList 要被赋值
                #重新修改计算完成以后
                #先只更新数组里的内容
                i=0
                while(i<tmpListLen):
                    #indexSt记录术语开始的位置
                    #indexEd记录术语结束的位置
                    #isTerm记录是否是术语
                    indexSt = i
                    indexEd = i
                    isTerm=0

                    for j in range(tmpAddListLen):
                        if (i >= tmpAddList[j]['start'] and i <= tmpAddList[j]['end']):
                            indexSt=tmpAddList[j]['start']
                            indexEd=tmpAddList[j]['end']
                            isTerm=1
                            wordListTag[tmpList[i]['num']]=1
                            i=tmpAddList[j]['end']
                    tmpDict={}
                    if(isTerm == 1):
                        tmpDict={'word':term,'mask':categoryLabel,'tag':0}
                    else:
                        tmpDict=tmpList[indexSt]
                    tmpListTranslate.append(tmpDict)
                    i=i+1
            else:
                tmpListTranslate=tmpList
            #在这之前确定index
            #print(tmpListTranslate)
            if(tmpListLen == 0):
                continue;
            index=tmpList[0]['num']
            wordSegmentationResults[ind]=tmpListTranslate
            #print(index)
            for j in range(ind,wordSegmentationResultsLen):
                tmpList=wordSegmentationResults[j]
                tmpListLen = len(tmpList)
                for k in range(tmpListLen):
                    wordSegmentationResults[j][k]['num']=index
                    index += 1
            #完成以后更新所有的值
        #上面的已经更新完了 然后把这个东西存回去就好了

        #wordListTag = []
        for ind in range(1,allWordLen):
            wordListTag[ind]+=wordListTag[ind-1]
        relationship_extract_result = retPageDocument['relationship_extract_result']
        event_extract_result = retPageDocument['event_extract_result']
        #print(relationship_extract_result)
        #print(event_extract_result)

        for val in relationship_extract_result:
            object_from_name_index=val["object_from_name_index"]
            object_to_name_index=val["object_to_name_index"]
            object_relationship_name_index=val["object_relationship_name_index"]
            object_from_name_index-=wordListTag[object_from_name_index]
            object_to_name_index-=wordListTag[object_to_name_index]
            object_relationship_name_index-=wordListTag[object_relationship_name_index]
            val["object_from_name_index"]=object_from_name_index
            val["object_to_name_index"]=object_to_name_index
            val["object_relationship_name_index"] = object_relationship_name_index
        for val in event_extract_result :
            eventSubjectIndex=val["eventSubjectIndex"]
            triggerWordIndex=val["triggerWordIndex"]
            eventSubjectIndex-=wordListTag[eventSubjectIndex]
            triggerWordIndex-= wordListTag[triggerWordIndex]
            val["eventSubjectIndex"]=eventSubjectIndex
            val["triggerWordIndex"]=triggerWordIndex
            if("eventObjectIndex" in val.keys()):
                eventObjectIndex=val["eventObjectIndex"]
                eventObjectIndex-=wordListTag[eventObjectIndex]
                val["eventObjectIndex"] = eventObjectIndex
        #print(relationship_extract_result)
        #print(event_extract_result)
        news_col.update_one({'_id': mongodbPage_id}, {"$set": {'relationship_extract_result': relationship_extract_result,'event_extract_result': event_extract_result, 'wordSegmentationResults': wordSegmentationResults}})
        #print()
        #for i in wordSegmentationResults:
        #    print(i)
        #这边后面还要修改抽取结果的内容
        ret_l={}
        #就直接找离触发词最近的那个
        #就是改这个就行了
        #现在这个加新词的把两个词合在一起tag是0
        #然后把后面的词num都更新一下
        #把事件和关系里部分有改动的更新一下就行

        return self.success("成功")
        #return render(request, "test.html", context=ret_l)

    def extractResultTagging(self, request):
        """
        功能:根据输入mongodb的_id 返回段落分词的结果和关系抽取事件抽取的结果
        并且把分词结果 和 颜色和类目 添加到mongodb里面
        mongodb里面添加事件关系在文章中的下标
        :param request: _id 数据类型str/int 需要分词的一段话在mongodb中id
        :return:  ret_l   数据类型dict      返回段落的分词结果 抽取的关系抽取的事件 分词结果的颜色和类目,所有的类目和id 所有的关系
        例子{'cutResult':
        [[{'word': '浙江', 'mask': 'location', 'tag': 6, 'num': 0}, {'word': ',', 'mask': 'w', 'tag': 0, 'num': 1}]]
        'relationship_extract_result':
        [{'object_from_category': '演员_1_1', 'object_to_category': '电影_1_1', 'object_from_name': '国家',
        'object_relationship_name': '组织', 'object_to_name': '片源', 'object_relationship_category': '组织test_1_1'},{}],
        'event_extract_result':
        [{'time': '2020-06-05 14:21:40', 'location': '浙江', 'eventSubject': '国家', 'eventSubjectLabel': '演员_1_1',
        'triggerLabel': '组织_1_1', 'triggerWord': '组织', 'eventObject': '片源', 'eventObjectLabel': '电影_1_1'},{}]}
        'tagCategory':
         [{'tag': 3, 'category': '演员'}, {'tag': 2, 'categ
        ory': '电影'}, {'tag': 1, 'category': '组织test,组织'}]
         'category':
         [{'id': 1, 'category_name': '事物'}, {'id': 3, 'category_name': '人物'}, {'id': 4, 'category_name': '演员'},
        {'id': 5, 'category_name': '导演'}]}
        'relationship':
        [{'id': 1, 'attribute_name': '电影'}, {'id': 2, 'attribute_name': '导演'}, {'id': 3, 'attribut
        e_name': '电影'},]
        """
        print("这里是extractResultTagging")
        _id = str(request.GET['_id'])
        # repoId=1
        # createId=1
        repoId = request.session['repo_id']
        createId = request.session['user_id']

        # _id="5f06fe7cf07991d5ee869d9b"
        mongodb_id = ObjectId(_id)
        try:
            news_col = Mongodb(db='knowledge', collection='text').get_collection()
        except Exception:
            return self.error("mongodb没有数据库或者表")
        tmpDict = {'_id': mongodb_id}
        retDict = news_col.find_one(tmpDict)

        value = retDict['value']
        content = value['内容']
        text = HanlpUnit().get_text_from_html(content)
        # print(text)
        text = ''.join(text.split())
        relationship_extract_result = retDict['relationship_extract_result']
        event_extract_result = retDict['event_extract_result']
        final_contents = [[]]
        tagCategoryDictList = []

        if "wordSegmentationResults" not in retDict.keys():
            tmpMap = {}
            countMap = {}
            colorMap = {}
            color = 1
            # word "tag": 1, "nums": 1
            for val in relationship_extract_result:
                object_from_category = val['object_from_category']
                object_to_category = val['object_to_category']
                object_from_name = val['object_from_name']
                object_to_name = val['object_to_name']
                object_relationship_name = val['object_relationship_name']
                object_relationship_category = val['object_relationship_category']
                # 关系主体
                tmpMap = some_data_deal_func().mapAddVal(object_from_name, object_from_category, tmpMap)
                # 关系客体
                tmpMap = some_data_deal_func().mapAddVal(object_to_name, object_to_category, tmpMap)
                # 关系
                tmpMap = some_data_deal_func().mapAddVal(object_relationship_name, object_relationship_category, tmpMap)
                # 添加入countMap和color map
                countMap = some_data_deal_func().addCountMap(
                    [object_relationship_name, object_to_name, object_from_name], countMap)
                # countMap = some_data_deal_func().addCountMap(object_to_name, countMap)
                # countMap = some_data_deal_func().addCountMap(object_relationship_name, countMap)

                # if(object_from_name in tmpMap.keys()):
                #     tmpList = tmpMap[object_from_name]
                #     if(object_from_category not in tmpList):
                #         tmpList.append(object_from_category)
                #         tmpMap[object_from_name]=tmpList
                # else:
                #     tmpList=[]
                #     tmpList.append(object_from_category)
                #     tmpMap[object_from_name]=tmpList

                # if( object_to_name in tmpMap.keys()):
                #     tmpList = tmpMap[object_to_name]
                #     if(object_to_category not in tmpList):
                #         tmpList.append(object_to_category)
                # else:
                #     tmpList=[]
                #     tmpList.append(object_to_category)
                # 关系名字
                # 这个少了
            for val in event_extract_result:
                time = val['time']
                location = val['location']

                eventSubject = val['eventSubject']
                eventSubjectLabel = val['eventSubjectLabel']
                triggerLabel = val['triggerLabel']
                triggerWord = val['triggerWord']

                tempWordList = []
                # time
                if (len(time) != 0):
                    tmpMap = some_data_deal_func().mapAddVal(time, 'time', tmpMap)
                    tempWordList.append(time)
                # location
                if (len(location) != 0):
                    tmpMap = some_data_deal_func().mapAddVal(location, 'location', tmpMap)
                    tempWordList.append(location)
                # 事件主题
                tmpMap = some_data_deal_func().mapAddVal(eventSubject, eventSubjectLabel, tmpMap)
                tempWordList.append(eventSubject)
                # 事件触发词
                tmpMap = some_data_deal_func().mapAddVal(triggerWord, triggerLabel, tmpMap)
                tempWordList.append(triggerWord)

                # 事件客体
                if ('eventObject' in val.keys()):
                    eventObject = val['eventObject']
                    eventObjectLabel = val['eventObjectLabel']
                    tmpMap = some_data_deal_func().mapAddVal(eventObject, eventObjectLabel, tmpMap)
                    tempWordList.append(eventObject)
                countMap = some_data_deal_func().addCountMap(tempWordList, countMap)
                # colorMap, color = some_data_deal_func().addColorMap(tempWordList, color, colorMap)
            # 先用一个map<str,list<str> > 这样可以存储每个词的词性
            # 之后再利用添加词汇 把后面这个改成一个字符串然后添加进去 然后进行分词
            # print(tmpMap)
            # 这里对所有的tmpMap的key,val里面的val生成颜色
            addColorList = []
            for val in tmpMap.keys():
                valList = tmpMap[val]
                valListStr = ""
                valCnt = 0
                for j in valList:
                    if (valCnt != 0):
                        valListStr += ","
                    valListStr += j
                    valCnt += 1
                addColorList.append(valListStr)
            colorMap, color = some_data_deal_func().addColorMap(addColorList, color, colorMap)
            wordList = []
            # print(tmpMap)
            # 将tmpMap里面词性转换成list [{},{}] 存入wordList
            for val in tmpMap.keys():
                tempList = tmpMap[val]
                cnt = 0
                tmpStr = ""
                for i in tempList:
                    if (cnt == 0):
                        tmpStr = tmpStr + i
                    else:
                        tmpStr = tmpStr + "/" + i
                    cnt = cnt + 1
                tempWordDict = {}
                tempWordDict['word'] = val
                tempWordDict['mask'] = tmpStr
                wordList.append(tempWordDict)
            # [浙江/ns, 杭州/ns, 明天/t, 林更新/演员_1_1, 出演/出演_1_1, 动作/n, 喜剧/n, 《/w, 快手枪手快枪手/电
            tmpHanlp = HanlpUnit()
            tmpHanlp.add_word_list(wordList)
            # print(11111,wordList)
            ret = tmpHanlp.cut(text)
            # 出问题了

            contents = tmpHanlp.get_text_subsection_from_html(content)
            cnt = 0
            i = 0
            index = 0
            temp = len(contents[0])
            # print(contents[0])
            # print(temp)
            # print('ret',ret)
            for item in ret:
                if cnt < temp:
                    tempDict = {}
                    word = item.split("/")[0]
                    mask = ','.join(item.split("/")[1:])
                    tempDict['word'] = word
                    tempDict['mask'] = mask

                    if (mask not in colorMap.keys()):
                        tempDict['tag'] = 0
                    else:
                        tempDict['tag'] = colorMap[mask]
                    tempDict['num'] = index
                    final_contents[i].append(tempDict)
                    cnt += len(item.split("/")[0])
                elif cnt >= temp:
                    i += 1
                    tempDict = {}
                    word = item.split("/")[0]
                    mask = ''.join(item.split("/")[1:])
                    tempDict['word'] = word
                    tempDict['mask'] = mask

                    if (mask not in colorMap.keys()):
                        tempDict['tag'] = 0
                    else:
                        tempDict['tag'] = colorMap[mask]
                    tempDict['num'] = index
                    final_contents.append([tempDict])
                    cnt += len(item.split("/")[0])
                    temp += len(contents[i])
                index = index + 1
            # print(22222,final_contents)
            for val in colorMap.keys():
                tagNum = colorMap[val]
                tmpList = val.split(',')
                retString = ""
                tmpCnt = 0
                for j in tmpList:
                    if (tmpCnt != 0):
                        retString += ','
                    retString += j.split('_')[0]
                    tmpCnt += 1
                tagCategoryDictList.append({'tag': tagNum, 'category': retString})
            # print(tagCategoryDictList)
            # 这个东西还是不对的
            #
            # 所有东西都完成以后
            # 进行原来事件的定位
            # 此处要构造一个全部的的数组
            tmpfinal_contents = []
            for i in final_contents:
                for j in i:
                    tmpfinal_contents.append(j)
            tmpfinal_contentsLen = len(tmpfinal_contents)
            relationship_extract_resultList = []
            for val in relationship_extract_result:
                object_from_category = val['object_from_category']
                object_to_category = val['object_to_category']
                object_from_name = val['object_from_name']
                object_to_name = val['object_to_name']
                object_relationship_name = val['object_relationship_name']
                object_relationship_category = val['object_relationship_category']
                # 从分词结果里面去找这个东西
                # 这三个词在句子中的下标
                object_from_name_index = 0
                object_to_name_index = 0
                object_relationship_name_index = 0
                for j in range(tmpfinal_contentsLen):
                    if (tmpfinal_contents[j]['word'] == object_relationship_name):
                        relaNum = 1
                        tmp_object_relationship_name_index = tmpfinal_contents[j]['num']
                        # 设置成一个很大的值
                        dis = 100000
                        endnum = j
                        for k in range(j - 1, 0, -1):
                            if (tmpfinal_contents[k]['word'] == object_from_name and j - k < dis):
                                dis = j - k
                                endnum = tmpfinal_contents[k]['num']
                                # tmp_object_from_name_index = tmpDictList[k]['num']
                                break
                        for k in range(j + 1, tmpfinal_contentsLen, 1):
                            if (tmpfinal_contents[k]['word'] == object_from_name and k - j < dis):
                                dis = k - j
                                endnum = tmpfinal_contents[k]['num']
                                # tmp_object_from_name_index = tmpDictList[k]['num']
                                break
                        # print(dis,tmpDictList[endnum]['word'])
                        # print(object_from_name)
                        # print(object_to_name)
                        # print(object_relationship_name)
                        # print(dis)
                        if (dis < 100000):
                            relaNum += 1
                            tmp_object_from_name_index = endnum
                        dis = 100000
                        endnum = j

                        for k in range(j + 1, tmpfinal_contentsLen, 1):
                            if (tmpfinal_contents[k]['word'] == object_to_name and k - j < dis):
                                dis = k - j
                                endnum = tmpfinal_contents[k]['num']
                                break
                        for k in range(j - 1, 0, -1):
                            if (tmpfinal_contents[k]['word'] == object_to_name and k - j < dis):
                                dis = j - k
                                endnum = tmpfinal_contents[k]['num']
                                break
                        if (dis < 100000):
                            relaNum += 1
                            tmp_object_to_name_index = endnum
                        # print(dis)
                        # print(tmpDictList)
                        # print(dis, tmpDictList[endnum]['word'])
                        # print(111, tmp_object_from_name_index, tmp_object_relationship_name_index, tmp_object_to_name_index)
                        if (relaNum == 3):
                            # 三者都有进行更新
                            object_from_name_index = tmp_object_from_name_index
                            object_to_name_index = tmp_object_to_name_index
                            object_relationship_name_index = tmp_object_relationship_name_index
                            # print(111,object_from_name_index,object_relationship_name_index,object_to_name_index)
                # 完成以后进行这个东西的更新
                relationshipDict = val
                relationshipDict['object_from_name_index'] = object_from_name_index
                relationshipDict['object_to_name_index'] = object_to_name_index
                relationshipDict['object_relationship_name_index'] = object_relationship_name_index
                relationship_extract_resultList.append(relationshipDict)
                # 这个东西要更新进去

            event_extract_resultList = []
            for val in event_extract_result:
                time = val['time']
                location = val['location']
                # 时间和地点先放过去
                ###有Bug

                eventSubject = val['eventSubject']
                eventSubjectLabel = val['eventSubjectLabel']
                triggerLabel = val['triggerLabel']
                triggerWord = val['triggerWord']
                if ('eventObject' in val.keys()):
                    eventObject = val['eventObject']
                    eventObjectLabel = val['eventObjectLabel']
                # 事件的还要分类讨论一下
                # 从分词结果里面去找这个东西
                # 这三个词在句子中的下标
                eventSubjectIndex = 0
                triggerWordIndex = 0
                eventObjectIndex = 0
                for j in range(tmpfinal_contentsLen):
                    if (tmpfinal_contents[j]['word'] == triggerWord):
                        relaNum = 1
                        tmpTriggerWordIndex = tmpfinal_contents[j]['num']
                        dis = 100000
                        ennum = j
                        for k in range(j - 1, 0, -1):
                            if (tmpfinal_contents[k]['word'] == eventSubject and j - k < dis):
                                dis = j - k
                                ennum = tmpfinal_contents[k]['num']
                                break
                        for k in range(j + 1, tmpfinal_contentsLen, 1):
                            if (tmpfinal_contents[k]['word'] == eventSubject and k - j < dis):
                                dis = k - j
                                ennum = tmpfinal_contents[k]['num']
                                break
                        if (dis < 100000):
                            tmpEventSubjectIndex = ennum
                            relaNum += 1
                        tmpEventObjectIndex = 0
                        if ('eventObject' in val.keys()):
                            dis = 100000
                            ennum = j
                            for k in range(j + 1, tmpfinal_contentsLen, 1):
                                if (tmpfinal_contents[k]['word'] == eventObject and k - j < dis):
                                    dis = k - j
                                    ennum = tmpfinal_contents[k]['num']
                                    # tmpEventObjectIndex = tmpDictList[k]['num']
                                    break
                            for k in range(j - 1, 0, -1):
                                if (tmpfinal_contents[k]['word'] == eventObject and j - k < dis):
                                    dis = j - k
                                    ennum = tmpfinal_contents[k]['num']
                                    # tmpEventObjectIndex = tmpDictList[k]['num']
                                    break
                            if (dis < 100000):
                                tmpEventOubjectIndex = ennum
                                relaNum += 1
                        if (relaNum == 3):
                            # 三者都有进行更新
                            eventSubjectIndex = tmpEventSubjectIndex
                            triggerWordIndex = tmpTriggerWordIndex
                            eventObjectIndex = tmpEventObjectIndex
                        elif (relaNum == 2 and 'eventObject' not in val.keys()):
                            eventSubjectIndex = tmpEventSubjectIndex
                            triggerWordIndex = tmpTriggerWordIndex
                # 完成以后进行这个东西的更新
                eventDict = val
                eventDict['eventSubjectIndex'] = eventSubjectIndex
                eventDict['triggerWordIndex'] = triggerWordIndex
                if ('eventObject' in val.keys()):
                    eventDict['eventObjectIndex'] = eventObjectIndex
                event_extract_resultList.append(eventDict)
            news_col.update_one({'_id': mongodb_id}, {
                "$set": {'relationship_extract_result': relationship_extract_resultList,
                         'event_extract_result': event_extract_resultList}})
            # print(11111,relationship_extract_resultList)
            # print(22222,event_extract_resultList)
            # 假如说我已经有这些标注了那么我要再把这个原来的句子进行一次标注
            # 使得其他的变成0
            # 然后进行更新
            # 这边要先把所有的index拿出来有用的标成1完成了以后再进行匹配
            tempArray = []
            allPageLen = 0
            final_contentsLen = len(final_contents)
            for i in range(final_contentsLen):
                tmpDictList = final_contents[i]
                tmpDictListLen = len(tmpDictList)
                allPageLen += tmpDictListLen
            for i in range(allPageLen):
                tempArray.append(0)

            for val in relationship_extract_resultList:
                object_from_name_index = val['object_from_name_index']
                object_to_name_index = val['object_to_name_index']
                object_relationship_name_index = val['object_relationship_name_index']
                tempArray[object_from_name_index] = 1
                tempArray[object_to_name_index] = 1
                tempArray[object_relationship_name_index] = 1
                # final_contentsLen = len(final_contents)
                # for i in range(final_contentsLen):
                #     tmpDictList = final_contents[i]
                #     tmpDictListLen = len(tmpDictList)
                #     for j in range(tmpDictListLen):
                #         if(final_contents[i][j]['word'] == object_from_name and final_contents[i][j]['num']!=object_from_name_index):
                #             final_contents[i][j]['tag']=0
                #         if (final_contents[i][j]['word'] == object_to_name and final_contents[i][j]['num'] != object_from_to_index):
                #             final_contents[i][j]['tag'] = 0
                #         if (final_contents[i][j]['word'] == object_from_name and final_contents[i][j]['num'] != object_from_name_index):
                #             final_contents[i][j]['tag'] = 0
            for val in event_extract_resultList:
                # print(val)
                eventSubjectIndex = val['eventSubjectIndex']
                triggerWordIndex = val['triggerWordIndex']
                if ('eventObject' in val.keys()):
                    eventObjectIndex = val['eventObjectIndex']
                    tempArray[eventObjectIndex] = 1
                tempArray[eventSubjectIndex] = 1
                tempArray[triggerWordIndex] = 1
            # print(tempArray)
            final_contentsLen = len(final_contents)
            for i in range(final_contentsLen):
                tmpDictList = final_contents[i]
                tmpDictListLen = len(tmpDictList)
                for j in range(tmpDictListLen):
                    if (tempArray[tmpDictList[j]['num']] == 0):
                        final_contents[i][j]['tag'] = 0
            # print(final_contents)
            news_col.update_one({'_id': mongodb_id}, {
                "$set": {'relationship_extract_result': relationship_extract_resultList,
                         'event_extract_result': event_extract_resultList, 'wordSegmentationResults': final_contents,
                         "tagCategory": tagCategoryDictList}})
            print(1)
        else:
            final_contents = retDict["wordSegmentationResults"]
            tagCategoryDictList = retDict["tagCategory"]
            print(2)
        # if("wordSegmentationResults" in retDict.keys()):
        retCategory = TCategory.objects.filter(repo_id=repoId, create_id=createId, category_type=1)
        categoryList = []
        # cnt=0
        for tmpCategory in retCategory:
            # print(22)
            tmpDict = {}
            tmpCategoryDict = model_to_dict(tmpCategory)
            tmpDict['id'] = tmpCategoryDict['id']
            tmpDict['category_name'] = tmpCategoryDict['category_name']
            categoryList.append(tmpDict)
            # cnt+=1
        # print("类目个数",cnt)
        relationshipList = some_data_deal_func().findAllRealtionship(repoId, createId)
        print(relationshipList)
        retEventCategory = TCategory.objects.filter(repo_id=repoId, create_id=createId, category_type=2)
        eventCategory = []
        for val in retEventCategory:
            valDict = model_to_dict(val)
            if (valDict['category_name'] == "事件"):
                continue
            eventCategory.append({'id': valDict['id'], 'category_name': valDict['category_name']})
        print(eventCategory)
        ret_l = {'id_': _id, 'cutResult': final_contents, 'relationship_extract_result': relationship_extract_result,
                 'event_extract_result': event_extract_result, 'tagCategory': tagCategoryDictList,
                 'category': categoryList, 'relationship': relationshipList, 'eventCategoryName':eventCategory}

        # for i in final_contents:
        #    for val in i:
        #        print(val['word'],val['mask'],val['tag'],val['num'])
        # print(final_contents)
        # word_list:词列表，格式[{"word": "", "mask": ""}] word为词名，mask为词性
        # ret_l = {'cutResult':final_contents,'relationship_extract_result':relationship_extract_result,'event_extract_result':event_extract_result,'tagCategory':tagCategoryDictList}
        # print(relationship_extract_result)
        # print(event_extract_result)
        # print(ret_l)
        # return render(request, "test.html", context=ret_l)
        return render(request, "index/contentanalysis.html", context=ret_l)

    def addRelationship(self,request):
        """
        功能：添加新的关系，更新分词结果的词性，更新mongodb里面关系抽取的结果(添加一条数据)
        假如neo4j中节点不存在，建立节点  建立关系
        :param request:
        _id             数据类型 str  抽取结果在mongodb里面id
        object1_id      数据类型 str  抽取主体在抽取结果中的下标
        object2_id      数据类型 str  抽取客体在抽取结果中的下标
        relationship_id 数据类型 str  属性id
        key_word_id     数据类型 str  关键词在抽取结果中的下标
        :return:
        """
        _id = str(request.POST['id'])
        object1_id=int(request.POST['object1_id'])
        object2_id=int(request.POST['object2_id'])
        relationship_id=int(request.POST['relationship_id'])
        key_word_id = int(request.POST['key_word_id'])

        #57,
        #"object_to_name_index": 63,
        #"object_relationship_name_index": 62
        #only for debug start
        # _id = '5ef6e30c7765440d7a6c2616'
        # object1_id=59
        # object2_id=63
        # relationship_id=42
        # key_word_id=62
        # only for debug end
        # request.session['repo_id']=1
        # request.session['user_id']=1
        repoId = request.session['repo_id']
        createId = request.session['user_id']
        mongodb_id = ObjectId(_id)
        try:
            news_col = Mongodb(db='knowledge', collection='text').get_collection()
        except Exception:
            return self.error("mongodb没有数据库或者表")
        ret=news_col.find_one({'_id':mongodb_id})
        relationship_extract_result =ret['relationship_extract_result']
        wordSegmentationResults=ret['wordSegmentationResults']
        tagCategory=ret['tagCategory']

        #维护一个颜色的最大值
        maxColor=0
        colorDict = {}
        tagCategoryLen = len(tagCategory)
        for i in range(tagCategoryLen):
            colorDict[tagCategory[i]['category']]=tagCategory[i]['tag']
            maxColor=max(maxColor,tagCategory[i]['tag'])

        #可以预处理一下把所有的都拿出来那么只要o(n)
        wordSegmentationResultsList = []
        wordSegmentationResultsLen = len(wordSegmentationResults)
        for i in range(wordSegmentationResultsLen):
            tmpList =wordSegmentationResults[i]
            tmpListLen =len(tmpList)
            for j in range(tmpListLen):
                wordSegmentationResultsList.append(tmpList[j])
        object_from_name=wordSegmentationResultsList[object1_id]['word']
        object_to_name = wordSegmentationResultsList[object2_id]['word']
        object_relationship_name = wordSegmentationResultsList[key_word_id]['word']

        #这个通过属性id找到一条关系
        retAttribute=TAttribute.objects.get(id=relationship_id)
        object_relationship_name_category=self.get_category_name(request,retAttribute.attribute_name)
        retCategory=TCategory.objects.get(id=retAttribute.category_id)
        object_from_name_category = self.get_category_name(request,retCategory.category_name)
        retDataType=TDataType.objects.get(id=retAttribute.data_type_id)
        object_to_name_category =self.get_category_name(request,retDataType.datatype_name)
        #把这个东西存入到数据库中
        #
        relationship_extract_result.append({'object_from_name':object_from_name,
                                            'object_to_name':object_to_name,
                                            'object_relationship_name':object_relationship_name,
                                            'object_from_category':object_from_name_category,
                                            'object_to_category':object_to_name_category,
                                            'object_relationship_category':object_relationship_name_category,
                                            'object_from_name_index':object1_id,
                                            'object_to_name_index':object2_id,
                                            'object_relationship_name_index':key_word_id
                                            })
        #更新数据库
        #news_col.update_one({'_id': mongodb_id}, {"$set": {'relationship_extract_result':relationship_extract_result}})
        #更新原来分词的结果
        object_from_name_label=retCategory.category_name
        object_to_name_label=retDataType.datatype_name
        object_relationship_name_label=retAttribute.attribute_name
        object_from_name_tag=0
        object_to_name_tag = 0
        object_relationship_name_tag = 0
        #假如颜色已经存在那么直接拿过来用
        #假如类目不存在那么添加数据 更新表内容
        maxColor,object_from_name_tag,colorDict=some_data_deal_func().updateColorDict(maxColor,object_from_name_label,colorDict)
        maxColor, object_to_name_tag, colorDict = some_data_deal_func().updateColorDict(maxColor, object_to_name_label,colorDict)
        maxColor, object_relationship_name_tag, colorDict = some_data_deal_func().updateColorDict(maxColor, object_relationship_name_label,colorDict)

        # if(object_from_name in colorDict.keys()):
        #     object_from_name_tag=colorDict['object_from_name']
        # else:
        #     maxColor +=1
        #     colorDict[object_from_name]=maxColor
        #     object_from_name_tag=maxColor

        for i in range(wordSegmentationResultsLen):
            tmpList =wordSegmentationResults[i]
            tmpListLen =len(tmpList)
            for j in range(tmpListLen):
                if(tmpList[j]['num'] == object1_id):
                    wordSegmentationResults[i][j]['mask']=object_from_name_category
                    wordSegmentationResults[i][j]['tag']=object_from_name_tag
                elif(tmpList[j]['num'] == object2_id):
                    wordSegmentationResults[i][j]['mask']=object_to_name_category
                    wordSegmentationResults[i][j]['tag']=object_to_name_tag
                elif(tmpList[j]['num'] == key_word_id):
                    wordSegmentationResults[i][j]['mask'] =object_relationship_name_category
                    wordSegmentationResults[i][j]['tag']=object_relationship_name_tag
        updateTagCategoryList=[]
        for key in colorDict.keys():
            updateTagCategoryList.append({'tag':colorDict[key],'category':key})
        #print(object_from_name_category,object_to_name_category,object_relationship_name_category)
        #更新原来的分词结果wordSegmentationResults
        #更新数据库中relationship_extract_result
        #更新tagCategory
        news_col.update_one({'_id': mongodb_id}, {"$set": {'relationship_extract_result': relationship_extract_result,'wordSegmentationResults':wordSegmentationResults,'tagCategory':updateTagCategoryList}})

        #neo4j里创建一条关系就是  对象一 ----属性名---》 对象二
        #判断这2个节点是否存在
        #存在就建立关系
        #不存在先建立节点 然后建立关系
        fromNodeIfExist=Neo4j().judgeNodeIfExistInNeo4j(object_from_name_category,Neo4j().dictToQuesDict({'名字':object_from_name}))
        #fromNodeIfExist = Neo4j().judgeNodeIfExistInNeo4j('电影_1_1',Neo4j().dictToQuesDict({'名字': '你的名字。'}))
        if(fromNodeIfExist == False):
            #Neo4j().create_node_mjy_edition('电影_1_1',Neo4j().dictToQuesDict({'名字': '你的名字。'}))
            Neo4j().create_node_mjy_edition(object_from_name_category, {'名字': object_from_name})
        #print(13)
        toNodeIfExist = Neo4j().judgeNodeIfExistInNeo4j(object_to_name_category,Neo4j().dictToQuesDict({'名字': object_to_name}))
        #print('结果',toNodeIfExist)
        #MATCH(a: 事件_1_1),(b:字符串_1_1) WHERE a.名字 ='国家' and b.名字='片源'  CREATE(a) - [r:组织] -> (b);
        if(toNodeIfExist == False):
            #Neo4j().create_node_mjy_edition('电影_1_1',{'名字': '我的名字。'})
            Neo4j().create_node_mjy_edition(object_to_name_category,{'名字': object_to_name})
        Neo4j().createRelationship(object_from_name_category,
                                   object_to_name_category,
                                   object_relationship_name,
                                   propertyOne={'名字': object_from_name},
                                   propertyTwo={'名字': object_to_name})
        #print(14)
        #Neo4j().createRelationship('电影_1_1',
        #                           '电影_1_1',
        #                           object_relationship_name,
        #                           propertyOne={'名字': '你的名字。'},
        #                           propertyTwo={'名字': '我的名字。'})
        #Neo4j().createRelationship(labelOne, labelTwo, relationShipName, propertyOne=None, propertyTwo=None,propertyRelationship=None):
        #print(15)
        ret_l={'relationship_extract_result': relationship_extract_result,'wordSegmentationResults':wordSegmentationResults,'tagCategory':updateTagCategoryList}
        return self.success(ret_l)

    def deleteRelationship(self, request):
        """
        功能 删除关系 删除mongodb里面关系抽取结果下标对应index的关系，更新分词之后的颜色
        在neo4j里面删除关系
        :param request:
        _id          数据类型int  mongodb数据库中的抽取结果id
        index        数据类型str  要删除的关系的下标
        object_from  数据类型str  关系主体
        object_event 数据类型str  关系名字
        object_to    数据类型str  关系客体
        :return:

        """
        _id = str(request.POST['id'])
        index = int(request.POST['index'])
        object_from = request.POST['object_from']
        object_event = request.POST['object_event']
        object_to = request.POST['object_to']

        # only for debug start
        # _id = "5ef6e30c7765440d7a6c2616"
        # index = 0
        # object_from="国家"
        # object_to="片源"
        # object_event = "组织"
        # request.session['repo_id']=1
        # request.session['user_id']=1
        # only for debug end
        repoId = request.session['repo_id']
        createId = request.session['user_id']
        mongodb_id = ObjectId(_id)
        try:
            news_col = Mongodb(db='knowledge', collection='text').get_collection()
        except Exception:
            return self.error("mongodb没有数据库或者表")
        document = news_col.find_one({'_id': mongodb_id})

        relationship_extract_result = document['relationship_extract_result']
        event_extract_result = document['event_extract_result']
        tagCategory = document['tagCategory']
        wordSegmentationResults = document['wordSegmentationResults']
        # print(5656)
        # 修改查询结果
        # 假如其他关系/事件还有用到这个词的的话 那么词性不用修改
        # 假如是最后一个用到这个词的 修改词性 修改这个颜色 修改tagCategory 关系抽取结果
        wordDict = {}
        # 先删除
        # 删除了以后加入关系会导致两个主演都被标出来了
        relationship_extract_resultLen = len(relationship_extract_result)
        # 写到这里了
        for i in range(relationship_extract_resultLen):
            print(relationship_extract_result[i]['object_from_name'])
            wordDict = some_data_deal_func().wordInsertToDict(relationship_extract_result[i]['object_from_name_index'],
                                                              wordDict)
            wordDict = some_data_deal_func().wordInsertToDict(relationship_extract_result[i]['object_to_name_index'],
                                                              wordDict)
            wordDict = some_data_deal_func().wordInsertToDict(
                relationship_extract_result[i]['object_relationship_name_index'], wordDict)
        # print(5656)
        event_extract_resultLen = len(event_extract_result)
        for i in range(event_extract_resultLen):
            # wordDict = some_data_deal_func().wordInsertToDict(event_extract_result[i]['time'],wordDict)
            # wordDict = some_data_deal_func().wordInsertToDict(event_extract_result[i]['location'], wordDict)
            wordDict = some_data_deal_func().wordInsertToDict(event_extract_result[i]['eventSubjectIndex'], wordDict)
            wordDict = some_data_deal_func().wordInsertToDict(event_extract_result[i]['triggerWordIndex'], wordDict)
            if ('eventObject' in event_extract_result[i].keys()):
                wordDict = some_data_deal_func().wordInsertToDict(event_extract_result[i]['eventObjectIndex'], wordDict)
        # print(index,relationship_extract_resultLen)
        if (index < relationship_extract_resultLen):
            # print(55555)
            tmpDict = {}
            ansRelationshipExtractResult = []
            for i in range(relationship_extract_resultLen):
                if (i == index):
                    tmpDict = relationship_extract_result[i]
                    continue
                else:
                    ansRelationshipExtractResult.append(relationship_extract_result[i])
            # object_from_name
            num = wordDict[tmpDict['object_from_name_index']]
            object_from_nameindex = tmpDict['object_from_name_index']
            wordSegmentationResultsLen = len(wordSegmentationResults)

            if (num == 1):
                # 更新tag
                # 更新wordDict
                wordSegmentationResults = some_data_deal_func().updatewordSegmentationResultsTag(object_from_nameindex,
                                                                                                 wordSegmentationResults,
                                                                                                 wordSegmentationResultsLen)
                del wordDict[tmpDict['object_from_name_index']]
            elif (num > 1):
                wordDict[tmpDict['object_from_name_index']] -= 1
            # object_to_name
            num = wordDict[tmpDict['object_to_name_index']]
            object_to_nameindex = tmpDict['object_to_name_index']
            if (num == 1):
                # 更新tag
                # 更新wordDict
                wordSegmentationResults = some_data_deal_func().updatewordSegmentationResultsTag(object_to_nameindex,
                                                                                                 wordSegmentationResults,
                                                                                                 wordSegmentationResultsLen)
                del wordDict[tmpDict['object_to_name_index']]
            elif (num > 1):
                wordDict[tmpDict['object_to_name_index']] -= 1
            # object_relationship_name
            num = wordDict[tmpDict['object_relationship_name_index']]
            object_relationship_nameindex = tmpDict['object_relationship_name_index']
            if (num == 1):
                # 更新tag
                # 更新wordDict
                wordSegmentationResults = some_data_deal_func().updatewordSegmentationResultsTag(
                    object_relationship_nameindex,
                    wordSegmentationResults,
                    wordSegmentationResultsLen)
                del wordDict[tmpDict['object_relationship_name_index']]
            elif num > 1:
                wordDict[tmpDict['object_relationship_name_index']] -= 1
            # 所有的东西完成以后进行颜色的更新
            # 封装一个颜色的结果
            tagCategory = some_data_deal_func().countColor(ansRelationshipExtractResult, event_extract_result)

            print(tagCategory)
            # print(wordSegmentationResults)
            news_col.update_one({'_id': mongodb_id}, {"$set": {'wordSegmentationResults': wordSegmentationResults,
                                                               'relationship_extract_result': ansRelationshipExtractResult,
                                                               'tagCategory': tagCategory}})
            # 删除neo4j关系
            # category  atrribute category  attribute relationshipname
            # Neo4j().deleteRealtionship(tmpDict['object_from_category'],
            #                    {'名字':tmpDict['object_from_name']},
            #                    tmpDict['object_to_category'],
            #                    {'名字':tmpDict['object_to_name']},
            #                    tmpDict['object_relationship_name'])
            # Neo4j().deleteRealtionship(tmpDict['object_from_category'],
            #                            {'名字': '孟佳营'},
            #                            tmpDict['object_to_category'],
            #                            {'名字': '我的名字。'},
            #                            tmpDict['object_relationship_name'])
        else:
            return self.error("下标超过范围")

        return self.success({'wordSegmentationResults': wordSegmentationResults,'relationship_extract_result':ansRelationshipExtractResult,'tagCategory':tagCategory})

    def addEvent(self,request):
        """
        功能 添加事件 在mongodb中event_extract_result中添加事件 修改分词结果 修改颜色
        在neo4j里面建立对应关系
        :param request:
        _id                          数据类型str  mongodb里面文件对应id
        event_time_key_word_index    数据类型int  时间下标
        event_place_key_word_index   数据类型int  地点下标
        event_subject_key_word_index 数据类型int  事件主体下标
        event_trigger_word_index     数据类型int  触发词下标
        event_object_key_word_index  数据类型int  事件客体下标没有就输入-1
        actual_event_time            数据类型str  真实的时间
        select_event_type_index      数据类型int  事件类目
        :return:
        """
        #整体思路 下标对应数据加入到事件抽取结果中
        #修改颜色
        #修改分词结果
        #更新到mongodb
        #更新neo4j
        #这些都是下标
        _id = request.POST['id']
        event_time_key_word_index = int(request.POST['event_time_key_word'])
        event_place_key_word_index = int(request.POST['event_place_key_word'])
        event_subject_key_word_index = int(request.POST['event_subject_key_word'])
        event_trigger_word_index = int(request.POST['event_trigger_word'])
        event_object_key_word_index = int(request.POST['event_object_key_word'])
        actual_event_time = str(request.POST['actual_event_time'])
        select_event_type_index = int(request.POST['select_event_type'])

        # _id = "5ef6e30c7765440d7a6c2616"
        # event_time_key_word_index = -1
        # event_place_key_word_index = 11
        # event_subject_key_word_index = 12
        # event_trigger_word_index = 13
        # event_object_key_word_index = 14
        # actual_event_time = "2020"
        # #这个是事件类目category
        # select_event_type_index =  8
        mongodb_id = ObjectId(_id)

        try:
            news_col =  Mongodb(db="knowledge",collection="text").get_collection()
        except:
            return self.error("数据库不存在")
        ret = news_col.find_one({'_id':mongodb_id})
        wordSegmentationResults = ret['wordSegmentationResults']
        tagCategory=ret['tagCategory']
        event_extract_result = ret['event_extract_result']
        #维护一个颜色的最大值
        maxColor=0
        colorDict = {}
        tagCategoryLen = len(tagCategory)
        for i in range(tagCategoryLen):
            colorDict[tagCategory[i]['category']]=tagCategory[i]['tag']
            maxColor=max(maxColor,tagCategory[i]['tag'])


        #这里稍微有点问题
        #触发词  触发词类目
        #t_trigger_word=TTriggerWord.objects.get(id = select_event_type_index)

        t_event_rule = TEventRule.objects.get(category_id=select_event_type_index)
        event_subject_id = t_event_rule.event_subject_id
        event_object_id = t_event_rule.event_object_id
        category_id = t_event_rule.category_id

        retCategory = TCategory.objects.get(id = category_id)
        eventCategory = retCategory.category_name
        trigger_word_category = retCategory.category_name
        retCategory = TCategory.objects.get(id =event_subject_id )
        event_subject_category = retCategory.category_name

        event_object_category=""
        if(event_object_id != -1):
            retCategory = TCategory.objects.get(id = event_object_id)
            event_object_category = retCategory.category_name

        #假如颜色已经存在那么直接拿过来用
        #假如类目不存在那么添加数据 更新表内容
        maxColor,event_time_tag,colorDict=some_data_deal_func().updateColorDict(maxColor,"time",colorDict)
        maxColor, event_place_tag, colorDict = some_data_deal_func().updateColorDict(maxColor, "location",colorDict)
        maxColor, event_subject_tag, colorDict = some_data_deal_func().updateColorDict(maxColor, event_subject_category,colorDict)
        maxColor, event_trigger_tag, colorDict = some_data_deal_func().updateColorDict(maxColor, trigger_word_category,colorDict)

        event_object_tag=0
        if (event_object_id != -1):
            maxColor, event_object_tag, colorDict = some_data_deal_func().updateColorDict(maxColor, event_object_category,colorDict)
        timeName=""
        locationName = ""
        subjectName =""
        triggerWordName =""
        objectName =""
        wordSegmentationResultsLen = len(wordSegmentationResults)
        for i in range(wordSegmentationResultsLen):
            tmpList = wordSegmentationResults[i]
            tmpListLen = len(tmpList)
            for j in range(tmpListLen):
                if(tmpList[j]['num'] == event_time_key_word_index):
                    timeName = wordSegmentationResults[i][j]['word']
                    wordSegmentationResults[i][j]['mask']="time"
                    wordSegmentationResults[i][j]['tag']=event_time_tag
                elif(tmpList[j]['num'] == event_place_key_word_index):
                    locationName=wordSegmentationResults[i][j]['word']
                    wordSegmentationResults[i][j]['mask'] = "location"
                    wordSegmentationResults[i][j]['tag'] = event_place_tag
                elif(tmpList[j]['num'] == event_subject_key_word_index):
                    subjectName = wordSegmentationResults[i][j]['word']
                    wordSegmentationResults[i][j]['mask'] = event_subject_category
                    wordSegmentationResults[i][j]['tag'] = event_subject_tag
                elif(tmpList[j]['num'] == event_trigger_word_index):
                    triggerWordName = wordSegmentationResults[i][j]['word']
                    wordSegmentationResults[i][j]['mask'] = trigger_word_category
                    wordSegmentationResults[i][j]['tag'] = event_trigger_tag

                if (event_object_id != -1 and tmpList[j]['num'] == event_object_key_word_index):
                    objectName = wordSegmentationResults[i][j]['word']
                    wordSegmentationResults[i][j]['mask'] = event_object_category
                    wordSegmentationResults[i][j]['tag'] = event_object_tag

        #time
        #location
        #eventSubject
        #eventSubjectLabel
        #triggerLabel
        #triggerWord
        #eventObject
        #eventObjectLabel

        #eventSubjectIndex
        #triggerWordIndex
        #eventObjectIndex
        #这里triggerLabel修一下
        if(event_object_id != -1 ):
            event_extract_result.append({'actual_event_time':actual_event_time,
                                        'time':timeName,
                                        'timeIndex':event_time_key_word_index,
                                        'location':locationName,
                                        'locationIndex':event_place_key_word_index,
                                        'eventName':subjectName+triggerWordName+objectName,
                                        'eventSubject':subjectName,
                                        'eventSubjectLabel':self.get_category_name(request,event_subject_category),
                                        'eventSubjectIndex': event_subject_key_word_index,
                                        'triggerWord':triggerWordName,
                                        'triggerLabel':self.get_category_name(request,trigger_word_category),
                                        'triggerWordIndex': event_trigger_word_index,
                                        'eventObject': objectName,
                                        'eventObjectLabel':self.get_category_name(request,event_object_category),
                                        'eventObjectIndex':event_object_key_word_index})
        else:
            event_extract_result.append({'actual_event_time':actual_event_time,
                                        'time':timeName,
                                        'timeIndex':event_time_key_word_index,
                                        'location':locationName,
                                        'locationIndex':event_place_key_word_index,
                                        'eventName': subjectName + triggerWordName,
                                        'eventSubject':subjectName,
                                        'eventSubjectLabel':self.get_category_name(request,event_subject_category),
                                        'eventSubjectIndex': event_subject_key_word_index,
                                        'triggerWord':triggerWordName,
                                        'triggerLabel':self.get_category_name(request,trigger_word_category),
                                        'triggerWordIndex':event_trigger_word_index})
        #把这个东西更新回去就好了wordSegmentationResults event_extract_result tagCategory

        updateTagCategoryList=[]
        for key in colorDict.keys():
            updateTagCategoryList.append({'tag':colorDict[key],'category':key})
        #print(object_from_name_category,object_to_name_category,object_relationship_name_category)
        #更新原来的分词结果wordSegmentationResults
        #更新数据库中event_extract_result
        #更新tagCategory
        news_col.update_one({'_id': mongodb_id}, {"$set": {'event_extract_result': event_extract_result,'wordSegmentationResults':wordSegmentationResults,'tagCategory':updateTagCategoryList}})
        #return self.success(123)
        #判断节点是否存在不存在就建立节点
        #判断事件主题是否存在
        fromNodeIfExist=Neo4j().judgeNodeIfExistInNeo4j(self.get_category_name(request,event_subject_category),Neo4j().dictToQuesDict({'名字':subjectName}))
        #fromNodeIfExist = Neo4j().judgeNodeIfExistInNeo4j('电影_1_1',Neo4j().dictToQuesDict({'名字': '你的名字。'}))
        if(fromNodeIfExist == False):
            #Neo4j().create_node_mjy_edition('电影_1_1',Neo4j().dictToQuesDict({'名字': '你的名字。'}))
            Neo4j().create_node_mjy_edition(self.get_category_name(request,event_subject_category), {'名字': subjectName})
        #名字  时间  地点
        #创建事件节点
        if(event_object_id != -1 ):
            eventName=subjectName + triggerWordName + objectName
        else:
            eventName=subjectName + triggerWordName

        eventNodeIfExist=Neo4j().judgeNodeIfExistInNeo4j(self.get_category_name(request,eventCategory),Neo4j().dictToQuesDict({'时间':actual_event_time,'地点':locationName,'名字': eventName}))
        #fromNodeIfExist = Neo4j().judgeNodeIfExistInNeo4j('电影_1_1',Neo4j().dictToQuesDict({'名字': '你的名字。'}))
        if(eventNodeIfExist == False):
            #Neo4j().create_node_mjy_edition('电影_1_1',Neo4j().dictToQuesDict({'名字': '你的名字。'}))
            Neo4j().create_node_mjy_edition(self.get_category_name(request,eventCategory), {'时间':actual_event_time,'地点':locationName,'名字': eventName})

        #建立关系
        Neo4j().createRelationship(self.get_category_name(request,event_subject_category),
                                   self.get_category_name(request,eventCategory),
                                   "主谓关系",
                                   propertyOne={'名字': subjectName},
                                   propertyTwo={'时间':actual_event_time,'地点':locationName,'名字': eventName})
        if(event_object_id != -1 ):
            toNodeIfExist = Neo4j().judgeNodeIfExistInNeo4j(self.get_category_name(request,event_object_category),Neo4j().dictToQuesDict({'名字': objectName}))
            # fromNodeIfExist = Neo4j().judgeNodeIfExistInNeo4j('电影_1_1',Neo4j().dictToQuesDict({'名字': '你的名字。'}))
            if (toNodeIfExist == False):
                # Neo4j().create_node_mjy_edition('电影_1_1',Neo4j().dictToQuesDict({'名字': '你的名字。'}))
                Neo4j().create_node_mjy_edition(self.get_category_name(request,event_object_category), {'名字': objectName})
            Neo4j().createRelationship(self.get_category_name(request, eventCategory),
                                       self.get_category_name(request, event_object_category),
                                       "动宾关系",
                                       propertyOne={'时间': actual_event_time, '地点': locationName, '名字': eventName},
                                       propertyTwo={'名字': objectName})
        #建立关系
        #这个函数要把时间和位置的下标也记录下来
        return self.success("添加成功")

    def deleteEvent(self, request):
        """
        功能: 删除事件删除mongodb里面事件抽取结果下标对应index的关系，更新分词之后的颜色
        在neo4j里面删除事件
        :param request:
        _id              数据类型int  mongodb数据库中的抽取结果id
        index            数据类型str  要删除的事件的下标
        time             数据类型str  时间
        location         数据类型str  地点
        event_subject    数据类型str  事件主题
        event_name       数据类型str  事件名字
        event_object     数据类型str  数事件客体
        :return:
        """
        _id = request.POST['id']
        index = int(request.POST['index'])
        time = request.POST['time']
        location = request.POST['location']
        event_subject = request.POST['event_subject']
        event_name = request.POST['event_name']
        event_object = request.POST['event_object']

        # _id="5ef6e30c7765440d7a6c2616"
        # index = 0
        # time = "2020"
        # location = "123456"
        # event_subject =  "123"
        # event_name = "123"
        # event_object = "123"
        # request.session['repo_id'] =1
        # request.session['user_id'] =1

        repoId = request.session['repo_id']
        createId = request.session['user_id']
        mongodb_id = ObjectId(_id)
        try:
            news_col = Mongodb(db='knowledge', collection='text').get_collection()
        except Exception:
            return self.error("mongodb没有数据库或者表")
        document = news_col.find_one({'_id': mongodb_id})

        relationship_extract_result = document['relationship_extract_result']
        event_extract_result = document['event_extract_result']
        tagCategory = document['tagCategory']
        wordSegmentationResults = document['wordSegmentationResults']
        # print(5656)
        # 修改查询结果
        # 假如其他关系/事件还有用到这个词的的话 那么词性不用修改
        # 假如是最后一个用到这个词的 修改词性 修改这个颜色 修改tagCategory 关系抽取结果
        wordDict = {}
        # 先删除
        # 删除了以后加入关系会导致两个主演都被标出来了
        relationship_extract_resultLen = len(relationship_extract_result)
        # 写到这里了
        for i in range(relationship_extract_resultLen):
            # print(relationship_extract_result[i]['object_from_name'])
            wordDict = some_data_deal_func().wordInsertToDict(relationship_extract_result[i]['object_from_name_index'],
                                                              wordDict)
            wordDict = some_data_deal_func().wordInsertToDict(relationship_extract_result[i]['object_to_name_index'],
                                                              wordDict)
            wordDict = some_data_deal_func().wordInsertToDict(
                relationship_extract_result[i]['object_relationship_name_index'], wordDict)
        # print(5656)
        event_extract_resultLen = len(event_extract_result)
        for i in range(event_extract_resultLen):
            wordDict = some_data_deal_func().wordInsertToDict(event_extract_result[i]['timeIndex'], wordDict)
            wordDict = some_data_deal_func().wordInsertToDict(event_extract_result[i]['locationIndex'], wordDict)
            wordDict = some_data_deal_func().wordInsertToDict(event_extract_result[i]['eventSubjectIndex'], wordDict)
            wordDict = some_data_deal_func().wordInsertToDict(event_extract_result[i]['triggerWordIndex'], wordDict)
            if ('eventObject' in event_extract_result[i].keys()):
                wordDict = some_data_deal_func().wordInsertToDict(event_extract_result[i]['eventObjectIndex'], wordDict)
        ansEventExtractResult = []

        if (index < event_extract_resultLen):
            # print(55555)
            tmpDict = {}
            ansEventExtractResult = []
            for i in range(event_extract_resultLen):
                if (i == index):
                    tmpDict = event_extract_result[i]
                    continue
                else:
                    ansEventExtractResult.append(event_extract_result[i])
            # time
            num = wordDict[tmpDict['timeIndex']]
            timeIndex = tmpDict['timeIndex']
            wordSegmentationResultsLen = len(wordSegmentationResults)

            if (num == 1):
                # 更新tag
                # 更新wordDict
                wordSegmentationResults = some_data_deal_func().updatewordSegmentationResultsTag(timeIndex,
                                                                                                 wordSegmentationResults,
                                                                                                 wordSegmentationResultsLen)
                del wordDict[tmpDict['timeIndex']]
            elif (num > 1):
                wordDict[tmpDict['timeIndex']] -= 1

            # location
            num = wordDict[tmpDict['locationIndex']]
            locationIndex = tmpDict['locationIndex']
            wordSegmentationResultsLen = len(wordSegmentationResults)

            if (num == 1):
                # 更新tag
                # 更新wordDict
                wordSegmentationResults = some_data_deal_func().updatewordSegmentationResultsTag(locationIndex,
                                                                                                 wordSegmentationResults,
                                                                                                 wordSegmentationResultsLen)
                del wordDict[tmpDict['locationIndex']]
            elif (num > 1):
                wordDict[tmpDict['locationIndex']] -= 1

            # eventSubject
            num = wordDict[tmpDict['eventSubjectIndex']]
            eventSubjectIndex = tmpDict['eventSubjectIndex']
            wordSegmentationResultsLen = len(wordSegmentationResults)

            if (num == 1):
                # 更新tag
                # 更新wordDict
                wordSegmentationResults = some_data_deal_func().updatewordSegmentationResultsTag(eventSubjectIndex,
                                                                                                 wordSegmentationResults,
                                                                                                 wordSegmentationResultsLen)
                del wordDict[tmpDict['eventSubjectIndex']]
            elif (num > 1):
                wordDict[tmpDict['eventSubjectIndex']] -= 1

            # triggerWord
            num = wordDict[tmpDict['triggerWordIndex']]
            triggerWordIndex = tmpDict['triggerWordIndex']
            wordSegmentationResultsLen = len(wordSegmentationResults)

            if (num == 1):
                # 更新tag
                # 更新wordDict
                wordSegmentationResults = some_data_deal_func().updatewordSegmentationResultsTag(triggerWordIndex,
                                                                                                 wordSegmentationResults,
                                                                                                 wordSegmentationResultsLen)
                del wordDict[tmpDict['triggerWordIndex']]
            elif (num > 1):
                wordDict[tmpDict['triggerWordIndex']] -= 1
            # eventObject

            # 这里要判断一下这个东西是否存在
            rule = 2
            if ('eventObjectIndex' in tmpDict.keys()):
                rule = 1
                num = wordDict[tmpDict['eventObjectIndex']]
                eventObjectIndex = tmpDict['eventObjectIndex']
                wordSegmentationResultsLen = len(wordSegmentationResults)

                if (num == 1):
                    # 更新tag
                    # 更新wordDict
                    wordSegmentationResults = some_data_deal_func().updatewordSegmentationResultsTag(eventObjectIndex,
                                                                                                     wordSegmentationResults,
                                                                                                     wordSegmentationResultsLen)
                    del wordDict[tmpDict['eventObjectIndex']]
                elif (num > 1):
                    wordDict[tmpDict['eventObjectIndex']] -= 1

            # 所有的东西完成以后进行颜色的更新
            # 封装一个颜色的结果
            tagCategory = some_data_deal_func().countColor(relationship_extract_result, ansEventExtractResult)

            print(tagCategory)
            # print(wordSegmentationResults)
            news_col.update_one({'_id': mongodb_id}, {"$set": {'wordSegmentationResults': wordSegmentationResults,
                                                               'event_extract_result': ansEventExtractResult,
                                                               'tagCategory': tagCategory}})
            # 删除neo4j关系
            # category  atrribute category  attribute relationshipname
            #
            eventName = ""
            if (rule == 1):
                # 三元
                eventName += tmpDict['eventSubject'] + tmpDict['triggerWord'] + tmpDict['eventObject']
            else:
                # 二元
                eventName += tmpDict['eventSubject'] + tmpDict['triggerWord']

            # 删除有点问题
            Neo4j().deleteRealtionship(tmpDict['eventSubjectLabel'],
                                       {'名字': tmpDict['eventSubject']},
                                       tmpDict['triggerLabel'],
                                       {'时间': tmpDict['actual_event_time'], '地点': tmpDict['location'], '名字': eventName},
                                       "主谓关系")
            if (rule == 1):
                Neo4j().deleteRealtionship(tmpDict['triggerLabel'],
                                           {'时间': tmpDict['actual_event_time'], '地点': tmpDict['location'],
                                            '名字': eventName},
                                           tmpDict['eventObjectLabel'],
                                           {'名字': tmpDict['eventObject']},
                                           "动宾关系")
        else:
            return self.error("下标超过范围")
        return self.success({'wordSegmentationResults': wordSegmentationResults,
                                                               'event_extract_result': ansEventExtractResult,
                                                               'tagCategory': tagCategory})
