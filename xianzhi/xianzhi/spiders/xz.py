# -*- coding: utf-8 -*-
from datetime import datetime
import logging
import pymongo
import scrapy
from xianzhi.items import XianzhiItem
from scrapy.conf import settings

class XzSpider(scrapy.Spider):
    name = 'xz'
    allowed_domains = ['xz.aliyun.com']
    start_urls = ['https://xz.aliyun.com/']
    # def start_requests(self):
    #     for i in range(1,3000):
    #         url = 'https://xz.aliyun.com/t/{}'.format(i)
    #         yield scrapy.Request(url=url, callback=self.parse)

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

    def parse(self, response):
        cate_urls = response.xpath('//*[@id="Wrapper"]/div/div[1]/div/div/div[1]/ol/li/a/@href').extract()
        for u in cate_urls:
            url = response.urljoin(u)
            yield scrapy.Request(url, self.parse_cate)

    def parse_cate(self,response):
        try:
            total_pages = response.xpath('//*[@id="Wrapper"]/div/div[1]/div/div/div[3]/ul/li[2]/a/text()').re(r'\d+')[1]
        except:
            total_pages = 1
        if self.page_max == 0:
            end_page = int(total_pages)
        else:
            end_page = self.page_max

        for n in range(1,end_page + 1):
            page = "{}?page={}".format(response.request.url, n)
            url = response.urljoin(page)
            yield scrapy.Request(url,self.parse_list)

    def parse_list(self,response):
        links = response.xpath('//*[@id="includeList"]/table/tr/td/p[1]/a/@href').extract()
        comments = response.xpath('//*[@id="includeList"]/table/tr/td/p[2]/span/span/text()').extract()
        for url,c in zip(links,comments):
            tid = url.split('/')[-1]
            # 获取评论数，评论数变化就更新
            if self.__need_update(tid, c) or self.__search_mongodb(tid) == False:
                url = response.urljoin(url)
                self.log.info("add url: {}".format(url))
                yield scrapy.Request(url,self.parse_detail)

    def parse_detail(self, response):
        item = XianzhiItem()
        item["tid"] = response.request.url.split('/')[-1]
        item["title"] = response.xpath('//*[@id="Wrapper"]/div/div[1]/div[1]/div/div/div[1]/p/span/text()').extract_first()
        item["author"] = response.xpath('//*[@id="Wrapper"]/div/div[1]/div[1]/div/div/div[1]/div/span[1]/a/span/text()').extract_first()
        date = response.xpath('//*[@id="Wrapper"]/div/div[1]/div[1]/div/div/div[1]/div/span[1]/span[2]/text()').extract_first().strip()
        item['date'] = datetime.strptime(date,'%Y-%m-%d %H:%M:%S')
        item["category"] = response.xpath('//*[@id="Wrapper"]/div/div[1]/div[1]/div/div/div[1]/div/span[1]/span[5]/span[2]/a/text()').extract_first()
        item["comment_count"] = response.xpath('//*[@id="Wrapper"]/div/div[1]/div[@class="row box"]/ol/li').re(r'\d+')[0]
        images_urls = response.xpath("//img/@src").extract()
        self.log.debug(images_urls)
        #
        item["image_urls"] = []
        for imgurl in images_urls:
            if imgurl.startswith('/'):
                imgurl = 'https://xz.aliyun.com' + imgurl
            if imgurl:
                item["image_urls"].append(imgurl)
        item["html"] = response.body_as_unicode()
        item["text"] = response.xpath('//*[@id="Wrapper"]/div/div[@class="span10"]').xpath('string(.)').extract_first().strip()

        yield item

    def __search_mongodb(self,tid):
        return True if self.collection.find({'tid':tid}).count() >0 else False

    def __need_update(self, tid, comment_count):
        item = self.collection.find_one({"tid":tid})
        if item:
            self.log.debug("tid: {} exists. comments_origin: {} comments_now: {}".format(tid,item.get('comment_count','0'),comment_count))
            if item.get('comment_count','0') != comment_count:
                self.log.info('tid: {} need update, comments {} => {}'.format(tid, item.get('comment_count','0'), comment_count))
                self.update = True
                return True
            else:
                return False
        else:
            self.log.info("tid: {} not exists, need crawl. ".format(tid))
            return True
