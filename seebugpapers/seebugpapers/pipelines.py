# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import logging
import re
import copy
import codecs
import pymongo
from scrapy.conf import settings
from scrapy.exceptions import DropItem

class SeebugpapersPipeline(object):
    def process_item(self, item, spider):
        post_data = copy.deepcopy(item)
        self.__process_html(post_data)
        pathname = "{}{}.html".format(settings['LOCAL_STORE'],item['pid'])
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
        item['html'] = re.sub(r'<script type="text/javascript" src="https[.\s\S]*</script>','',item['html'],flags=re.S)
        item['html'] = re.sub(r'<script>[.\s\S]*?</script>','',item['html'],flags=re.S)
        # 处理 baidu css
        item['html'] = re.sub(r'//libs.baidu.com','/static',item['html'])
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
        #
        pid_exsist = True if self.collection.find({'pid':item['pid']}).count()>0 else False
        if pid_exsist == False:
            self.collection.insert_one(dict(post_data))
            self.log.debug('pid:%s added to mongdb!'%item['pid'],)
        else:
            if spider.update:
                self.collection.update_one({'pid':item['pid']},{'$set':dict(post_data)})
                self.log.debug('pid:%s exist,update!' %item['pid'])
            else:
                self.log.debug('pid:%s exist,not update!' %item['pid'])

        return item