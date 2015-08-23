from scrapy.spiders import CrawlSpider
from scrapy.selector import Selector
from scrapy.http import Request, FormRequest

from bs4 import UnicodeDammit

import os
import logging
import time
import random
import json

class LinkedinSearchSpider(CrawlSpider):
	name = "LinkedinSearchSpider"
	allowed_domains = ["linkedin.com"]
	login_page = 'https://www.linkedin.com/uas/login?goback=&trk=hb_signin'
	start_urls = [
		"https://www.linkedin.com/vsearch/p?school=Nanjing%20University%20of%20Aeronautics%20and%20Astronautics&openAdvancedForm=true&locationType=Y&rsid=3709674281439886724647&orig=MDYS&openFacets=N,G,CC&page_num=2"
	]
	headers = {
		"Accept": "*/*",
		"Accept-Encoding": "gzip,deflate",
		"Accept-Language": "zh-CN,zh;q=0.8",
		"Connection": "keep-alive",
		"Content-Type": "application/x-www-form-urlencoded",
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.155 Safari/537.36",
		"Host": "www.linkedin.com",
		"Origin": "https://www.linkedin.com"
		#"Referer": "https://www.linkedin.com"
    }
	
	def start_requests(self):
		return [Request(
					url = self.start_urls[0], 
					headers = self.headers,
					meta = {'cookiejar' : 1}, 
					callback = self.parse
					)]
	
	def login(self, response):
		sel = Selector(response)
		trk = sel.xpath('//input[@name="trk"]/@value').extract()[0].encode("utf-8")
		loginCsrfParam = sel.xpath('//input[@name="loginCsrfParam"]/@value').extract()[0].encode("utf-8")
		csrfToken = sel.xpath('//input[@name="csrfToken"]/@value').extract()[0].encode("utf-8")
		sourceAlias = sel.xpath('//input[@name="sourceAlias"]/@value').extract()[0].encode("utf-8")
		
		session_key = '*************'
		session_password = '***********'
		client_ts = int(round(time.time() * 1000))
		client_n = [int(9E8 * random.random() + 1E8), int(9E8 * random.random() + 1E8), int(9E8 * random.random() + 1E8)]
		client_output = self.cal_client_output(client_n, session_key, client_ts)
		client_n = ':'.join(str(i) for i in client_n)
		client_r = session_key + ':' + client_n
		client_v = '1.0.1'
		form_data = {
				'isJsEnabled':'true',
				'source_app':'',
				'tryCount':'',
				'session_redirect':'',
				'clickedSuggestion':'false',
				'session_key': session_key, 
				'session_password': session_password,
				'signin':'Sign In',
				'trk':trk,
				'loginCsrfParam':loginCsrfParam,
				'fromEmail':'',
				'csrfToken':csrfToken,
				'sourceAlias':sourceAlias,
				'client_ts':str(client_ts),
				'client_r':client_r,
				'client_output':str(client_output),
				'client_n':client_n,
				'client_v':client_v
			}
		logging.debug("form_date " + str(form_data))
		return FormRequest.from_response(
			response,
			meta = {
				'cookiejar': response.meta['cookiejar']
			},
			headers = self.headers,
			formdata = form_data,
			callback = self.parse
			)
	
	def cal_client_output(self, n, email, ts):
		f1_out = self.f1(n, ts)
		f2_out = self.f2(f1_out, ts)
		if f1_out[0] % 1000 > f1_out[1] % 1000:
			v = f1_out[0]
		else:
			v = f1_out[1]
		
		return self.f3(v, f2_out, email)
	
	def f1(self, vs, ts):
		output = [vs[0] + vs[1] + vs[2], (vs[0] % 100 + 30) * (vs[1] % 100 + 30) * (vs[2] % 100 + 30)]
		for i in range(10):
			output[0] = output[0] + (output[1] % 1000 + 500) * (ts % 1000 + 500)
			output[1] = output[1] + (output[0] % 1000 + 500) * (ts % 1000 + 500)

		return output
	
	def f2(self, vs, ts):
		sum = vs[0] + vs[1]
		n = sum % 3000
		m = sum % 10000
		p = ts % 10000
		if n < 1000:
			return pow(m + 12345, 2) + pow(p + 34567, 2)
		elif n < 2000:
			return pow(m + 23456, 2) + pow(p + 23456, 2)
		else:
			return pow(m + 34567, 2) + pow(p + 12345, 2)
	
	def f3(self, v1, v2, email):
		v3 = 0
		for i in range(len(email)):
			v3 = v3 + (ord(email[i]) << ((5 * i) % 32))
		return(v1 * v2 * v3) % 1000000007
	
	def after_login(self, response):
		logging.info("Successfully logged in. Let's start crawling!")
		for url in self.start_urls:
			yield self.make_requests_from_url(url)
	
	def parse(self, response):
