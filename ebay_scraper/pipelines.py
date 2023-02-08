# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy import signals
import xlsxwriter
import os

class AbcdinClPipeline(object):
    # def process_item(self, item, spider):
    #     return item
    workbook = None
    sheet = None
    row_num = 0
    headers = []

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        filepath = 'output/output.xlsx'
        if os.path.isfile(filepath):
            os.remove(filepath)
        self.workbook = xlsxwriter.Workbook(filepath, {'strings_to_urls': False})
        self.sheet = self.workbook.add_worksheet('output')
        self.headers = spider.fields

        for col, key in enumerate(self.headers):
            self.sheet.write(self.row_num, col, key)
        self.row_num += 1

    #
    def spider_closed(self, spider):
        for item in spider.total_items:
            for col, key in enumerate(item.values()):
                self.sheet.write(self.row_num, col, key)
            self.row_num += 1
        self.workbook.close()



    def process_item(self, item, spider):
        # if not self.workbook:

        for col, key in enumerate(self.headers):
            if not item[key]:
                continue
            self.sheet.write(self.row_num, col, item[key])
        self.row_num += 1
        return item
