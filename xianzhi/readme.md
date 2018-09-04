参考wooyun_backup做的先知社区的备份站点

使用了 scrapy 做爬虫，并存储静态文件，mongodb存储数据（为了检索），flask做站点和搜索

mongodb需要建立对date建立索引

    db.xianzhi_list.ensureIndex({"date":-1})

## setup

```
apt-get install mongodb
pip3 install -r requirements.txt
```

`crontab -e` 添加计划任务

    1 *  *   *   * cd /path/ && scrapy crawl xz >> /tmp/xianzhispider.log 2>&1