#		print response.headers
#		print response.url
#		print response.meta
#		print response.request.headers
#		print response.request.url
#		print response.request.meta
#		print response.request.cookies
		
		url = response.url
#		if '_splash_processed' in response.meta:
#			url  = response.meta['_splash_processed']['args']['url']
		
		level = self.determine_level(url)
		logging.info("Parse: index level:" + str(level))
		self.save_to_file_system(level, url, response.body)
		
		if level in [0]:
			logging.info("Parse: login page: raising log in form request")
			yield self.login(response)
		elif level in [1]:
			logging.info("Parse: home page: raise a request to its Referer")
			yield Request(
				url = self.start_urls[0], 
				meta = {'cookiejar': response.meta['cookiejar'],
#						'splash': {
#							'endpoint': 'render.html',
#							'args': {'wait': 0.5}
#						}
					}, 
				headers = self.headers,
				callback = self.parse,
				dont_filter=True
				)
		elif level in [2]:
			logging.info("Parse: search page")
			yield None
		elif level in [3]:
			logging.info("Parse: profile page")
			yield None
			
	def prase_people_urls(self, response):
		import re
		json_str = UnicodeDammit(re.search('<!--(?P<json_str>{"content".+"status":"ok"})-->', response.body).groupdict()['json_str']).markup
		print json_str
		
		json_data = json.loads(json_str)
		print json_data
	
	def determine_level(self, url):
		"""
		determine the index level of current response, so we can decide if to continue crawl or not.
		level 0: login
		level 1: hp/nhome
		level 2: vsearch
		level 3: profile
		"""
		import re
		if re.match(".+/login.+", url):
			return 0
		elif re.match(".+/hp.+", url) or re.match(".+/nhome.+", url):
			return 1
		elif re.match(".+/vsearch.+", url):
			return 2
		elif re.match(".+/profile.+", url):
			return 3
		logging.error("Crawl cannot determine the url's level: " + url)
		return None
	
	def save_to_file_system(self, level, url, body):
		if level in [2, 3]:
			fileName = self.get_clean_file_name(level, url)
			if fileName is None:
				return
		
			fn = os.path.join(self.settings["DOWNLOAD_FILE_FOLDER"], str(level), fileName)
			self.create_path_if_not_exist(fn)
			if not os.path.exists(fn):
				with open(fn, "w") as f:
					f.write(body)
										
	def get_clean_file_name(self, level, url):
		import re
		logging.debug("url " + url)
		if level in [2]:
			school_match = re.search("school=(?P<school>[%\w\d\s]+)", url)
			school = school_match.groupdict()["school"].replace("%20", "_")
			logging.debug("school_match " + str(school_match.groupdict()))
			logging.debug("school " + school)
			return school + '-' + self.get_page_num(url)
		elif level in [3]:
			return self.get_linkedin_id(url)
		logging.error("Crawl cannot determine the url's file name: " + url)
		return None
		
	def get_page_num(self, url):
		import re
		page_match = re.search("page_num=(?P<page>[\d]+)", url)
		logging.debug("page_match " + str(page_match.groupdict()))
		if page_match:
			return page_match.groupdict()["page"]
		 
		return -1
			
	def get_linkedin_id(self, url):
		import re
		id_match = re.search("id=(?P<id>[\d])", url)
		logging.debug("id_match " + str(id_match.groupdict()))
		if id_match:
			return id_match.groupdict()["id"]
		 
		return None
			
	def create_path_if_not_exist(self, filePath):
		if not os.path.exists(os.path.dirname(filePath)):
			os.makedirs(os.path.dirname(filePath))