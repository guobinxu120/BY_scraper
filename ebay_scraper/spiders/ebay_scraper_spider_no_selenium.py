import scrapy, json, requests, random
import csv
from collections import OrderedDict
from scrapy import Request

class ebay_scraper_no_selenium(scrapy.Spider):
    name = "ebay_scraper"

    start_urls = []

    f2 = open('input/urls.csv')

    csv_items = csv.DictReader(f2)
    cat_data = {}

    for i, row in enumerate(csv_items):
        start_urls.append(row['url'])
    f2.close()

    ################

    use_selenium = True
    total_count = 0
    bhnum_list = []

    total_items = []

    fields = ["Url", "PartNumber", "Auction No", "Title", "Manufacturer", "UpcCode", "VendorNumber", "Description", "ListPrice",
              "SalePrice", "Condition", "Seller Notes", "seller_notes_data", "Shipping", "Depth", "Height", "Weight", "Width", "VendorName", "Category",
              "Quantity", "Quantity Sold", "Returns", "Auction Body"]
    for i in range(20):
        fields.append("Image " + str(i + 1))

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-ch-ua': '"Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"',
        'sec-ch-ua-mobile': '?0',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'
    }

    # get proxies from free proxy site
    # proxy_text = requests.get('https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt').text
    # list_proxy_temp = proxy_text.split('\n')
    #
    # proxy = None
    # list_proxy = []
    # for line in list_proxy_temp:
    # 	if line.strip() != '' and (line.strip()[-1] == '+' or line.strip()[-1] == '-'):
    # 		ip = line.strip().split(':')[0].replace(' ', '')
    # 		port = line.split(':')[-1].split(' ')[0]
    # 		list_proxy.append('http://' + ip + ':' + port)

    def start_requests(self):
        # self.proxy = random.choice(self.list_proxy)
        for url in self.start_urls:
            yield Request(url, callback=self.parseProductList, meta={"main": True})
            # break

    # def parseCat1(self, response):
    # 	categories = response.xpath('//ul[@class="nav-E capital"]/li/a/@href').extract()
    # 	for cat_url in categories:
    # 		yield Request(cat_url, callback=self.parseCat, meta={"CatURL": cat_url, 'page_num':1})


    def parseProductList(self, response):
        see_all_btn = response.xpath('//a[text()="See All"]/@href').extract_first()
        if see_all_btn:
            yield Request(see_all_btn, callback=self.parseProductList, meta={"main": True})

            return
        product_list = response.xpath('//ul[contains(@class,"srp-results")]/li')
        if not product_list:
            product_list = response.xpath('//ul[@id="ListViewInner"]/li/h3')
        for product in product_list:
            href = product.xpath('.//div[@class="s-item__image"]/a/@href').extract_first()
            if href:

                ### test ####
                # href = "https://www.ebay.com/itm/294896500370"
                #####################

                yield Request(href, callback=self.parseProduct)

                # break

        ########### test ############
        next_url = response.xpath('//a[@type="next"]/@href').extract_first()
        if not next_url:
            next_url = response.xpath('//a[@aria-label="Next page of results"]/@href').extract_first()
        if next_url:
            yield Request(next_url, callback=self.parseProductList, meta={"main": True})
        ################################

    def parseProduct(self, response):

        # itemdata = product.xpath('./@data-itemdata').extract_first()
        itemdata_json = OrderedDict()

        for field in self.fields:
            itemdata_json[field] = ""

        itemdata_json["Url"] = response.url

        itemdata_json["PartNumber"] = response.xpath('//div[@id="viTabs_0_is"]//span[@itemprop="mpn"]/div/span/text()').extract_first()
        itemdata_json["Auction No"] = response.url.split("?")[0].split("/")[-1]
        itemdata_json["Title"] = response.xpath('//h1[@class="x-item-title__mainTitle"]/span/text()').extract_first()
        itemdata_json["Manufacturer"] = response.xpath(
            '//div[@id="viTabs_0_is"]//span[@itemprop="brand"]/span/div/span/text()').extract_first()
        itemdata_json["UpcCode"] = response.xpath(
            '//div[@id="viTabs_0_is"]//span[@itemprop="gtin13"]/div/span/text()').extract_first()
        itemdata_json["VendorNumber"] = ""

        list_price = response.xpath('//span[@class="ux-textspans ux-textspans--STRIKETHROUGH"]/text()').extract_first()
        sale_price = response.xpath('//span[@itemprop="price"]/@content').extract_first()
        if list_price:
            itemdata_json["ListPrice"] = list_price.split("$")[-1]
            itemdata_json["SalePrice"] = sale_price
        else:
            itemdata_json["ListPrice"] = sale_price
            itemdata_json["SalePrice"] = sale_price
        if itemdata_json["SalePrice"]:
            itemdata_json["SalePrice"] = itemdata_json["SalePrice"].replace("$", "").replace(",", "")
        if itemdata_json["ListPrice"]:
            itemdata_json["ListPrice"] = itemdata_json["ListPrice"].replace("$", "").replace(",", "")

        itemdata_json["Condition"] = ""

        section_rows = response.xpath('//div[@id="viTabs_0_is"]//div[contains(@class,"ux-layout-section__row")]/div')
        i = 0
        for section_row in section_rows:
            if len(section_rows) > i + 1:
                if section_row.xpath('./div/div/span/text()').extract_first() == "Condition:":
                    value = section_rows[i + 1].xpath('.//span[@data-testid="text"]/span/text()').extract_first()
                    if not value:
                        value = section_rows[i + 1].xpath('.//span/text()').extract_first()
                        if value:
                            value = value.split(":")[0]
                    else:
                        value = value.split(":")[0]
                    itemdata_json["Condition"] = value
                elif section_row.xpath('./div/div/span/text()').extract_first() == "Seller Notes:":
                    value = section_rows[i + 1].xpath('.//span[@data-testid="text"]/span/text()').extract_first()
                    if not value:
                        value = section_rows[i + 1].xpath('.//span/text()').extract_first()
                        if value:
                            value = value.split(":")[0]
                    else:
                        value = value.split(":")[0]
                    itemdata_json["Seller Notes"] = value
            i += 1

        # fshippingCost = response.xpath('//span[@id="fshippingCost"]/span/text()').extract_first()
        fshippingCost = response.xpath('//span[@id="fshippingCost"]/span/text()').re(r'[\d.,]+')
        # if response.xpath('//span[@id="fShippingSvc"]/text()').extract_first():
        #     fShippingSvc = response.xpath('//span[@id="fShippingSvc"]/text()').extract_first().strip()
        # else:
        #     fShippingSvc = ' '
        # if fshippingCost:
        #     fShippingSvc = fshippingCost + " " + fShippingSvc
        if fshippingCost:
            fshippingCost = fshippingCost[0]
        else:
            fshippingCost = response.xpath('//*[@id="shippingSummary"]//span/text()').re(r'[\d.,]+')
            if fshippingCost:
                fshippingCost = fshippingCost[0]
                if not fshippingCost.isnumeric():
                    fshippingCost = 0
            else:
                fshippingCost = 0

        itemdata_json["Shipping"] = fshippingCost

        category_list = response.xpath('//nav[contains(@class, "breadcrumbs")]/ul/li/a/span/text()').extract()
        category_list = category_list[: len(category_list) - 1]
        itemdata_json["Category"] = " > ".join(category_list)

        qty = response.xpath('//div[@class="d-quantity__availability"]/span/text()').re(r'[\d.,]+')
        if qty:
            qty = qty[0].replace(",", "")
        else:
            if response.xpath('//div[@class="vim x-bin-action vim-flex-cta"]'):
                qty = 3
            else:
                qty = 0
            # if response.xpath('//*[@id="binBtn_btn"]'):
            #     qty = 1
            # else:
            #     qty = 0
        itemdata_json["Quantity"] = qty

        qty_sold = response.xpath('//div[@class="d-quantity__availability"]/a/span/text()').re(r'[\d.,]+')
        if qty_sold:
            qty_sold = qty_sold[0].replace(",", "")
        else:
            qty_sold = 0
        itemdata_json["Quantity Sold"] = qty_sold

        vendor_name = response.xpath('//div[@class="vim d-shipping-minview"]//div[@class="ux-labels-values__values-content"]/div[3]/span/text()').extract_first()
        if vendor_name:
            vendor_name = vendor_name.replace('Located in: ', "")
        itemdata_json["VendorName"] = vendor_name

        returns = response.xpath('//div[@class="vim x-returns-minview"]//div[@class="ux-labels-values__values-content"]/div/span/text()').extract()
        if returns:
            returns = returns[: len(returns) - 1]
        itemdata_json["Returns"] = " ".join(returns)
        itemdata_json["Description"] = response.xpath('//meta[@name="description"]/@content').extract_first()

        specs = response.xpath('//div[@class="vim x-about-this-item"]//div[@class="ux-layout-section__row"] | //div[@class="vim x-product-details"]//div[@class="ux-layout-section__row"]')
        for spec in specs:
            labels = spec.xpath('.//div[contains(@class, "ux-labels-values__labels")]//span/text()').extract()
            values = spec.xpath('.//div[contains(@class, "ux-labels-values__values")]//span/text()').extract()
            i = 0
            for name in labels:
                if len(values) < i + 1:
                    continue
                value = values[i]
                if "Item Depth" in name:
                    itemdata_json["Depth"] = value
                elif "Item Height" in name:
                    itemdata_json["Height"] = value
                elif "Item Weight" in name:
                    itemdata_json["Weight"] = value
                elif "Item Width" in name:
                    itemdata_json["Width"] = value

                i += 1

        images = response.xpath('//div[@id="vi_main_img_fs"]//img/@src').extract()
        i = 0
        for img in images:
            i += 1
            if i > 20:
                break
            itemdata_json["Image " + str(i)] = img.replace("s-l64", "s-l1600")

        ifram_src = response.xpath('//iframe[@id="desc_ifr"]/@src').extract_first()
        if ifram_src:
            yield Request(ifram_src, callback=self.parseIframe, meta={"item": itemdata_json})

    def parseIframe(self, response):
        itemdata_json = response.meta["item"]

        seller_notes_data = response.xpath('//div[@id="ds_div"]//text() | //div[@id="ds_div"]/font/div/text() | //div[@id="ds_div"]/font/div/i/text()').extract()
        itemdata_json["seller_notes_data"] = "\n".join(seller_notes_data)

        specifications_tags = response.xpath('//div[@class="lft-flt specifications"]/div/table//td')
        if specifications_tags:
            i = 0
            for specifications_tag in specifications_tags:
                if len(specifications_tags) > i + 1 and (i % 2 == 0):
                    name = specifications_tag.xpath('./b/text()').extract_first()
                    if not name:
                        continue
                    value = specifications_tags[i + 1].xpath('./text()').extract_first()
                    if "Product Depth" in name:
                        itemdata_json["Depth"] = value
                    elif "Product Height" in name:
                        itemdata_json["Height"] = value
                    elif "Product Weight" in name:
                        itemdata_json["Weight"] = value
                    elif "Product Width" in name:
                        itemdata_json["Width"] = value
                i += 1

        else:
            specifications_tags = response.xpath('//div[@id="ds_div"]//table//tr')
            if specifications_tags:
                for specifications_tag in specifications_tags:
                    values = specifications_tag.xpath('./td/text()').extract()
                    if len(values) < 2:
                        continue
                    name = values[0]
                    value = values[1]
                    if 'Depth' in name:
                        itemdata_json["Depth"] = value
                    elif 'Height' in name:
                        itemdata_json["Height"] = value
                    elif 'Width' in name:
                        itemdata_json["Width"] = value
                    elif 'Weight' in name:
                        itemdata_json["Weight"] = value

        temps = response.xpath('//body/table//text()').extract()
        data = []
        for t in temps:
            t = t.strip()
            if not t:
                continue
            data.append(t)
        itemdata_json["Auction Body"] = "\n".join(data)
        self.total_items.append(itemdata_json)

        self.total_count += 1
        print('\n##################################\ntotal count: ' + str(self.total_count) + '\n##################################\n')


    def errCall(self, response):
        # try:
        #     if response.value.response.xpath('//pre/text()').extract_first() != 'Retry later\n':
        #         print('no result: {}'.format(response.request.meta['ean']))
        #         return
        # except:
        #     pass
        ban_proxy = response.request.meta['proxy']
        if '154.16.' in ban_proxy:
            ban_proxy = ban_proxy.replace('http://', 'http://eolivr4:bntlyy3@')
        if ban_proxy in self.list_proxy:
            self.list_proxy.remove(ban_proxy)
        if len(self.list_proxy) < 1:
            proxy_text = requests.get(
                'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt').text
            list_proxy_temp = proxy_text.split('\n')
            self.list_proxy = []
            for line in list_proxy_temp:
                if line.strip() != '' and (line.strip()[-1] == '+' or line.strip()[-1] == '-'):
                    ip = line.strip().split(':')[0].replace(' ', '')
                    port = line.split(':')[-1].split(' ')[0]
                    self.list_proxy.append('http://' + ip + ':' + port)

        self.proxy = random.choice(self.list_proxy)
        # response.request.meta['proxy'] = proxy
        print ('err proxy: ' + self.proxy)
        response.request.meta['proxy'] = self.proxy
        if not 'errpg' in response.request.url:
            yield Request(response.request.url,
                          callback=self.parse,
                          headers=self.headers,
                          meta=response.request.meta,
                          dont_filter=True,
                          errback=self.errCall)