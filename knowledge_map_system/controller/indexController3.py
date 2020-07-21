import os
from datetime import datetime
from django.core.serializers import json
from django.http import HttpResponse
from bson import ObjectId
import re
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
        return render(request, 'test1.html', context={result: 'success'})

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
        return render(request, 'test1.html', context={result: 'success'})

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
        return render(request, 'test1.html', context={1: 'success'})

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
        return render(request, 'test1.html', context={1: 'success'})

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

        return render(request, 'test1.html', context={1: 'success'})

    #删除
    def delete_attrubite(self,request):
        _attribute_id = request.POST['attribute_id']
        #_attribute_id = 28
        _attribute_alias_delete = TAttrbuteAlias.objects.filter(attribute_id=_attribute_id)
        _attribute_alias_delete.delete()
        _attribute_delete = TAttribute.objects.filter(id=_attribute_id)
        _attribute_delete.delete()
        return render(request, 'test1.html', context={1: 'success'})

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
        return render(request, 'test1.html', context=ret_l)

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
        return render(request, 'test1.html', context=ret_l)

    #把文件从前端传递到后台
    def upload_file(self,request):
        if request.method == "POST":  # 请求方法为POST时，进行处理
            myFile = request.FILES.get("myfile", None)  # 获取上传的文件，如果没有文件，则默认为None
            if not myFile:
                return HttpResponse("no files for upload!")
            destination = open(os.path.join("E:\\upload", myFile.name), 'wb+')  # 打开特定的文件进行二进制的写操作
            for chunk in myFile.chunks():  # 分块写入文件
                destination.write(chunk)
            destination.close()
            return HttpResponse("upload over!")
        ret_l={}
        #这边还要写入到日志里面
        return render(request, 'test1.html', context=ret_l)

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
        return render(request, 'test1.html', context=ret_l)

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
        return render(request, 'test1.html', context=ret_l)

    #从文件中读取数据 然后存入到Mongodb
    def save_data_to_mongodb(self,request):
        #新建类目表
        #数据的话从文件里面读出
        repo_id = request.POST['repo_id']
        #create_id = request.POST['create_id']
        file_id = request.POST['file_id']

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
        list_attribute = list(table.row_values(0))
        list_json = []
        row = table.nrows
        col = table.ncols

        for i in range(1, row):
            dict_data = {}
            for j in range(0, col):
                dict_data[list_attribute[j]] = table.row_values(i)[j]
            dict_data['file_id']=file_id
            x=news_col.insert_one(dict_data)

        ret_l={'context':'success'}

        return render(request, 'test1.html', context=ret_l)


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
        return render(request, 'test1.html', context=ret_l)

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
        return render(request, 'test1.html', context=ret_l)

    #根据id更新属性id
    #更新neo4j数据库的属性名
    #就是把第一个换成第二个
    def update_mapping_rule(self,request):
        #t_mapping_rule_id = request.POST['t_mapping_rule_id']
        #map_attribute_id = request.POST['map_attribute_id']
        t_mapping_rule_id = 1
        map_attribute_id = 2
        repo_id = 1
        create_id = 1

        #修改映射id
        obj = TMappingRule.objects.get(id=t_mapping_rule_id)
        obj.map_attribute_id = map_attribute_id
        obj.save()
        #获得旧的属性名字
        old_att_name  =model_to_dict(obj)['attribute_name']

        #获得新的属性名字
        obj_att = TAttribute.objects.get(id=map_attribute_id)
        new_att_name  = model_to_dict(obj_att)['attribute_name']

        #获得要更新的类目名字 也就是这个知识图谱中的所有数据
        res = TCategory.objects.filter(repo_id=repo_id,create_id=create_id)
        all_list = []
        for val in res:
            val_dict = model_to_dict(val)
            all_list.append(val_dict['category_name'])
        neo4j = Neo4j().update_attribute(all_list, old_att_name,new_att_name)
        ret_l={}
        return render(request, 'test1.html', context=ret_l)

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
        return render(request, 'test1.html', context=ret_l)

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
        #rule_number  0 - 6  分别是清洗的 0 - 3 是小数点 4 - 6 是日趋 7 是自定义
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
        return render(request, 'test1.html', context=ret_l)
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
        ret_category = TCategory.objects.filter(repo_id=repo_id)
        for val in ret_category:
            val_dict = model_to_dict(val)
            category_name_list.append(val_dict['category_name'])

        ret_l = {'category_name': category_name_list, 'context': ret_list}
        print(ret_l)
        return render(request, 'test1.html', context=ret_l)

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
        return render(request, 'test1.html', context=ret_l)

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
        return render(request, 'test1.html', context=ret_l)

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
        return render(request, 'test1.html', context=ret_l)

    #