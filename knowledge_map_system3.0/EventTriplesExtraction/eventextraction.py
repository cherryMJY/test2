

from EventTriplesExtraction.triple_extraction import *


extractor = TripleExtractor()
#content = '''视频中，周迅、董洁、陶虹、冯绍峰、张歆艺、董子健、崔永元、游本昌、贾樟柯、张一白、曹保平、伍仕贤、肖洋、杨庆、严艺丹等众星齐亮相支持《寻龙诀》，对电影大为称赞，如《烈日灼心》导演曹保平认为“视效上基本达到了中国电影现在最好的高度”，崔永元也表示很骄傲：“看完以后真觉得特别好，我们终于可以拿得出手了，可以跟好莱坞的大片争一争高下了'''
#svos = extractor.triples_main(content)

content="视频中，周迅、董洁、陶虹、冯绍峰、张歆艺、董子健、崔永元、游本昌、贾樟柯、张一白、曹保平、伍仕贤、肖洋、杨庆、严艺丹等众星齐亮相支持《寻龙诀》"
svos = extractor.triples_main(content)
print(svos)
content="对电影大为称赞"
svos = extractor.triples_main(content)
print(svos)
content="如《烈日灼心》导演曹保平认为“视效上基本达到了中国电影现在最好的高度”"
svos = extractor.triples_main(content)
print(svos)
content="崔永元也表示很骄傲：“看完以后真觉得特别好，我们终于可以拿得出手了，可以跟好莱坞的大片争一争高下了"
svos = extractor.triples_main(content)
print(svos)