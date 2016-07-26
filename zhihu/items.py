# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ZhihuItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field()
    business = scrapy.Field()
    location = scrapy.Field()
    topics = scrapy.Field()
    pass

class TopicItem(scrapy.Item):
    topic_id = scrapy.Field()
    topic_name = scrapy.Field()
    topic_answers = scrapy.Field()
