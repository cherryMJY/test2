import ast
import functools
import os
from datetime import datetime
import pandas
from django.core.serializers import json
from django.http import HttpResponse
from bson import ObjectId, json_util
import re
import arrow

from model.hanlpUnit import HanlpUnit
from Time_NLP.time_deal import Time_deal
from controller.baseController import BaseController
from model.models import *
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.shortcuts import HttpResponseRedirect
from django.utils import timezone
from django.forms.models import model_to_dict
from django.utils import timezone as datetime
import xlrd
import openpyxl

from model.some_data_deal_func import some_data_deal_func
from model.mongodb import Mongodb
from model.neo4j import Neo4j


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
                return self.success("登录成功")
            else:
                return self.error("密码错误")
        except ObjectDoesNotExist:
            return self.error("账户不存在")

    def homepage(self, request):
        return render(request, 'index/homepage.html', context={})

    def knowledge_definition(self, request):
        return render(request, 'index/knowledge_definition.html')

    #自己测试用的接口
    def mongodb_insert(self,request):

        news_col = Mongodb(db='knowledge', collection='text').get_collection()
        dic={'孟':123,'佳':456,'营':999,'category_id':11}
        news_col.insert_one(dic)
        dic = { '佳': 456, '营': 999,'category_id':11}
        news_col.insert_one(dic)
        dic = { '营': 999,'category_id':11}
        news_col.insert_one(dic)

        return render(request, 'test.html', context={'result': 'success'})

    def add_repo(self,request):

        repo_name = request.POST['repo_name']
        repo_describe = request.POST['repo_describe']
        user_id = request.session['user_id']

        #repo_name = '3'
        #repo_describe = 'i am a pig'
        #user_id = 1
        TRepository.objects.create(repo_name=repo_name,repo_description=repo_describe,create_id=user_id)
        print(1)
        result = 'result'
        return render(request, 'test.html', context={result: 'success'})

    def get_repo_id_return_all_category(self, request):
        repo_id = request.POST['repo_id']
        #repo_id = 1
        result = TCategory.objects.filter(repo_id=repo_id)

        num = 0
        #获得事务的id
        work_id = 0
        tmp_description =''
        tmp_id = 0
        for category in result:
            ret_result = model_to_dict(category)
            if ret_result['category_name'] == '事务':
                work_id = ret_result['id']
                tmp_description = ret_result['category_description']
                tmp_id = ret_result['id']
            num +=1
        now =1
        #print(work_id)

        multilist = [[0] * (num+1) for row in range(num+1)]
        multilist_id = [[0] * (num + 1) for row in range(num + 1)]
        cnt_list  = [0 for i  in range(num+1)]

        ind = 1
        for category in result:
            ret_result = model_to_dict(category)
            if int(ret_result['category_level']) == int(3):
                ind2 =1
                for  category1 in result:
                    ret_result1 = model_to_dict(category1)
                    if int(ret_result1['id']) ==  int(ret_result['father_category_id']):
                        multilist[ind2][cnt_list[ind2]] = ret_result['category_name']
                        multilist_id[ind2][cnt_list[ind2]] = ret_result['id']
                        cnt_list[ind2]+=1
                    ind2+=1
            ind+=1;
        ind =1;
        test = {}
        tmp_list_2 = []
        tmp_list_1 = []
        for out_category in result:
            #有第三层的
            ret_result = model_to_dict(out_category)
            if cnt_list[ind]>0:
                dic={}
                now_list = []
                for j  in range(0,cnt_list[ind]):
                    tmp={}
                    tmp['id']=multilist_id[ind][j]
                    tmp['category_name']=multilist[ind][j]
                    now_list.append(tmp)
                cnt = 1;
                tmp_name1 = ""
                tmp_id1   =  ""
                for  category in result:
                     if cnt == ind:
                        cate_map=model_to_dict(category)
                        tmp_name1 = cate_map['category_name']
                        tmp_id1  = cate_map['id']
                     cnt+=1
                dic['id']=tmp_id1
                dic['category_name'] = tmp_name1
                dic['level3_child']  = now_list
                tmp_list_2.append(dic)
            elif int(ret_result['category_level']) == 2:
                dic={'id':ret_result['id'],'category':ret_result['category_name'],'level3_child':[]}
                tmp_list_2.append(dic)
            ind+=1

        find_attribute = TAttribute.objects.filter(category_id=work_id)
        #这个属性
        tmp_list_attribute = []
        for attribute in find_attribute:
            ret_result = model_to_dict(attribute)
            tmp_list_attribute.append(ret_result)

        test['id']  =tmp_id
        test['category'] = {'category_description': tmp_description, 'attribute':tmp_list_attribute}
        test['level2_child'] = tmp_list_2
        print(test)
        return render(request, 'test.html', context={result: 'success'})

    #添加新的类目
    def new_class_submit(self, request):
        _category_name = request.POST['category_name']
        _category_describe = request.POST['category_describe']
        _father_category_id = request.POST['father_category_id']

        _repo_id = request.session['repo_id']
        _create_id = request.session['create_id']

        #_category_name = "test1"
        #_category_describe = "123"
        #_father_category_id = 5
        #_repo_id = 1
        #_create_id = 1

        obj = TCategory.objects.get(id=_father_category_id)
        now_level = obj.category_level + 1
        dt=datetime.now()
        TCategory.objects.create(category_name=_category_name,father_category_id=_father_category_id,is_temporary=0,
                                 category_description=_category_describe,repo_id=_repo_id,create_id=_create_id,create_time=dt,category_level=now_level)
        return render(request, 'test.html', context={1: 'success'})

    #添加属性
    def add_attribute(self,request):
        _attribute_name = request.POST['attribute_name']
        _attribute_datatype = request.POST['attribute_datatype']
        _is_single_value = request.POST['is_single_value']
        _attribute_description = request.POST['attribute_description']
        _category_id = request.POST['category_id']
        #属性别名要用逗号分开
        _attribute_alias = request.POST['attribute_alias']
        _create_id =request.session['create_id']

        dt = datetime.now()
        TAttribute.objects.create(attribute_name=_attribute_name,attribute_datatype=_attribute_datatype,
                                  is_single_value=_is_single_value,attribute_description=_attribute_description,
                                  category_id=_category_id,create_time=dt)
        li = _attribute_alias.split(',')
        attribute_obj = TAttribute.objects.get(attribute_name=_attribute_name,attribute_datatype=_attribute_datatype,
                                  is_single_value=_is_single_value,attribute_description=_attribute_description,
                                  category_id=_category_id,create_time=dt)
        _attribute_id = attribute_obj.id
        for val in li:
            TAttrbuteAlias.objects.create(attribute_id = _attribute_id,attribute_alias=val,create_id = _create_id,create_time=dt)

        #添加 导致这个属性本来在表里面的后面要删除
        #修改 如果表里面有的  后面改了以后同名了 表里要删除
        #删除属性 更新表就行

        return render(request, 'test.html', context={1: 'success'})

    #修改属性
    def  update_attribute(self,request):
        _attribute_id = request.POST['attribute_id']
        _attribute_name = request.POST['attribute_name']
        _attribute_alias = request.POST['attribute_alias']
        _attribute_datatype = request.POST['attribute_datatype']
        _is_single_value = request.POST['is_single_value']
        _attribute_description = request.POST['attribute_description']
        _create_id = request.session['create_id']

        #_attribute_id = 28
        #_attribute_name = '123'
        #_attribute_alias = '1,5,9'
        #_attribute_datatype = '字符串'
        #_is_single_value = '1'
        #_attribute_description = '123'
        #_create_id = '1'


        _attribute = TAttribute.objects.get(id = _attribute_id)

        #obj = TRepository.objects.get(c_id=repo_id , c_name=repo_name)
        #obj.c_description = repo_describe
        #obj.save();
        _attribute.attribute_name = _attribute_name
        _attribute.attribute_datatype= _attribute_datatype
        _attribute.is_single_value = _is_single_value
        _attribute.attribute_description = _attribute_description
        _attribute.save();
        _attribute_alias_delete = TAttrbuteAlias.objects.filter(attribute_id=_attribute_id)
        _attribute_alias_delete.delete()
        #删除属性别名
        #添加属性别名
        li = _attribute_alias.split(',')
        dt=datetime.now()
        for val in li:
            TAttrbuteAlias.objects.create(attribute_id=_attribute_id, attribute_alias=val, create_id=_create_id,
                                          create_time=dt)

        return render(request, 'test.html', context={1: 'success'})

    # 删除
    def delete_attribute(self, request):
        _attribute_id = request.POST['attribute_id']
        create_id = request.session['user_id']
        repo_id = request.session['repo_id']
        #_attribute_id = 1
        #create_id = 1
        #repo_id   = 1
        _attribute_alias_delete = TAttrbuteAlias.objects.filter(attribute_id=_attribute_id)

        try:
            _attribute_delete = TAttribute.objects.get(id=_attribute_id)
        except ObjectDoesNotExist:
            return self.error("不存在该属性数据！")
        cleaning_rule = TCleaningRule.objects.filter(attribute_id=_attribute_delete.id)
        _attribute_delete_dict = model_to_dict(_attribute_delete)
        category_id = _attribute_delete_dict['category_id']


        # 还需要修改，删除操作后会对清洗和映射内容造成影响
        return_map_rule =TMappingRule.objects.filter(map_attribute_id = _attribute_id,category_id=category_id,create_id = create_id)
        for val in return_map_rule:
            val_dict  = model_to_dict(val)
            print(val_dict)
            old_map_attribute_id= val_dict['map_attribute_id']
            t_mapping_rule_id=val_dict['id']
            map_attribute_id = -1
            #这边要改的东西
            #假如说已经是-1 那么直接continue
            #不是-1 上面有日志
            #然后那 attribute_map_log
            if(old_map_attribute_id == -1):
                continue

            old_att_name = val_dict['attribute_name']
            old_name_show_in_database = old_att_name
            ret_attribute_log = TAttributeMapLog.objects.filter(map_rule_id=t_mapping_rule_id, create_id=create_id,
                                                                repo_id=repo_id)
            for val_log in ret_attribute_log:
                val_log_dict = model_to_dict(val_log)
                print(val_log_dict)
                return_attribtue_log = TAttribute.objects.get(id=val_log_dict['map_attribute_id'], category_id=category_id)
                return_attribtue_log_dict = model_to_dict(return_attribtue_log)
                print(return_attribtue_log_dict)
                old_att_name = return_attribtue_log_dict['attribute_name']
                # 就一直更新就行 那最下面的那个
            new_att_name = val_dict['attribute_name']
            ret_category = TCategory.objects.get(id=category_id, repo_id=repo_id, create_id=create_id)
            category_name = model_to_dict(ret_category)['category_name']
            print(old_att_name,new_att_name)
            neo4j = Neo4j().update_attribute(category_id, t_mapping_rule_id, category_name, old_att_name,
                                                 new_att_name,
                                                 map_attribute_id,old_name_show_in_database, create_id, repo_id)
            val.map_attribute_id=-1
            val.save()

        _attribute_alias_delete.delete()
        _attribute_delete.delete()
        cleaning_rule.delete()
        #在这个之后那个覆盖也要修改
        some_data_deal_func().update_t_mapping_rule(repo_id, create_id)
        return self.success("删除成功！")
        #return render(request, 'test.html', context={1: 'success'})

    #返回他和他的所有的祖先的category还有他们的attribute
    def return_category_and_father(self,request):
        #_category_id = request.POST['category_id']
        _category_id = 5
        ret_l = {}
        _category_now =TCategory.objects.get(id=_category_id)
        _category_now_dict=model_to_dict(_category_now)
        #_category_now_dict  要增加attribute
        _category_now_attribute = []
        tmp_res = TAttribute.objects.filter(category_id=_category_id)
        for  val in tmp_res:
            tem_res_dict = model_to_dict(val)
            _category_now_attribute.append(tem_res_dict)
        _category_now_dict['attribute']= _category_now_attribute
        #print(_category_now_dict)
        ret_l['category']=_category_now_dict
        father_list = []
        _catgegory_father_id =_category_now.father_category_id
        _category_father = TCategory.objects.get(id=_catgegory_father_id)
        _category_father_dict = model_to_dict(_category_father)
        tmp_res = TAttribute.objects.filter(category_id=_catgegory_father_id)
        _category_father_attribute = []
        for  val in tmp_res:
            tem_res_dict = model_to_dict(val)
            _category_father_attribute.append(tem_res_dict)
        _category_father_dict['attribute']= _category_father_attribute
        father_list.append(_category_father_dict)

        if _catgegory_father_id != -1 and _category_father_dict['father_category_id'] != -1:
            _category_father_father_id = _category_father_dict['father_category_id']
            _category_father_father = TCategory.objects.get(id=_category_father_father_id)
            _category_father_father_dict = model_to_dict(_category_father_father)
            tmp_res = TAttribute.objects.filter(category_id=_category_father_father_id)
            _category_father_father_attribute = []
            for val in tmp_res:
                tem_res_dict = model_to_dict(val)
                _category_father_father_attribute.append(tem_res_dict)
            _category_father_father_dict['attribute'] = _category_father_father_attribute
            father_list.append(_category_father_father_dict)

        ret_l['father_category'] = father_list
        return render(request, 'test.html', context=ret_l)

    #通过知识库的id  返回日志 这个接口等表修改了才能用
    def ret_log(self,request):
        ret_l={}
        repo_id = request.POST['repo_id']
        #repo_id  = 1
        ret_log = TDataAcquisitionLog.objects.filter(repo_id=repo_id)
        repo_list = []
        for val in ret_log :
            ret_log_list = model_to_dict(val)
            repo_list.append(ret_log_list)
        ret_l['ret_log'] = repo_list
        print(ret_l)
        return render(request, 'test.html', context=ret_l)

    #把文件从前端传递到后台
    #更新t_entity_extraction_log
    #更新t_data_acquisition_log
    def upload_file(self, request):
        # d / 名字ID / 知识库名字ID
        # repo_id = request.session['repo_id']
        repo_id = 1
        # create_id = request.session['user_id']
        create_id = 1
        # data_access=request.POST['data_access']
        data_access = '文件'

        repo = TRepository.objects.get(id=repo_id)
        repo_dict = model_to_dict(repo)
        repo_name = repo_dict['repo_name']

        user = TUser.objects.get(id=create_id)
        user_dict = model_to_dict(user)
        user_name = user_dict['user_name']

        if request.method == "POST":  # 请求方法为POST时，进行处理
            myFile = request.FILES.get("myfile", None)  # 获取上传的文件，如果没有文件，则默认为None
            if not myFile:
                return HttpResponse("no files for upload!")
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
            dt = datetime.now()
            file_name_1 = str(dt)[:19] + ".xlsx"
            file_name = file_name_1.replace(":", "")
            true_file_name = myFile.name
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

            #data = xlrd.open_workbook(path + '\\' + file_name)
            #table_name = data.sheet_names()[0]
            # 这边是第几个工作表
            #table = data.sheet_by_name(table_name)
            #list_attribute = list(table.row_values(0))
            #list_json = []

            data_acqisition_id = return_data_acquisition_log_dict['id']
            entity_number = 0
            is_extract = 0
            dt = datetime.now()
            TEntityExtractionLog.objects.create(data_acquisition_id=data_acqisition_id,
                                                is_extract=is_extract,
                                                entity_number=entity_number,
                                                create_id=create_id,
                                                repo_id=repo_id,
                                                extract_time=dt)
            return HttpResponse("upload over!")
        ret_l = {}
        return render(request, 'test.html', context=ret_l)

    #从excel中读取数据 进行相似度计算
    def read_data_from_excel(self,request):
        file_name =  't_log.xlsx'
        path_str= 'D://upload/'
        data  = xlrd.open_workbook(path_str + file_name)
        print(data.sheet_names())
        table_name = data.sheet_names()[0]
        table = data.sheet_by_name(table_name)
        print(str(table.row_values(0)))
        list_attribute  = list(table.row_values(0))

        #repo_id = request.POST['repo_id']
        repo_id = 1
        category_res =TCategory.objects.filter(repo_id = repo_id)
        ans_id =  -1
        ans_sim = -1
        for category in category_res:
            category_dict = model_to_dict(category)
            tmp_category_id = category_dict['id']
            print(tmp_category_id)
            attribute_res = TAttribute.objects.filter(category_id = tmp_category_id)
            list_attribute_name = []
            for attribute in attribute_res:
                attribute_dict = model_to_dict(attribute)
                list_attribute_name.append(attribute_dict['attribute_name']);
            print(list_attribute_name)
            cnt  = 0
            list1_size = len(list_attribute)
            list2_size = len(list_attribute_name)

            for i in list_attribute_name:
                for j in list_attribute:
                    print(i, j)
                    if( i ==  j):
                        cnt += 1
            sim = 1.0 * cnt / (list1_size + list2_size - cnt )
            if(sim > ans_sim):
                ans_sim = sim
                ans_id  =  tmp_category_id
            #然后在attribte中查询出来
        print(ans_sim,ans_id)
        #这边可以设定一个一定的阈值然后超过阈值就存入到neo4j中 或者将要归入的类目先返回到前端界面然后人工判断下在加入到neo4j中
        ret_l={}
        return render(request, 'test.html', context=ret_l)

    #把数据从文件中读出来然后 返回给前端
    def read_data_from_excel_return_data(self,request):
        file_name = 't_log.xlsx'
        path_str= 'D://upload/'
        data  = xlrd.open_workbook(path_str + file_name)
        table_name = data.sheet_names()[0]
        table = data.sheet_by_name(table_name)
        list_attribute= list(table.row_values(0))
        list_json = []
        row=table.nrows
        col=table.ncols
        print(row,col)
        for i in range(1,row):
            dict_data ={}
            for j in range(0,col):
                dict_data[list_attribute[j]]=table.row_values(i)[j]
            list_json.append(dict_data)

        ret_l = {'data':list_json}
        print(ret_l)
        return render(request, 'test.html', context=ret_l)

    #从文件中读取数据 然后存入到Mongodb
    def save_data_to_mongodb(self,request):
        #新建类目表
        #数据的话从文件里面读出
        repo_id = request.POST['repo_id']
        #create_id = request.POST['create_id']
        file_id = request.POST['file_id']

        #这个存入到mongodb里面先不用
        #category_id = request.POST['category_id']
        try:
            news_col = Mongodb(db='knowledge', collection='text').get_collection()
        except Exception:
            return self.error("mongodb没有数据库或者表")

        try:
            ret_file_data = TDataAcquisitionLog.objects.get(id=file_id)
        except Exception:
            return  self.error("id没有对应文件")

        ret_file_data_dict = model_to_dict(ret_file_data)
        file_name = ret_file_data_dict['data_source']
        path_str =  ret_file_data_dict['data_access']
        try:
            data = xlrd.open_workbook(path_str + file_name)
        except Exception:
            return self.error("没有找到对应文件")

        table_name = data.sheet_names()[0]
        table = data.sheet_by_name(table_name)
        list_json = []
        row = table.nrows
        col = table.ncols

        list_attribute = list(table.row_values(0))

        category_id = some_data_deal_func().calculate_nearest_category(list_attribute,repo_id)
        return_category_name = TCategory.objects.get(id=category_id).category_name
        print("相似的category",return_category_name)
        for i in range(1, row):
            dict_data = {}
            for j in range(0, col):
                dict_data[list_attribute[j]] = table.row_values(i)[j]
            dict_data['file_id']=file_id
            x=news_col.insert_one(dict_data)

        ret_l={'context':'success'}

        return render(request, 'test.html', context=ret_l)


    #这个借口目前没什么用
    def find_relationship_from_excel(self,request):

        #而且要对excel中的每行数据都进行匹配
        li = ['123','456','789']
        repo_id = request.POST['repo_id']
        create_id = request.POST['create_id']
        res  = TCategory.objects.filter(repo_id=repo_id,create_id=create_id)
        ques_cate_name = []
        for val in res:
            val_dict =  model_to_dict(val)
            ques_cate_name.append(val_dict['category_name'])

        #假如说能匹配的话 那么就把这些关系都拿出来好了
        ret_l = {}
        return render(request, 'test.html', context=ret_l)

    #返回类目，属性，
    def return_category_attribute_mapping(self,request):
        #repo_id = request.POST['repo_id']
        #create_id = request.POST['create_id']
        repo_id=1
        create_id=1
        res_cate = TCategory.objects.filter(repo_id=repo_id,create_id=create_id)
        ret_l = {}
        cate_list = []
        for val in res_cate:
            cate_dict = model_to_dict(val)
            cate_id = cate_dict['id']
            cate_name = cate_dict['category_name']
            now_dict = {}
            now_dict['id']=cate_id
            now_dict['category_name'] = cate_name
            cate_list.append(now_dict)
        ret_l['category']=cate_list
        att_list = []
        for val in cate_list:
            cate_id  = val['id']
            res = TAttribute.objects.filter(category_id = cate_id)
            for att in res:
                att_dict = model_to_dict(att)
                now_dict ={}
                now_dict['id']=att_dict['id']
                now_dict['attribute_name']=att_dict['attribute_name']
                att_list.append(now_dict)
                break
        ret_l['attribute'] = att_list
        att_map_list = []
        for val in cate_list:
            cate_id = val['id']
            res  = TMappingRule.objects.filter(category_id = cate_id,create_id=create_id)
            for att in res:
                att_dict = model_to_dict(att)
                att_dict['create_time']=str(att_dict['create_time'])
                att_map_list.append(att_dict)
                break
        ret_l['attribute_mapping']=att_map_list
        print(ret_l)
        return render(request, 'test.html', context=ret_l)

    #根据id更新属性id
    #更新neo4j数据库的属性名
    #就是把第一个换成第二个
    #这个属性映射了以后
    #连续2次map_attribute_id = -1 那么就返回错误信息
    #1 -1 变成 正常数字
    #2 正常数字变成-1
    #3正常数字 变成 正常数字
    def update_mapping_rule(self, request):
        #t_mapping_rule_id = request.POST['map_rule_id']
        #map_attribute_id = request.POST['map_attribute_id']
        t_mapping_rule_id = 13
        map_attribute_id = 1
        #repo_id = request.session["repo_id"]
        #create_id = request.session["user_id"]
        repo_id = 1
        create_id = 1

        # 修改映射id
        obj = TMappingRule.objects.get(id=t_mapping_rule_id)
        old_map_attribute_id = obj.map_attribute_id
        obj.map_attribute_id = map_attribute_id
        obj.save()
        #print(type(old_map_attribute_id),type(map_attribute_id))
        #-1 变成 -1
        if(old_map_attribute_id == -1 and map_attribute_id == -1):
            return self.error("错误信息")
        # 获得旧的属性名字
        #这个旧的属性名字可能不是这个因为可能已经映射过一次
        #根据map_rule_id 来查询 如果没有映射日志 那么就是这个
        #不然就是最近的那个
        #这个初始化为本身
        print(old_map_attribute_id)
        category_id = model_to_dict(obj)['category_id']

        old_att_name = model_to_dict(TMappingRule.objects.get(id=t_mapping_rule_id))['attribute_name']
        ret_attribute_log=TAttributeMapLog.objects.filter(map_rule_id=t_mapping_rule_id,create_id=create_id,repo_id=repo_id)
        old_name_show_in_database = old_att_name
        for val in ret_attribute_log:
            val_dict = model_to_dict(val)
            print(val_dict)
            return_attribtue_log = TAttribute.objects.get(id = val_dict['map_attribute_id'],category_id=category_id)
            return_attribtue_log_dict = model_to_dict(return_attribtue_log)
            print(return_attribtue_log_dict)
            old_att_name = return_attribtue_log_dict['attribute_name']
                #就一直更新就行 那最下面的那个

        #假如说他是-1 那么上面的都要删掉

        # 获得新的属性名字
        #这个新的属性也可能没有因为可能是不映射 那么新的名字是原来的属性名字
        if(-1 != map_attribute_id):
            obj_att = TAttribute.objects.get(id=map_attribute_id)
            new_att_name = model_to_dict(obj_att)['attribute_name']
        else:
            #这个应该是一开始的名字
            return_new_att = TMappingRule.objects.get(id=t_mapping_rule_id,category_id=category_id)
            new_att_name = model_to_dict(return_new_att)['attribute_name']
        print(new_att_name)
        # 获得要更新的类目名字
        # 只要更新这个类目的这个attribute就好了
        print(old_att_name,new_att_name)
        ret_category = TCategory.objects.get(id=category_id, repo_id=repo_id, create_id=create_id)
        category_name = model_to_dict(ret_category)['category_name']
        neo4j = Neo4j().update_attribute(category_id,t_mapping_rule_id,category_name, old_att_name, new_att_name, map_attribute_id,old_name_show_in_database,create_id,repo_id)
        ret_l = {}

        return self.success("更新成功！")
        #return render(request, 'test.html', context=ret_l)

    #已知create_id category_id 返回他的所有cleaning rule 和 attribute
    def return_category_id_t_cleaning_rule(self,request):
        # category_id  = request.POST['category_id']
        # create_id = request.POST['create_id']
        create_id = 1
        category_id = 3

        res_cate = TCleaningRule.objects.filter(create_id=create_id, category_id=category_id)
        ret_l = {}
        cate_list = []
        for val in res_cate:
            cate_dict = model_to_dict(val)
            attribute_id = cate_dict['attribute_id']
            res_attribute = TAttribute.objects.get(id = attribute_id)
            res_attribute_dict = model_to_dict(res_attribute)
            cate_dict['attribute']=res_attribute_dict
            cate_list.append(cate_dict)
        ret_l['cleaning_rule']=cate_list

        print(ret_l)
        return render(request, 'test.html', context=ret_l)

    def acquire_movie_piaofang(self,request):
        movie_id  = request.POST['movie_id']
        print(movie_id);
        list_date=[]
        list_data=[]
        for i in range(1,50):
            list_date.append('开始'+str(i)+'天');
            if(i<=10):
                list_data.append(i*10000);
            else:
                list_data.append(i*100000000);
        ret_l = {'date':list_date,'data':list_data}
        return self.success(ret_l)
        #return render(request, 'index.html', context=ret_l)

    #输入规则id  是否自定义  规则内容
    def cleaning_rule_realize(self,request):
        #rule_id =   request.POST['rule_id']
        #is_custom = request.POST['is_custom']
        #rule_content = request.POST['rule_content']
        user_id = 1
        repo_id=1
        create_id = 1
        rule_id=1
        is_custom=0
        #rule_number  0 - 6  分别是清洗的 0 - 3 是小数点 4 - 6 是日期 7 是自定义
        rule_number = 5
        #假如说这个是0 那么就是自定义正则表达式 否则是按固定的
        rule_content=123

        #上面都是初始化
        obj = TCleaningRule.objects.get(id=rule_id)
        obj.cleaning_rule = rule_content
        obj.is_custom = is_custom
        attribute_id = obj.attribute_id
        obj.save()
        #进行表的修改
        att = TAttribute.objects.get(id  = attribute_id)
        att_dict = model_to_dict(att)
        attribute_name  =att_dict['attribute_name']
        res = TCategory.objects.filter(repo_id=repo_id,create_id=create_id)
        all_list = []
        all_list_cate_id = []
        for val in res:
            val_dict = model_to_dict(val)
            all_list.append(val_dict['category_name'])
            all_list_cate_id.append(val_dict['id'])
        neo4j = Neo4j().update_attribute_value(all_list, attribute_name,rule_number,rule_content,user_id,rule_id,all_list_cate_id,repo_id)
        ret_l = {}
        return render(request, 'test.html', context=ret_l)

    #从后台传输事件数据到前端
    def knowledge_test(self,request):
        tmpList=request.POST['log_id']

        time1 = datetime.now()
        year = time1.year
        month = time1.month
        day = time1.day
        print(year,month,day)
        yearStr = str(year)
        monthStr = str(month)
        dayStr = str(day)
        if(len(monthStr) <2):
            monthStr='0'+str(month)
        if (len(dayStr) < 2):
            dayStr = '0' + str(day)
        print(yearStr,monthStr,dayStr)
        tmpLen = len(tmpList)
        tmpDict ={'data':tmpList}
        tmpDict['time']=yearStr+monthStr+dayStr
        news_col = Mongodb(db='ttjj', collection='fund_data').get_collection()
        news_col.insert_one(tmpDict)
        ret_l = {'category':1}
        return  self.success("插入成功")
        #return render(request, 'index.html', context=ret_l)

    def relationshipExtraction(self,request):
        sentence = "1997年浙江孟佳营,杨启胜,攻城狮不可能起飞,崔硕"
        subjectCategoryId  = 4
        triggerWordId =  1
        objectCategoryId = 5
        ruleId = 2
        repoId = 1
        createId = 1

        event=some_data_deal_func().eventExtractionByTemplateMatching(request,sentence,subjectCategoryId,triggerWordId,ruleId,repoId,createId,objectCategoryId)
        #关系要转化成neo4j之中的关系
        returnExtractContent={}
        return render(request, 'test.html', context=returnExtractContent)


    #利用模式匹配的方法进行事件抽取
    # 根据事件内容查询事件id的时候会出问题
    #根据内容查询id的时候如何处理
    #假如说内容相同怎么办

    def eventExtraction(self,request):
        #加入ruleId 1或者2 1的话变成三个 2的话变成两个
        #only for debug
        request.session['user_id'] = 1
        request.session['repo_id'] = 1
        fileId = 13
        # only for debug

        #fileId = request.POST['fileId']
        repoId =  request.session['repo_id']
        createId = request.session['user_id']


        tmp_info = {'file_id': fileId,'user_id':createId,'repo_id':repoId}
        try:
            news_col = Mongodb(db='knowledge', collection='text').get_collection()
        except Exception:
            return self.error("mongodb没有数据库或者表")
        cnt=1
        ret_entity_map = news_col.find(tmp_info)

        #在这个之前把所有的词语都加进去
        #整个循环都是为了把这个repoId的所有的触发词以及他们的事件主题客体都加入进去
        retTriggerWordList = TTriggerWord.objects.filter(repo_id=repoId)
        eventLabelList=[]
        hanlpUnit=HanlpUnit()

        for i in retTriggerWordList:
            tmpLableList=[]
            ruleId=1
            retTriggerWordDict = model_to_dict(i)
            triggerId = retTriggerWordDict['id']
            eventId = retTriggerWordDict['event_rule_id']
            #触发词名字和触发词标注

            triggerWord = retTriggerWordDict['trigger_word']
            triggerWordId =self.get_category_name(request,triggerWord)

            eventRule = TEventRule.objects.get(id=eventId, repo_id=repoId)
            eventRuleDict = model_to_dict(eventRule)
            eventCategoryId = eventRuleDict['category_id']
            eventCategory=TCategory.objects.get(id=eventCategoryId,repo_id=repoId,create_id=createId)
            eventCategoryDict = model_to_dict(eventCategory)
            eventCategoryName = eventCategoryDict['category_name']
            tmpLableList.append(eventCategoryName)
            #事件类目

            subjectCategoryId = eventRuleDict['event_subject_id']
            subjectCategory = TCategory.objects.get(id=subjectCategoryId, repo_id=repoId, create_id=createId)
            subjectCategoryDict = model_to_dict(subjectCategory)
            subjectCategoryName = subjectCategoryDict['category_name']
            subjectId=self.get_category_name(request,subjectCategoryName)
            tmpLableList.append(subjectId)
            retListId,retListVal = some_data_deal_func().inputCategoryIdReturnName(subjectCategoryId,repoId,createId)
            #对于retListVal里面的所有的值都把他们加入到分词器中然后进行分词
            #构造wordList word 和mask 对应
            constructWordList=[]
            tmpSet=hanlpUnit.added_word_list

            for word in retListVal:
                tmpDict={}
                tmpDict['word'] =word
                #item["word"], item["mask"]
                tmpDict['mask'] = subjectId
                constructWordList.append(tmpDict)

            #这边这个要加入list[{'word':123,mask:13}]
            hanlpUnit.add_word_list(constructWordList)
            #print(constructWordList)
            objectCategoryId = eventRuleDict['event_object_id']
            negativeOne = -1
            if (objectCategoryId == negativeOne):
                ruleId = 2

            constructWordList = []
            tmpDict={}
            tmpDict['word']=triggerWord
            tmpDict['mask']=str(triggerWordId)
            tmpSet = hanlpUnit.added_word_list
            constructWordList.append(tmpDict)
            hanlpUnit.add_word_list(constructWordList)
            tmpLableList.append(str(triggerWordId))

            if( ruleId== 1):
                objectCategoryId = eventRuleDict['event_object_id']
                objectCategory = TCategory.objects.get(id=objectCategoryId, repo_id=repoId, create_id=createId)
                objectCategoryDict = model_to_dict(objectCategory)
                objectCategoryName = objectCategoryDict['category_name']
                objectId = self.get_category_name(request,objectCategoryName)
                retListId, retListVal = some_data_deal_func().inputCategoryIdReturnName(objectCategoryId, repoId,
                                                                            createId)
                tmpLableList.append(objectId)
                constructWordList = []
                tmpSet = hanlpUnit.added_word_list
                #这个代码有变动需要改一下
                for word in retListVal:
                    tmpDict = {}
                    tmpDict['word'] = word
                    # item["word"], item["mask"]
                    tmpDict['mask'] = str(objectId)
                    constructWordList.append(tmpDict)
                # 这边这个要加入list[{'word':123,mask:13}]
                #print(constructWordList)
                hanlpUnit.add_word_list(constructWordList)

            eventLabelList.append(tmpLableList)
        print(eventLabelList)
        print("list里面内容")
        tmpS=hanlpUnit.added_word_list
        for name in tmpS:
            print(name)
        print("list里面内容结束")

        #name
        attribute = TAttribute.objects.get(category_id=1)
        attributeDict = model_to_dict(attribute)
        attributeName = attributeDict['attribute_name']

        for i in ret_entity_map:
            _id = i['_id']
            value=i['value']
            basetime = str(value['时间'])
            content = value['内容']
            text = HanlpUnit().get_text_from_html(content)
            sentenceList=some_data_deal_func().cut_sent(text)
            #print(sentenceList)
            for sent in sentenceList:
                sent=sent.strip()
                print(sent)
                #对每一个sent进行分词获取他们的事件
                #11111
                sent="浙江杭州明天林更新出演的动作喜剧《快手枪手快枪手》"
                event = some_data_deal_func().eventExtractionByTemplateMatching(request,hanlpUnit,sent,eventLabelList,repoId,createId)
                #事件抽取完成
                #dateTime还要调整一下basetime会出问题
                print(basetime)
                dateTime = Time_deal().deal_time(sent, basetime)
                print(dateTime)
                locationList = Time_deal().deal_area(sent);
                location = ''
                for val in locationList:
                    if(len(val) > len(location)):
                        location = val
                print(location)
                #这三个的名字需要和事件一起返回
                for eve in event:
                    ruleId = 1
                    if(len(eve) == 3):
                        ruleId =2
                    eveId = eve[0]
                    subjectLabel = eventLabelList[eveId][1]
                    triggerLabel = eventLabelList[eveId][2]

                    attribute = {}
                    attribute['time'] = dateTime
                    attribute['place'] = location
                    eveString = ''

                    for j in range(1,len(eve),1):
                        eveString = eveString + str(eve[j])
                    attribute['event'] = eveString
                    #eventlabel要通过查询结果得到
                    eventLabel =  self.get_category_name(request,eventLabelList[eveId][0])
                    print(eventLabel)
                    print(eventLabelList[eveId])
                    print(event)
                    subjectLabel = eventLabelList[eveId][1]


                    Neo4j().create_node_mjy_edition(eventLabel, attribute)
                    subjectNameVal = eve[1]
                    # print(subjectCategoryName,attributeName,subjectNameVal)
                    neo4jSubjectId = Neo4j().quesIdByLabelAttribute(subjectLabel, attributeName, subjectNameVal)
                    neo4jEventId = Neo4j().quesIdByLabelAttribute(eventLabel, 'event', eveString)
                    Neo4j().createRelationship(subjectLabel,eventLabel,"主谓关系",{'id':neo4jSubjectId},{'id':neo4jEventId})
                    if (ruleId == 1):
                        objectNameVal = eve[3]
                        objectLabel = eventLabelList[eveId][3]
                        neo4jObjectId = Neo4j().quesIdByLabelAttribute(objectLabel, attributeName, objectNameVal)
                        Neo4j().createRelationship(eventLabel, objectLabel, "动宾关系", {'id':neo4jEventId}, {'id':neo4jObjectId})
                        print(neo4jSubjectId,neo4jEventId,neo4jObjectId)
            cnt+=1
            if(cnt>=2):
                break
        returnExtractContent = {}
        return render(request, 'test.html', context=returnExtractContent)


    def knowledge_definition1(self, request):
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
        ret_l['first_tree'] = some_data_deal_func().find_children(repo_id,create_id,1)
        ret_l['second_tree'] = some_data_deal_func().find_children(repo_id,create_id,2)
        return render(request, 'index/knowledge_definition.html', context=self.get_base_info(request, ret_l))

    # 输入repo_id返回类目树level1_child :{ id ,category,attribute,level_2child{ id, }}
    # 这边事物的attribute要返回其他的不用
    def knowledge_definition(self, request):
        """
        属性信息中落掉了属性别名，需要去别名表里去
        :param request:
        :return:
        """
        try:
            #repo_id = request.session['repo_id']
            a=1
        except Exception:
            return self.error("没有得到repo_id")
        try:
            #create_id = request.session['user_id']
            a=1
        except Exception:
            return self.error("没有得到create_id")
        repo_id = 1
        user = 1
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
            tmp_attribute_alias = ''
            tmp_attribute_id = ret_result['id']
            ret_attribute_alias = TAttrbuteAlias.objects.filter(attribute_id=tmp_attribute_id, create_id=create_id)
            num = 0
            for val in ret_attribute_alias:
                val_dict = model_to_dict(val)
                if (num != 0):
                    tmp_attribute_alias += ','
                tmp_attribute_alias += val_dict['attribute_alias']
                num += 1
            ret_result['attribute_alias'] = tmp_attribute_alias
            tmp_list_attribute.append(ret_result)

        test['id'] = tmp_id
        test['category'] = {'category_description': tmp_description, 'attribute': tmp_list_attribute}
        test['level2_child'] = tmp_list_2
        print(test)

        return render(request, 'test.html', context=test)
        #return render(request, 'index/knowledge_definition.html', context=self.get_base_info(request, test))
    #从mongodb中返回对应文件id的所有数据
    def return_data_from_mongodb(self,request):

        try:
            repo_id = request.session['repo_id']
            #repo_id=1
        except Exception:
            return self.error('没有知识库id')
        try:
            file_id = request.POST['file_id']
            #file_id  = 1
        except Exception:
            return self.error('没有文件id')
        tmp_info = {'file_id': file_id}
        try:
            news_col = Mongodb(db='knowledge', collection='text').get_collection()
        except Exception:
            return self.error("mongodb没有数据库或者表")

        ret_entity_map = news_col.find(tmp_info)
        ret_list = []
        for val in ret_entity_map:
            ret_list.append(val)
        category_name_list = []
        ret_category = TCategory.objects.filter(repo_id=repo_id);
        for val in ret_category:
            val_dict = model_to_dict(val)
            category_name_list.append(val_dict['category_name'])

        ret_l = {'category_name': category_name_list, 'context': ret_list}
        print(ret_l)
        return render(request, 'test.html', context=ret_l)

    #点击确认键 输入是entity_id(实体id)和类目id(category_id)
    def save_mongodb_data_to_neo4j(self,request):
        try:
            #entity_id  = request.POST['entity_id']
            entity_id = ObjectId("5eb52fc9d03fe5b0f31b6f40")
        except Exception:
            return self.error("没有收到entity_id")
        try:
            #category_id = request.POST['category_id']
            category_id=1
        except Exception:
            return self.error("没有收到category_id")

        try:
            news_col = Mongodb(db='knowledge', collection='text').get_collection()
        except Exception:
            return self.error("mongodb没有数据库或者表")
        category_val =  TCategory.objects.get(id=category_id)
        category_val_dict = model_to_dict(category_val)
        category_name = category_val_dict['category_name']
        tmp_data={'_id':entity_id}
        ret_entity  = news_col.find(tmp_data)
        for val in ret_entity:
            print(category_name,val,1)
            Neo4j().create_node_mjy_edition(category_name,val)


        ret_l = {}
        return render(request, 'test.html', context=ret_l)

    #输入是repo_id  返回t_normalize_rule表中的数据
    def  ret_t_normalize_rule_data(self,request):
        #repo_id = request.session['category_id']
        repo_id = 1
        ret_date_from_t_normalize_rule =TNormalizedRule.objects.filter(repo_id=repo_id)
        ret_list = []
        cnt = 1
        for val in ret_date_from_t_normalize_rule:
            val_dict = model_to_dict(val)
            category_id = val_dict['category_id']
            tmp_dict = {}
            tmp_dict['id']=cnt
            tmp_dict['rule_number']=val_dict['rule_number']
            tmp_dict['update_time'] = str(val_dict['update_time'])
            tmp_dict['overall_threshold'] = val_dict['overall_threshold']
            category_ques = TCategory.objects.get(id=category_id)
            category_ques_dict = model_to_dict(category_ques)
            tmp_dict['category_name'] = category_ques_dict['category_name']
            cnt+=1
            ret_list.append(tmp_dict)

        ret_l = {}
        ret_l['context']=ret_list
        #print(ret_l)
        return render(request, 'test.html', context=ret_l)

    # 输入是normalized_rule_id 返回t_normalize_rule_detail中内容
    def get_normalize_rule_detail(self, request):
        normalized_rule_id = request.POST['merging_rule_id']
        create_id = request.session['user_id']
        #normalized_rule_id=1
        #create_id=1
        #查询到category_id
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
            #attribute_id = val_dict['attribute_id']
            tmp_dict['attribute_id']=val_dict['attribute_id']
            #attribute = TAttribute.objects.get(id=attribute_id)
            #attribute_dict = model_to_dict(attribute)
            #tmp_dict['attribute_name'] = attribute_dict['attribute_name']
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
        ret_l['attribute']=ret_attribute_list
        print(ret_l)
        return self.success(ret_l)

    #输入一些详细的规则 实体归一规则详细 如果id是-1那么添加数据  如果不是-1那么更新数据库 然后更新归一规则表
    #
    def add_update_normalized_rule_detail(self,request):
        #overall_threshold = request.POST['overall_threshold']
        #normalized_rule_id = request.POST['rule_id']
        #normalized_rule_detail_list=request.POST.get('rule_list')
        #create_id = request.session['create_id']
        #category_id = request.session['category_id']
        #repo_id = request.session['repo_id']
        overall_threshold=1
        normalized_rule_id=1
        normalized_rule_detail_list=[{'id':1,'attribute_id':1,'similarity_threshold':0.5},{'id':2,'attribute_id':2,'similarity_threshold':0.5}]
        create_id=1
        category_id=1
        repo_id=1
        num = 0
        key_attribute_list = []
        key_attribute_list_similarity_threshold=[]
        for val in normalized_rule_detail_list:
            type = val['id']
            dt = datetime.now()
            # 通过val['attribute_id']得到attribute_name
            ret_attribute = TAttribute.objects.get(id=val['attribute_id'])
            ret_attribute_dict = model_to_dict(ret_attribute)
            key_attribute_list.append(ret_attribute_dict['attribute_name'])
            key_attribute_list_similarity_threshold.append(val['similarity_threshold'])

            if -1 == type:
                TNormalizedRuleDetail.objects.create(normalized_rule_id=normalized_rule_id,attribute_id=val['attribute_id'],similarity_threshold=val['similarity_threshold'],update_time=dt,create_id=create_id)
            else:
                obj = TNormalizedRuleDetail.objects.get(id=type)
                obj.normalized_rule_id=normalized_rule_id
                obj.attribute_id=val['attribute_id']
                obj.similarity_threshold=val['similarity_threshold']
                obj.update_time=dt
                obj.create_id=create_id
                obj.save()
            num+=1
        obj = TNormalizedRule.objects.get(id=normalized_rule_id,category_id=category_id,repo_id=repo_id)
        obj.rule_number=num
        obj.update_time = datetime.now()
        obj.overall_threshold=overall_threshold
        obj.save()

        #进行同名实体  有类目名字 把所有的数据都拿出来 然后比较名字是否相同
        #把id和名字拿出 然后n^2去找一样的
        #找到以后相似度计算 可以用文本的那个
        category_val = TCategory.objects.get(id=category_id)
        category_val_dict = model_to_dict(category_val)
        category_name = category_val_dict['category_name']
        #获得到名字的那个属性名 就是category_id为1的那个属性
        attribute_val = TAttribute.objects.get(category_id=1)
        attribute_val_dict = model_to_dict(attribute_val)
        attribute_name = attribute_val_dict['attribute_name']
        #进行neo4j的查询

        ret_list_id,ret_list_val = Neo4j().ques_id_val(category_name,attribute_name)
        vis=[0  for i in range(0,100)]
        ret_list_id_len = len(ret_list_id)
        for i in range(0,ret_list_id_len):
            if vis[i] ==0:
                for j in range(i+1,ret_list_id_len):
                    if vis[j]!=0:
                        continue
                    if ret_list_val[i]==ret_list_val[j]:
                        #先写一个neo4j中的处理 把里面关键属性的名字和值拿出来
                        attribute_name_one,attribute_val_one = Neo4j().find_key_value(category_name,ret_list_id[i],key_attribute_list)
                        attribute_name_two,attribute_val_two = Neo4j().find_key_value(category_name,ret_list_id[j],key_attribute_list)
                        #这边传入的是2个neo4j中的map 把他们关键属性拿出来就好了
                        #直接计算val_one和val_two他们之间的相似度就好了
                        similarity= some_data_deal_func().calculate_similarity(attribute_val_one, attribute_val_two,key_attribute_list_similarity_threshold)
                        print(similarity)
                        if similarity >=   overall_threshold:
                            #大于这个阈值可以写入到数据库日志里面这边还没想好
                            a=1
        ret_l = {}
        ret_l['context']='success'
        return render(request, 'test.html', context=ret_l)

    # 返回这个知识库所有category和id
    # 第一个类目的所有节点每个节点返回加点名字和id
    def show_entity(self, request):
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
        return render(request, "test.html", context={"data": ret_l})


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
        return render(request, "test.html", context={"data": ret_l})

    #输入是实体id 返回这个实体的所有信息
    def ret_entity_all_info(self,request):
        try:
            #entity_id = request.POST['entity_id']
            entity_id = '5ebf9026a3a203e4bc0b66c0'
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
        return render(request, "test.html", context=ret_l)

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
        print(ret_l)
        return render(request, "test.html", context=ret_l)

    # 根据类目ID获取映射规则
    #返回自己还有所有父亲节点的属性
    def get_map_rule(self, request):
        create_id = request.session["user_id"]
        #create_id = 1
        category_id = request.POST["category_id"]
        #category_id = 1

        ret_l = {}
        att_list = []
        father_category_id = TCategory.objects.get(id=category_id).father_category_id
        #print(father_category_id,type(father_category_id))
        att_list = some_data_deal_func().input_category_id_return_attribute_list(category_id,att_list)

        if(str(-1) != father_category_id):

            father_father_category_id = TCategory.objects.get(id=father_category_id).father_category_id
            att_list = some_data_deal_func().input_category_id_return_attribute_list(father_category_id, att_list)

            if(str(-1) != father_father_category_id):
                att_list = some_data_deal_func().input_category_id_return_attribute_list(father_father_category_id, att_list)
            #python {} 默认不排序 按顺序输入 就和List一样


        ret_l['attribute'] = att_list
        #father

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
        #return render(request, "test.html", context=ret_l)

    #返回所有的类目 第一个用户定义的类目的属性以及他的父亲节点的属性
    def map_rule(self, request):

        repo_id = request.session["repo_id"]
        create_id = request.session["user_id"]
        #repo_id = 1
        #create_id = 1
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
        #这边可能会有一个Bug
        #基本是返回第一个自己定义的数据
        #这边先默认变成1 事物好了
        cate_id = 1
        if( len(cate_list) > 1):
            cate_id = cate_list[1]["id"]

        # for val in cate_list:
        #     cate_id = val['id']
        print(cate_id)
        att_list=some_data_deal_func().input_category_id_return_attribute_list(cate_id,att_list)
        father_category_id  =TCategory.objects.get(id=cate_id).father_category_id
        if(str(-1) != father_category_id):
            father_father_category_id = TCategory.objects.get(id=father_category_id).father_category_id
            att_list = some_data_deal_func().input_category_id_return_attribute_list(father_category_id, att_list)

            if(str(-1) != father_father_category_id):
                att_list = some_data_deal_func().input_category_id_return_attribute_list(father_father_category_id, att_list)


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
        #return render(request,"test.html",context=ret_l)
        return render(request, "index/map_rule.html", context=self.get_base_info(request, ret_l))


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
            tmp_map['create_time'] = str(val_dict['create_time'])
            tmp_map['data_source'] = val_dict['data_source']
            tmp_map['data_access'] = val_dict['data_access']
            log_list.append(tmp_map)
        ret_l = {'context': log_list}
        print(ret_l)
        return render(request, "test.html", context={"data": ret_l})

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
        print(ret_l)
        return render(request, "test.html", context={"data": ret_l})

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
        print(ret_l)
        return render(request, "test.html", context={"data": ret_l})

        # 把文件中的内容存入到mongodb 然后更新2个表 计算最近category 更新neo4j
    def knowledge_extract(self, request):
        # 新建类目表
        # 数据的话从文件里面读出
        log_id = request.POST['log_id']
        repo_id = request.session['repo_id']
        create_id = request.session['user_id']
        news_col = Mongodb(db='knowledge', collection='text').get_collection()

        file_id = TEntityExtractionLog.objects.get(id=log_id).data_acquisition_id
        try:
            ret_file_data = TDataAcquisitionLog.objects.get(id=file_id)
        except Exception:
            return self.error("id没有对应文件")

        ret_file_data_dict = model_to_dict(ret_file_data)

        try:
            data = xlrd.open_workbook(ret_file_data_dict['data_path'])
        except Exception:
            return self.error("没有找到对应文件")

        table_name = data.sheet_names()[0]
        table = data.sheet_by_name(table_name)
        list_attribute = list(table.row_values(0))
        list_json = []
        row = table.nrows
        col = table.ncols
        dt = datetime.now()
        entity_number =table.nrows - 1
        is_extract = 0
        obj=TEntityExtractionLog.objects.get(data_acquisition_id=file_id)
        obj.is_extract = is_extract
        obj.entity_number  =  entity_number
        obj.extract_time = str(dt)[:19]
        obj.save();

        #这边还要计算这个的类目
        list_attribute = list(table.row_values(0))
        category_id = some_data_deal_func().calculate_nearest_category(list_attribute,repo_id)
        return_category_name=''
        if(category_id!=-1):
            return_category_name = TCategory.objects.get(id=category_id).category_name
        print("相似的category",return_category_name)

        for i in range(1, row):
            dict_data = {}
            for j in range(0, col):
                dict_data[list_attribute[j]] = table.row_values(i)[j]
                #print(list_attribute[j],table.row_values(i)[j])
            dict_data['file_id'] = file_id
            dict_data['category_id'] = category_id
            x = news_col.insert_one(dict_data)
            #print(dict_data)

            #这个insert_one好像会自动帮你的字典里加_id
            #这边如果category_!=-1
            if(category_id!=-1):
                Neo4j().create_node_mjy_edition(return_category_name , dict_data)
        #所有数据插入完了以后可以更新这个表
        some_data_deal_func().update_t_mapping_rule(repo_id,create_id)

        return self.success("抽取成功！")

    #点击确认后 输入_id和类目id 然后我要更新mongodb中的这个类目的id 和neo4j中的数据
    def confirm_update_mongodb_neo4j(self,request):

        #repo_id = request.session['repo_id']
        repo_id=1
        #create_id = request.session['user_id']
        create_id=1
        some_data_deal_func().update_t_mapping_rule(repo_id, create_id)
        neo4j_entity_id = request.POST['entity_id']
        mongodb_entity_id = ObjectId(neo4j_entity_id)
        #neo4j_entity_id = '5ec1dd47d2cbe96d835db79b'
        #mongodb_entity_id = ObjectId("5ec1dd47d2cbe96d835db79b")
        category_id = request.POST['category_id']
        #category_id=-1
        #category_id = 3
        #更新Mongodb
        news_col = Mongodb(db='knowledge', collection='text').get_collection()
        #这边要找到原来那个category_id
        try:
            last_category_id = news_col.find_one({"_id":mongodb_entity_id})['category_id']
        except Exception:
            return self.error("mongodb里面没有这个id对应的实体")
        print(last_category_id)
        try:
            news_col.update_one({'_id':mongodb_entity_id},{"$set":{'category_id':category_id}})
        except Exception:
            return self.error("mongodb中没有这个实体id")

        if(last_category_id!=-1):
            #前面已经插入到数据库假如说不是-1那么酒正常写入
            if(-1!=category_id):
                last_category_name  = TCategory.objects.get(id=last_category_id).category_name
                category_name = TCategory.objects.get(id=category_id).category_name
                Neo4j().update_one_node_label(last_category_name,'_id',neo4j_entity_id,category_name)
            else:
                #删除这个节点的数据
                print("删除")
                last_category_name = TCategory.objects.get(id=last_category_id).category_name
                Neo4j().delete_one_node(last_category_name,neo4j_entity_id)
        else:
            #这边要从mongodb里面插入到数据库
            ret =  news_col.find_one({"_id":mongodb_entity_id})
            #print(ret)
            category_name = TCategory.objects.get(id=category_id).category_name
            Neo4j().create_node_mjy_edition(category_name,ret)

        #这边完了可以更新表
        some_data_deal_func().update_t_mapping_rule(repo_id, create_id)
        return self.success("修改成功！")


    def return_excel_html(self, request):

        # 通过pandas.ExcelFie函数，将excel文件转成html
        path_obj = "D:\\\\upload\\t_log.xlsx"
        p = path_obj.split('\\')
        name=p[3]
        new_file_name = "D:\\\\upload\\" + name + '.html'
        #new_file_name = "C:\\Users\\cherryMJY\\PycharmProjects\\knowledge_map_system2.0\\templates" + name+'.html'
        print(new_file_name)
        xd = pandas.ExcelFile(path_obj)
        df = xd.parse()
        html = df.to_html(header=True, index=True)
        # 将转换后的html写入，一定要加编码方式utf-8，要不页面中打开会乱码
        with open(new_file_name, 'w', encoding='utf-8') as file:
            file.writelines('<meta charset="UTF-8">\n')
            file.write(html)

        ret_l={}
        return render(request, "test.html", context={"data": ret_l})

    #返回抽取结果
    def extract_result(self, request):
        repo_id = request.session['repo_id']
        #repo_id =1
        file_id = request.GET['file_id']
        #file_id=1
        tmp_info = {'fil知识图谱的应用e_id': file_id}
        try:
            news_col = Mongodb(db='knowledge', collection='text').get_collection()
        except Exception:
            return self.error("mongodb没有数据库或者表")

        ret_entity_map = news_col.find(tmp_info)
        ret_list = []
        for val in ret_entity_map:
            del val["file_id"]
            ret_list.append(val)
        category_name_list = []
        ret_category = TCategory.objects.filter(repo_id=repo_id)
        for val in ret_category:
            val_dict = model_to_dict(val)
            tmp_map = {}
            tmp_map['category_name']=val_dict['category_name']
            tmp_map['category_id']  =val_dict['id']
            category_name_list.append(tmp_map)

        ret_l = {'category': category_name_list, 'context': ret_list}
        print(ret_l)
        #return self.success("成功")
        return render(request, 'index/extract_result.html', context=self.get_base_info(request, ret_l))

    # 返回四个日志表里面的内容要求一个方法
    # t_normalized_log
    # t_entity_extraction_log
    # ret_t_data_acquisition_log
    # t_attribute_map_log

    # 返回四个日志表里面的内容要求一个方法
    # t_normalized_log
    # t_entity_extraction_log
    # t_cleaning_log
    # t_attribute_map_log
    def build_map(self, request):
        repo_id = request.session['repo_id']
        #repo_id =1
        create_id = request.session['user_id']
        #create_id=1
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
            #id
            #entity_id
            #cleaning_rule_id
            #cleaning_content
            #cleaning_result
            #category_id

            tmp_map['id'] = val_dict['id']
            tmp_map['entity_id'] = val_dict['entity_id']
            #tmp_map['cleaning_rule_id'] = val_dict['cleaning_rule_id']
            cleaning_rule_id = val_dict['cleaning_rule_id']
            cleaning_rule = TCleaningRule.objects.get(id=cleaning_rule_id)
            cleaning_rule_dict =model_to_dict(cleaning_rule)
            attribute_id = cleaning_rule_dict['attribute_id']
            return_attribute = TAttribute.objects.get(id=attribute_id)
            return_attribute_dict = model_to_dict(return_attribute)
            tmp_map['attribute_name'] =return_attribute_dict['attribute_name']
            tmp_map['attribute_datatype'] = return_attribute_dict['attribute_datatype']
            tmp_map['cleaning_content'] = val_dict['cleaning_content']
            tmp_map['cleaning_result'] = val_dict['cleaning_result']
            category_id=val_dict['category_id']
            ret_category = TCategory.objects.get(id=category_id)
            ret_category_dict = model_to_dict(ret_category)
            tmp_map['category_name'] = ret_category_dict['category_name']
            log_list.append(tmp_map)

        ret_list.setdefault('t_cleaning_log', log_list)

        ret_log = TEntityExtractionLog.objects.filter(repo_id=repo_id, create_id=create_id)
        log_list = []
        for val in ret_log:
            val_dict = model_to_dict(val)
            tmp_map = {}
            tmp_map['id'] = val_dict['id']
            tmp_map['data_source'] = val_dict['data_source']
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
        #return render(request,"test.html",ret_list)
        return render(request, 'index/build_map.html', self.get_base_info(request, ret_list))


    #返回t_cleaning_rule中的内容
    def cleaning_rule(self, request):
        #repo_id = request.session["repo_id"]
        repo_id =1
        #create_id = request.session["user_id"]
        create_id =1
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
            cate_dict['crate_time']=str(cate_dict['crate_time'])[:19]
            cate_dict['attribute'] = res_attribute_dict
            cate_list.append(cate_dict)
        ret_l['cleaning_rule'] = cate_list
        print(ret_l)
        #return render(request, "index/cleaning_rule.html", context=ret_l)
        return render(request, "test.html", context=ret_l)


    def event_extraction(self,request):
        #event_nostruct = '12.11.9杭州,我是一头猪浙江绍兴,曾今来自诸暨杭州,杭州,我是一头猪浙江绍兴,曾今来自诸暨杭州,杭州,我是一头猪浙江绍兴,曾今来自诸暨杭州,杭州,我是一头猪浙江绍兴,曾今来自诸暨杭州,杭州,我是一头猪浙江绍兴,曾今来自诸暨杭州,杭州,我是一头猪浙江绍兴,曾今来自诸暨杭州,'
        news_col = Mongodb(db='movies', collection='useful_sentence_detail').get_collection()
        all_data = news_col.find()
        cnt = 1
        sentence_list = []
        for val in all_data:
            print(val)
            cnt +=1
            sentence_list.append(val['sentence'])
            if(cnt >=3):
                break
        destination=open("D:\\data_result\\result.txt", 'a', encoding='UTF-8')
        #destination = open("D:\\data_result\\result.txt", 'wb+')
        for event_nostruct in sentence_list:
            #从mongodb里面读取数据
            date_time=Time_deal().deal_time(event_nostruct)
            location_list= Time_deal().deal_area(event_nostruct);
            #print(date_time,location_list)
            event_li=Time_deal().deal_event(event_nostruct)
            #destination = open(os.path.join(path, file_name), 'wb+')  # 打开特定的文件进行二进制的写操作
            #for chunk in myFile.chunks():  # 分块写入文件
                #destination.write(chunk)
            #print(event_nostruct)
            destination.writelines("原话:"+event_nostruct)
            destination.writelines('\r\n')
            destination.writelines("时间:"+date_time)
            destination.writelines('\r\n')
            destination.writelines("地点:")
            destination.writelines(location_list)
            destination.writelines('\r\n')
            #destination.writelines(" ".join(event_li))
            destination.writelines("事件:")
            for list_one in event_li:
                destination.writelines(list_one)
            destination.writelines('\r\n')
        destination.close()
        ret_l= {}
        return  render(request,"test.html",context =ret_l);


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

        #categoryId = request.POST['categoryId']
        #keyWord = request.POST['keyWord']
        #repoId=request.session['repo_id']
        #createId=request.session['user_id']


        #only for debug
        request.session['repo_id']=1
        request.session['user_id']=1
        categoryId = 4
        keyWord = "孟佳营"
        repoId=1
        createId=1
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
                tmpRelationShip['source']=startId

                tmpDict ={}
                tmpDict['id']=relationShipId
                endId = val['id(m)']

                tmpRelationShip['target'] =endId
                tmpRelationShip['name'] = relationShipType['type(r)']
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
                            print(1111,node)
                            nodeId = node['id(n)']
                            retNode=Neo4j().analysisNode(node['n'])
                            tmpNode = {}
                            #修改event变成
                            #print(retNode)
                            if(retAttributeEventName in retNode.keys()):
                                tmpNode['name']=retNode[retAttributeEventName]
                            else:
                                tmpNode['name'] = nodeId
                            tmpNode['id']=nodeId
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
        print(111,ret_l)
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

    def searchEvent(self,request):
        """
        :param _id: 一个节点的mongodb id
        :return: 排好序的事件node {'event':[{'名字': '孟佳营主演快手枪手快枪手', 'time': 1, 'place': '', '_id': 1}]
                                'category':[{"category_id": 类目id, "category_name": "", "attribute": []}]}
        """
        _id = request.session['_id']
        repoId = request.session['repo_id']
        createId = request.session['user_id']

        #only for debug
        #_id = 444
        #repoId = 1
        #createId = 1
        #only for debug

        retNode = Neo4j().returnNode({'_id':_id})
        nodeLabel = Neo4j().getLabelByid(_id)
        #print(retNode)
        #print(111,nodeLabel)
        #print(nodeLabel['labels(n)'][0])
        ansNode = 1

        #n节点的查询结果变成dict
        #print(type(retNode))
        for val in retNode:
            ansNode=Neo4j().analysisNode(val)
            ansNode=Neo4j().dictToQuesDict(ansNode)
        #查询之前数字不用变 str要变成\' +str+ \'

        endNodeList=Neo4j().getEndNode(nodeLabel['labels(n)'][0],"主谓关系",ansNode)
        nodeList =[]
        categorySet = set()
        endNodeSet=set()
        categoryList=[]
        for val in endNodeList:
            tmpNode = Neo4j().analysisNode(val)
            nodeList.append(tmpNode)
            #tmpNode 是节点 根据节点查询label  set 去同
            #最终节点也要去同
            #print(1111,tmpNode)

            tmpNodeId = tmpNode['_id']
            if(tmpNodeId in endNodeSet):
                continue
            endNodeSet.add(tmpNodeId )
            tmpNodeLabel = Neo4j().getLabelByid(tmpNodeId)
            #print(tmpNodeLabel)
            nodeDict ={}

            nodeCategory=tmpNodeLabel['labels(n)'][0].split('_')[0]
            #print(nodeCategory)
            print(nodeCategory)
            retCategory=TCategory.objects.get(category_name =nodeCategory,repo_id=repoId,create_id=createId)
            retCategoryDict = model_to_dict(retCategory)
            nodeCategoryId = retCategoryDict['id']
            nodeDict['category_id'] = nodeCategoryId
            nodeDict['category_name'] = nodeCategory
            nodeDict['attribute']=[]
            if(nodeCategoryId not in categorySet):
                categorySet.add(nodeCategoryId)
                print(nodeCategoryId)
                print(categorySet)
                #获得attribute
                att_list = []
                father_category_id = TCategory.objects.get(id=nodeCategoryId,repo_id=repoId,create_id=createId).father_category_id
                # print(father_category_id,type(father_category_id))
                att_list = some_data_deal_func().input_category_id_return_attribute_list(nodeCategoryId, att_list)

                if (str(-1) != father_category_id):

                    father_father_category_id = TCategory.objects.get(id=father_category_id,repo_id=repoId,create_id=createId).father_category_id
                    att_list = some_data_deal_func().input_category_id_return_attribute_list(father_category_id,
                                                                                             att_list)

                    if (str(-1) != father_father_category_id):
                        att_list = some_data_deal_func().input_category_id_return_attribute_list(
                            father_father_category_id, att_list)
                nodeDict['attribute'] =att_list
            categoryList.append(nodeDict)
        #print(categoryList)
        #ret_l['attribute'] = att_list
            #Neo4j().getLabelByid(_id)
        #print(nodeList)
        sorted(nodeList, key=functools.cmp_to_key(some_data_deal_func().nodeCmp))
        #for val in retNode:
            #print(val)
        #    id=Neo4j().quesIdByLabelAttribute(nodeLabel['labels(n)'][0],'_id',str(_id))
            #print(id)
        ret_l={'event':nodeList,'category':categoryList}
        print(ret_l)
        return  render(request,"test.html",context =ret_l)


    def acquireGraphInf(self,request):
        """
        :param  id  neo4j中的某个要查询节点的Neo4jId
        :param  category_id 查询的末端节点的category_id
        :param  attributeHorizontalId  横坐标attribute_id
        :param  attributeVerticalId  纵坐标attribute_id
        :return: dict  横的 纵的 数值{'horizontal':[1,2,3],'vertical':[4,5,6]}
        """
        repoId = request.session['repo_id']
        createId = request.session['create_id']
        id  =request.POST['id']
        categoryId = request.POST['category_id']
        attributeHorizontalId = request.POST['attributeHorizontalId']
        attributeVerticalId =request.POST['attributeVerticalId']


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
        attributeDictTrans =Neo4j().dictToQuesDict(attributeDict)
        ret=Neo4j().getEndNode(None,None,attributeDictTrans,labelName)

        #print(ret)
        vertical = []
        horizontal = []

        lowestUnit = 3
        for node in node:
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
        for node in ret:
            nodeId = node['id(m)']
            nodeTrans = Neo4j().analysisNode(node['m'])
            #print(nodeTrans,attributeVerticalName,attributeHorizontalName)

            retHorizontal=nodeTrans[attributeHorizontalName]
            retVertical = nodeTrans[attributeVerticalName]
            #print(retHorizontal)
            num = 0
            try:
                resultNumStr = re.findall("\d+[.]{0,1}\d+", retVertical)[0]
                resultNumFloat = float(resultNumStr)
                num = resultNumFloat
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
        return render(request, "test.html", context=ret_l)

    def view_file_content111(self, request):
        file_id = request.GET["file_id"]
        repoId = request.session['repo_id']
        createId = request.session['create_id']
        #file_id =12
        #repoId = 1
        #createId = 1
        data_access = TDataAcquisitionLog.objects.get(id=file_id, repo_id=repoId, create_id=createId).data_access
        ret_l = []
        if (data_access == "文件"):
            # 文件分词excel 和json
            path_obj = TDataAcquisitionLog.objects.get(id=file_id).data_path
            suffix = path_obj.split('.')[1]
            print(suffix)
            if(suffix == "xlsx"):
                data = xlrd.open_workbook(path_obj)
                table = data.sheets()[0]  # 通过索引顺序获取
                print(table.row_values(1))
                rowlen=table.nrows
                collen=table.ncols
                #0-34  总共35个
                attributeNameList = table.row_values(0)
                print(attributeNameList)
                for i in range(1,rowlen):
                    tmpDict ={}
                    tmpList=table.row_values(i)
                    for j in range(0,collen):
                        tmpDict[attributeNameList[j]] =tmpList[j]
                    ret_l.append(tmpDict)
                #print(ret_l)
                #行数
                #print(table.col_values(1))
                #print(df)
                #for val in df :
                #    print(111,val)
                # 将转换后的html写入，一定要加编码方式utf-8，要不页面中打开会乱码
            elif(suffix == "json"):
                #从文件里面一行一行读
                #print(1231)
                #print(path_obj)
                with open(path_obj, 'r') as fp:
                    for val in fp:
                        #print(l,type(l))
                        tmpDict=ast.literal_eval(val)
                        ret_l.append(tmpDict)

        elif (data_access == "爬虫"):
            #爬虫相关
            tmp_info = {'file_id': file_id, 'user_id': createId, 'repo_id': repoId}
            try:
                news_col = Mongodb(db='knowledge', collection='text').get_collection()
            except Exception:
                return self.error("mongodb没有数据库或者表")
            cnt = 1
            ret_entity_map = news_col.find(tmp_info)
            for val in ret_entity_map:
                ret_l.append(val['val'])
        #return render(request, "test.html", context=ret)
        return render(request, 'index/extract_result.html', context=self.get_base_info(request, ret_l))



    def update_cleaning_rule(self, request):
        #category_id = request.POST['category_id']
        #rule_id = request.POST['rule_id']
        #is_custom = request.POST['is_custom']
        #rule_content = request.POST['rule_content']
        #rule_number = int(request.POST["rule_number"])
        #repo_id = request.session["repo_id"]
        #create_id = request.session["user_id"]

        request.session['repo_id'] = 1
        request.session['user_id'] = 1
        category_id = 2
        rule_id = 2
        # 假如说这个是0 那么就是自定义正则表达式 否则是按固定的
        is_custom = 0
         #rule_number  0 - 6  分别是清洗的 0 - 3 是小数点 4 - 6 是日期 7 是自定义
        rule_content = 123
        repo_id = 1
        create_id = 1
        rule_number = 4

        # 上面都是初始化
        obj = TCleaningRule.objects.get(id=rule_id,create_id=create_id)
        obj.cleaning_rule = rule_content
        obj.is_custom = is_custom
        attribute_id = obj.attribute_id
        obj.save()
        # 进行表的修改
        att = TAttribute.objects.get(id=attribute_id)
        att_dict = model_to_dict(att)
        attribute_name = att_dict['attribute_name']
        res = TCategory.objects.filter(id=category_id,repo_id=repo_id, create_id=create_id)
        all_list = []
        all_list_cate_id = []
        for val in res:
            val_dict = model_to_dict(val)
            category_name = val_dict['category_name']
            categoryLabel  = self.get_category_name(request,category_name)
            all_list.append(categoryLabel)
            all_list_cate_id.append(val_dict['id'])
        print(all_list)
        Neo4j().update_attribute_value(all_list, attribute_name, rule_number, rule_content, create_id,
                                               rule_id, all_list_cate_id, repo_id)
        return self.success("更新成功！")

    def test(self,request):
        file_id = 30
        self.eventExtraction111(request,file_id)

        return self.success("更新成功！")

    def eventExtraction111(self, request, file_id):
        #加入ruleId 1或者2 1的话变成三个 2的话变成两个
        #only for debug
        # request.session['user_id'] = 1
        # request.session['repo_id'] = 1
        # fileId = 13
        # only for debug
        print(111)
        #fileId = request.POST['fileId']
        request.session['repo_id']=1
        request.session['user_id']=1
        repoId = request.session['repo_id']
        createId = request.session['user_id']

        #存到这个file_id 里面
        tmp_info = {'file_id': file_id,'user_id':createId,'repo_id':repoId}
        news_col = Mongodb(db='knowledge', collection='text').get_collection()
        cnt = 1
        ret_entity = news_col.find(tmp_info)
        ret_entity_map = list()
        for item in ret_entity:
            if "内容" in item["value"]:
                ret_entity_map.append(item)
        #print(ret_entity_map)
        if len(ret_entity_map) == 0:
            return

        print("--------------------事件抽取")
        #在这个之前把所有的词语都加进去
        #整个循环都是为了把这个repoId的所有的触发词以及他们的事件主题客体都加入进去
        retTriggerWordList = TTriggerWord.objects.filter(repo_id=repoId)
        eventLabelList=[]
        # hanlpUnit=HanlpUnit()
        for i in retTriggerWordList:
            tmpLableList=[]
            ruleId=1
            retTriggerWordDict = model_to_dict(i)
            triggerId = retTriggerWordDict['id']
            eventId = retTriggerWordDict['event_rule_id']
            #触发词名字和触发词标注

            triggerWord = retTriggerWordDict['trigger_word']
            triggerWordId =BaseController.get_category_name(request, triggerWord)
            print(triggerWordId)
            eventRule = TEventRule.objects.get(id=eventId, repo_id=repoId)
            eventRuleDict = model_to_dict(eventRule)
            eventCategoryId = eventRuleDict['category_id']
            eventCategory = TCategory.objects.get(id=eventCategoryId, repo_id=repoId, create_id=createId)
            eventCategoryDict = model_to_dict(eventCategory)
            eventCategoryName = eventCategoryDict['category_name']
            tmpLableList.append(eventCategoryName)
            print(tmpLableList)
            #事件类目

            subjectCategoryId = eventRuleDict['event_subject_id']
            subjectCategory = TCategory.objects.get(id=subjectCategoryId, repo_id=repoId, create_id=createId)
            subjectCategoryDict = model_to_dict(subjectCategory)
            subjectCategoryName = subjectCategoryDict['category_name']
            subjectId=BaseController.get_category_name(request,subjectCategoryName)
            tmpLableList.append(subjectId)
            print(subjectCategoryId,repoId,createId)
            retListId,retListVal = some_data_deal_func().inputCategoryIdReturnName(subjectCategoryId,repoId,createId)
            #对于retListVal里面的所有的值都把他们加入到分词器中然后进行分词
            #构造wordList word 和mask 对应
            print(retListVal)
            constructWordList=[]
            tmpSet = self.hanlp_tool.added_word_list
            print(retListVal)
            for word in retListVal:
                tmpDict={}
                tmpDict['word'] =word
                #item["word"], item["mask"]
                tmpDict['mask'] = subjectId
                print(tmpDict)
                constructWordList.append(tmpDict)
            print(constructWordList)
            #这边这个要加入list[{'word':123,mask:13}]
            self.hanlp_tool.add_word_list(constructWordList)
            #print(constructWordList)
            objectCategoryId = eventRuleDict['event_object_id']
            negativeOne = -1
            if (objectCategoryId == negativeOne):
                ruleId = 2

            constructWordList = []
            tmpDict={}
            tmpDict['word']=triggerWord
            tmpDict['mask']=str(triggerWordId)
            tmpSet = self.hanlp_tool.added_word_list
            constructWordList.append(tmpDict)
            self.hanlp_tool.add_word_list(constructWordList)
            tmpLableList.append(str(triggerWordId))

            if( ruleId== 1):
                objectCategoryId = eventRuleDict['event_object_id']
                objectCategory = TCategory.objects.get(id=objectCategoryId, repo_id=repoId, create_id=createId)
                objectCategoryDict = model_to_dict(objectCategory)
                objectCategoryName = objectCategoryDict['category_name']
                objectId = BaseController.get_category_name(request, objectCategoryName)
                retListId, retListVal = some_data_deal_func().inputCategoryIdReturnName(objectCategoryId, repoId,
                                                                            createId)
                tmpLableList.append(objectId)
                constructWordList = []
                tmpSet = self.hanlp_tool.added_word_list
                #这个代码有变动需要改一下
                for word in retListVal:
                    tmpDict = {}
                    tmpDict['word'] = word
                    # item["word"], item["mask"]
                    tmpDict['mask'] = str(objectId)
                    constructWordList.append(tmpDict)
                # 这边这个要加入list[{'word':123,mask:13}]
                #print(constructWordList)
                self.hanlp_tool.add_word_list(constructWordList)

            eventLabelList.append(tmpLableList)
        # print(eventLabelList)
        # print("list里面内容")
        # tmpS=self.hanlp_tool.added_word_list
        # for name in tmpS:
        #     print(name)
        # print("list里面内容结束")

        #name
        attribute = TAttribute.objects.get(category_id=1)
        attributeDict = model_to_dict(attribute)
        attributeName = attributeDict['attribute_name']
        print("孟佳营")
        for i in ret_entity_map:
            _id = i['_id']
            #根据这个id放回去就好了
            value = i['value']
            basetime = str(value['时间'])
            content = value['内容']
            text = HanlpUnit().get_text_from_html(content)
            sentenceList = self.hanlp_tool.split_paragraph(text)
            #print(sentenceList)
            #这边把所有的东西都拿出来
            event_extract_result=[]
            count = 0
            #时间 地点 事件主体 事件客体 主体的类目 和客体的类目
            for sent in sentenceList:
                sent = sent.strip()
                print(sent)
                #对每一个sent进行分词获取他们的事件
                #11111
                # sent="浙江杭州明天林更新出演的动作喜剧《快手枪手快枪手》"
                event = self.eventExtractionByTemplateMatching(sent, eventLabelList)
                #事件抽取完成
                #dateTime还要调整一下basetime会出问题
                dateTime = Time_deal().deal_time(sent, basetime)
                locationList = Time_deal().deal_area(sent)
                location = ''
                for val in locationList:
                    if(len(val) > len(location)):
                        location = val
                #这三个的名字需要和事件一起返回

                for eve in event:
                    ruleId = 1
                    if(len(eve) == 3):
                        ruleId =2
                    eveId = eve[0]
                    subjectLabel = eventLabelList[eveId][1]
                    triggerLabel = eventLabelList[eveId][2]

                    attribute = {}
                    attribute['发生时间'] = dateTime
                    attribute['地点'] = location
                    eveString = ''

                    for j in range(1,len(eve),1):
                        eveString = eveString + str(eve[j])
                    attribute['名字'] = eveString
                    #eventlabel要通过查询结果得到
                    eventLabel = BaseController.get_category_name(request, eventLabelList[eveId][0])
                    print(eventLabel)
                    print(eventLabelList[eveId])
                    print(event)
                    subjectLabel = eventLabelList[eveId][1]

                    Neo4j().create_node_mjy_edition(eventLabel, attribute)
                    subjectNameVal = eve[1]
                    # print(subjectCategoryName,attributeName,subjectNameVal)
                    neo4jSubjectId = Neo4j().quesIdByLabelAttribute(subjectLabel, attributeName, subjectNameVal)
                    neo4jEventId = Neo4j().quesIdByLabelAttribute(eventLabel, 'event', eveString)
                    Neo4j().createRelationship(subjectLabel,eventLabel,"主谓关系",{'id':neo4jSubjectId},{'id':neo4jEventId})
                    if (ruleId == 1):
                        objectNameVal = eve[3]
                        objectLabel = eventLabelList[eveId][3]
                        neo4jObjectId = Neo4j().quesIdByLabelAttribute(objectLabel, attributeName, objectNameVal)
                        Neo4j().createRelationship(eventLabel, objectLabel, "动宾关系", {'id':neo4jEventId}, {'id':neo4jObjectId})
                        print(neo4jSubjectId, neo4jEventId, neo4jObjectId)
                    tmpEventDict = {}
                    tmpEventDict['time'] = dateTime
                    tmpEventDict['location'] = location
                    tmpEventDict['eventSubject'] =eve[1]
                    tmpEventDict['eventSubjectLabel']=subjectLabel
                    tmpEventDict['triggerLabel']=triggerLabel
                    tmpEventDict['triggerWord'] = eve[1]
                    if (ruleId == 1):
                        tmpEventDict['eventObject'] = eve[3]
                        objectLabel = eventLabelList[eveId][3]
                        tmpEventDict['eventOubjectLabel'] = objectLabel
                    event_extract_result.append({'['+str(count)+']':tmpEventDict})
                    count +=1
            #插入到mongodb
            news_col.update_one({'_id': _id}, {"$set": {'event_extract_result':event_extract_result }})
            #news_col.insert_one()
            # cnt+=1
            # if(cnt>=2):
            #     break
        return True

    def InsertToMongodb(self,request):
        #数据传输过来就好了
        #(item, index) in newsList
        ret_l={'newsList':[(2,{'title':13,'user':123,'dates':123})]}
        return render(request, 'index.html',ret_l)

    def countCommentNum(self,request):
        #neo4j数据统计完 插入到mongodb里面
        #然后json数据导出插入到ysx里面就好了
        #可以分批次查询
        idLow = 0
        idHei = 2000
        for i in range(1500):
            ret=Neo4j().retNode("comments",idLow,idHei)
            idLow = idHei
            idHei = idLow+2000
            news_col = Mongodb(db='knowledge', collection='comments').get_collection()
            print(1)
            for val in ret:
                node=val['n']
                node=Neo4j().analysisNode(node)
                del node["f_id"]
                news_col.insert_one(node)
            print("插入完成")

        ret_l ={}
        return self.success(ret_l)

    def countCommentNumMongodb(self, request):
        news_col = Mongodb(db='movies', collection='comments').get_collection()


        st=ObjectId("5d980db811647d23bcf24111")
        st="5d980db811647d23bcf24111"
        print(st)
        #some_data_deal_func().calchexadd("5d980db811647d23bcf24111","1")
        idLow = '5d980db811647d23bcf24112'
        idHei = some_data_deal_func().calchexadd(idLow, "1000")
        #ans = news_col.find({'_id':ObjectId(idLow)})
        #ans = news_col.find({"_id": {'$gt': ObjectId(idLow), '$lt': ObjectId(idHei)}})
        #for j in ans:
        #   print(j)
        map = {}

        idLow =  '5d980db811647d23bcf24112'
        #ObjectId("5dbbb64311647d2de85161e4")
        #               1000000000000000000
        cnt = 0
        for i in range(15000):
            ans=news_col.find({"_id" : {'$gt': ObjectId(idLow), '$lt':ObjectId(idHei)} })
            for j in ans:
                #print(j)
                movieName=j['movie_name']
                movieTime=j['time']
                tmpName=movieName+'*'+movieTime
                if(tmpName in map.keys()):
                    map[tmpName]= map[tmpName]+1
                else:
                    map[tmpName] = 1
                cnt+=1
            idLow = idHei
            idHei = some_data_deal_func().calchexadd(idLow, "1000000000000000000")
            #接下来要在这边进行统计
            if(i%100==0):
                print(i)
        print(cnt)
        movieNameSet=set()
        ret=Neo4j().ret_node_list_get_one_category_node_name_id("电影_1_1","名字",1)
        for val in ret:
            tmpName = val['name']
            if(len(tmpName)==0):
                continue
            movieNameSet.add(tmpName)
        news=Mongodb(db='movies', collection='commentscount').get_collection()
        tmpList=[]
        cnt=0
        for key in map.keys():
            tmpDict = {}
            tmpL=key.split('*')
            if(len(tmpL) < 2 ):
                continue
            tmpDict['电影名']=tmpL[0]
            if(tmpL[0]  not in movieNameSet):
                continue
            tmpDict['日期']=tmpL[1]
            tmpDict['评论数']=map[key]
            tmpList.append(tmpDict)
            cnt+=1
        print(cnt)
        news.insert_many(tmpList)
        ret_l = {}
        return self.success(ret_l)

    def acquireGraphInf(self,request):

        repoId = request.session['repo_id']
        createId = request.session['user_id']
        id = request.POST['id']
        categoryId = request.POST['link_category_id']
        attributeHorizontalId = request.POST['abscissa_id']
        attributeVerticalId =request.POST['ordinate_id']
        ret_l=self.acquireGraphInfDetail(request, id, categoryId, attributeHorizontalId, attributeVerticalId)
        print(ret_l)
        return ret_l

    #self.acquireGraphInf(self, request, id, categoryIdOne, attributeHorizontalIdOne, attributeVerticalIdOne)
    def acquireGraphInfDetail(self,request,id,categoryId,attributeHorizontalId,attributeVerticalId):
        """
        :param  id  neo4j中的某个要查询节点的Neo4jId
        :param  category_id 查询的末端节点的category_id
        :param  attributeHorizontalId  横坐标attribute_id
        :param  attributeVerticalId  纵坐标attribute_id
        :return: dict  横的 纵的 数值{'horizontal':[1,2,3],'vertical':[4,5,6]}
        """
        request.session['repo_id']=1
        request.session['user_id']=1
        repoId = request.session['repo_id']
        createId = request.session['user_id']
        #id = request.POST['id']
        #categoryId = request.POST['link_category_id']
        #attributeHorizontalId = request.POST['abscissa_id']
        #attributeVerticalId =request.POST['ordinate_id']


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

        lowestUnit=3
        #0 1  2  3
        #% 1 万 亿

        for node in ret:

            nodeId = node['id(m)']
            nodeTrans = Neo4j().analysisNode(node['m'])
            retVertical = nodeTrans[attributeVerticalName]
            #print(retVertical)
            tmpUnit = 3
            if(retVertical.find("%")!=-1):
                tmpUnit = 0
            elif(retVertical.find("亿")!=-1 ):
                tmpUnit = 3
            elif(retVertical.find("万")!=-1 ):
                tmpUnit = 2
            else:
                tmpUnit = 1
            if(tmpUnit < lowestUnit):
                lowestUnit = tmpUnit
        #print(lowestUnit)
        ret = Neo4j().getEndNode(attribute=attributeDict, category_name=labelName)
        for node in ret:
            #print(111111)
            nodeId = node['id(m)']
            nodeTrans = Neo4j().analysisNode(node['m'])
            #print(nodeTrans,attributeVerticalName,attributeHorizontalName)
            retHorizontal=nodeTrans[attributeHorizontalName]
            retVertical = nodeTrans[attributeVerticalName]
            #print(retVertical)
            num = 0
            try:
                num= float(re.search("\d+(\.\d+)?", retVertical).group())
                if(retVertical.find("万") != -1):
                    if(lowestUnit == 1):
                        num = num * 10000
                if (retVertical.find("亿") != -1):
                    if(lowestUnit == 1):
                        num = num * 100000000
                    elif(lowestUnit == 2):
                        num = num * 10000
                if (retVertical.find("%") != -1):
                    num = num /100
            except:
                num = 0
            #print(retVertical,resultNumFloat)
            #print(num)
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
        return ret_l;

    #票房和评论数目
    def acquireGraphInfOneAbscissaTwoOrdinates(self,request):
        """
        :param  id  neo4j中的某个要查询节点的Neo4jId
        :param  category_id 查询的末端节点的category_id
        :param  attributeHorizontalId  横坐标attribute_id
        :param  attributeVerticalId  纵坐标attribute_id
        :return: dict  横的 纵的 数值{'horizontal':[1,2,3],'vertical':[4,5,6]}
        """
        request.session['repo_id']=1
        request.session['user_id']=1
        repoId = request.session['repo_id']
        createId = request.session['user_id']
        #id = request.POST['id']
        #categoryId = request.POST['link_category_id']
        #categoryId = request.POST['link_category_id']
        #attributeHorizontalId = request.POST['abscissa_id']
        #attributeVerticalIdOne =request.POST['ordinate_id_one']
        #attributeVerticalIdTow = request.POST['ordinate_id_tow']
        #match(m:`票房_1_1`) where m.电影名='恋人絮语'  return m
        #match(n:电影_1_1)-[r]-(m:`票房_1_1`) where m.电影名='恋人絮语'  return m
        id = str(2998899)
        categoryIdOne =16
        categoryIdTwo =34
        #先票房
        #后评论
        attributeHorizontalIdOne = 15
        attributeHorizontalIdTwo = 41
        attributeVerticalIdOne =14
        attributeVerticalIdTow = 40
        self.acquireGraphInfDetail(request, id, categoryIdOne, attributeHorizontalIdOne, attributeVerticalIdOne)
        self.acquireGraphInfDetail(request, id, categoryIdTwo, attributeHorizontalIdTwo, attributeVerticalIdTow)
        ret_l = {}
        return self.success(ret_l)

    #把句子和关系抽取事件抽取的结果拿出来然后对句子进行标注
    #/ /

    # {
    #     "_id": ObjectId("5edb57f53fa8cd40781e7adf"),
    #     "file_id": 6,
    #     "category_id": 13,
    #     "spider_id": 3,
    #     "user_id": 1,
    #     "repo_id": 1,
    #     "value": {
    #         "标题": "导演刘杰有意拍摄《青春派》续集\n最近突然有了新想法 想讲述大学里的故事",
    #         "时间": "2020-06-02 09:31:49",
    #         "来源": "Mtime时光网",
    #         "内容": "<i class=\"icon_note \"></i>刘杰透露，他原本没有计划拍摄《青春派》的续集，但最近突然有了新的想法。<div><img src=\"http://img5.mtime.cn/CMS/News/2020/06/02/094150.48749802_620X620.jpg\"><br><br></div>&nbsp; &nbsp; &nbsp; <b>时光网讯</b> 日前，<a href=\"http://movie.mtime.com/201620/\" target=\"_blank\" class=\"tagnews\" method=\"movieidcard\" movieid=\"201620\">《青春派》</a>导演<a href=\"http://people.mtime.com/1250931/\" target=\"_blank\" class=\"tagnews\" method=\"personidcard\" personid=\"1250931\">刘杰</a>在直播时透露，他有意拍摄《青春派》的续集，续集不会继续聚焦高中生活，而是讲述大学里的故事。<div><br></div><div>&nbsp; &nbsp; &nbsp; 刘杰透露，他原本没有计划拍摄《青春派》的续集，但最近突然有了新的想法。“在我印象中，大学里有一半人学习，一半人不学习。基本就是放羊了、解放了。”</div><div><br></div><div>&nbsp; &nbsp; &nbsp; 《青春派》2013年上映，<a href=\"http://people.mtime.com/2047035/\" target=\"_blank\" class=\"tagnews\" method=\"personidcard\" personid=\"2047035\">董子健</a>、<a href=\"http://people.mtime.com/956797/\" target=\"_blank\" class=\"tagnews\" method=\"personidcard\" personid=\"956797\">秦海璐</a>等主演，讲述了一群90后青少年的青春生活：男主角居然（董子健饰）向女神表白遭母亲棒打鸳鸯，高考落榜被嘲笑，在失恋和身体伤痛的双重打击下居然为了能挽救恋情决定复读。当他重新踏上青春路，遇到了一群同样问题多多的同龄人。</div>",
    #         "作者": "羊羊",
    #         "crawl_from": "http://news.mtime.com/2020/06/02/1602610.html",
    #         "crwal_time": "2020-06-06 16:14:11"
    #     },
    #     "relationship_extract_result": [
    #         {
    #             "object_from_category": "演员_1_1",
    #             "object_to_category": "电影_1_1",
    #             "object_from_name": "董子健",
    #             "object_relationship_name": "主演",
    #             "object_to_name": "青少年"
    #         },
    #         {
    #             "object_from_category": "演员_1_1",
    #             "object_to_category": "电影_1_1",
    #             "object_from_name": "董子健",
    #             "object_relationship_name": "主演",
    #             "object_to_name": "青春"
    #         },
    #         {
    #             "object_from_category": "演员_1_1",
    #             "object_to_category": "电影_1_1",
    #             "object_from_name": "董子健",
    #             "object_relationship_name": "主演",
    #             "object_to_name": "母亲"
    #         },
    #         {
    #             "object_from_category": "演员_1_1",
    #             "object_to_category": "电影_1_1",
    #             "object_from_name": "秦海璐",
    #             "object_relationship_name": "主演",
    #             "object_to_name": "青少年"
    #         },
    #         {
    #             "object_from_category": "演员_1_1",
    #             "object_to_category": "电影_1_1",
    #             "object_from_name": "秦海璐",
    #             "object_relationship_name": "主演",
    #             "object_to_name": "青春"
    #         },
    #         {
    #             "object_from_category": "演员_1_1",
    #             "object_to_category": "电影_1_1",
    #             "object_from_name": "秦海璐",
    #             "object_relationship_name": "主演",
    #             "object_to_name": "母亲"
    #         }
    #     ],
    #     "event_extract_result": [
    #         {
    #             "time": "2013-01-01 00:00:00",
    #             "location": "",
    #             "eventSubject": "青春派",
    #             "eventSubjectLabel": "电影_1_1",
    #             "triggerLabel": "上映_1_1",
    #             "triggerWord": "上映",
    #             "eventName": "青春派上映"
    #         }
    #     ]
    # }

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
        #repoId=1
        #createId=1
        repoId = request.session['repo_id']
        createId = request.session['user_id']

        #_id="5f06fe7cf07991d5ee869d9b"
        mongodb_id = ObjectId(_id)
        try:
            news_col = Mongodb(db='knowledge', collection='text').get_collection()
        except Exception:
            return self.error("mongodb没有数据库或者表")
        tmpDict={'_id':mongodb_id}
        retDict=news_col.find_one(tmpDict)

        value = retDict['value']
        content = value['内容']
        text = HanlpUnit().get_text_from_html(content)
        #print(text)
        text = ''.join(text.split())
        relationship_extract_result = retDict['relationship_extract_result']
        event_extract_result = retDict['event_extract_result']
        final_contents = [[]]
        tagCategoryDictList = []

        if("wordSegmentationResults" not in retDict.keys()):
            tmpMap={}
            countMap={}
            colorMap={}
            color=1
            #word "tag": 1, "nums": 1
            for val in relationship_extract_result:
                object_from_category=val['object_from_category']
                object_to_category=val['object_to_category']
                object_from_name=val['object_from_name']
                object_to_name=val['object_to_name']
                object_relationship_name=val['object_relationship_name']
                object_relationship_category=val['object_relationship_category']
                #关系主体
                tmpMap=some_data_deal_func().mapAddVal(object_from_name,object_from_category,tmpMap)
                #关系客体
                tmpMap=some_data_deal_func().mapAddVal(object_to_name,object_to_category, tmpMap)
                #关系
                tmpMap = some_data_deal_func().mapAddVal(object_relationship_name, object_relationship_category, tmpMap)
                # 添加入countMap和color map
                countMap = some_data_deal_func().addCountMap([object_relationship_name,object_to_name,object_from_name],countMap)
                #countMap = some_data_deal_func().addCountMap(object_to_name, countMap)
                #countMap = some_data_deal_func().addCountMap(object_relationship_name, countMap)

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
                #关系名字
                #这个少了
            for val in event_extract_result:
                time=val['time']
                location=val['location']

                eventSubject=val['eventSubject']
                eventSubjectLabel=val['eventSubjectLabel']
                triggerLabel=val['triggerLabel']
                triggerWord=val['triggerWord']

                tempWordList = []
                #time
                if(len(time) !=0):
                    tmpMap = some_data_deal_func().mapAddVal(time, 'time', tmpMap)
                    tempWordList.append(time)
                #location
                if(len(location) !=0):
                    tmpMap = some_data_deal_func().mapAddVal(location, 'location', tmpMap)
                    tempWordList.append(location)
                #事件主题
                tmpMap=some_data_deal_func().mapAddVal(eventSubject,eventSubjectLabel,tmpMap)
                tempWordList.append(eventSubject)
                #事件触发词
                tmpMap=some_data_deal_func().mapAddVal(triggerWord,triggerLabel,tmpMap)
                tempWordList.append(triggerWord)

                #事件客体
                if('eventObject' in val.keys()):
                    eventObject=val['eventObject']
                    eventObjectLabel=val['eventObjectLabel']
                    tmpMap = some_data_deal_func().mapAddVal(eventObject, eventObjectLabel, tmpMap)
                    tempWordList.append(eventObject)
                countMap = some_data_deal_func().addCountMap(tempWordList,countMap)
                #colorMap, color = some_data_deal_func().addColorMap(tempWordList, color, colorMap)
            #先用一个map<str,list<str> > 这样可以存储每个词的词性
            #之后再利用添加词汇 把后面这个改成一个字符串然后添加进去 然后进行分词
            #print(tmpMap)
            #这里对所有的tmpMap的key,val里面的val生成颜色
            addColorList=[]
            for val in tmpMap.keys():
                valList =tmpMap[val]
                valListStr=""
                valCnt=0
                for j in valList:
                    if(valCnt!=0):
                        valListStr+=","
                    valListStr+=j
                    valCnt+=1
                addColorList.append(valListStr)
            colorMap, color = some_data_deal_func().addColorMap(addColorList, color, colorMap)
            wordList =[]
            #print(tmpMap)
            #将tmpMap里面词性转换成list [{},{}] 存入wordList
            for val in tmpMap.keys():
                tempList = tmpMap[val]
                cnt = 0
                tmpStr = ""
                for i in tempList:
                    if(cnt == 0):
                        tmpStr=tmpStr+i
                    else:
                        tmpStr=tmpStr+"/"+i
                    cnt=cnt+1
                tempWordDict = {}
                tempWordDict['word']=val
                tempWordDict['mask']=tmpStr
                wordList.append(tempWordDict)
            #[浙江/ns, 杭州/ns, 明天/t, 林更新/演员_1_1, 出演/出演_1_1, 动作/n, 喜剧/n, 《/w, 快手枪手快枪手/电
            tmpHanlp=HanlpUnit()
            tmpHanlp.add_word_list(wordList)
            #print(11111,wordList)
            ret = tmpHanlp.cut(text)
            #出问题了

            contents = tmpHanlp.get_text_subsection_from_html(content)
            cnt = 0
            i = 0
            index = 0
            temp = len(contents[0])
            #print(contents[0])
            #print(temp)
            #print('ret',ret)
            for item in ret:
                if cnt < temp:
                    tempDict = {}
                    word = item.split("/")[0]
                    mask = ','.join(item.split("/")[1:])
                    tempDict['word']=word
                    tempDict['mask']=mask

                    if(mask not in colorMap.keys()):
                        tempDict['tag']=0
                    else:
                        tempDict['tag'] = colorMap[mask]
                    tempDict['num']=index
                    final_contents[i].append(tempDict)
                    cnt += len(item.split("/")[0])
                elif cnt >= temp:
                    i += 1
                    tempDict = {}
                    word = item.split("/")[0]
                    mask = ''.join(item.split("/")[1:])
                    tempDict['word'] = word
                    tempDict['mask'] = mask

                    if(mask not in colorMap.keys()):
                        tempDict['tag']=0
                    else:
                        tempDict['tag'] = colorMap[mask]
                    tempDict['num'] = index
                    final_contents.append([tempDict])
                    cnt += len(item.split("/")[0])
                    temp += len(contents[i])
                index = index + 1
            #print(22222,final_contents)
            for val in colorMap.keys():
                tagNum= colorMap[val]
                tmpList = val.split(',')
                retString=""
                tmpCnt=0
                for j in tmpList:
                    if(tmpCnt != 0):
                        retString+=','
                    retString+= j.split('_')[0]
                    tmpCnt+=1
                tagCategoryDictList.append({'tag':tagNum,'category':retString})
            #print(tagCategoryDictList)
            #这个东西还是不对的
            #
            #所有东西都完成以后
            #进行原来事件的定位
            #此处要构造一个全部的的数组
            tmpfinal_contents=[]
            for i in final_contents:
                for j in i:
                    tmpfinal_contents.append(j);
            tmpfinal_contentsLen = len(tmpfinal_contents)
            relationship_extract_resultList=[]
            for val in relationship_extract_result:
                object_from_category = val['object_from_category']
                object_to_category = val['object_to_category']
                object_from_name = val['object_from_name']
                object_to_name = val['object_to_name']
                object_relationship_name = val['object_relationship_name']
                object_relationship_category = val['object_relationship_category']
                #从分词结果里面去找这个东西
                #这三个词在句子中的下标
                object_from_name_index=0
                object_to_name_index = 0
                object_relationship_name_index = 0
                for j in range(tmpfinal_contentsLen):
                    if(tmpfinal_contents[j]['word'] ==object_relationship_name ):
                        relaNum=1
                        tmp_object_relationship_name_index=tmpfinal_contents[j]['num']
                        #设置成一个很大的值
                        dis = 100000
                        endnum=j
                        for k in range(j-1,0,-1):
                            if(tmpfinal_contents[k]['word']==object_from_name and j-k<dis):
                                dis=j-k
                                endnum=tmpfinal_contents[k]['num']
                                #tmp_object_from_name_index = tmpDictList[k]['num']
                                break
                        for k in range(j+1,tmpfinal_contentsLen,1):
                            if(tmpfinal_contents[k]['word']==object_from_name and k-j<dis ):
                                dis = k - j
                                endnum = tmpfinal_contents[k]['num']
                                #tmp_object_from_name_index = tmpDictList[k]['num']
                                break
                        #print(dis,tmpDictList[endnum]['word'])
                        #print(object_from_name)
                        #print(object_to_name)
                        #print(object_relationship_name)
                        #print(dis)
                        if(dis <100000):
                            relaNum+=1
                            tmp_object_from_name_index = endnum
                        dis=100000
                        endnum = j

                        for k in range(j +1, tmpfinal_contentsLen, 1):
                            if (tmpfinal_contents[k]['word'] == object_to_name and k-j<dis):
                                dis = k - j
                                endnum = tmpfinal_contents[k]['num']
                                break
                        for k in range(j-1,0, -1):
                            if (tmpfinal_contents[k]['word'] == object_to_name and k-j<dis):
                                dis = j - k
                                endnum = tmpfinal_contents[k]['num']
                                break
                        if (dis < 100000):
                            relaNum += 1
                            tmp_object_to_name_index = endnum
                        #print(dis)
                        #print(tmpDictList)
                        #print(dis, tmpDictList[endnum]['word'])
                        #print(111, tmp_object_from_name_index, tmp_object_relationship_name_index, tmp_object_to_name_index)
                        if(relaNum == 3):
                            #三者都有进行更新
                            object_from_name_index = tmp_object_from_name_index
                            object_to_name_index = tmp_object_to_name_index
                            object_relationship_name_index = tmp_object_relationship_name_index
                            #print(111,object_from_name_index,object_relationship_name_index,object_to_name_index)
                #完成以后进行这个东西的更新
                relationshipDict =val
                relationshipDict['object_from_name_index']=object_from_name_index
                relationshipDict['object_to_name_index'] = object_to_name_index
                relationshipDict['object_relationship_name_index'] = object_relationship_name_index
                relationship_extract_resultList.append(relationshipDict)
                #这个东西要更新进去

            event_extract_resultList=[]
            for val in event_extract_result:
                time=val['time']
                location=val['location']
                #时间和地点先放过去
                ###有Bug

                eventSubject=val['eventSubject']
                eventSubjectLabel=val['eventSubjectLabel']
                triggerLabel=val['triggerLabel']
                triggerWord=val['triggerWord']
                if('eventObject' in val.keys()):
                    eventObject = val['eventObject']
                    eventObjectLabel = val['eventObjectLabel']
                #事件的还要分类讨论一下
                #从分词结果里面去找这个东西
                #这三个词在句子中的下标
                eventSubjectIndex=0
                triggerWordIndex = 0
                eventObjectIndex = 0
                for j in range(tmpfinal_contentsLen):
                    if(tmpfinal_contents[j]['word'] ==triggerWord ):
                        relaNum=1
                        tmpTriggerWordIndex=tmpfinal_contents[j]['num']
                        dis=100000
                        ennum=j
                        for k in range(j-1,0,-1):
                            if(tmpfinal_contents[k]['word']==eventSubject and j-k<dis):
                                dis=j-k
                                ennum = tmpfinal_contents[k]['num']
                                break
                        for k in range(j+1,tmpfinal_contentsLen,1):
                            if(tmpfinal_contents[k]['word']==eventSubject and k-j<dis):
                                dis=k-j
                                ennum = tmpfinal_contents[k]['num']
                                break
                        if(dis<100000):
                            tmpEventSubjectIndex=ennum
                            relaNum+=1
                        tmpEventObjectIndex=0
                        if('eventObject' in val.keys()):
                            dis = 100000
                            ennum = j
                            for k in range(j +1, tmpfinal_contentsLen, 1):
                                if (tmpfinal_contents[k]['word'] == eventObject and k-j<dis):
                                    dis = k-j
                                    ennum = tmpfinal_contents[k]['num']
                                    #tmpEventObjectIndex = tmpDictList[k]['num']
                                    break
                            for k in range(j -1, 0, -1):
                                if (tmpfinal_contents[k]['word'] == eventObject and j-k<dis):
                                    dis = j-k
                                    ennum = tmpfinal_contents[k]['num']
                                    #tmpEventObjectIndex = tmpDictList[k]['num']
                                    break
                            if (dis < 100000):
                                tmpEventOubjectIndex = ennum
                                relaNum += 1
                        if(relaNum == 3):
                            #三者都有进行更新
                            eventSubjectIndex = tmpEventSubjectIndex
                            triggerWordIndex = tmpTriggerWordIndex
                            eventObjectIndex = tmpEventObjectIndex
                        elif (relaNum==2 and 'eventObject' not in val.keys()):
                            eventSubjectIndex = tmpEventSubjectIndex
                            triggerWordIndex = tmpTriggerWordIndex
                #完成以后进行这个东西的更新
                eventDict =val
                eventDict['eventSubjectIndex']=eventSubjectIndex
                eventDict['triggerWordIndex'] = triggerWordIndex
                if ('eventObject' in val.keys()):
                    eventDict['eventObjectIndex'] = eventObjectIndex
                event_extract_resultList.append(eventDict)
            news_col.update_one({'_id': mongodb_id}, {"$set": {'relationship_extract_result':relationship_extract_resultList,'event_extract_result':event_extract_resultList}})
            #print(11111,relationship_extract_resultList)
            #print(22222,event_extract_resultList)
            #假如说我已经有这些标注了那么我要再把这个原来的句子进行一次标注
            #使得其他的变成0
            #然后进行更新
            #这边要先把所有的index拿出来有用的标成1完成了以后再进行匹配
            tempArray=[]
            allPageLen=0
            final_contentsLen = len(final_contents)
            for i in range(final_contentsLen):
                tmpDictList = final_contents[i]
                tmpDictListLen = len(tmpDictList)
                allPageLen+=tmpDictListLen
            for i in range(allPageLen):
                tempArray.append(0)

            for val in relationship_extract_resultList:
                object_from_name_index = val['object_from_name_index']
                object_to_name_index = val['object_to_name_index']
                object_relationship_name_index = val['object_relationship_name_index']
                tempArray[object_from_name_index]=1
                tempArray[object_to_name_index]=1
                tempArray[object_relationship_name_index]=1
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
                #print(val)
                eventSubjectIndex=val['eventSubjectIndex']
                triggerWordIndex=val['triggerWordIndex']
                if ('eventObject' in val.keys()):
                    eventObjectIndex=val['eventObjectIndex']
                    tempArray[eventObjectIndex] = 1
                tempArray[eventSubjectIndex]=1
                tempArray[triggerWordIndex]=1
            #print(tempArray)
            final_contentsLen = len(final_contents)
            for i in range(final_contentsLen):
                tmpDictList = final_contents[i]
                tmpDictListLen = len(tmpDictList)
                for j in range(tmpDictListLen):
                    if(tempArray[tmpDictList[j]['num']]==0):
                        final_contents[i][j]['tag']=0
            #print(final_contents)
            news_col.update_one({'_id': mongodb_id}, {"$set": {'relationship_extract_result':relationship_extract_resultList,'event_extract_result':event_extract_resultList,'wordSegmentationResults': final_contents,"tagCategory":tagCategoryDictList}})
            print(1)
        else:
            final_contents=retDict["wordSegmentationResults"]
            tagCategoryDictList=retDict["tagCategory"]
            print(2)
        #if("wordSegmentationResults" in retDict.keys()):
        retCategory=TCategory.objects.filter(repo_id=repoId,create_id=createId,category_type=1)
        categoryList=[]
        #cnt=0
        for tmpCategory in retCategory:
            #print(22)
            tmpDict={}
            tmpCategoryDict = model_to_dict(tmpCategory)
            tmpDict['id']=tmpCategoryDict['id']
            tmpDict['category_name'] = tmpCategoryDict['category_name']
            categoryList.append(tmpDict)
            #cnt+=1
        #print("类目个数",cnt)
        relationshipList=some_data_deal_func().findAllRealtionship(repoId,createId)
        print(relationshipList)

        retEventCategory=TCategory.objects.filter(repo_id =repoId,create_id=createId,category_type=2)
        eventCategory=[]
        for val in retEventCategory:
            valDict = model_to_dict(val)
            if(valDict['category_name'] == "事件"):
                continue
            eventCategory.append({'id':valDict['id'],'category_name':valDict['category_name']})
        ret_l = {'cutResult':final_contents,'relationship_extract_result':relationship_extract_result,'event_extract_result':event_extract_result,'tagCategory':tagCategoryDictList,'category':categoryList,'relationship':relationshipList,'eventCategoryName':eventCategory}

        #for i in final_contents:
        #    for val in i:
        #        print(val['word'],val['mask'],val['tag'],val['num'])
        #print(final_contents)
        #word_list:词列表，格式[{"word": "", "mask": ""}] word为词名，mask为词性
        #ret_l = {'cutResult':final_contents,'relationship_extract_result':relationship_extract_result,'event_extract_result':event_extract_result,'tagCategory':tagCategoryDictList}
        #print(relationship_extract_result)
        #print(event_extract_result)
        #print(ret_l)
        #return render(request, "test.html", context=ret_l)
        return render(request, "index/contentanalysis.html", context=ret_l)

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
        term=request.POST("term")
        categoryId=request.POST("categoryId")
        page_id = str(request.GET['_id'])

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
        print("整个句子的长度=",allWordLen)
        wordListTag =[]
        for ind in range(allWordLen):
            wordListTag.append(0)
        print(wordSegmentationResults)
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
            print('tmpAddListLen',tmpAddListLen)

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
        print(11111)
        print(wordSegmentationResults)
        #wordListTag = []
        for ind in range(1,allWordLen):
            wordListTag[ind]+=wordListTag[ind-1]
        relationship_extract_result = retPageDocument['relationship_extract_result']
        event_extract_result = retPageDocument['event_extract_result']
        #print(relationship_extract_result)
        #print(event_extract_result)
        print(11111)
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

        return  self.success("成功")
        #return render(request, "test.html", context=ret_l)

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
                                            'object_from_name_category':object_from_name_category,
                                            'object_to_name_category':object_to_name_category,
                                            'object_relationship_name_category':object_relationship_name_category,
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
        ret_l={}
        return self.success("添加成功")

    def deleteRelationship(self,request):
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
        _id = str(request.GET['_id'])
        index= int(request.GEt['index'])
        object_from=request.GET['object_from']
        object_event=request.GET['object_event']
        object_to = request.GET['object_to']

        #only for debug start
        # _id = "5ef6e30c7765440d7a6c2616"
        # index = 0
        # object_from="国家"
        # object_to="片源"
        # object_event = "组织"
        # request.session['repo_id']=1
        # request.session['user_id']=1
        #only for debug end
        repoId = request.session['repo_id']
        createId = request.session['user_id']
        mongodb_id = ObjectId(_id)
        try:
            news_col = Mongodb(db='knowledge',collection='text').get_collection()
        except Exception:
            return self.error("mongodb没有数据库或者表")
        document = news_col.find_one({'_id':mongodb_id})

        relationship_extract_result=document['relationship_extract_result']
        event_extract_result = document['event_extract_result']
        tagCategory=document['tagCategory']
        wordSegmentationResults=document['wordSegmentationResults']
        #print(5656)
        #修改查询结果
        #假如其他关系/事件还有用到这个词的的话 那么词性不用修改
        #假如是最后一个用到这个词的 修改词性 修改这个颜色 修改tagCategory 关系抽取结果
        wordDict={}
        #先删除
        #删除了以后加入关系会导致两个主演都被标出来了
        relationship_extract_resultLen = len(relationship_extract_result)
        #写到这里了
        for i in range(relationship_extract_resultLen):
            print(relationship_extract_result[i]['object_from_name'])
            wordDict = some_data_deal_func().wordInsertToDict(relationship_extract_result[i]['object_from_name_index'],wordDict)
            wordDict = some_data_deal_func().wordInsertToDict(relationship_extract_result[i]['object_to_name_index'],wordDict)
            wordDict = some_data_deal_func().wordInsertToDict(relationship_extract_result[i]['object_relationship_name_index'],wordDict)
        #print(5656)
        event_extract_resultLen = len(event_extract_result)
        for i in range(event_extract_resultLen):
            #wordDict = some_data_deal_func().wordInsertToDict(event_extract_result[i]['time'],wordDict)
            #wordDict = some_data_deal_func().wordInsertToDict(event_extract_result[i]['location'], wordDict)
            wordDict = some_data_deal_func().wordInsertToDict(event_extract_result[i]['eventSubjectIndex'], wordDict)
            wordDict = some_data_deal_func().wordInsertToDict(event_extract_result[i]['triggerWordIndex'], wordDict)
            if('eventObject' in event_extract_result[i].keys()):
                wordDict = some_data_deal_func().wordInsertToDict(event_extract_result[i]['eventObjectIndex'], wordDict)
        #print(index,relationship_extract_resultLen)
        if(index < relationship_extract_resultLen):
            #print(55555)
            tmpDict={}
            ansRelationshipExtractResult=[]
            for i in range(relationship_extract_resultLen):
                if(i == index):
                    tmpDict=relationship_extract_result[i]
                    continue
                else:
                    ansRelationshipExtractResult.append(relationship_extract_result[i])
            #object_from_name
            num=wordDict[tmpDict['object_from_name_index']]
            object_from_nameindex = tmpDict['object_from_name_index']
            wordSegmentationResultsLen = len(wordSegmentationResults)

            if(num == 1):
                #更新tag
                #更新wordDict
                wordSegmentationResults=some_data_deal_func().updatewordSegmentationResultsTag(object_from_nameindex,
                                                                       wordSegmentationResults,
                                                                       wordSegmentationResultsLen)
                del wordDict[tmpDict['object_from_name_index']]
            elif(num>1):
                wordDict[tmpDict['object_from_name_index']]-=1
            #object_to_name
            num = wordDict[tmpDict['object_to_name_index']]
            object_to_nameindex = tmpDict['object_to_name_index']
            if (num == 1):
                # 更新tag
                # 更新wordDict
                wordSegmentationResults=some_data_deal_func().updatewordSegmentationResultsTag(object_to_nameindex,
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
                wordSegmentationResults=some_data_deal_func().updatewordSegmentationResultsTag(object_relationship_nameindex,
                                                                       wordSegmentationResults,
                                                                       wordSegmentationResultsLen)
                del wordDict[tmpDict['object_relationship_name_index']]
            elif num > 1:
                wordDict[tmpDict['object_relationship_name_index']] -= 1
            #所有的东西完成以后进行颜色的更新
            #封装一个颜色的结果
            tagCategory=some_data_deal_func().countColor(ansRelationshipExtractResult,event_extract_result)

            print(tagCategory)
            #print(wordSegmentationResults)
            news_col.update_one({'_id': mongodb_id},{"$set": {'wordSegmentationResults': wordSegmentationResults,'relationship_extract_result':ansRelationshipExtractResult,'tagCategory':tagCategory}})
            # 删除neo4j关系
            #category  atrribute category  attribute relationshipname
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

        return self.success("删除成功")

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
        select_event_type_index =  int(request.POST['select_event_type'])

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

    def deleteEvent(self,request):
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
        # _id=request.POST['id']
        # index = request.POST['index']
        # time = request.POST['time']
        # location = request.POST['location']
        # event_subject =  request.POST['event_subject']
        # event_name = request.POST['event_name']
        # event_object = request.POST['event_object']

        _id="5ef6e30c7765440d7a6c2616"
        index = 0
        time = "2020"
        location = "123456"
        event_subject =  "123"
        event_name = "123"
        event_object = "123"
        request.session['repo_id'] =1
        request.session['user_id'] =1

        repoId = request.session['repo_id']
        createId = request.session['user_id']
        mongodb_id = ObjectId(_id)
        try:
            news_col = Mongodb(db='knowledge',collection='text').get_collection()
        except Exception:
            return self.error("mongodb没有数据库或者表")
        document = news_col.find_one({'_id':mongodb_id})
        
        relationship_extract_result=document['relationship_extract_result']
        event_extract_result = document['event_extract_result']
        tagCategory=document['tagCategory']
        wordSegmentationResults=document['wordSegmentationResults']
        #print(5656)
        #修改查询结果
        #假如其他关系/事件还有用到这个词的的话 那么词性不用修改
        #假如是最后一个用到这个词的 修改词性 修改这个颜色 修改tagCategory 关系抽取结果
        wordDict={}
        #先删除
        #删除了以后加入关系会导致两个主演都被标出来了
        relationship_extract_resultLen = len(relationship_extract_result)
        #写到这里了
        for i in range(relationship_extract_resultLen):
            #print(relationship_extract_result[i]['object_from_name'])
            wordDict = some_data_deal_func().wordInsertToDict(relationship_extract_result[i]['object_from_name_index'],wordDict)
            wordDict = some_data_deal_func().wordInsertToDict(relationship_extract_result[i]['object_to_name_index'],wordDict)
            wordDict = some_data_deal_func().wordInsertToDict(relationship_extract_result[i]['object_relationship_name_index'],wordDict)
        #print(5656)
        event_extract_resultLen = len(event_extract_result)
        for i in range(event_extract_resultLen):
            wordDict = some_data_deal_func().wordInsertToDict(event_extract_result[i]['timeIndex'],wordDict)
            wordDict = some_data_deal_func().wordInsertToDict(event_extract_result[i]['locationIndex'], wordDict)
            wordDict = some_data_deal_func().wordInsertToDict(event_extract_result[i]['eventSubjectIndex'], wordDict)
            wordDict = some_data_deal_func().wordInsertToDict(event_extract_result[i]['triggerWordIndex'], wordDict)
            if('eventObject' in event_extract_result[i].keys()):
                wordDict = some_data_deal_func().wordInsertToDict(event_extract_result[i]['eventObjectIndex'], wordDict)
        ansEventExtractResult=[]

        if(index < event_extract_resultLen):
            #print(55555)
            tmpDict={}
            ansEventExtractResult=[]
            for i in range(event_extract_resultLen):
                if(i == index):
                    tmpDict=event_extract_result[i]
                    continue
                else:
                    ansEventExtractResult.append(event_extract_result[i])
            #time
            num=wordDict[tmpDict['timeIndex']]
            timeIndex = tmpDict['timeIndex']
            wordSegmentationResultsLen = len(wordSegmentationResults)

            if(num == 1):
                #更新tag
                #更新wordDict
                wordSegmentationResults=some_data_deal_func().updatewordSegmentationResultsTag(timeIndex,
                                                                       wordSegmentationResults,
                                                                       wordSegmentationResultsLen)
                del wordDict[tmpDict['timeIndex']]
            elif(num>1):
                wordDict[tmpDict['timeIndex']]-=1

            #location
            num=wordDict[tmpDict['locationIndex']]
            locationIndex = tmpDict['locationIndex']
            wordSegmentationResultsLen = len(wordSegmentationResults)

            if(num == 1):
                #更新tag
                #更新wordDict
                wordSegmentationResults=some_data_deal_func().updatewordSegmentationResultsTag(locationIndex,
                                                                       wordSegmentationResults,
                                                                       wordSegmentationResultsLen)
                del wordDict[tmpDict['locationIndex']]
            elif(num>1):
                wordDict[tmpDict['locationIndex']]-=1

            #eventSubject
            num=wordDict[tmpDict['eventSubjectIndex']]
            eventSubjectIndex = tmpDict['eventSubjectIndex']
            wordSegmentationResultsLen = len(wordSegmentationResults)

            if(num == 1):
                #更新tag
                #更新wordDict
                wordSegmentationResults=some_data_deal_func().updatewordSegmentationResultsTag(eventSubjectIndex,
                                                                       wordSegmentationResults,
                                                                       wordSegmentationResultsLen)
                del wordDict[tmpDict['eventSubjectIndex']]
            elif(num>1):
                wordDict[tmpDict['eventSubjectIndex']]-=1

            #triggerWord
            num=wordDict[tmpDict['triggerWordIndex']]
            triggerWordIndex = tmpDict['triggerWordIndex']
            wordSegmentationResultsLen = len(wordSegmentationResults)

            if(num == 1):
                #更新tag
                #更新wordDict
                wordSegmentationResults=some_data_deal_func().updatewordSegmentationResultsTag(triggerWordIndex,
                                                                       wordSegmentationResults,
                                                                       wordSegmentationResultsLen)
                del wordDict[tmpDict['triggerWordIndex']]
            elif(num>1):
                wordDict[tmpDict['triggerWordIndex']]-=1
            #eventObject

            #这里要判断一下这个东西是否存在
            rule = 2
            if('eventObjectIndex' in tmpDict.keys()):
                rule = 1
                num=wordDict[tmpDict['eventObjectIndex']]
                eventObjectIndex = tmpDict['eventObjectIndex']
                wordSegmentationResultsLen = len(wordSegmentationResults)

                if(num == 1):
                    #更新tag
                    #更新wordDict
                    wordSegmentationResults=some_data_deal_func().updatewordSegmentationResultsTag(eventObjectIndex,
                                                                           wordSegmentationResults,
                                                                           wordSegmentationResultsLen)
                    del wordDict[tmpDict['eventObjectIndex']]
                elif(num>1):
                    wordDict[tmpDict['eventObjectIndex']]-=1

            #所有的东西完成以后进行颜色的更新
            #封装一个颜色的结果
            tagCategory=some_data_deal_func().countColor(relationship_extract_result,ansEventExtractResult)

            print(tagCategory)
            #print(wordSegmentationResults)
            news_col.update_one({'_id': mongodb_id},{"$set": {'wordSegmentationResults': wordSegmentationResults,'event_extract_result':ansEventExtractResult,'tagCategory':tagCategory}})
            # 删除neo4j关系
            #category  atrribute category  attribute relationshipname
            #
            eventName=""
            if(rule == 1):
                #三元
                eventName +=tmpDict['eventSubject'] + tmpDict['triggerWord']+tmpDict['eventObject']
            else:
                #二元
                eventName +=tmpDict['eventSubject'] + tmpDict['triggerWord']


            #删除有点问题
            Neo4j().deleteRealtionship(tmpDict['eventSubjectLabel'],
                                {'名字':tmpDict['eventSubject']},
                                tmpDict['triggerLabel'],
                                {'时间':tmpDict['actual_event_time'],'地点':tmpDict['location'],'名字':eventName},
                                "主谓关系")
            if(rule == 1):
                Neo4j().deleteRealtionship(tmpDict['triggerLabel'],
                                           {'时间': tmpDict['actual_event_time'], '地点': tmpDict['location'], '名字': eventName},
                                            tmpDict['eventObjectLabel'],
                                           {'名字':tmpDict['eventObject']},
                                           "动宾关系")
        else:
            return self.error("下标超过范围")
        return self.success("添加成功")

    def test111(self,request):
        from  model.extractUnit import ExtractUnit
        ExtractUnit().eventExtraction(request,43);
        return self.success("成功")