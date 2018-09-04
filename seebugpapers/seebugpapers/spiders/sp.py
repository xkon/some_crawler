# -*- coding: utf-8 -*-
from datetime import datetime
import logging
import pymongo
import scrapy
from seebugpapers.items import SeebugpapersItem
from scrapy.conf import settings

class SpSpider(scrapy.Spider):
    name = 'sp'
    allowed_domains = ['paper.seebug.org']
    start_urls = ['https://paper.seebug.org/']

    def __init__(self,page_max=settings['PAGE_MAX_DEFAULT'],local_store=settings['LOCAL_STORE_DEFAULT'],\
            update=settings['UPDATE_DEFAULT'],*args, **kwargs):
        self.page_max = int(page_max)
        # self.local_store = 'true' == local_store.lower()
        self.update = 'true' == update.lower()

        self.connection_string = "mongodb://%s:%d" % (settings['MONGODB_SERVER'],settings['MONGODB_PORT'])
        self.client = pymongo.MongoClient(self.connection_string)
        self.db = self.client[settings['MONGODB_DB']]
        self.collection = self.db[settings['MONGODB_COLLECTION']]
        self.log = logging.getLogger(self.name)

    def closed(self,reason):
        self.client.close()

    def parse(self,response):
        total_pages = response.xpath('//*[@id="wrapper"]/main/div/nav/span/text()').re(r'\d+')[1]
        if self.page_max == 0:
            end_page = int(total_pages)
        else:
            end_page = self.page_max

        for n in range(1,end_page + 1):
            page = "https://paper.seebug.org/?page=%d"%n
            url = response.urljoin(page)
            yield scrapy.Request(url,self.parse_list)

    def parse_list(self,response):
        links = response.xpath('//*[@id="wrapper"]/main/div/article/header/h5/a/@href').extract()
        for url in links:
            pid = url.split('/')[-2]
            # 获取评论数，评论数变化就更新
            if self.update or self.__search_mongodb(pid) == False:
                url = response.urljoin(url)
                self.log.info("add url: {}".format(url))
                yield scrapy.Request(url,self.parse_detail)

    def parse_detail(self, response):
        item = SeebugpapersItem()
        item["pid"] = response.request.url.split('/')[-2]
        item["title"] = response.xpath('//*[@id="wrapper"]/main/div/article/header/h1/text()').extract_first()
        date = response.xpath('//*[@id="wrapper"]/main/div/article/header/section/span/time[@class="fulldate"]/@datetime').extract_first()
        item['date'] = datetime.strptime(date,'%Y-%m-%d')
        item["category"] = response.xpath('//*[@id="wrapper"]/main/div/article/header/section/a/text()').extract_first()
        category_uri = response.xpath('//*[@id="wrapper"]/main/div/article/header/section/a/@href').extract_first().split('/')
        item["category_uri"] = category_uri[2] if len(category_uri)>2 else ""
        images_urls = response.xpath("//img/@src").extract()
        self.log.debug(images_urls)
        #
        item["image_urls"] = []
        for imgurl in images_urls:
            if imgurl.startswith('/'):
                imgurl = 'https://paper.seebug.org' + imgurl
            if imgurl:
                item["image_urls"].append(imgurl)
        item["html"] = response.body_as_unicode()

        yield item

    def __search_mongodb(self,pid):
        return True if self.collection.find({'pid':pid}).count() >0 else False
