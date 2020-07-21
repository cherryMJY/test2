from py2neo import *
from decimal import Decimal
import re

from model.models import TAttribute, TCleaningLog


class Neo4j(object):
    def __init__(self, host='bolt://localhost:7687', user='neo4j', passwd='13141314'):
        """

        :param host:
        :param user:
        :param passwd:
        """
        self.host = host
        self.user = user
        self.passwd = passwd
        self.graph = Graph(self.host, username=self.user, password=self.passwd)

    def json2str(self, one_json_info):
        result = "{"
        for item in one_json_info.keys():
           result += item + ":" + " '" + one_json_info[item] + "',"
        result = result[:-1] + "}"
        return result

    def create_node_mjy_edition(self, label_name="", property=None):
        print(label_name,property)
        if label_name == "":
            return
        sql="create(n:" + label_name + ") set "
        ok = 0
        if property is not None:
            for key in property.keys():
                if ok !=0 :
                    sql = sql + ','
                sql = sql + 'n.'+str(key) + '=\'' +str(property[key]) + '\''
                ok+=1
        self.graph.run(sql)


    def create_node(self, label_name="", property=None):
        print(label_name,property)
        if label_name == "":
            return
        node = Node(label_name)

        if property is not None:
            for key in property.keys():
                node.setdefault(key, property[key])
        print(node)
        self.graph.create(node)
        print(111)
        return node

    def create_relationship(self, node1=None, node2=None, label_name="", property=None):
        one_relationship = Relationship(node1, label_name, node2)
        if property is not None:
            for key in property.keys():
                one_relationship.setdefault(key, property[key])
        self.graph.create(one_relationship)

    def match(self, object_from=None, relationship=None, object_to=None, return_info="1"):
        # a = Node('label', name='a')
        # self.graph.create(a)
        # matcher = NodeMatcher(self.graph)
        # test1 = matcher.match(labels=label_name)
        # print(test1)
        if object_from is None:
            return
        sql = "MATCH "
        if object_from is not None:
            sql += "(n1:" + object_from["label_name"]
            if "content" in object_from.keys():
                sql += self.json2str(object_from["content"])
            sql += ")"
        if object_to is not None:
            sql += ",(n3:" + object_to["label_name"]
            if "content" in object_to.keys():
                sql += self.json2str(object_to["content"])
            sql += ")"
        if relationship is not None:
            sql += ",n2=(n1)-[r:" + relationship["label_name"]
            if "content" in relationship.keys():
                sql += self.json2str(relationship["content"])
            sql += "]-(n3)"
        sql += " return n" + return_info[0]

        for i in range(1, len(return_info)):
            sql += ", n" + return_info[i]
        sql += ";"
        print(sql)
        result = self.graph.run(sql).data()
        # result = self.graph.run("MATCH (n:director{member_name:'洪金宝'}),(n1:movie{movie_name:'一个好人'}),p=(n)-[]-(n1) return p;").data()
        print(len(result))
        return result

    #更新neo4j中的数据属性 把all_list列表中的， 然后包括include_name 变成change_to_name
    def update_attribute(self,all_list,include_name,change_to_name, object_from=None, relationship=None, object_to=None, return_info="1"):
        for val in all_list :
            sql = "match(n:"+val+") set n."+change_to_name+"=n."+include_name+" remove n." + include_name
            self.graph.run(sql)
        return 1
    def deal_datetime(self,date_string,ret_type):
        ret_l = ['','','','','','']

        #可能是1997年2月24日也可能是1997/2/24这种
        #也可能就是符合条件的1997-2-24
        #或者2997-2-24 00：00：00
        print(date_string)
        str_len = len(date_string)

        if re.match(r'\d+年\d+月\d+日', date_string):
            ind = 0
            tmp_num = 0
            for i in range(0,str_len):
                if(date_string[i]==' '):
                    continue
                elif(date_string[i]>='0' and date_string[i]<='9'):
                    tmp_num = tmp_num * 10 + ord(date_string[i])-ord('0')
                elif(date_string[i]=='年'):
                    ret_l[0]=str(tmp_num)
                    tmp_num=0
                elif (date_string[i] == '月'):
                    ret_l[1] = str(tmp_num)
                    tmp_num = 0
                elif (date_string[i] == '日'):
                    ret_l[2] = str(tmp_num)
                    tmp_num = 0
        elif(re.match(r'\d+-\d+-\d+\s\d+:\d+:\d+',date_string)):
            tmp_num = 0
            ind=0
            for i in range(0, str_len):
                if (date_string[i] >= '0' and date_string[i] <= '9'):
                    tmp_num = tmp_num * 10 + ord(date_string[i]) - ord('0')
                elif (date_string[i] == ':' or date_string[i] == '-' or date_string[i] == ' '):
                    ret_l[ind] = str(tmp_num)
                    tmp_num = 0
                    ind+=1
            if(tmp_num!=0):
                ret_l[5]=str(tmp_num)
        elif(re.match(r'\d+/\d+/\d+',date_string)):
            tmp_num = 0
            ind = 0
            for i in range(0, str_len):
                if (date_string[i] >= '0' and date_string[i] <= '9'):
                    tmp_num = tmp_num * 10 + ord(date_string[i]) - ord('0')
                elif (date_string[i] == '/' ):
                    ret_l[ind] = str(tmp_num)
                    tmp_num = 0
                    ind += 1
            if (tmp_num != 0):
                ret_l[2] = str(tmp_num)
        elif(re.match(r'\d+-\d+-\d+',date_string)):
            tmp_num = 0
            ind = 0
            for i in range(0, str_len):
                if (date_string[i] >= '0' and date_string[i] <= '9'):
                    tmp_num = tmp_num * 10 + ord(date_string[i]) - ord('0')
                elif (date_string[i] == '-'):
                    ret_l[ind] = str(tmp_num)
                    tmp_num = 0
                    ind += 1
            if (tmp_num != 0):
                ret_l[2] = str(tmp_num)
        for i in range(1,6):
            while(len(ret_l[i])<2):
                ret_l[i] = '0'+ret_l[i]
        ret_string = ''
        print(ret_l)
        if(ret_type == 4 ):
            ret_string = ret_string + ret_l[0] + '-' + ret_l[1] +'-' + ret_l[2]
        elif(ret_type == 5):
            ret_string = ret_string + ret_l[0] + '-' + ret_l[1]
        elif(ret_type == 6 ):
            ret_string = ret_string + ret_l[0] + '-' + ret_l[1] + '-' + ret_l[2] + ' ' + ret_l[3]+ ':' + ret_l[4]+':' + ret_l[5]
        return ret_string

    def update_attribute_value(self, all_list, attribute, change_to,rule_content,user_id,rule_id,all_list_cate_id,repo_id):
        cnt = 0
        for val in all_list :
            #0 变成小数点后0位
            if(change_to == 0):
                print(val,attribute)
                sql = "match(n:"+val+") return n."+attribute + ",id(n)"
                ret = self.graph.run(sql)
                tmp_list = []
                tmp_list_id = []
                for i in ret.data():
                    tmp_list.append(i['n.'+attribute])
                    tmp_list_id.append(i['id(n)'])
                len_list = len(tmp_list)
                print(tmp_list)
                print(tmp_list_id)
                for i in range(len_list):
                    tmp_list[i]=Decimal(tmp_list[i]).quantize(Decimal('0'))
                print(tmp_list)

                for i in range(0,len_list):
                    try:
                        sql = "match(n:" + val + ") where id(n)="+ str(tmp_list_id[i])+ " set n."+attribute+"= "+str(tmp_list[i])
                        self.graph.run(sql)
                        TCleaningLog.objects.create(entity_id=str(tmp_list_id[i]),
                                                  user_id=user_id,
                                                  cleaning_rule_id=rule_id,
                                                  cleaning_content=rule_content,
                                                  cleaning_result = 'success',
                                                  category_id=all_list_cate_id[cnt], repo_id=repo_id)
                    except   Exception as e:
                        TCleaningLog.objects.create(entity_id=str(tmp_list_id[i]),
                                                    user_id=user_id,
                                                    cleaning_rule_id=rule_id,
                                                    cleaning_content=rule_content,
                                                    cleaning_result='fail',
                                                    category_id=all_list_cate_id[cnt], repo_id=repo_id)
            elif(change_to == 1):
                print(val, attribute)
                sql = "match(n:" + val + ") return n." + attribute + ",id(n)"
                ret = self.graph.run(sql)
                tmp_list = []
                tmp_list_id = []
                for i in ret.data():
                    tmp_list.append(i['n.' + attribute])
                    tmp_list_id.append(i['id(n)'])
                len_list = len(tmp_list)
                print(tmp_list)
                print(tmp_list_id)
                for i in range(len_list):
                    tmp_list[i] = Decimal(tmp_list[i]).quantize(Decimal('0.0'))
                print(tmp_list)

                for i in range(0, len_list):
                    try:
                        sql = "match(n:" + val + ") where id(n)=" + str(
                            tmp_list_id[i]) + " set n." + attribute + "= " + str(tmp_list[i])
                        self.graph.run(sql)
                        TCleaningLog.objects.create(entity_id=str(tmp_list_id[i]),
                                                    user_id=user_id,
                                                    cleaning_rule_id=rule_id,
                                                    cleaning_content=rule_content,
                                                    cleaning_result='success',
                                                    category_id=all_list_cate_id[cnt], repo_id=repo_id)
                    except   Exception as e:
                        TCleaningLog.objects.create(entity_id=str(tmp_list_id[i]),
                                                    user_id=user_id,
                                                    cleaning_rule_id=rule_id,
                                                    cleaning_content=rule_content,
                                                    cleaning_result='fail',
                                                    category_id=all_list_cate_id[cnt], repo_id=repo_id)
            # 2  2位
            elif (change_to == 2):
                print(val, attribute)
                sql = "match(n:" + val + ") return n." + attribute + ",id(n)"
                ret = self.graph.run(sql)
                tmp_list = []
                tmp_list_id = []
                for i in ret.data():
                    tmp_list.append(i['n.' + attribute])
                    tmp_list_id.append(i['id(n)'])
                len_list = len(tmp_list)
                print(tmp_list)
                print(tmp_list_id)
                for i in range(len_list):
                    tmp_list[i] = Decimal(tmp_list[i]).quantize(Decimal('0.00'))
                print(tmp_list)

                for i in range(0, len_list):
                    try:
                        sql = "match(n:" + val + ") where id(n)=" + str(
                            tmp_list_id[i]) + " set n." + attribute + "= " + str(tmp_list[i])
                        self.graph.run(sql)
                        TCleaningLog.objects.create(entity_id=str(tmp_list_id[i]),
                                                    user_id=user_id,
                                                    cleaning_rule_id=rule_id,
                                                    cleaning_content=rule_content,
                                                    cleaning_result='success',
                                                    category_id=all_list_cate_id[cnt], repo_id=repo_id)
                    except   Exception as e:
                        TCleaningLog.objects.create(entity_id=str(tmp_list_id[i]),
                                                    user_id=user_id,
                                                    cleaning_rule_id=rule_id,
                                                    cleaning_content=rule_content,
                                                    cleaning_result='fail',
                                                    category_id=all_list_cate_id[cnt], repo_id=repo_id)
            # 3  3位
            elif (change_to == 3):
                print(val, attribute)
                sql = "match(n:" + val + ") return n." + attribute + ",id(n)"
                ret = self.graph.run(sql)
                tmp_list = []
                tmp_list_id = []
                for i in ret.data():
                    tmp_list.append(i['n.' + attribute])
                    tmp_list_id.append(i['id(n)'])
                len_list = len(tmp_list)
                print(tmp_list)
                print(tmp_list_id)
                for i in range(len_list):
                    tmp_list[i] = Decimal(tmp_list[i]).quantize(Decimal('0.000'))
                print(tmp_list)

                for i in range(0, len_list):
                    try:
                        sql = "match(n:" + val + ") where id(n)="+ str(tmp_list_id[i])+ " set n."+attribute+"= "+str(tmp_list[i])
                        self.graph.run(sql)
                        TCleaningLog.objects.create(entity_id=str(tmp_list_id[i]),
                                                  user_id=user_id,
                                                  cleaning_rule_id=rule_id,
                                                  cleaning_content=rule_content,
                                                  cleaning_result = 'success',
                                                  category_id=all_list_cate_id[cnt], repo_id=repo_id)
                    except   Exception as e:
                        TCleaningLog.objects.create(entity_id=str(tmp_list_id[i]),
                                                    user_id=user_id,
                                                    cleaning_rule_id=rule_id,
                                                    cleaning_content=rule_content,
                                                    cleaning_result='fail',
                                                    category_id=all_list_cate_id[cnt], repo_id=repo_id)
            # 4  这边从4开始  4 5 6 是清洗 日期时间 变成 a b c   a b  a b c d e的样子
            elif (change_to == 4):
                sql = "match(n:" + val + ") return n." + attribute + ",id(n)"
                ret = self.graph.run(sql)
                tmp_list = []
                tmp_list_id = []
                for i in ret.data():
                    tmp_list.append(i['n.' + attribute])
                    tmp_list_id.append(i['id(n)'])
                len_list = len(tmp_list)
                print(tmp_list)
                print(tmp_list_id)
                for i in range(len_list):
                    tmp_list[i] = self.deal_datetime(str(tmp_list[i]),4)
                print(tmp_list)
                for i in range(0, len_list):
                    try:
                        sql = "match(n:" + val + ") where id(n)=" + str(
                            tmp_list_id[i]) + " set n." + attribute + "= \'" + tmp_list[i] + "\'"
                        self.graph.run(sql)
                        TCleaningLog.objects.create(entity_id=str(tmp_list_id[i]),
                                                  user_id=user_id,
                                                  cleaning_rule_id=rule_id,
                                                  cleaning_content=rule_content,
                                                  cleaning_result = 'success',
                                                  category_id=all_list_cate_id[cnt], repo_id=repo_id)
                    except   Exception as e:
                        TCleaningLog.objects.create(entity_id=str(tmp_list_id[i]),
                                                    user_id=user_id,
                                                    cleaning_rule_id=rule_id,
                                                    cleaning_content=rule_content,
                                                    cleaning_result='fail',
                                                    category_id=all_list_cate_id[cnt], repo_id=repo_id)
            elif (change_to == 5):
                sql = "match(n:" + val + ") return n." + attribute + ",id(n)"
                ret = self.graph.run(sql)
                tmp_list = []
                tmp_list_id = []
                for i in ret.data():
                    tmp_list.append(i['n.' + attribute])
                    tmp_list_id.append(i['id(n)'])
                len_list = len(tmp_list)
                print(tmp_list)
                print(tmp_list_id)
                for i in range(len_list):
                    tmp_list[i] = self.deal_datetime(str(tmp_list[i]),5)
                print(tmp_list)
                for i in range(0, len_list):
                    try:
                        sql = "match(n:" + val + ") where id(n)=" + str(
                            tmp_list_id[i]) + " set n." + attribute + "= \'" + tmp_list[i] + "\'"
                        self.graph.run(sql)
                        TCleaningLog.objects.create(entity_id=str(tmp_list_id[i]),
                                                    user_id=user_id,
                                                    cleaning_rule_id=rule_id,
                                                    cleaning_content=rule_content,
                                                    cleaning_result='success',
                                                    category_id=all_list_cate_id[cnt], repo_id=repo_id)
                    except   Exception as e:
                        TCleaningLog.objects.create(entity_id=str(tmp_list_id[i]),
                                                    user_id=user_id,
                                                    cleaning_rule_id=rule_id,
                                                    cleaning_content=rule_content,
                                                    cleaning_result='fail',
                                                    category_id=all_list_cate_id[cnt], repo_id=repo_id)
            elif (change_to == 6):
                sql = "match(n:" + val + ") return n." + attribute + ",id(n)"
                ret = self.graph.run(sql)
                tmp_list = []
                tmp_list_id = []
                for i in ret.data():
                    tmp_list.append(i['n.' + attribute])
                    tmp_list_id.append(i['id(n)'])
                len_list = len(tmp_list)
                print(tmp_list)
                print(tmp_list_id)
                for i in range(len_list):
                    tmp_list[i] = self.deal_datetime(str(tmp_list[i]),6)
                print(tmp_list)
                for i in range(0, len_list):
                    try:
                        sql = "match(n:" + val + ") where id(n)=" + str(
                            tmp_list_id[i]) + " set n." + attribute + "= \'" + tmp_list[i] + "\'"
                        self.graph.run(sql)
                        TCleaningLog.objects.create(entity_id=str(tmp_list_id[i]),
                                                    user_id=user_id,
                                                    cleaning_rule_id=rule_id,
                                                    cleaning_content=rule_content,
                                                    cleaning_result='success',
                                                    category_id=all_list_cate_id[cnt], repo_id=repo_id)
                    except   Exception as e:
                        TCleaningLog.objects.create(entity_id=str(tmp_list_id[i]),
                                                    user_id=user_id,
                                                    cleaning_rule_id=rule_id,
                                                    cleaning_content=rule_content,
                                                    cleaning_result='fail',
                                                    category_id=all_list_cate_id[cnt], repo_id=repo_id)
            elif (change_to == 7):
                sql = "match(n:" + val + ") return n." + attribute + ",id(n)"
                ret = self.graph.run(sql)
                tmp_list = []
                tmp_list_id = []
                for i in ret.data():
                    tmp_list.append(i['n.' + attribute])
                    tmp_list_id.append(i['id(n)'])
                len_list = len(tmp_list)
                print(tmp_list)
                print(tmp_list_id)
                for i in range(len_list):
                    tmp_list[i] = re.match(rule_content,str(tmp_list[i]))
                print(tmp_list)
                for i in range(0, len_list):
                    try:
                        sql = "match(n:" + val + ") where id(n)=" + str(
                            tmp_list_id[i]) + " set n." + attribute + "= \'" + tmp_list[i] + "\'"
                        self.graph.run(sql)
                        TCleaningLog.objects.create(entity_id=str(tmp_list_id[i]),
                                                    user_id=user_id,
                                                    cleaning_rule_id=rule_id,
                                                    cleaning_content=rule_content,
                                                    cleaning_result='success',
                                                    category_id=all_list_cate_id[cnt], repo_id=repo_id)
                    except   Exception as e:
                        TCleaningLog.objects.create(entity_id=str(tmp_list_id[i]),
                                                    user_id=user_id,
                                                    cleaning_rule_id=rule_id,
                                                    cleaning_content=rule_content,
                                                    cleaning_result='fail',
                                                    category_id=all_list_cate_id[cnt], repo_id=repo_id)
            cnt +=1
        return 1

    #通过类型名字和属性名字 获得id和属性
    def ques_id_val(self,type_name,attribute_name):
        ret_list_id=[]
        ret_list_val=[]
        sql = "match(n:" + type_name + ") return n." + attribute_name + ",id(n)"
        ret = self.graph.run(sql)
        for i in ret.data():
            ret_list_val.append(i['n.' + attribute_name])
            ret_list_id.append(i['id(n)'])
        return ret_list_id,ret_list_val

    #输入是neo4j中的id 和关键属性,输出是他们的属性和属性名字
    def find_key_value(self,category_name,id_in_neo4j,key_attribute_list):
        sql_ques = ''
        key_attribute_list_len =len(key_attribute_list)
        for i in range(0,key_attribute_list_len):
            if(i!=0):
                sql_ques += ','
            sql_ques += 'n.'+key_attribute_list[i]
        sql = "match(n:"+category_name+") where id(n) =" +str(id_in_neo4j) +" return "+sql_ques
        ret =  self.graph.run(sql)
        ret_attribute_name_list=[]
        ret_attribute_value_list=[]
        for i in ret.data():
            for val in key_attribute_list:
                ret_attribute_name_list.append(val)
                ret_attribute_value_list.append(i['n.'+val])

        return ret_attribute_name_list, ret_attribute_value_list

    def ret_node_list_get_one_category_node_name_id(self,node_type,attribute_name,category_id):
        sql = "match(n:" + node_type + ") return n._id,n."+attribute_name
        node_list = []
        res = self.graph.run(sql)
        num = 1
        print(node_type,attribute_name)
        for i in res.data():
            tmp_map={}
            tmp_map['name']=i['n.' + attribute_name]
            tmp_map['category_id']=category_id
            tmp_map["id"] = i['n._id']
            node_list.append(tmp_map)

        return node_list

    def ques_node_by_id(self,entity_id,name_attribute):

        sql = "MATCH (n) WHERE id(n) = " + str(entity_id) +" RETURN labels(n) "
        res = self.graph.run(sql)
        category_name=''
        for i in res.data():
            category_name = i['labels(n)'][0]

        sql = "MATCH (n) WHERE id(n) = " + str(entity_id) + " return n"
        res = self.graph.run(sql)
        tmp_map={}
        id = 1
        name_attribute_val = ''
        map_other = {}
        for a in res:
            for tk, tv in a.items():
                for val in tv:
                    if(val == '_id'):
                        id = tv[val]
                    elif(val == name_attribute):
                        name_attribute_val=tv[val]
                    else:
                        map_other[val]=tv[val]
        tmp_map['_id'] = id
        tmp_map['name'] = name_attribute_val
        tmp_map['category_name']=category_name
        tmp_map['other']=map_other
        return  tmp_map