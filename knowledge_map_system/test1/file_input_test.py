from model.mongodb import Mongodb
import json
from bson import json_util, objectid

a = b'{"_id":{"$oid":"5dfc557411647d60345088a3"},"datetime":"2011-01-01","movie_name":"\xe8\xae\xa9\xe5\xad\x90\xe5\xbc\xb9\xe9\xa3\x9e","release_time":"\xe4\xb8\x8a\xe6\x98\xa017\xe5\xa4\xa9","crawl_from":"\xe7\x8c\xab\xe7\x9c\xbc\xe4\xb8\x93\xe4\xb8\x9a\xe7\x89\x88","crawl_time":"2019-12-20 13:00:36","boxoffice_ratio":"47.7%","screenings_number":"11587","screenings_ratio":"37.3%","field_trips":"0","attendance_rate":"--","boxoffice_statistics":"3008.13","total_boxoffice":"5.20\xe4\xba\xbf"}\n'
a = json.loads(a, object_hook=json_util.object_hook)
print(type(a["_id"]))
print(isinstance(a["_id"], objectid.ObjectId))
Mongodb(db="test1", collection="test1").get_collection().insert_one(a)

