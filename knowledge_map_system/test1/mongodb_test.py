from model.mongodb import Mongodb
from bson import ObjectId

if __name__ == '__main__':
    test_col = Mongodb(db='test', collection='test').get_collection()
    # for i in test_col.find():
    #     if "file_id" in i:
    #         print(i["file_id"])
    #     test_col.update_one({"_id": i["_id"]}, {"$set": {"alexa": "12"}})
    test = test_col.find({"file_id": 1, "value.test1": {"$exists": True}})

    for item in test:
        print(item["_id"])
