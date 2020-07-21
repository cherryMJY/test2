import re
import time
from django.core.exceptions import ObjectDoesNotExist
from django.forms import model_to_dict
from numpy import unicode

from model.models import *
from django.utils import timezone
from model.mongodb import Mongodb
from model.neo4j import Neo4j
from pyhanlp import *


class some_data_deal_func(object):
    def __init__(self):
        self.a = 1

    #计算两个neo4j数据的相似度
    def calculate_similarity(self,attribute_val_one,attribute_val_two,key_attribute_list_similarity_threshold):
        list_len = len(attribute_val_one)
        #相似度计算
        #1数字
        #2文本
        ans = 0.0
        ok = 0
        for i in range(0,list_len):
            tmp = 0
            if self.is_number(attribute_val_one[i]):
                tmp = self.calculate_digit_similarity(attribute_val_one[i],attribute_val_two[i])

            else:
                tmp = self.calculate_text_similarity(attribute_val_one[i],attribute_val_two[i])
            ans = ans + tmp
            if tmp <key_attribute_list_similarity_threshold[i]:
                ok = 1
        if(ok == 1):
            return 0
        else:
            return ans / list_len

    def is_number(self, num):
        '''
        判断是否为数字
        :param num:
        :return:
        '''
        pattern = re.compile(r'^[-+]?[-0-9]\d*\.\d*|[-+]?\.?[0-9]\d*$')
        result = pattern.match(str(num))
        if result:
            return True
        else:
            return False

    def calculate_digit_similarity(self, number1, number2):
        tmp = max(number1-number2,number2-number1)
        tmp = 1 - 1.0 * tmp / max(number1, number2)
        return tmp

    def calculate_text_similarity(self, text1, text2):
        print(111)
        text1_len = len(text1)
        text2_len = len(text2)
        dp = [[0 for i in range(10)] for j in range(10)]
        for i in range(1, text1_len+1):
            dp[i][0] = i
        for i in range(1, text2_len+1):
            dp[0][i] = i
        dp[0][0] = 0
        print(text1, text2)
        for i in range(1, text1_len+1):
            for j in range(1, text2_len+1):
                if text1[i-1] == text2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = min(min(dp[i-1][j]+1, dp[i][j-1]+1), dp[i-1][j-1]+1)

        return  1 - dp[text1_len][text2_len] / max(text1_len, text2_len)

    # 需要一个方法 传入一个属性名list 然后返回最相近的类目名字和相似度
    # 最接近的catetory计算
    def calculate_nearest_category(self, list_attribute, repo_id):
        # repo_id = request.POST['repo_id']
        category_res = TCategory.objects.filter(repo_id=repo_id)
        ans_id = -1
        ans_sim = -1
        for category in category_res:
            category_dict = model_to_dict(category)
            tmp_category_id = category_dict['id']
            attribute_res = TAttribute.objects.filter(category_id=tmp_category_id)
            list_attribute_name = []
            for attribute in attribute_res:
                attribute_dict = model_to_dict(attribute)
                list_attribute_name.append(attribute_dict['attribute_name'])
            cnt = 0
            list1_size = len(list_attribute)
            list2_size = len(list_attribute_name)

            for i in list_attribute_name:
                for j in list_attribute:
                    if (i == j):
                        cnt += 1
            sim = 1.0 * cnt / (list1_size + list2_size - cnt)
            if (sim > ans_sim):
                ans_sim = sim
                ans_id = tmp_category_id
            # 然后在attribte中查询出来
        if (ans_sim <= 0.2):
            ans_id = -1
        return (ans_id)

    def update_t_mapping_rule(self, repo_id, create_id):
        """
        功能
        跑一遍mongodb里面数据，拿出没有出现在t_attribute表里面的属性，建立属性映射规则
        在属性映射规则里面如果有新建立的同名属性 那么删除这条规则
        :param repo_id:    数据类型int 知识图谱id
        :param create_id:  数据类型int 创建者id
        :return:
        """
        # 要对每个类目进行计算
        return_category = TCategory.objects.filter(repo_id=repo_id, create_id=create_id)

        category_name_list = []
        category_id_list = []
        for val in return_category:
            val_dict = model_to_dict(val)
            category_name_list.append(val_dict['category_name'])
            category_id_list.append(val_dict['id'])

        list_len = len(category_name_list)
        # print(list_len)
        # print(category_name_list)
        # print(category_id_list)
        for i in range(0, list_len):
            tmp_id = category_id_list[i]
            attribute_name_alias_map = {}
            return_attribute = TAttribute.objects.filter(category_id=tmp_id)

            # 把这个函数封装一下不然就太长了
            # 输入是查询的所有attribute 返回一个map
            # attribute 不仅是自己的attribute 还有父亲节点的attribute
            # 这边这个attribute_name_alias_map里面还要放进去他们夫妻节点的东西
            attribute_name_alias_map = self.return_attribute_name_map(return_attribute, attribute_name_alias_map)
            # print(attribute_name_alias_map)

            ret_cate = TCategory.objects.get(id=tmp_id)
            ret_cate_dict = model_to_dict(ret_cate)
            father_category_id = ret_cate_dict['father_category_id']
            # print(father_category_id,type(father_category_id))
            if (str(-1) != father_category_id):
                return_attribute_father = TAttribute.objects.filter(category_id=father_category_id)
                attribute_name_alias_map = self.return_attribute_name_map(return_attribute_father,
                                                                          attribute_name_alias_map)
                ret_cate_father = TCategory.objects.get(id=father_category_id)
                ret_cate_dict_father = model_to_dict(ret_cate_father)
                father_father_category_id = ret_cate_dict_father['father_category_id']
                # print(father_father_category_id)
                if (str(-1) != father_father_category_id):
                    return_attribute_father_father = TAttribute.objects.filter(category_id=father_father_category_id)
                    attribute_name_alias_map = self.return_attribute_name_map(return_attribute_father_father,
                                                                              attribute_name_alias_map)

            # print(attribute_name_alias_map)

            news_col = Mongodb(db='knowledge', collection='text').get_collection()
            # print(list_len)

            # 这边所有的名字已经在attribute_name_alias_map里面
            _insert_mapping_rule_attribute_name_list = []
            _insert_mapping_rule_attribute_coverage_rate_list = []
            category_id = category_id_list[i]
            # 从mongodb里面找
            attribute_name_map = {}
            tmp_list = news_col.find({'category_id': category_id})
            num = 0
            for val in tmp_list:
                val = val["value"]
                num += 1
                if val is not None:
                    for key in val.keys():
                        # print(key)
                        # print(attribute_name_map)
                        # print(key in attribute_name_map )
                        if key == '_id' or key == 'file_id' or key == 'category_id':
                            continue
                        elif key in attribute_name_map:
                            attribute_name_map[key] += 1
                        else:
                            attribute_name_map[key] = 1
            # 这边这个在没有实体的时候 假如说t_mapping_rule里面有多余的值那么就要进行更新
            # 所以只要有一个就不用删除一旦一个都没有了 那么就不用删除
            # 如果你想写得再细致一点那么就确认这个属性还在 假如说不在了那么就删除
            #
            delete_id_list = []
            # print(111)

            return_mapping_rule = TMappingRule.objects.filter(category_id=category_id, create_id=create_id)
            # print(111)
            for rule in return_mapping_rule:

                rule_dict = model_to_dict(rule)
                print(rule_dict)
                rule_dict_id = rule_dict['id']
                rule_dict_attribute_name = rule_dict['attribute_name']
                if rule_dict_attribute_name not in attribute_name_map.keys():
                    delete_id_list.append(rule_dict_id)
            for mapping_rule_id in delete_id_list:
                # 其实删除的话最好存到日志里面不然又会出问题
                rule_mapping = TMappingRule.objects.get(id=mapping_rule_id)
                rule_mapping.delete()
            #
            # print(attribute_name_map)
            #计算实体覆盖率
            if attribute_name_map is not None:
                for key in attribute_name_map.keys():
                    if (key in attribute_name_alias_map):
                        a = 1
                    else:
                        _insert_mapping_rule_attribute_name_list.append(key)
                        coverage_rate = 1.0 * attribute_name_map[key] / num
                        _insert_mapping_rule_attribute_coverage_rate_list.append(coverage_rate)
            attribute_name_list_len = len(_insert_mapping_rule_attribute_name_list)
            dt = timezone.now()
            # print(attribute_name_list_len)
            # print(_insert_mapping_rule_attribute_name_list)
            for k in range(0, attribute_name_list_len):
                attribute_name_val = _insert_mapping_rule_attribute_name_list[k]
                attribute_coverage_val = _insert_mapping_rule_attribute_coverage_rate_list[k]
                obj = TMappingRule.objects.filter(attribute_name=attribute_name_val, category_id=category_id,
                                                  create_id=create_id).first()
                # print(attribute_name_val,attribute_coverage_val)
                if (obj is None):
                    # create
                    TMappingRule.objects.create(attribute_name=attribute_name_val,
                                                coverage_rate=attribute_coverage_val,
                                                create_time=str(dt)[:19],
                                                category_id=category_id,
                                                create_id=create_id)
                else:
                    # upadte
                    obj.coverage_rate = attribute_coverage_val
                    obj.create_time = str(dt)[:19]
                    obj.save()
        #在添加属性的时候t_mapping_rule进行删除
        retCategory = TCategory.objects.filter(repo_id=repo_id,create_id=create_id)
        for val in retCategory:
            categoryDict = model_to_dict(val)
            categoryId = categoryDict['id']
            retAttribute = TAttribute.objects.filter(category_id=categoryId)
            attributeNameList=[]
            for att in retAttribute:
                attDict =model_to_dict(att)
                attributeNameList.append(attDict['attribute_name'])
            retMappingRule=TMappingRule.objects.filter(category_id=category_id,create_id=create_id)
            deleteMappingRuleIdList=[]
            for rule in retMappingRule:
                ruleDict = model_to_dict(rule)
                attributeName = ruleDict['attribute_name']
                if(attributeName in attributeNameList):
                    deleteMappingRuleIdList.append(ruleDict['id'])
            for mapRuleId in  deleteMappingRuleIdList:
                mapRule = TMappingRule.objects.get(id=mapRuleId)
                mapRule.delete()
        return 1

    def return_attribute_name_map(self, return_attribute, first_map):
        for val in return_attribute:
            val_dict = model_to_dict(val)
            # print(val_dict)
            attribute_id = val_dict['id']
            # 属性名
            attribute_name = val_dict['attribute_name']
            first_map[attribute_name] = 1
            # 属性别名

            return_attribute_alias = TAttrbuteAlias.objects.filter(attribute_id=attribute_id)
            # print(attribute_id)
            for j in return_attribute_alias:
                j_dict = model_to_dict(j)
                attribute_alias = j_dict['attribute_alias']
                first_map[attribute_alias] = 1
        return first_map

    #输入category_id  然后返回属性表 添加到ret_list上
    def input_category_id_return_attribute_list(self, category_id, ret_list):
        res = TAttribute.objects.filter(category_id=category_id)
        # 把这一块进行封装 输入catgory_id 返回list
        for att in res:
            att_dict = model_to_dict(att)
            now_dict = {}
            now_dict['id'] = att_dict['id']
            now_dict['attribute_name'] = att_dict['attribute_name']
            ret_list.append(now_dict)
        return ret_list

    def find_children(self, repo_id, create_id, father_id):
        ret_l = {}
        level_two = TCategory.objects.filter(repo_id=repo_id, create_id=create_id, category_level=2)
        level_three = TCategory.objects.filter(repo_id=repo_id, create_id=create_id, category_level=3)
        level_tow_list = []
        for val_two in level_two:
            val_two_dict = model_to_dict(val_two)
            val_two_id = val_two_dict['id']
            # print(val_two_dict)
            # print(type(val_two_dict['father_category_id']),type(father_id))
            if (int(val_two_dict['father_category_id']) == father_id):
                tmp_list_two = {}
                tmp_list = []
                for val_three in level_three:
                    val_three_dict = model_to_dict(val_three)
                    # print(type(val_three_dict['father_category_id']),type(val_two_id))
                    if (int(val_three_dict['father_category_id']) == val_two_id):
                        tmp_map = {}
                        tmp_map['id'] = val_three_dict['id']
                        tmp_map['category_name'] = val_three_dict['category_name']
                        tmp_list.append(tmp_map)
                tmp_list_two['level3_child'] = tmp_list
                tmp_list_two['id'] = val_two_id
                tmp_list_two['category_name'] = val_two_dict['category_name']
                level_tow_list.append(tmp_list_two)
        ret_l['level2_child'] = level_tow_list
        ret_l['id'] = father_id
        return_root = TCategory.objects.get(id=father_id)
        return_root_dict = model_to_dict(return_root)
        tmp_category = {}
        tmp_category['category_description'] = return_root_dict['category_description']

        find_attribute = TAttribute.objects.filter(category_id=father_id)
        tmp_list_attribute = []
        for attribute in find_attribute:
            ret_result = model_to_dict(attribute)
            ret_result.setdefault("attribute_datatype", TDataType.objects.get(id=ret_result["data_type_id"]).datatype_name)
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
            ret_result['create_time'] = str(ret_result["create_time"])[:19]
            tmp_list_attribute.append(ret_result)
        tmp_category['attribute'] = tmp_list_attribute
        ret_l['category'] = tmp_category
        return ret_l

    @staticmethod
    def get_all_attribute_by_category_id(category_id, return_field_list=None):
        """
        通过类目ID获取所有属性内容(包括父类继承的属性)
        :param category_id:类目ID
        :param return_field_list:设定返回哪些字段
        :return: return_field_list默认None时返回一个一个属性名列表，否则返回一个json列表，异常返回None
        """
        attribute_list = []
        try:
            while True:
                cur_category = TCategory.objects.get(id=category_id)
                attributes = TAttribute.objects.filter(category_id=cur_category.id)
                for item in attributes:
                    if return_field_list is None:
                        attribute_list.append(item.attribute_name)
                    else:
                        item = model_to_dict(item)
                        one_attribute = {}
                        for field in return_field_list:
                            one_attribute.setdefault(field, item[field])
                        attribute_list.append(one_attribute)
                if int(cur_category.father_category_id) != -1:
                    category_id = cur_category.father_category_id
                else:
                    break
        except ObjectDoesNotExist:
            return None
        return attribute_list

    def eventExtractionByTemplateMatching(self, request, hanlpUnit, sentence, eventLabelList, repoId, createId):
        """
        把术语单词假如到分词库里面 然后进行分词 得出想要的结果
        :param request:
        :param hanlpUnit:
        :param sentence:
        :param eventLabelList:
        :param repoId:
        :param createId:
        :return:
        """
        reteventList = []

        # print(sentence)
        sentenceDealResult = hanlpUnit.cut(sentence)
        # print(sentenceDealResult)
        wordList = []
        natureList = []
        for i in sentenceDealResult:
            splitRes = str(i).split(r"/")
            wordList.append(splitRes[0])
            natureList.append(splitRes[1])
        wordSize = len(wordList)
        # print(wordSize,natureList)
        cnt = 0
        for tmpList in eventLabelList:
            print(tmpList)
            ruleId = 1
            if (len(tmpList) == 3):
                ruleId = 2

            triggerWordList = []
            triggerWordIdList = []
            subjectCategoryList = []
            subjectCategoryIdList = []
            objectCategoryList = []
            objectCategoryIdList = []

            if (ruleId == 1):
                for i in range(wordSize):
                    if (natureList[i] == tmpList[2]):
                        triggerWordList.append(wordList[i])
                        triggerWordIdList.append(i)
                    elif (natureList[i] == tmpList[1]):
                        subjectCategoryList.append(wordList[i])
                        subjectCategoryIdList.append(i)
                    elif (natureList[i] == tmpList[3]):
                        objectCategoryList.append(wordList[i])
                        objectCategoryIdList.append(i)
                # 枚举三元组
                for subjectId in subjectCategoryIdList:
                    for triggerId in triggerWordIdList:
                        if (subjectId > triggerId):
                            continue
                        for objectId in objectCategoryIdList:
                            if (triggerId > objectId):
                                continue
                            oneEventList = []
                            oneEventList.append(cnt)
                            oneEventList.append(wordList[subjectId])
                            oneEventList.append(wordList[triggerId])
                            oneEventList.append(wordList[objectId])
                            reteventList.append(oneEventList)
            else:
                for i in range(wordSize):
                    if (natureList[i] == tmpList[2]):
                        triggerWordList.append(wordList[i])
                        triggerWordIdList.append(i)
                    elif (natureList[i] == tmpList[1]):
                        subjectCategoryList.append(wordList[i])
                        subjectCategoryIdList.append(i)
                # 枚举两元组
                for subjectId in subjectCategoryIdList:
                    for triggerId in triggerWordIdList:
                        if (subjectId > triggerId):
                            continue
                        oneEventList = []
                        oneEventList.append(cnt)
                        oneEventList.append(wordList[subjectId])
                        oneEventList.append(wordList[triggerId])
                        reteventList.append(oneEventList)
            cnt += 1
        print(reteventList)
        return reteventList

    #输入是 categoryID repoID createId 返回这个类目的所有在neo4j里面的名字
    def inputCategoryIdReturnName(self, categoryId, repoId, createId):
        """
        返回这个类目的所有在neo4j里面的名字
        :param categoryId:
        :param repoId:
        :param createId:
        :return:
        """
        categoryName = ''
        # return category_name + "_" + str(request.session["user_id"]) + "_" + str(request.session["repo_id"])
        retCategory = TCategory.objects.filter(id=categoryId, repo_id=repoId, create_id=createId)
        for i in retCategory:
            oneCategory = model_to_dict(i)
            categoryName = oneCategory['category_name']
        neo4jLabelName = categoryName + "_" + str(createId) + "_" + str(repoId)
        numberOne = 1
        attributeaffair = TAttribute.objects.get(category_id=numberOne)
        attributeaffairDict = model_to_dict(attributeaffair)
        attributeName = attributeaffairDict['attribute_name']

        return Neo4j().ques_id_val(neo4jLabelName, attributeName)

    def nodeCmp(self, first, second):
        # global  attributeName
        if (first['发生时间'] > second['发生时间']):
            return 1
        elif (first['发生时间'] < second['发生时间']):
            return -1
        return 0

    def bubbleSort(self, idList, priorityList):
        """
        :param idList: 序号列表
        :param priorityList: 优先级列表
        :return: 排完序  (序号列表，优先级列表)
        """
        lens = len(idList)

        for i in range(0, lens):
            minInd = i
            for j in range(i + 1, lens):
                if (priorityList[j] < priorityList[minInd]):
                    minInd = j
            t = idList[i]
            idList[i] = idList[minInd]
            idList[minInd] = t

            t = priorityList[i]
            priorityList[i] = priorityList[minInd]
            priorityList[minInd] = t

        return (idList, priorityList)

    def mapAddVal(self, key, value, tmpMap):
        """
        功能:把(key,value)插入到tmpMap
        返回tmpMap
        :param key:     数据类型str   要插入的词
        :param value:   数据类型str   要插入词的词性
        :param tmpMap:  数据类型dict  要插入的map
        :return: tmpMap 数据类型dict  返回tmpMap
        """
        if (key in tmpMap.keys()):
            tmpList = tmpMap[key]
            if (value not in tmpList):
                tmpList.append(value)
                tmpMap[key] = tmpList
        else:
            tmpList = []
            tmpList.append(value)
            tmpMap[key] = tmpList
        return tmpMap

    def addCountMap(self, keyList, countMap):
        """
        功能 把keyList里面的词当做1插入到countMap里面去
        :param keyList:  数据类型list 要插入进去的字符串list
        :param countMap: 数据类型Dict map<string,int>
        :return: countMap 数据类型Dict
        """
        for key in keyList:
            if (key in countMap.keys()):
                countMap[key] = countMap[key] + 1
            else:
                countMap[key] = 1
        return countMap

    def addColorMap(self, keyList, color, colorMap):
        """
        功能 把keyList里面的词当做1插入到colorMap里面去 如果没出现过，那么用一个新的数字
        否则用原来的数字
        :param keyList:  数据类型list 要插入进去的字符串list
        :param color:    数据类型int 当前用到的颜色的数字
        :param colorMap: 数据类型Dict map<string,int>
        :return: colorMap 数据类型Dict
        color 数据类型int 已经用到的颜色数字(这个数字还没用)
        """
        for key in keyList:
            if (key not in colorMap.keys()):
                colorMap[key] = color
                color = color + 1
        return colorMap, color

    def findAllRealtionship(self, repoId, createId):
        """
        :param repoId:    数据类型int 知识图谱id
        :param createId:  数据类型int 用户id
        :return:
        retList  数据类型Dict   id和关系名字
        例子
        [{'id': 1, 'attribute_name': '电影'}, {'id': 2, 'attribute_name': '导演'}, {'id': 3, 'attribut
        e_name': '电影'}, {'id': 4, 'attribute_name': '演员'}, {'id': 5, 'attribute_name': '123'}, {'i
        d': 6, 'attribute_name': ''}, {'id': 7, 'attribute_name': '123'}, {'id': 8, 'attribute_name':
        ''}]
        """
        retCategory = TCategory.objects.filter(repo_id=repoId, create_id=createId, category_type=1)

        retList = []
        for item in retCategory:
            data_type = TDataType.objects.get(category_id=item.id)
            attributes = TAttribute.objects.filter(data_type_id=data_type.id)
            for attribute_item in attributes:
                retList.append({"id": attribute_item.id, "attribute_name": attribute_item.attribute_name})

        return retList

    def updateColorDict(self, maxColor, object_name, colorDict):
        """
        功能:查询object_name的对应color
        假如color不存在再colorDict里面添加这个东西
        :param maxColor:    数据类型int   当前用到的最大颜色的数值
        :param object_name: 数据类型str   要查询的目标的名字
        :param colorDict:   数据类型dict  dict[key]=val
        :return: maxColor          数据类型int   当前最大颜色
                 object_name_tag   数据类型int   当前查询颜色
                 colorDict         数据类型Dict  颜色的Dict
        """
        object_name_tag = 0
        if (colorDict != None and object_name in colorDict.keys()):
            object_name_tag = colorDict[object_name]
        else:
            maxColor += 1
            colorDict[object_name] = maxColor
            object_name_tag = maxColor
        return maxColor, object_name_tag, colorDict

    def countColor(self,ansRelationshipExtractResult,event_extract_result):
        """
        功能 统计事件抽取和关系抽取结果中每个词对应的类目
        对于每一个类目找到对应的颜色
        :param ansRelationshipExtractResult:  数据类型listdict 关系抽取的结果
        :param event_extract_result:          数据类型listdict 事件抽取的结果
        :return: tagCategory                  数据类型listdict 类目对应颜色
        """
        tmpMap = {}
        countMap = {}
        colorMap = {}
        color = 1
        # word "tag": 1, "nums": 1
        for val in ansRelationshipExtractResult:
            object_from_category = val['object_from_category']
            object_to_category = val['object_to_category']
            object_from_name = val['object_from_name']
            object_to_name = val['object_to_name']
            object_relationship_name = val['object_relationship_name']
            object_relationship_category = val['object_relationship_category']
            # 关系主体
            tmpMap = some_data_deal_func().mapAddVal(object_from_name, object_from_category.split('_')[0], tmpMap)
            # 关系客体
            tmpMap = some_data_deal_func().mapAddVal(object_to_name, object_to_category.split('_')[0], tmpMap)
            # 关系
            tmpMap = some_data_deal_func().mapAddVal(object_relationship_name, object_relationship_category.split('_')[0], tmpMap)

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
            tmpMap = some_data_deal_func().mapAddVal(eventSubject, eventSubjectLabel.split('_')[0], tmpMap)
            tempWordList.append(eventSubject)
            # 事件触发词
            tmpMap = some_data_deal_func().mapAddVal(triggerWord, triggerLabel.split('_')[0], tmpMap)
            tempWordList.append(triggerWord)

            # 事件客体
            if ('eventObject' in val.keys()):
                eventObject = val['eventObject']
                eventObjectLabel = val['eventObjectLabel']
                tmpMap = some_data_deal_func().mapAddVal(eventObject, eventObjectLabel.split('_')[0], tmpMap)
                tempWordList.append(eventObject)

        #里面存着这些东西dict(word ->list)
        for key in tmpMap.keys():
            value=tmpMap[key]
            valueLen = len(value)
            valStr = ''
            for i in range(valueLen):
                if(i>=1):
                    valStr+=','
                valStr += value[i]
            if(valStr not in colorMap.keys()):
                colorMap[valStr]=color
                color += 1
        tagCategory = []
        for key in colorMap.keys():
            tagCategory.append({'tag':colorMap[key],'category':key})
        return tagCategory

    def wordInsertToDict(self,word,wordDict):
        """
        功能: 在wordDict统计词的数目
        :param word:      数据类型str   要插入的词的下标
        :param wordDict:  数据类型dict  词要插入的dict
        :return: wordDict 数据类型dict  返回dict
        """
        if word is None:
            return wordDict
        if word in wordDict.keys():
            wordDict[word] += 1
        else:
            wordDict[word] = 1
        return wordDict

    def updatewordSegmentationResultsTag(self, object_nameindex, wordSegmentationResults, wordSegmentationResultsLen):
        """
        功能:在分词结果中把下标为object_nameindex的tag更新成为0
        :param object_nameindex:           数据类型int      要更新的下标
        :param wordSegmentationResults:    数据类型[[dict]] 分词结果
        :param wordSegmentationResultsLen: 数据类型int      分词结果第一维长度
        :return:wordSegmentationResults    数据类型[[dict]] 修改后的分词结果
        """
        for ind in range(wordSegmentationResultsLen):
            tmpList = wordSegmentationResults[ind]
            tmpListLen = len(tmpList)
            for j in range(tmpListLen):
                if wordSegmentationResults[ind][j]['num'] == object_nameindex:
                    wordSegmentationResults[ind][j]['tag'] = 0
        return wordSegmentationResults

    def dealArea(self, content):
        """
        :param content:         数据类型str   要处理的句子
        :return: locationList   数据类型list  列表里面是dict {'place':'浙江','index':10};
        """
        # for val in locationList:
        #    if (len(val['place']) > len(location)):
        #        location = val['place']
        #        locationindex = val['index'] + countIndex
        locationList = []
        cutResult = HanlpUnit().cut(content)
        cutResultlen = len(cutResult)
        for i in range(cutResultlen):
            tmp = str(cutResult[i]).split('/')
            if (tmp[1] == 'ns'):
                locationList.append({'place': tmp[0], 'index': i})
        return locationList

    def dealTime(self, content, timebase):
        """
        输入句子和基准事件返回事件的时间
        :param content:    数据类型str  要处理的句子
        :param timebase:   数据类型str  基准事件
        :return:  时间词语的下标 int  时间词语 str  时间str
        """
        timeformat = arrow.get(timebase).format('YYYY-M-D-H-m-s')
        timeList = timeformat.split('-')
        for i in range(6):
            timeList[i] = int(timeList[i])
        date_string = content
        str_len = len(date_string)
        # print(111)
        if re.match(r'\d+年\d+月\d+日', date_string):
            ind = 0
            tmp_num = 0
            for i in range(0, str_len):
                if (date_string[i] == ' '):
                    continue
                elif (date_string[i] >= '0' and date_string[i] <= '9'):
                    tmp_num = tmp_num * 10 + ord(date_string[i]) - ord('0')
                elif (date_string[i] == '年'):
                    timeList[0] = str(tmp_num)
                    tmp_num = 0
                elif (date_string[i] == '月'):
                    timeList[1] = str(tmp_num)
                    tmp_num = 0
                elif (date_string[i] == '日'):
                    timeList[2] = str(tmp_num)
                    tmp_num = 0
            timeStr = ''
            for i in range(6):
                if (i == 1 or i == 2):
                    timeStr += "-"
                elif (i == 3):
                    timeStr += " "
                elif (i == 4 or i == 5):
                    timeStr += ":"
                timeStr += str(timeList[i]);
            return -1, "", timeStr
        # print(222)
        wordList = ['今天', '明天', '后天', '昨天', '前天']
        valList = [0, 1, 2, -1, -2]
        # 这里会有问题
        # print(555)
        cutResult = HanlpUnit().cut(date_string)
        # print(666)
        cnt = 0
        print(111, cutResult)
        # print(type(cutResult))
        for val in cutResult:
            # print(val)
            # print(type(val))
            # print(str(val).split('/'))
            tmp = str(val).split('/')[0]
            print(tmp)
            if (tmp in wordList):
                ind = -1
                for i in range(5):
                    if (wordList[i] == tmp):
                        ind = i
                timeList[2] += valList[ind]
                timeStr = ''
                for i in range(6):
                    if (i == 1 or i == 2):
                        timeStr += "-"
                    elif (i == 3):
                        timeStr += " "
                    elif (i == 4 or i == 5):
                        timeStr += ":"
                    timeStr += str(timeList[i])
                # print(cnt, timeStr)
                return cnt, tmp, timeStr
            cnt += 1
        print(444)
        timeStr = ''
        for i in range(6):
            if (i == 1 or i == 2):
                timeStr += "-"
            elif (i == 3):
                timeStr += " "
            elif (i == 4 or i == 5):
                timeStr += ":"
            timeStr += str(timeList[i])
        print(333)
        return -1, "", timeStr