# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


class ZhihuPipeline(object):
    def process_item(self, item, spider):
        return item


import json
import codecs


class JsonWriterPipeline(object):
    def __init__(self):
        # 写完之后需要在开头和结尾分别加上 [和]才是合法的json格式
        self.file = codecs.open('users.json', 'a', encoding='utf-8')

    def process_item(self, item, spider):
        line = json.dumps(dict(item)) + ','
        # 中文写入编码问题
        self.file.write(line.encode('latin-1').decode('unicode_escape'))
        return item
