from django.forms import model_to_dict
from py2neo import *
from decimal import Decimal
import re

from model.models import TAttribute, TCleaningLog, TAttributeMapLog


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
        if one_json_info is None or len(one_json_info) == 0:
            return ""
        result = "{"
        for item in one_json_info.keys():
           result += item + ":" + " \"" + str(one_json_info[item]).replace("\"", "'") + "\","
        result = result[:-1] + "}"
        return result

    #插入的函数要写返回的id 不然又要去重新查询
    def create_node_mjy_edition(self, label_name="", property=None, retain_field=None):
        """
        插入neo4j
        :param label_name: 要插入的类目名
        :param property: json格式，插入的数据
        :param retain_field: 保留的字段
        :return:
        """
        if label_name == "":
            return
        sql = "create(n:" + label_name + ") set "
        ok = 0
        if property is not None:
            if retain_field is None:
                retain_field = list(property.keys())
            for key in property.keys():
                if key in retain_field:
                    if ok != 0:
                        sql = sql + ','
                    sql = sql + 'n.`'+str(key) + '`=\'' + str(property[key]).replace("'", "\"") + '\''
                    ok += 1
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
        # test = matcher.match(labels=label_name)
        # print(test)
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

    # 更新neo4j中的数据属性 把all_list列表中的， 然后包括include_name 变成change_to_name
    def update_attribute(self,category_id,map_rule_id, category_name, include_name, change_to_name, map_attribute_id,old_name_show_in_database,create_id,repo_id, object_from=None,
                         relationship=None, object_to=None, return_info="1"):

        # sql = "match(n:"+val+") set n."+change_to_name+"=n."+include_name+" remove n." + include_name
        sql = "match(n:" + category_name + ") where exists (n." + include_name + ") return n._id"
        ret = self.graph.run(sql)
        for val in ret:
            _id = val['n._id']
            #更新neo4j
            if(change_to_name == include_name):
                update_sql = "match(n:" + category_name + ") where n._id=\'" + _id + "\' set n." + change_to_name + "=n." + include_name
            else:
                update_sql = "match(n:"+category_name+") where n._id=\'"+_id+"\' set n."+change_to_name+"=n."+include_name+" remove n." + include_name
            print(update_sql)
            self.graph.run(update_sql)

            print(_id)

            #更新mysql表 attribute_log表
            _attribute_name=include_name
            _is_map = 1
            _entity_id = _id
            _map_attribute_id = map_attribute_id
            _category_id = category_id
            _map_rule_id = map_rule_id
            _create_id = create_id
            _repo_id = repo_id
            #删除上面的关于这条规则的日志
            return_map_attribute_log = TAttributeMapLog.objects.filter(map_rule_id=map_rule_id,create_id=create_id,repo_id=repo_id)
            return_map_attribute_log.delete()
            TAttributeMapLog.objects.create(attribute_name=old_name_show_in_database,
                                            is_map=_is_map,
                                            entity_id=_entity_id,
                                            map_attribute_id=_map_attribute_id,
                                            category_id=category_id,
                                            map_rule_id=map_rule_id,
                                            create_id=_create_id,
                                            repo_id=_repo_id)
            #<id>:2962827_id: 5ec5dc262cc49ce0185b524 ccategory_id: 4file_id: 7姓名: 孟佳营性别: 男高低: 18.0
        if(map_attribute_id == -1):
            return_att_map_log=TAttributeMapLog.objects.filter(map_rule_id=map_rule_id,category_id=category_id,create_id=create_id,repo_id=repo_id)
            return_att_map_log.delete()
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
                print(val, attribute)
                self.cleaningAttributeNum(val,attribute,user_id,rule_id,rule_content,all_list_cate_id,cnt,repo_id,'0')
            elif(change_to == 1):
                print(val, attribute)
                self.cleaningAttributeNum(val,attribute,user_id,rule_id,rule_content,all_list_cate_id,cnt,repo_id,'0.0')
            # 2  2位
            elif (change_to == 2):
                print(val, attribute)
                self.cleaningAttributeNum(val,attribute,user_id,rule_id,rule_content,all_list_cate_id,cnt,repo_id,'0.00')
            # 3  3位
            elif (change_to == 3):
                print(val, attribute)
                self.cleaningAttributeNum(val,attribute,user_id,rule_id,rule_content,all_list_cate_id,cnt,repo_id,'0.000')
            # 4  这边从4开始  4 5 6 是清洗 日期时间 变成 a b c   a b  a b c d e f的样子
            elif (change_to == 4):
                print(val, attribute)
                self.cleaningAttributeTime(val, attribute, user_id, rule_id, rule_content, all_list_cate_id, cnt,repo_id, 4)
            elif (change_to == 5):
                print(val, attribute)
                self.cleaningAttributeTime(val, attribute, user_id, rule_id, rule_content, all_list_cate_id, cnt,
                                           repo_id, 5)
            elif (change_to == 6):
                print(val, attribute)
                self.cleaningAttributeTime(val, attribute, user_id, rule_id, rule_content, all_list_cate_id, cnt,
                                           repo_id, 6)
            elif (change_to == 7):
                sql = "match(n:" + val + ") return n." + attribute + ",id(n)"
                ret = self.graph.run(sql)
                tmp_list = []
                tmp_list_id = []
                frontVal = []
                for i in ret.data():
                    tmpAttributeVal = i['n.' + attribute]
                    if (tmpAttributeVal == None):
                        continue
                    tmp_list.append(tmpAttributeVal)
                    tmp_list_id.append(i['id(n)'])
                len_list = len(tmp_list)
                print(tmp_list)
                print(tmp_list_id)
                for i in range(len_list):
                    frontVal.append(tmp_list[i])
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
                                                    cleaning_content=frontVal[i],
                                                    cleaning_result='success',
                                                    category_id=all_list_cate_id[cnt], repo_id=repo_id)
                    except   Exception as e:
                        TCleaningLog.objects.create(entity_id=str(tmp_list_id[i]),
                                                    user_id=user_id,
                                                    cleaning_rule_id=rule_id,
                                                    cleaning_content=frontVal[i],
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

        return ret_attribute_name_list,ret_attribute_value_list

    def ret_node_list_get_one_category_node_name_id(self, node_type, attribute_name, category_id):
        """
        根据类目名返回节点部分属性内容
        :param node_type: 节点类型
        :param attribute_name: name
        :param category_id: 输入的category_id
        :return: DictList  [{'id':neo4jId,'name':n.name,'category':category_id}]
        """
        sql = "match(n:" + node_type + ") return id(n),n."+attribute_name
        node_list = []
        res = self.graph.run(sql)
        num = 1
        print(node_type, attribute_name)
        #把_id 变成id(n)
        for i in res.data():
            tmp_map = {}
            tmp_map['name']=i['n.' + attribute_name]
            tmp_map['category'] = category_id
            tmp_map["id"] = i['id(n)']
            node_list.append(tmp_map)

        return node_list

    def ques_node_by_id(self,entity_id,name_attribute):

        sql = "MATCH (n) WHERE n._id = \'" + str(entity_id) +"\' RETURN labels(n) "
        res = self.graph.run(sql)
        category_name=''
        for i in res.data():
            category_name = i['labels(n)'][0]

        sql = "MATCH (n) WHERE n._id = \'" + str(entity_id) + "\' return n"
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
        tmp_map[name_attribute] = name_attribute_val
        tmp_map['category_name']=category_name
        tmp_map['other']=map_other
        return  tmp_map

    # 根据id 修改标签名字 输入是 标签名 修改的属性和属性内容  新的标签名字
    def update_one_node_label(self,label_name,ques_attribute_name,ques_attribute_context,update_lable_name):
        sql = "match(n:" + label_name + ") where n." + ques_attribute_name + "=\'" +ques_attribute_context +"\'" + " remove n:" + label_name+" set n:"+update_lable_name
        print(sql)
        self.graph.run(sql)
        return 1

    def createRelationship(self, labelOne, labelTwo, relationShipName, propertyOne=None, propertyTwo=None,
                               propertyRelationship=None):
        """
        创建关系
        :param labelOne:第一个节点类目名
        :param labelTwo:第二个节点类目名
        :param relationShipName:关系名
        :param propertyOne: 第一个节点属性内容，格式{“id”:“neo4j的id”, "属性1":"属性内容"}
        :param propertyTwo: 第二个节点属性内容，格式同上
        :param propertyRelationship: 创建关系的属性，格式同上
        :return:
        """
        try:
            match_property_list = []
            sql = "MATCH(a: " + str(labelOne)+")," + "(b:" + str(labelTwo) + ") WHERE "
            if propertyOne is not None:
                for key in propertyOne.keys():
                    if key == "id":
                        match_property_list.append("id(a) = " + str(propertyOne["id"]))
                    else:
                        match_property_list.append("a." + key + " = '" + str(propertyOne[key]) + "'")
            if propertyTwo is not None:
                for key in propertyTwo.keys():
                    if key == "id":
                        match_property_list.append("id(b) = " + str(propertyTwo["id"]))
                    else:
                        match_property_list.append("b." + key + " = '" + str(propertyTwo[key]) + "'")

            if len(match_property_list) >= 1:
                sql += match_property_list[0]
                for i in range(1, len(match_property_list)):
                    sql += " and " + match_property_list[i]
            sql += " CREATE(a) - [r: " + relationShipName + self.json2str(propertyRelationship) + "] -> (b);"
        # MATCH(a: 导演_1_1), (b:演员_1_1) WHERE id(a) = 2962886 and id(b) = 2962885 CREATE(a) - [r: RELTYPE] -> (b);
        #     sql = "MATCH(a: " + str(labelOne)+")," + "(b:" + str(labelTwo) + ") WHERE id(a) = " + str(idOne) + " and id(b) =" + str(idTwo) + " CREATE(a) - [r: " + str(relationShipName) + "] -> (b)"
            #print(sql)
            print(sql)
            self.graph.run(sql)
            return True
        except Exception as e:
            print(e)
            return False

    #添加关系
    #def createRelationship(self,labelOne,labelTwo,idOne,idTwo,relationShipName):
    #    # MATCH(a: 导演_1_1), (b:演员_1_1) WHERE id(a) = 2962886 and id(b) = 2962885 CREATE(a) - [r: RELTYPE] -> (b);
    #    sql = "MATCH(a: "+str(labelOne)+")," + "(b:" + str(labelTwo) +") WHERE id(a) = " + str(idOne) + " and id(b) =" + str(idTwo) + " CREATE(a) - [r: " +str(relationShipName) + "] -> (b)"
    #    #print(sql)
    #    self.graph.run(sql)
    #    return 1

    def quesIdByLabelAttribute(self,label,attributeName,attributeVal):
        """
        根据Label和Attribute的名字返回他的id
        在属性有同名的时候解决不了 只能返回第一个的id
        :param label: 查询的类目名
        :param attributeName: 属性名字
        :param attributeVal: 属性值
        :return  id :  在neo4j中的id:
        """
        #print(label, attributeName, attributeVal)
        sql = "match(n: "+label + ") where n." +attributeName+"=" +attributeVal+" return id(n)"
        #print(label,attributeName,attributeVal)
        #print(sql)
        ret = self.graph.run(sql)
        for val in ret:
            #print(val)
            return val['id(n)']
        return 1

    def delete_one_node(self,label_name,neo4j_entity_id):
        sql = "match(n:" + label_name + ") where n._id=\'" + neo4j_entity_id + "\' DETACH DELETE n"
        print(sql)
        self.graph.run(sql)

        return 1

    #这个函数要重新发给
    def getNearRelationshipNode(self,nodeLabel,attributeName,attributeVal):
        """
        :param nodeLabel: 开始节点的标签
        :param attributeName: 开始节点属性名字
        :param attributeLabel: 开始节点属性值
        :return: 返回listDict[{,,,}]
        """
        sql = "match(n:" + nodeLabel + "{"+attributeName+":\'"+attributeVal+"\'}) -[r]-(m) return id(n),id(r),id(m)"
        #print(sql)
        res=self.graph.run(sql)
        retList = []
        for val in res:
            retList.append(val)
        return retList

    #这个函数有改动
    def getEndNode(self, startLabel=None, relationshipName=None, attribute=None,category_name=None):
        # print(startLabel)
        sql = "match(n"
        if (startLabel != None):
            sql = sql + ":" + startLabel
        sql = sql + ")-[r"
        if (relationshipName != None):
            sql = sql + ":" + relationshipName
        sql = sql + "]-(m "
        if(category_name!=Neo4j):
            sql = sql +":" + category_name
        sql=sql+")"
        print (attribute)
        if (attribute != None):
            sql = sql + "where "
            cnt = 0
            for key in attribute.keys():
                if (cnt != 0):
                    sql = sql + " and "
                # print(key, attribute[key])
                if (key == 'id'):
                    sql = sql + "id(n)" + "=" + str(attribute[key])
                else:
                    sql = sql + "n." + str(key) + "=" + str(attribute[key])
                cnt += 1
        sql = sql + " return id(m),m "
        print(sql)
        # sql = "match(n:" + startLabel+")-[r:"+relationshipName+"]-(m) where "
        # match(n: 演员_1_1)-[r: `主谓关系`]-(m) where id(n) = 2962843 and n.名字 = '孟佳营'return m
        res = self.graph.run(sql)
        # for val in res:
        #    print(val)
        # print(sql)
        return res

    def returnRelationShip(self,id):
        """
        :param id: 关系id
        :return:  关系的名字
        """
        sql = "Match ()-[r]-() Where ID(r)="+str(id)+" return type(r)"

        ans =self.graph.run(sql)
        for val in ans:
            #print(val)
            return val
        return "没有关系名"

    def returnNode(self,attributeMap=None):
        """
        :param attribiueMap: 各种已知属性
        :return:             返回 所有属性和输入相同的 整个节点的属性
        """
        try:
            if(attributeMap==None):
                return
            sql = "match (n) where "
            cnt = 0
            for key in attributeMap.keys():
                if(cnt != 0):
                    sql = sql + " , "
                if(key == "id"):
                    sql = sql + "id(n)="+str(attributeMap[key])
                else:
                    sql = sql + "n."+key + "="+ str(attributeMap[key])
                #print(key,attributeMap[key])
                cnt  = cnt +1
            sql = sql + " return n"
            #print(sql)
            ret=self.graph.run(sql)
            #for val in ret:
            #    print(val)
            return ret
        except Exception as e:
            print(e)
            return False

    def  returnIdAndNode(self,attributeMap=None):
        """
        :param attribiueMap: 各种已知属性
        :return:             返回 所有属性和输入相同的 整个节点的属性
        """
        try:
            if(attributeMap==None):
                return
            sql = "match (n) where "
            cnt = 0
            for key in attributeMap.keys():
                if(cnt != 0):
                    sql = sql + " , "
                if(key == "id"):
                    sql = sql + "id(n)="+str(attributeMap[key])
                else:
                    sql = sql + "n."+key + "="+ str(attributeMap[key])
                #print(key,attributeMap[key])
                cnt  = cnt +1
            sql = sql + " return id(n),n"
            #print(sql)
            ret=self.graph.run(sql)
            #for val in ret:
            #    print(val)
            return ret
        except Exception as e:
            print(e)
            return False

    def getLabelByNeo4jId(self, id):
        """
        :param id: 节点的Neo4j id
        :return:   返回这个节点的label
        """
        sql = "match(n) where id(n)=" + str(id) + " return labels(n)"
        res = self.graph.run(sql)
        for val in res:
            return val
        # print("没有类目")
        return ""
    def retNode(self,label,idLow,idHei):
        sql = "match(n"
        if(label!=None):
            sql = sql +":" + str(label)
        sql = sql + ") "
        sql = sql + " where id(n) >" +str(idLow) +" and id(n)<="+str(idHei)
        sql =sql +" return n"
        ret=self.graph.run(sql)
        return ret;

    def getLabelByid(self,id):
        """
        :param id: 节点的mongodb id
        :return:   返回这个节点的label 格式 dict {'labels(n)' :'发布_1_1'}
        """
        sql = "match(n) where n._id="+str(id)+" return labels(n)"
        res = self.graph.run(sql)
        for val in res:
            return val
        #print("没有类目")
        return ""

    # 把neo4j查询结果node转换成字典形式
    def analysisNode(self, tmpNode):
        """
        :param node: neo4j查询结果  retNode['n'] 变成元组 ('id(m)': 2963044, 'm': (d3c08fb:`出演_1_1` {category_id:1,place:"",`发生时间`:"",`名字`:"林更新主演快手枪手快枪手"}))
        :return:     返回字典
        """
        nodeMap = {}
        for i in tmpNode:
            nodeMap[i] = tmpNode[i]
        # print(nodeMap)
        return nodeMap

    def dictToQuesDict(self,node):
        """
        :param node: dict  {'id':123,'name':'孟佳营'}
        :return:   dict  {'id':123,'name':'\'孟佳营\'',}
        """
        for val in node.keys():
            tmpVal = node[val]
            if(type(tmpVal) is str):
                tmpVal='\'' + tmpVal +'\''
            node[val] = tmpVal
        #print(node)
        return node

    def cleaningAttributeTime(self,val,attribute,user_id,rule_id,rule_content,all_list_cate_id,cnt,repo_id,timeType):
        sql = "match(n:" + val + ") return n." + attribute + ",id(n)"
        ret = self.graph.run(sql)
        tmp_list = []
        tmp_list_id = []
        frontVal = []
        for i in ret.data():
            tmpAttributeVal = i['n.' + attribute]
            if(tmpAttributeVal == None):
                continue
            if(self.judgeAttributeFitTime(tmpAttributeVal,timeType)):
                continue
            tmp_list.append(tmpAttributeVal)
            tmp_list_id.append(i['id(n)'])
        len_list = len(tmp_list)
        print(tmp_list)
        print(tmp_list_id)
        for i in range(len_list):
            frontVal.append(tmp_list[i])
            tmp_list[i] = self.deal_datetime(str(tmp_list[i]),timeType)
        print(tmp_list)
        for i in range(0, len_list):
            try:
                sql = "match(n:" + val + ") where id(n)=" + str(
                    tmp_list_id[i]) + " set n." + attribute + "= \'" + tmp_list[i] + "\'"
                self.graph.run(sql)
                TCleaningLog.objects.create(entity_id=str(tmp_list_id[i]),
                                            user_id=user_id,
                                            cleaning_rule_id=rule_id,
                                            cleaning_content=frontVal[i],
                                            cleaning_result='success',
                                            category_id=all_list_cate_id[cnt], repo_id=repo_id)
            except   Exception as e:
                TCleaningLog.objects.create(entity_id=str(tmp_list_id[i]),
                                            user_id=user_id,
                                            cleaning_rule_id=rule_id,
                                            cleaning_content=frontVal[i],
                                            cleaning_result='fail',
                                            category_id=all_list_cate_id[cnt], repo_id=repo_id)

    def cleaningAttributeNum(self,val,attribute,user_id,rule_id,rule_content,all_list_cate_id,cnt,repo_id,ruleStr):
        sql = "match(n:" + val + ") return n." + attribute + ",id(n)"
        ret = self.graph.run(sql)
        tmp_list = []
        tmp_list_id = []
        frontVal = []
        for i in ret.data():
            tmpAttributeVal = i['n.' + attribute]
            if (tmpAttributeVal == None):
                continue
            if(self.judgeAttributeFitNum(tmpAttributeVal,ruleStr)):
                continue
            #print(str(tmpAttributeVal),ruleStr)
            tmp_list.append(tmpAttributeVal)
            tmp_list_id.append(i['id(n)'])
        len_list = len(tmp_list)
        #print(tmp_list)
        #print(tmp_list_id)
        for i in range(len_list):
            frontVal.append(tmp_list[i])
            tmp_list[i] = Decimal(tmp_list[i]).quantize(Decimal(ruleStr))
        #print(tmp_list)

        for i in range(0, len_list):
            try:
                sql = "match(n:" + val + ") where id(n)=" + str(
                    tmp_list_id[i]) + " set n." + attribute + "= " + str(tmp_list[i])
                self.graph.run(sql)
                print(sql)
                TCleaningLog.objects.create(entity_id=str(tmp_list_id[i]),
                                            user_id=user_id,
                                            cleaning_rule_id=rule_id,
                                            cleaning_content=frontVal[i],
                                            cleaning_result='success',
                                            category_id=all_list_cate_id[cnt], repo_id=repo_id)
            except   Exception as e:
                TCleaningLog.objects.create(entity_id=str(tmp_list_id[i]),
                                            user_id=user_id,
                                            cleaning_rule_id=rule_id,
                                            cleaning_content=frontVal[i],
                                            cleaning_result='fail',
                                            category_id=all_list_cate_id[cnt], repo_id=repo_id)


    def judgeAttributeFitTime(self,tmpAttributeVal,timeType):

        tmpAttributeValStr = str(tmpAttributeVal)
        #判断tmpAttributeVal 和 timeType对应的类型是否相同
        ######
        #_numrule 规则 '-' 的数目 colonnumrule 规则':'的数目
        #_num '-'的数目 colnnum ':'的数目
        _numrule = 0
        colonnumrule = 0
        _num = 0
        colonnum = 0

        if(timeType == 4):
            _numrule=2
        elif(timeType == 5):
            _numrule=1
        elif(timeType == 6):
            _numrule=2
            colonnumrule=2
        strLen = len(tmpAttributeValStr)
        for i in range(strLen):
            if(tmpAttributeValStr[i] == '-'):
                _num+=1
            elif(tmpAttributeValStr[i] == ':'):
                colonnum+=1
                #print(self.calcDigicalNum(tmpAttributeValStr),self.calcDigicalNum(ruleStr) )
        if(_numrule == _num and  colonnumrule ==colonnum  ):
            return True
        #if(ret_type == 4 ):
        #    ret_string = ret_string + ret_l[0] + '-' + ret_l[1] +'-' + ret_l[2]
        #elif(ret_type == 5):
        #    ret_string = ret_string + ret_l[0] + '-' + ret_l[1]
        #elif(ret_type == 6 ):
        #    ret_string = ret_string + ret_l[0] + '-' + ret_l[1] + '-' + ret_l[2] + ' ' + ret_l[3]+ ':' + ret_l[4]+':' + ret_l[5]
        return False

    def judgeAttributeFitNum(self,tmpAttributeVal,ruleStr):

        ok = 0
        tmpAttributeValStr = str(tmpAttributeVal)
        #print(self.calcDigicalNum(tmpAttributeValStr),self.calcDigicalNum(ruleStr) )
        if(self.calcDigicalNum(tmpAttributeValStr) ==self.calcDigicalNum(ruleStr) ):
            return True
        return False

    def calcDigicalNum(self,numberString):
        strLen = len(numberString)
        st = -1
        for  i in range(strLen):
            if(numberString[i] == '.'):
                st = i+1
        num = 0
        if(st !=-1):
            num = strLen-1 - st + 1
        return num

    def judgeNodeIfExistInNeo4j(self,label, attributeDict):
        """
        功能: 判断这个节点是否存在
        :param label:   数据类型str  节点标签
        :param attributeDict:  数据类型dict 节点属性
        :return: 节点存在True  不存在False
        """
        sql = ' match(n'
        if(label !=None):
            sql = sql + ':'+label
        sql +=' )'
        if(attributeDict != None):
            sql = sql +" where "
            cnt = 0
            for key in attributeDict.keys():
                if(cnt !=0):
                    sql = sql + ' and '
                if(key == 'id'):
                    sql += ' id(n)='+str(attributeDict[key])
                else:
                    sql +=' n.'+str(key) +"="+str(attributeDict[key])
                cnt +=1
        #print(sql)
        sql = sql + "return id(n) "
        result=self.graph.run(sql)
        count = 0
        for node in result:
            print(node['id(n)'])
            count +=1
        ans =False
        if(count > 0):
            ans = True
        return  ans

    def deleteRealtionship(self,categoryOne,attributeDictOne,categoryTwo,attributeDictTwo,relationshipName):
        """
        功能删除两个节点的关系
        categoryOne        数据类型str  第一个节点的类目
        attributeDictOne   数据类型dict 第一个节点的属性
        categoryTow        数据类型str  第二个节点的类目
        attributeDictTwo   数据类型dict 第二个节点的属性
        relationshipName   数据类型str  关系的名字
        :return: 无
        """
        #match(n: 开开开_1_1)-[r: 组织]->(m:电影_1_1) where n.名字 = '部门' and m.名字 = '片源' delete  r

        sql = "match(n"
        if(categoryOne!=None and len(categoryOne)!=0):
            sql = sql + ":"+str(categoryOne)
        sql= sql +")"
        sql=sql + "-[r"
        if(relationshipName!=None and len(relationshipName)!=0):
            sql = sql + ":"+relationshipName
        sql=sql +"]"
        sql = sql + "->(m"
        if(categoryTwo!=None and len(categoryTwo)!=0):
            sql = sql + ":"+str(categoryTwo)
        sql = sql + ")"
        if(attributeDictOne != None or attributeDictTwo !=None ):
            sql =sql + " where "
            cnt = 0
            if(attributeDictOne != None):
                for key in attributeDictOne.keys():
                    if(cnt !=0):
                        sql = sql + " and "
                    if(key=='id'):
                        sql = sql + " id(n)="+str(attributeDictOne[key])
                    else:
                        sql = sql + " n."+str(key)+"="+"\'"+str(attributeDictOne[key])+"\'"
                    cnt+=1
            if (attributeDictTwo != None):
                for key in attributeDictTwo.keys():
                    if (cnt != 0):
                        sql = sql + " and "
                    if (key == 'id'):
                        sql = sql + " id(m)=" + str(attributeDictTwo[key])
                    else:
                        sql = sql + " m." + str(key) +"="+ "\'" + str(attributeDictTwo[key]) + "\'"
                    cnt += 1
        sql = sql + " delete r"
        print(sql)
        self.graph.run(sql);
        #建立关系
        #match(n:演员_1_1),(m:电影_1_1) where n.名字='孟佳营' and m.名字='我的名字。'  create(n)-[r:组织]->(m)
