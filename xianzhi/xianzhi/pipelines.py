# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import logging
import re
import os
import copy
import codecs
import pymongo
from scrapy.conf import settings
from scrapy.exceptions import DropItem


class XianzhiPipeline(object):
    def __init__(self):
        self.connection_string = "mongodb://%s:%d" % (settings['MONGODB_SERVER'],settings['MONGODB_PORT'])

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.connection_string)
        self.db = self.client[settings['MONGODB_DB']]
        self.collection = self.db[settings['MONGODB_COLLECTION']]
        self.log = logging.getLogger("xianzhipipleline")

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        exist_item = self.collection.find_one({"tid":item["tid"]})
        need_update = True
        pathname = "{}{}.html".format(settings['LOCAL_STORE'],item['tid'])
        if (not exist_item) or (len(exist_item['html']) < len(item['html'])):
            need_update = True
        elif not os.path.exists(pathname):
            need_update = True
        else:
            need_update = False
        self.log.info("tid: {} need update: {}".format(item['tid'], need_update))
        if not need_update:
            return item
        post_data = copy.deepcopy(item)
        self.__process_html(post_data)
        with codecs.open(pathname,mode='w',encoding='utf-8',errors="ignore") as f:
            f.write(post_data['html'])
        return item

    def __process_html(self,item):
        if not item["html"]:
            print("no html")
            return False

        for img in item["images"]:
            item['html'] = re.sub('<img(.*)src=[\'\"]%s[\'\"]'%img['url'],'<img\\1src=\'%s\''%img['path'],item['html'],flags=re.S)

        # 处理js
        item['html'] = re.sub('//g.alicdn.com/sd/ncpc/nc.js','static/js/nc.js',item['html'])
        return True

class MongoDBPipeline(object):
    def __init__(self):
        self.connection_string = "mongodb://%s:%d" % (settings['MONGODB_SERVER'],settings['MONGODB_PORT'])

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.connection_string)
        self.db = self.client[settings['MONGODB_DB']]
        self.collection = self.db[settings['MONGODB_COLLECTION']]
        self.log = logging.getLogger(spider.name)

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        #
        post_data = copy.deepcopy(item)
        post_data.pop('image_urls')
        post_data.pop('images')
        post_data.pop('html')
        #
        tid_exsist = True if self.collection.find({'tid':item['tid']}).count()>0 else False
        if tid_exsist == False:
            self.collection.insert_one(dict(post_data))
            self.log.debug('tid:%s added to mongdb!'%item['tid'],)
        else:
            if spider.update:
                self.collection.update_one({'tid':item['tid']},{'$set':dict(post_data)})
                self.log.debug('tid:%s exist,update!' %item['tid'])
            else:
                self.log.debug('tid:%s exist,not update!' %item['tid'])

        return item