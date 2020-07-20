from model.hanlpUnit import HanlpUnit
from django.core.exceptions import ObjectDoesNotExist
from controller.baseController import BaseController
from model.neo4j import Neo4j
from model.models import *
from model.mongodb import Mongodb
from django.forms.models import model_to_dict
from model.some_data_deal_func import some_data_deal_func
from Time_NLP.time_deal import Time_deal
from bson import ObjectId


class ExtractUnit:
    def __init__(self):
        self.hanlp_tool = HanlpUnit()

    @staticmethod
    def extract_relationship_from_structured_data(request, category_id, json_data):
        """
        从结构化数据中抽取关系
        :param request:
        :param category_id:类目id
        :param json_data:新增节点数据
        :return:
        """
        if category_id == -1:
            return
        neo4j = Neo4j()
        # 片段1 找出所有由该条数据指出的关系
        relationship_attribute_list = []
        new_node_category_name = TCategory.objects.get(id=category_id).category_name
        new_node_category_name = BaseController.get_category_name(request=request, category_name=new_node_category_name)
        all_attribute = TAttribute.objects.filter(category_id=category_id)
        # 获取所有该数据所属类目指向的类目
        for item in all_attribute:
            cur_data_type = TDataType.objects.get(id=item.data_type_id)
            if cur_data_type.category_id == -1 or item.attribute_name not in json_data:
                continue
            else:
                if item.is_single_value == 1 or type(json_data[item.attribute_name]) == "str":
                    attribute_content = [json_data[item.attribute_name]]
                else:
                    attribute_content = json_data[item.attribute_name]
                relationship_attribute_list.append(
                    {"attribute_name": attribute_content, "object_category_id": cur_data_type.category_id,
                     "relationship_name": item.attribute_name})

        # 遍历类目数据匹配名字
        for item in relationship_attribute_list:
            for attribute_item in item["attribute_name"]:
                category_name = TCategory.objects.get(id=item["object_category_id"]).category_name
                category_name_to = BaseController.get_category_name(request=request, category_name=category_name)
                # category_name_to = category_name + "_1_2"

                object_from = {"label_name": category_name_to, "content": {"名字": attribute_item}}
                match_result = neo4j.match(object_from=object_from)
                if match_result is not None and len(match_result) == 1:
                    node = match_result[0]["n1"]
                    relationship_match = neo4j.match(
                        object_from={"label_name": new_node_category_name, "content": {"_id": json_data["_id"]}},
                        object_to={"label_name": category_name_to, "content": {"_id": node["_id"]}},
                        relationship={"label_name": item["relationship_name"], "content": {}}, return_info="2")
                    print(relationship_match)
                    if relationship_match is not None and len(relationship_match) == 0:
                        neo4j.createRelationship(
                            labelOne=new_node_category_name,
                            labelTwo=category_name_to, relationShipName=item["relationship_name"],
                            propertyOne={"_id": json_data["_id"]}, propertyTwo={"_id": node["_id"]})

        # 片段2 找出所有指向该数据的参数
        if "名字" not in json_data or json_data["名字"] == "":
            return
        data_type_to = TDataType.objects.get(category_id=category_id)
        relationship_attribute_from = TAttribute.objects.filter(data_type_id=data_type_to.id)
        for item in relationship_attribute_from:
            try:
                category_from = TCategory.objects.get(id=item.category_id, repo_id=request.session["repo_id"], create_id=request.session["user_id"])
                category_name_from = BaseController.get_category_name(request=request, category_name=category_from.category_name)
                object_from = {"label_name": category_name_from, "content": {item.attribute_name: json_data["名字"]}}
                match_result = neo4j.match(object_from=object_from)
                if match_result is not None and len(match_result) == 1:
                    node = match_result[0]["n1"]
                    relationship_match = neo4j.match(
                        object_from={"label_name": category_name_from, "content": {"_id": node["_id"]}},
                        object_to={"label_name": new_node_category_name, "content": {"_id": json_data["_id"]}},
                        relationship={"label_name": item.attribute_name, "content": {}}, return_info="2")
                    print(relationship_match)
                    if relationship_match is not None and len(relationship_match) == 0:
                        neo4j.createRelationship(
                            labelOne=category_name_from,
                            labelTwo=new_node_category_name, relationShipName=item.attribute_name,
                            propertyOne={"_id": node["_id"]}, propertyTwo={"_id": json_data["_id"]})
            except ObjectDoesNotExist:
                continue

    @staticmethod
    def merge_list(list1, list2):
        for item in list2:
            if item not in list1:
                list1.append(item)
        return list1

    def extract_relationship_from_unstructured_data(self, request, file_id):
        """
        从非结构化数据中抽取关系
        :param request:
        :return:
        """
        print("------------------------非结构关系抽取")
        tmp_info = {'file_id': file_id, 'user_id': request.session["user_id"], 'repo_id': request.session["repo_id"]}
        collection = Mongodb(db='knowledge', collection='text').get_collection()
        ret_entity = collection.find(tmp_info)
        ret_entity_map = list()
        for item in ret_entity:
            if "内容" in item["value"]:
                ret_entity_map.append(item)

        if len(ret_entity_map) == 0:
            print("无可抽取内容")
            return
        relationship_list = []
        all_category = TCategory.objects.filter(repo_id=request.session["repo_id"], create_id=request.session["user_id"], category_type=1)
        added_category_id = set()
        for category_item in all_category:
            try:
                one_data_type = TDataType.objects.get(category_id=category_item.id, repo_id=request.session["repo_id"], create_id=request.session["user_id"])
                attribute_list = TAttribute.objects.filter(data_type_id=one_data_type.id)
                category_to_name = BaseController.get_category_name(request, category_item.category_name)
                for attribute_item in attribute_list:
                    category_from = TCategory.objects.get(id=attribute_item.category_id)
                    category_from_name = BaseController.get_category_name(request, category_from.category_name)
                    one_relationship = list()
                    one_relationship.append(attribute_item.attribute_name)
                    one_relationship.append(category_from_name)
                    one_relationship.append(BaseController.get_category_name(request, attribute_item.attribute_name))
                    one_relationship.append(category_to_name)
                    relationship_list.append(one_relationship)
                    self.hanlp_tool.add_word_list([{"word": alia_item.attribute_alias,
                                                   "mask": BaseController.get_category_name(request,
                                                                                            attribute_item.attribute_name)}
                                                  for alia_item in
                                                  TAttrbuteAlias.objects.filter(attribute_id=attribute_item.id)])
                    print([{"word": alia_item.attribute_alias,
                                                   "mask": BaseController.get_category_name(request,
                                                                                            attribute_item.attribute_name)}
                                                  for alia_item in
                                                  TAttrbuteAlias.objects.filter(attribute_id=attribute_item.id)])
                    if category_from.id not in added_category_id:
                        ret_list_id, ret_list_val = some_data_deal_func().inputCategoryIdReturnName(categoryId=category_from.id, repoId=request.session["repo_id"], createId=request.session["user_id"])
                        self.hanlp_tool.add_word_list([{"word": val_item, "mask": category_from_name} for val_item in ret_list_val])
                        added_category_id.add(category_from.id)
                if category_item.id not in added_category_id:
                    ret_list_id, ret_list_val = some_data_deal_func().inputCategoryIdReturnName(
                        categoryId=category_item.id, repoId=request.session["repo_id"],
                        createId=request.session["user_id"])
                    self.hanlp_tool.add_word_list(
                        [{"word": val_item, "mask": category_to_name} for val_item in ret_list_val])
                    added_category_id.add(category_item.id)
            except ObjectDoesNotExist:
                continue
        neo4j = Neo4j()
        cout = 0
        for i in ret_entity_map:
            _id = i['_id']
            value = i['value']
            content = value['内容']
            text = HanlpUnit().get_text_from_html(content)

            sentenceList = self.hanlp_tool.split_paragraph(text)
            extract_relationship = []
            for sent in sentenceList:
                sent = sent.strip()

                relationships = self.eventExtractionByTemplateMatching(sent, relationship_list)
                # relationships = self.eventExtractionByTemplateMatching(text.strip(), relationship_list)
                for item in relationships:
                    relation_id = item[0]
                    cur_relationship = relationship_list[relation_id]

                    extract_relationship.append(
                        {"object_from_category": cur_relationship[1], "object_to_category": cur_relationship[3],
                         "object_from_name": item[1], "object_relationship_name": item[2], "object_to_name": item[3]})
                    object1 = neo4j.match(object_from={"label_name": cur_relationship[1], "content": {"名字": item[1]}})
                    object2 = neo4j.match(object_from={"label_name": cur_relationship[3], "content": {"名字": item[3]}})
                    if object1 is not None and len(object1) == 1 and object2 is not None and len(object2) == 1:
                        neo4j.createRelationship(labelOne=cur_relationship[1], labelTwo=cur_relationship[3],
                                                   relationShipName=item[2], propertyOne={"名字": item[1]},
                                                   propertyTwo={"名字": item[3]})
            if "relationship_extract_result" in i:
                extract_relationship = self.merge_list(extract_relationship, i["relationship_extract_result"])
            cout += 1
            print(str(cout) + "个文章" + ",抽取数量：" + str(len(extract_relationship)))
            collection.update_one({"_id": ObjectId(_id)},  {"$set": {"relationship_extract_result": extract_relationship}})

    def eventExtractionByTemplateMatching(self, sentence, eventLabelList):
        """
        把术语单词假如到分词库里面 然后进行分词 得出想要的结果
        :param sentence:
        :param eventLabelList:
        :return:
        """
        reteventList = []

        # print(sentence)
        sentenceDealResult = self.hanlp_tool.cut(sentence)
        print(sentenceDealResult)
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
        return reteventList

    #这个代码还要调
    def eventExtraction(self, request, file_id):
        #加入ruleId 1或者2
        #1的事件是三元组主谓宾 2的话变事件是主谓
        #only for debug
        # request.session['user_id'] = 1
        # request.session['repo_id'] = 1
        # fileId = 13
        # only for debug

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
            #print(111,eventId)
            #触发词名字和触发词标注
            retEventRule=TEventRule.objects.get(id=eventId)
            #print(333,retEventRule.category_id)
            retCategoryName=TCategory.objects.get(id=retEventRule.category_id).category_name
            #print(444,retCategoryName)
            #这里的时候触发词的label要变成事件的label
            #到时候改一下
            triggerWord = retTriggerWordDict['trigger_word']
            triggerWordId =BaseController.get_category_name(request, retCategoryName)
            #print(222,eventId)

            eventRule = TEventRule.objects.get(id=eventId, repo_id=repoId)
            eventRuleDict = model_to_dict(eventRule)
            eventCategoryId = eventRuleDict['category_id']
            eventCategory = TCategory.objects.get(id=eventCategoryId, repo_id=repoId, create_id=createId)
            eventCategoryDict = model_to_dict(eventCategory)
            eventCategoryName = eventCategoryDict['category_name']
            tmpLableList.append(eventCategoryName)
            #事件类目

            subjectCategoryId = eventRuleDict['event_subject_id']
            subjectCategory = TCategory.objects.get(id=subjectCategoryId, repo_id=repoId, create_id=createId)
            subjectCategoryDict = model_to_dict(subjectCategory)
            subjectCategoryName = subjectCategoryDict['category_name']
            subjectId=BaseController.get_category_name(request,subjectCategoryName)
            tmpLableList.append(subjectId)
            retListId,retListVal = some_data_deal_func().inputCategoryIdReturnName(subjectCategoryId,repoId,createId)
            #对于retListVal里面的所有的值都把他们加入到分词器中然后进行分词
            #构造wordList word 和mask 对应
            constructWordList=[]
            tmpSet = self.hanlp_tool.added_word_list
            #print(len(retListVal ))
            for word in retListVal:
                if (word == None):
                    continue
                tmpDict={}
                tmpDict['word'] =word
                #print(word)
                #item["word"], item["mask"]
                tmpDict['mask'] = subjectId
                constructWordList.append(tmpDict)

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
            print(ruleId)
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
                    if(word==None):
                        continue
                    tmpDict = {}
                    tmpDict['word'] = word
                    # item["word"], item["mask"]
                    tmpDict['mask'] = str(objectId)
                    constructWordList.append(tmpDict)
                # 这边这个要加入list[{'word':123,mask:13}]
                #print(constructWordList)
                self.hanlp_tool.add_word_list(constructWordList)

            eventLabelList.append(tmpLableList)

        #eventLabelList
        #事件类目 事件主题  事件触发词 事件客体
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
        #print(self.hanlp_tool.added_word_list)
        cnt =1
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
            countIndex = 0 ;
            #时间 地点 事件主体 事件客体 主体的类目 和客体的类目
            tmpEventSet = set()
            for sent in sentenceList:
                sent = sent.strip()
                print(sent)
                #对每一个sent进行分词获取他们的事件
                #11111
                #sent="浙江杭州明天林更新出演动作喜剧《快手枪手快枪手》"
                sentenceDealResult = self.hanlp_tool.cut(sent)
                event = self.eventExtractionByTemplateMatching(sent, eventLabelList)
                #事件抽取完成
                #dateTime还要调整一下basetime会出问题
                #print(basetime)

                dateTime=basetime
                timeIndex = -1
                print(123,timeIndex)
                timeIndex,timeWord,dateTime = Time_deal().dealtime(sent, basetime)
                if(timeIndex!=-1):
                    timeIndex = timeIndex+countIndex
                print(46, timeIndex)
                print(11111111,dateTime)

                locationList = Time_deal().deal_area(sent)
                location = ''
                locationindex = -1
                for val in locationList:
                    if(len(val['place']) > len(location)):
                        location = val['place']
                        locationindex=val['index']+countIndex

                countIndex+= len(sentenceDealResult)

                #这三个的名字需要和事件一起返回
                #print(event)
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
                    #print(eventLabel)
                    #print(eventLabelList[eveId])
                    #print(event)
                    subjectLabel = eventLabelList[eveId][1]

                    Neo4j().create_node_mjy_edition(eventLabel, attribute)
                    subjectNameVal = eve[1]
                    # print(subjectCategoryName,attributeName,subjectNameVal)
                    neo4jSubjectId = Neo4j().quesIdByLabelAttribute(subjectLabel, attributeName, subjectNameVal)
                    neo4jEventId = Neo4j().quesIdByLabelAttribute(eventLabel, '名字', eveString)
                    Neo4j().createRelationship(subjectLabel,eventLabel,"主谓关系",{'id':neo4jSubjectId},{'id':neo4jEventId})
                    if (ruleId == 1):
                        objectNameVal = eve[3]
                        objectLabel = eventLabelList[eveId][3]
                        neo4jObjectId = Neo4j().quesIdByLabelAttribute(objectLabel, attributeName, objectNameVal)
                        Neo4j().createRelationship(eventLabel, objectLabel, "动宾关系", {'id':neo4jEventId}, {'id':neo4jObjectId})
                        #print(neo4jSubjectId, neo4jEventId, neo4jObjectId)
                    tmpEventDict = {}
                    tmpEventDict['actual_event_time']=dateTime
                    #事件抽取内容拿出来
                    tmpEventDict['time'] = timeWord
                    tmpEventDict['timeIndex']=timeIndex
                    tmpEventDict['location'] = location
                    tmpEventDict['locationIndex']=locationindex
                    print(111,dateTime,location)
                    tmpEventDict['eventSubject'] =eve[1]
                    tmpEventDict['eventSubjectLabel']=subjectLabel
                    tmpEventDict['triggerLabel']=triggerLabel
                    tmpEventDict['triggerWord'] = eve[2]
                    tmpEventDict['eventName'] = eveString
                    if (ruleId == 1):
                        tmpEventDict['eventObject'] = eve[3]
                        objectLabel = eventLabelList[eveId][3]
                        tmpEventDict['eventObjectLabel'] = objectLabel
                    if(eveString not in tmpEventSet):
                        tmpEventSet.add(eveString)
                        event_extract_result.append(tmpEventDict)
                    print(tmpEventDict)
                    count +=1
            #插入到mongodb
            #print(count,event_extract_result)
            news_col.update_one({'_id': _id}, {"$set": {'event_extract_result':event_extract_result }})
            #news_col.insert_one()
            cnt+=1
            #if(cnt>=2):
            #     break
        return True