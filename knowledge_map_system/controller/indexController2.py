from controller.baseController import BaseController
from model.models import *
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.shortcuts import HttpResponseRedirect
from django.utils import timezone
from django.forms.models import model_to_dict
# from django.views.decorators.csrf import csrf_exempt
from model.neo4j import Neo4j
import json
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
        request.session['repo_id'] = repo_id
        return self.success("")

    def knowledge_definition(self, request):
        """
        属性信息中落掉了属性别名，需要去别名表里去
        :param request:
        :return:
        """
        repo_id = request.session['repo_id']
        print(repo_id)
        # repo_id = 1
        result = TCategory.objects.filter(repo_id=repo_id)

        num = 0
        # 获得事务的id
        work_id = 0
        tmp_description = ''
        tmp_id = 0

        object_category = TCategory.objects.get(id=1)
        # for category in result:
        ret_result = model_to_dict(object_category)
            # if ret_result['category_name'] == '事务':
        work_id = ret_result['id']
        tmp_description = ret_result['category_description']
        tmp_id = ret_result['id']
        num = len(result)
            # num += 1
        now = 1
        print(num)
        # print(work_id)

        multilist = [[0] * (num + 1) for row in range(num + 1)]
        multilist_id = [[0] * (num + 1) for row in range(num + 1)]
        cnt_list = [0 for i in range(num + 1)]

        ind = 1
        for category in result:
            ret_result = model_to_dict(category)
            if int(ret_result['category_level']) == int(3):
                ind2 = 1
                for category1 in result:
                    ret_result1 = model_to_dict(category1)
                    if int(ret_result1['id']) == int(ret_result['father_category_id']):
                        multilist[ind2][cnt_list[ind2]] = ret_result['category_name']
                        multilist_id[ind2][cnt_list[ind2]] = ret_result['id']
                        cnt_list[ind2] += 1
                    ind2 += 1
            ind += 1
        ind = 1
        test = {}
        tmp_list_2 = []
        tmp_list_1 = []
        for out_category in result:
            # 有第三层的
            ret_result = model_to_dict(out_category)
            if cnt_list[ind] > 0:
                dic = {}
                now_list = []
                for j in range(0, cnt_list[ind]):
                    tmp = {}
                    tmp['id'] = multilist_id[ind][j]
                    tmp['category_name'] = multilist[ind][j]
                    now_list.append(tmp)
                cnt = 1
                tmp_name1 = ""
                tmp_id1 = ""
                for category in result:
                    if cnt == ind:
                        cate_map = model_to_dict(category)
                        tmp_name1 = cate_map['category_name']
                        tmp_id1 = cate_map['id']
                    cnt += 1
                dic['id'] = tmp_id1
                dic['category_name'] = tmp_name1
                dic['level3_child'] = now_list
                tmp_list_2.append(dic)
            elif int(ret_result['category_level']) == 2:
                dic = {'id': ret_result['id'], 'category_name': ret_result['category_name'], 'level3_child': []}
                tmp_list_2.append(dic)
            ind += 1

        find_attribute = TAttribute.objects.filter(category_id=work_id)
        # 这个属性
        tmp_list_attribute = []
        for attribute in find_attribute:
            ret_result = model_to_dict(attribute)
            tmp_list_attribute.append(ret_result)

        test['id'] = tmp_id
        test['category'] = {'category_description': tmp_description, 'attribute': tmp_list_attribute}
        test['level2_child'] = tmp_list_2
        print(test)
        return render(request, 'index/knowledge_definition.html', context=test)

    # 返回他和他的所有的祖先的category还有他们的attribute
    def category_query(self, request):
        """
        属性别名内容缺少
        :param request:
        :return:
        """
        _category_id = request.POST['category_id']
        # _category_id = 5
        ret_l = {}

        _category_now = TCategory.objects.get(id=_category_id)
        _category_now_dict = model_to_dict(_category_now)
        # _category_now_dict  要增加attribute
        _category_now_attribute = []

        tmp_res = TAttribute.objects.filter(category_id=_category_id)
        for val in tmp_res:
            tem_res_dict = model_to_dict(val)
            attribute_id = tem_res_dict['id']
            attribute_alias_val = TAttrbuteAlias.objects.filter(attribute_id=attribute_id)
            num = 0
            attribute_alias= ''
            for attribute_val  in  attribute_alias_val:
                attribute_val_dict = model_to_dict(attribute_val)
                if(num!=0):
                    attribute_alias+=','
                attribute_alias += attribute_val_dict['attribute_alias']
                num+=1
            tem_res_dict['attribute_alias']=attribute_alias
            _category_now_attribute.append(tem_res_dict)

        _category_now_dict['attribute'] = _category_now_attribute

        # print(_category_now_dict)
        ret_l['category'] = _category_now_dict

        father_list = []
        _catgegory_father_id = _category_now.father_category_id

        if(str(-1) == _catgegory_father_id ):
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
            tem_res_dict['attribute_alias'] = attribute_alias
            _category_father_attribute.append(tem_res_dict)
        _category_father_dict['attribute'] = _category_father_attribute

        father_list.append(_category_father_dict)

        if str(-1) !=_catgegory_father_id   and str(-1) !=_category_father_dict['father_category_id'] :
            _category_father_father_id = _category_father_dict['father_category_id']
            _category_father_father = TCategory.objects.get(id=_category_father_father_id)
            _category_father_father_dict = model_to_dict(_category_father_father)
            tmp_res = TAttribute.objects.filter(category_id=_category_father_father_id)
            _category_father_father_attribute = []

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
                tem_res_dict['attribute_alias'] = attribute_alias
                _category_father_father_attribute.append(tem_res_dict)

            _category_father_father_dict['attribute'] = _category_father_father_attribute
            father_list.append(_category_father_father_dict)

        ret_l['father_category'] = father_list

        return self.success(ret_l)

    # 添加新的类目
    def add_category(self, request):
        _category_name = request.POST['category_name']
        _category_describe = request.POST['category_describe']
        _father_category_id = request.POST['inherit_category']

        _repo_id = request.session['repo_id']
        _create_id = request.session['user_id']

        obj = TCategory.objects.get(id=_father_category_id)
        now_level = obj.category_level + 1
        dt = timezone.now()
        TCategory.objects.create(category_name=_category_name,father_category_id=_father_category_id,is_temporary=0,
                                 category_description=_category_describe,repo_id=_repo_id,create_id=_create_id,create_time=dt,category_level=now_level)
        return self.success("添加成功！")

    # 添加属性
    def add_attribute(self, request):
        _attribute_name = request.POST['attribute_name']
        _attribute_datatype = request.POST['attribute_type']
        _is_single_value = request.POST['attribute_is_single_value']
        _attribute_description = request.POST['attribute_describe']
        _category_id = request.POST['category_id']
        # 属性别名要用逗号分开
        _attribute_alias = request.POST['attribute_alias']
        _create_id = request.session['user_id']

        dt = timezone.now()
        attribute_obj = TAttribute.objects.create(attribute_name=_attribute_name, attribute_datatype=_attribute_datatype,
                                  is_single_value=_is_single_value, attribute_description=_attribute_description,
                                  category_id=_category_id, create_time=dt)
        li = _attribute_alias.split(',')
        _attribute_id = attribute_obj.id
        for val in li:
            TAttrbuteAlias.objects.create(attribute_id=_attribute_id, attribute_alias=val, create_id=_create_id,
                                          create_time=dt)
        return self.success("添加成功！")

    # 修改属性
    def update_attribute(self, request):
        _attribute_id = request.POST['attribute_id']
        _attribute_name = request.POST['attribute_name']
        _attribute_alias = request.POST['attribute_alias']
        _attribute_datatype = request.POST['attribute_type']
        _is_single_value = request.POST['attribute_is_single_value']
        _attribute_description = request.POST['attribute_describe']
        _create_id = request.session['user_id']

        _attribute = TAttribute.objects.get(id=_attribute_id)

        _attribute.attribute_name = _attribute_name
        _attribute.attribute_datatype = _attribute_datatype
        _attribute.is_single_value = _is_single_value
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
        # _attribute_id = 28
        _attribute_alias_delete = TAttrbuteAlias.objects.filter(attribute_id=_attribute_id)
        _attribute_alias_delete.delete()
        _attribute_delete = TAttribute.objects.filter(id=_attribute_id)
        _attribute_delete.delete()
        return self.success("删除成功！")

    def knowledge_acquire(self, request):
        ret_l = {}
        repo_id = request.session['repo_id']
        # repo_id  = 1
        ret_log = TDataAcquisitionLog.objects.filter(repo_id=repo_id)
        repo_list = []
        for val in ret_log:
            ret_log_list = model_to_dict(val)
            ret_log_list["create_time"] = str(ret_log_list["create_time"])[:19]
            repo_list.append(ret_log_list)
        ret_l['ret_log'] = repo_list
        return render(request, 'index/knowledge_acquire.html', context=ret_l)

    # 把文件从前端传递到后台
    # @csrf_exempt
    def upload_file(self, request):
        if request.method == "POST":  # 请求方法为POST时，进行处理
            myFile = request.FILES.get("file", None)  # 获取上传的文件，如果没有文件，则默认为None
            if not myFile:
                return self.error("没有文件!")
            destination = open(os.path.join("D:\\upload", myFile.name), 'wb+')  # 打开特定的文件进行二进制的写操作
            for chunk in myFile.chunks():  # 分块写入文件
                destination.write(chunk)
            destination.close()

            one_record = TDataAcquisitionLog()
            one_record.create_time = timezone.now()
            one_record.repo_id = request.session['repo_id']
            one_record.create_id = request.session['user_id']
            one_record.data_source = myFile.name
            one_record.data_access = "文件"
            one_record.save()
            return self.success("上传成功！")

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

    def build_map(self, request):
        return render(request, 'index/build_map.html')

    def map_rule(self, request):
        # repo_id = request.POST['repo_id']
        # create_id = request.POST['create_id']
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
        att_list = []
        cate_id = cate_list[0]["id"]
        # for val in cate_list:
        #     cate_id = val['id']
        res = TAttribute.objects.filter(category_id=cate_id)
        for att in res:
            att_dict = model_to_dict(att)
            now_dict = {}
            now_dict['id'] = att_dict['id']
            now_dict['attribute_name'] = att_dict['attribute_name']
            att_list.append(now_dict)
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
        return render(request, "index/map_rule.html", context=ret_l)

    # 根据类目ID获取映射规则
    def get_map_rule(self, request):
        create_id = request.session["user_id"]
        category_id = request.POST["select_category_id"]
        res = TAttribute.objects.filter(category_id=category_id)
        ret_l = {}
        att_list = []
        for att in res:
            att_dict = model_to_dict(att)
            now_dict = {}
            now_dict['id'] = att_dict['id']
            now_dict['attribute_name'] = att_dict['attribute_name']
            att_list.append(now_dict)
        ret_l['attribute'] = att_list

        att_map_list = []
        # for val in cate_list:
        #     cate_id = val['id']
        res = TMappingRule.objects.filter(category_id=category_id, create_id=create_id)
        for att in res:
            att_dict = model_to_dict(att)
            att_dict['create_time'] = str(att_dict['create_time'])
            att_map_list.append(att_dict)
        ret_l['attribute_mapping'] = att_map_list
        return self.success(ret_l)

        # 根据id更新属性id
        # 更新neo4j数据库的属性名
        # 就是把第一个换成第二个

    # 没有考虑不映射的情况，也就是map_attribute_id是-1的情况
    def update_mapping_rule(self, request):
        t_mapping_rule_id = request.POST['map_rule_id']
        map_attribute_id = request.POST['map_attribute_id']

        repo_id = request.session["repo_id"]
        create_id = request.session["user_id"]
        # 修改映射id
        obj = TMappingRule.objects.get(id=t_mapping_rule_id)
        obj.map_attribute_id = map_attribute_id
        obj.save()
        # 获得旧的属性名字
        old_att_name = model_to_dict(obj)['attribute_name']

        # 获得新的属性名字
        obj_att = TAttribute.objects.get(id=map_attribute_id)
        new_att_name = model_to_dict(obj_att)['attribute_name']

        # 获得要更新的类目名字 也就是这个知识图谱中的所有数据
        res = TCategory.objects.filter(repo_id=repo_id, create_id=create_id)
        all_list = []
        for val in res:
            val_dict = model_to_dict(val)
            all_list.append(val_dict['category_name'])
        neo4j = Neo4j().update_attribute(all_list, old_att_name, new_att_name)
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
            cate_dict['attribute'] = res_attribute_dict
            cate_list.append(cate_dict)
        ret_l['cleaning_rule'] = cate_list
        print(ret_l)
        return render(request, "index/cleaning_rule.html", context=ret_l)

    # 已知create_id category_id 返回他的所有cleaning rule 和 attribute
    def get_cleaning_rule(self, request):
        category_id = request.POST['select_category_id']
        create_id = request.session['user_id']

        res_cate = TCleaningRule.objects.filter(create_id=create_id, category_id=category_id)
        ret_l = {}
        cate_list = []
        for val in res_cate:
            cate_dict = model_to_dict(val)
            attribute_id = cate_dict['attribute_id']
            res_attribute = TAttribute.objects.get(id=attribute_id)
            res_attribute_dict = model_to_dict(res_attribute)
            cate_dict['attribute'] = res_attribute_dict
            cate_list.append(cate_dict)
        ret_l['cleaning_rule'] = cate_list

        print(ret_l)
        return self.success(ret_l)

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
        return render(request, "index/merging_rule.html", context=ret_l)

        # 输入是normalized_rule_id 返回t_normalize_rule_detail中内容
        def get_normalize_rule_detail(self, request):
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
            ret_val = TAttribute.objects.filter(category_id=category_id)
            for att in ret_val:
                att_dict = model_to_dict(att)
                tmp_attribute_dict = {}
                tmp_attribute_dict['id'] = att_dict['id']
                tmp_attribute_dict['attribute_name'] = att_dict['attribute_name']
                ret_attribute_list.append(tmp_attribute_dict)
            ret_l = {}
            ret_l['context'] = ret_list
            ret_l['attribute'] = ret_attribute_list
            print(ret_l)
            return self.success(ret_l)

    def extract_result(self, request):
        return render(request, 'index/extract_result.html')

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

    #输入是实体id 返回这个实体的所有信息
    def ret_entity_all_info(self,request):
        try:
            #entity_id = request.POST['entity_id']
            entity_id = 2962783
        except Exception:
            return self.error("没有实体id")
        #把名字id 和类目跳出来
        #attribute name
        res_attribute = TAttribute.objects.get(category_id=1)
        res_attribute_dict = model_to_dict(res_attribute)
        attribute_name = res_attribute_dict['attribute_name']
        ret_node = Neo4j().ques_node_by_id(entity_id,attribute_name)

        ret_l={'context':ret_node}
        print((ret_l))
        return render(request, "test1.html", context=ret_l)

    # 返回这个知识库所有category和id
    # 第一个类目的所有节点每个节点返回加点名字和id
    def return_knowledge_graph(self, request):
        try:
            #repo_id = request.session["repo_id"]
            repo_id = 1
        except Exception:
            return self.error("没有repo_id")
        try:
            #create_id = request.session["user_id"]
            create_id=1
        except Exception:
            return self.error("没有create_id")

        ret_category = TCategory.objects.filter(repo_id=repo_id)
        category_list = []
        first_category_name = ''
        first_category_id=0
        num = 0
        for val in ret_category:
            val_dict = model_to_dict(val)
            tmp_map={}
            tmp_map['id'] = val_dict['id']
            tmp_map['category_name'] = val_dict['category_name']
            category_list.append(tmp_map)
            if (1 == repo_id):
                if(num == 1):
                    first_category_name=val_dict['category_name']
                    first_category_id = val_dict['id']
            else:
                if (num == 0):
                    first_category_name = val_dict['category_name']
                    first_category_id = val_dict['id']
            num+=1
        #查询事物的第一个attribute_name  其实就是名字
        affair_attribute = TAttribute.objects.get(category_id=1)
        affair_attribute_dict = model_to_dict(affair_attribute)
        first_category_attribute_name = affair_attribute_dict['attribute_name']
        ret_Node = Neo4j().ret_node_list_get_one_category_node_name_id(first_category_name,first_category_attribute_name,first_category_id)
        ret_l={}
        ret_l['category']=category_list
        ret_l['nodes']=ret_Node
        ret_l['links']=[]
        print(ret_l)
        return render(request, "test1.html", context={"data": ret_l})

    #输入是类目id
    #返回这个类目的所有节点
    def ret_category_all_node(self,request):
        try:
            #repo_id = request.session['repo_id']
            repo_id = 1
        except Exception:
            return  self.error("没有repo_id")
        try:
            #category_id = request.POST['category_id']
            category_id= 2
        except Exception:
            return  self.error("没有category_id")
        ret_category = TCategory.objects.get(id=category_id)
        ret_category_dict = model_to_dict(ret_category)
        category_name = ret_category_dict['category_name']
        affair_attribute = TAttribute.objects.get(category_id=1)
        affair_attribute_dict = model_to_dict(affair_attribute)
        first_category_attribute_name = affair_attribute_dict['attribute_name']
        ret_Node = Neo4j().ret_node_list_get_one_category_node_name_id(category_name,
                                                                       first_category_attribute_name,category_id)

        ret_l={}
        ret_l['nodes']=ret_Node
        ret_l['links']=[]
        print(ret_l)
        return render(request, "test1.html", context={"data": ret_l})

    #返回t_attribute_map_log的内容
    def ret_t_attribute_map_log(self,request):
        try:
            #repo_id = request.session['repo_id']
            repo_id = 1
        except Exception:
            return self.error("没有repo_id")
        try:
            #create_id = request.session['create_id']
            create_id = 1
        except Exception:
            return self.error("没有create_id")
        ret_log = TAttributeMapLog.objects.filter(create_id = create_id,repo_id=repo_id)
        log_list =[]
        for val in ret_log:
            val_dict = model_to_dict(val)
            tmp_map = {}
            tmp_map['id'] = val_dict['id']
            tmp_map['attribute_name'] = val_dict['attribute_name']
            tmp_map['is_map']=val_dict['is_map']
            tmp_map['entity_id'] = val_dict['entity_id']
            #tmp_map['map_attribute_id']
            map_attribute_id= val_dict['map_attribute_id']
            res_attribute = TAttribute.objects.get(id = map_attribute_id)
            res_attribute_dict = model_to_dict(res_attribute)
            tmp_map['map_attribute_name'] = res_attribute_dict['attribute_name']
            tmp_map['map_rule_id'] =val_dict['map_rule_id']
            #tmp_map['category_id']
            res_category = TCategory.objects.get(id=val_dict['category_id'])
            res_category_dict = model_to_dict(res_category)
            tmp_map['category_name'] = res_category_dict['category_name']
            log_list.append(tmp_map)
        ret_l = {'context':log_list}
        return render(request, "test1.html", context=ret_l)

    # 返回ret_t_data_acquisition_log的内容
    def ret_t_data_acquisition_log(self, request):
        try:
            #repo_id = request.session['repo_id']
            repo_id = 1
        except Exception:
            return self.error("没有repo_id")
        try:
            #create_id = request.session['create_id']
            create_id = 1
        except Exception:
            return self.error("没有create_id")
        ret_log = TDataAcquisitionLog.objects.filter(repo_id = repo_id,create_id=create_id)
        log_list = []
        for val in ret_log:
            val_dict = model_to_dict(val)
            tmp_map = {}
            tmp_map['id'] = val_dict['id']
            tmp_map['create_time'] = str(val_dict['attribute_name'])
            tmp_map['data_source'] = val_dict['data_source']
            tmp_map['data_access'] = val_dict['data_access']
            log_list.append(tmp_map)
        ret_l = {'context': log_list}
        return render(request, "test1.html", context={"data": ret_l})

    # 返回t_entity_extraction_log的内容
    def ret_t_entity_extraction_log(self, request):
        try:
            # repo_id = request.session['repo_id']
            repo_id = 1
        except Exception:
            return self.error("没有repo_id")
        try:
            # create_id = request.session['create_id']
            create_id = 1
        except Exception:
            return self.error("没有create_id")
        ret_log = TEntityExtractionLog.objects.filter(repo_id=repo_id, create_id=create_id)
        log_list = []
        for val in ret_log:
            val_dict = model_to_dict(val)
            tmp_map = {}
            tmp_map['id'] = val_dict['id']
            tmp_map['data_source'] = val_dict['data_source']
            tmp_map['is_extract'] = val_dict['is_extract']
            tmp_map['entity_number'] = val_dict['entity_number']
            tmp_map['extract_time'] = str(val_dict['extract_time'])
            log_list.append(tmp_map)
        ret_l = {'context': log_list}
        return render(request, "test1.html", context={"data": ret_l})

    # 返回t_normalized_log的内容
    def ret_t_normalized_log(self, request):
        try:
            # repo_id = request.session['repo_id']
            repo_id = 1
        except Exception:
            return self.error("没有repo_id")
        try:
            # create_id = request.session['create_id']
            create_id = 1
        except Exception:
            return self.error("没有create_id")
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
        ret_l = {'context': log_list}
        return render(request, "test1.html", context={"data": ret_l})

