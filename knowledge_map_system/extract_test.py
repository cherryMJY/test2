from model.extractUnit import ExtractUnit


if __name__ == '__main__':
    test = ExtractUnit().extract_relationship_from_structured_data(request=None, category_id=11, json_data={"关系测试": "霸王别姬"})
