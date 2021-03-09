import json

import scrapy

from scrapy.loader import ItemLoader
from w3lib.html import remove_tags

from ..items import SlspskItem
from itemloaders.processors import TakeFirst

import requests

url = "https://www.slsp.sk/bin/erstegroup/gemesgapi/feature/gem_site_sk_www_slsp_sk-es7/,"

base_payload="{\"filter\":[{\"key\":\"path\",\"value\":\"/content/sites/sk/slsp/www_slsp_sk/sk/aktuality\"}," \
             "{\"key\":\"tags\",\"value\":\"sk:slsp/aktuality/financie,sk:slsp/aktuality/obchodne," \
             "sk:slsp/aktuality/oznamenia,sk:slsp/aktuality/spravy,sk:slsp/aktuality/komentare," \
             "sk:slsp/aktuality/analyzy\"}],\"page\":%s,\"query\":\"*\",\"items\":10,\"sort\":\"DATE_RELEVANCE\"," \
             "\"requiredFields\":[{\"fields\":[\"teasers.NEWS_DEFAULT\",\"teasers.NEWS_ARCHIVE\"," \
             "\"teasers.newsArchive\"]}]} "
headers = {
  'Connection': 'keep-alive',
  'Pragma': 'no-cache',
  'Cache-Control': 'no-cache',
  'sec-ch-ua': '"Chromium";v="88", "Google Chrome";v="88", ";Not A Brand";v="99"',
  'sec-ch-ua-mobile': '?0',
  'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36',
  'Content-Type': 'application/json',
  'Accept': '*/*',
  'Origin': 'https://www.slsp.sk',
  'Sec-Fetch-Site': 'same-origin',
  'Sec-Fetch-Mode': 'cors',
  'Sec-Fetch-Dest': 'empty',
  'Referer': 'https://www.slsp.sk/sk/aktuality',
  'Accept-Language': 'en-US,en;q=0.9,bg;q=0.8',
  'Cookie': 'TCPID=12132166157247797973; TC_PRIVACY=1@003@@@1614693979031@; TC_PRIVACY_CENTER=; tracking_disabled=false; _ga=GA1.2.506027339.1614840962; TS01d4cc80=tTCHVG3mm0NYgzV9ap00UWeuPPngw2Ma; TS01d4cc90=T12uKMcuzjWBrgxiG5E6VRCpkOfJJP85; AMCVS_FF8851515B7C27640A495D95%40AdobeOrg=1; AMCV_FF8851515B7C27640A495D95%40AdobeOrg=-432600572%7CMCIDTS%7C18696%7CMCMID%7C36407981906635158371299230388735697670%7CMCAAMLH-1615898036%7C6%7CMCAAMB-1615898036%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCCIDH%7C-1089773470%7CMCOPTOUT-1615300436s%7CNONE%7CvVersion%7C4.5.2; _gid=GA1.2.937483413.1615293238; 3cf5c10c8e62ed6f6f7394262fadd5c2=38152618e0350b39d330076005a62c18; _gat_dtm_alpha=1; _gat_dtm_beta=1'
}


class SlspskSpider(scrapy.Spider):
	name = 'slspsk'
	start_urls = ['https://www.slsp.sk/sk/aktuality']
	page = 0

	def parse(self, response):
		payload = base_payload % self.page
		data = requests.request("POST", url, headers=headers, data=payload)
		raw_data = json.loads(data.text)
		for post in raw_data['hits']['hits']:
			link = post['_source']['url']
			date = post['_source']['date']
			title = post['_source']['title']
			yield response.follow(link, self.parse_post, cb_kwargs={'date': date, 'title': title})
		if self.page < raw_data['hits']['total'] // 10:
			self.page += 1
			yield response.follow(response.url, self.parse, dont_filter=True)

	def parse_post(self, response, date, title):
		description = response.xpath('//div[@class="w-auto mw-full rte"]//text()[normalize-space() and not(ancestor::a)]').getall()
		description = [remove_tags(p).strip() for p in description]
		description = ' '.join(description).strip()

		item = ItemLoader(item=SlspskItem(), response=response)
		item.default_output_processor = TakeFirst()
		item.add_value('title', title)
		item.add_value('description', description)
		item.add_value('date', date)

		return item.load_item()
