import zhihu.settings as projectsetting
from zhihu.items import ZhihuItem

import scrapy
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher
from scrapy.selector import Selector
from scrapy.http import Request, FormRequest
from scrapy.http.cookies import CookieJar
from scrapy.spiders import CrawlSpider, Rule

import os
import json
import time
import sys

from http.cookiejar import Cookie

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

if sys.platform == 'win32':
    from win32api import GetSystemMetrics


class zhihuCrawler(CrawlSpider):
    allowed_domains = ["www.zhihu.com"]
    host_url = "https://www.zhihu.com"
    start_urls = [
        "https://www.zhihu.com"
    ]
    headers = {
        'Connection': 'Keep-Alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': 'text / html, application / xhtml + xml, image / jxr, * / *',
        'Accept-Language': 'zh-Hans-CN,zh-Hans;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586',
        'Host': 'www.zhihu.com',
        'Referer': 'https://www.zhihu.com/'
        # ' Cookie': '_za=5852b28b-399a-4bd8-8282-59070203151f; _xsrf=7d7cdde47226ee4e485a9cc9925f2715; __utmc=51854390; q_c1=73b48dcd9e84486f81814ea556dac319|1468220250000|1468220250000; l_cap_id=NjFiN2M2YzBmYmMwNDRmODk3ZGU3NTQ0ODllMzYyYzY=|1468827275|ccd88305461b2a3f2d9c38ec5c651e1bfcba81de; cap_id=ZGQ1MjFjMzM5MGI2NDY5ZmFjMGQ5NzMxODI2M2EzNWM=|1468827275|e44ef0b232dd85e4a62077a6a67e83ccbe963692; _zap=82d8c931-4ad6-464b-8e3f-2e430cce84e0; d_c0=AIBAeHJDNgqPTo5KKrizojLF6zLSb8c38qo=|1468220251; login=ZGNlMjUwYzNjNmMxNDI0N2I1YjQyMjVlMDM3YjMwN2Y=|1468827275|1c4c6a2dd0dec9d3948653906728e6ceb22154b2; __utma=51854390.1408714905.1468575990.1468819740.1468824510.5; __utmz=51854390.1468824510.5.4.utmcsr=zhihu.com|utmccn=(referral)|utmcmd=referral|utmcct=/topic/19552832/top-answers; __utmv=51854390.000--|2=registration_date=20130613=1^3=entry_date=20160711=1; __utmb=51854390.8.10.1468824510; n_c=1'
    }

    name = 'zhihu'
    _xsrf = ''
    cookie_jar = CookieJar()
    driver = None
    login_cookies = None
    login_cookies_dict = None

    # rules = (
    #     Rule(SgmlLinkExtractor(allow=(r'/question/\d+',)), follow=True),
    #     Rule(SgmlLinkExtractor(allow=(r'/people/(\w+-?)+$',)), callback='parse_page'),
    # )

    def __init__(self):
        super(CrawlSpider, self).__init__()
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        Request('http://www.zhihu.com/logout', method='GET', callback=self.logout)
        pass

    def logout(self):
        print('退出成功')
        pass

    def start_requests(self):
        _driver = webdriver.PhantomJS(service_log_path='./phantomjs.log')
        _driver.set_window_size(GetSystemMetrics(0), GetSystemMetrics(1))
        self.driver = _driver
        (cookies, expires) = self.getcookies()
        if expires < time.time():
            expires = False
            print('cookie过期')
        print(cookies)
        if cookies and expires:
            self.cookie_jar = CookieJar()
            for key in cookies:
                self.cookie_jar.set_cookie(cookies[key])
            for url in self.start_urls:
                requset = Request(url, headers=self.headers,
                                  meta={'dont_merge_cookies': True, 'cookie_jar': self.cookie_jar},
                                  callback=self.parse_page)
                self.cookie_jar.add_cookie_header(requset)
                return [requset]
        _driver.get("https://www.zhihu.com/#signin")
        # wait = WebDriverWait(driver, 12)  # 等待
        time.sleep(8)  # 等待页面加载完毕
        _xsrf = _driver.find_element_by_xpath('//input[@name="_xsrf"]')
        _xsrf = _xsrf.get_attribute('value')
        print('_xsrf------->', _xsrf)
        input_wrapper = _driver.find_element_by_xpath('//div[@data-za-module="SignInForm"]')
        # iCaptcha = True
        # 等待验证码加载完成
        try:
            # input_captcha = wait.until(
            #     EC.presence_of_element_located((By.XPATH, './/div[@class="input-wrapper captcha-module"]')))
            input_captcha = input_wrapper.find_element_by_xpath('.//div[@class="input-wrapper captcha-module"]')
        except:
            try:
                # input_captcha = wait.until(
                #     EC.presence_of_element_located((By.XPATH, './/div[@class="iCaptcha input-wrapper"]')))
                # iCaptcha = False
                input_captcha = input_wrapper.find_element_by_xpath('.//div[@class="iCaptcha input-wrapper"]')
            except:
                input_captcha = None
        if input_captcha:
            hasShow = input_captcha.is_displayed()
        else:
            hasShow = False
        print(input_captcha, '-----captcha_url----->', hasShow)

        if hasShow:
            # 有验证码,先下载验证码
            # todo 这个地方还需要在处理一下,不能直接下载验证码不然会被服务器刷新验证码
            captcha_url = input_wrapper.find_element_by_xpath('.//img').get_attribute('src')
            print('captcha_url---->', captcha_url)
            # input_wrapper.screenshot('./captcha.png')
            _driver.close()
            return [Request(captcha_url, headers=self.headers, callback=self.download_captcha, meta={'_xsrf': _xsrf})]
        else:
            _driver.close()
            return [self.post_login(_xsrf)]

    def download_captcha(self, response):
        # 下载验证码
        with open('captcha.gif', 'wb') as fp:
            fp.write(response.body)
        # 用软件打开验证码图片
        os.system('start captcha.gif')
        # 输入验证码
        print('Please enter captcha: ')
        captcha = input()
        return self.post_login(response.meta['_xsrf'], captcha)

    def post_login(self, _xsrf, captcha=None):
        # sel = Selector(response)
        # _xsrf = sel.xpath('//input[@name="_xsrf"]/@value').extract()[0]
        # self.cookie_jar = response.meta.setdefault('cookie_jar', CookieJar())
        formdata = {'_xsrf': _xsrf,
                    'password': projectsetting.PASS_WORD,  # 你的密码
                    'captcha_type': 'cn',
                    'remember_me': 'true',
                    'email': projectsetting.USER_NAME}  # 你的账号

        if captcha != None:
            formdata['captcha'] = captcha
        return FormRequest("https://www.zhihu.com/login/email", method='POST', headers=self.headers,
                           callback=self.login_result,
                           meta={'dont_merge_cookies': True},
                           formdata=formdata)  # 你的账号

        pass

    def login_result(self, response):
        body = json.loads(response.body.decode('utf-8'))
        print('content---->', body)
        if body.get('r') != 0:
            return
        self.cookie_jar = response.meta.setdefault('cookie_jar', CookieJar())
        self.cookie_jar.extract_cookies(response, response.request)
        for url in self.start_urls:
            requset = Request(url, headers=self.headers,
                              meta={'dont_merge_cookies': True, 'cookie_jar': self.cookie_jar},
                              callback=self.parse_page)
            self.cookie_jar.add_cookie_header(requset)
            yield requset
        pass

    def savecookies(self, cookies):
        copyCookie = dict()
        with open('login_cookie.json', 'w') as cookiesfile:
            def convterall(cookies):
                for key in cookies.keys():
                    value = cookies.get(key)
                    if isinstance(value, Cookie):
                        copyCookie[key] = self.class2str(value)
                    elif isinstance(value, dict):
                        convterall(value)

            convterall(cookies)
            self.login_cookies_dict = copyCookie
            cookiesfile.write(json.dumps(copyCookie))
        pass

    def class2str(self, dictdata):
        dic = {}
        dic.update(dictdata.__dict__)
        return dic
        pass

    def dict2cookie(self, cookie_dict):
        result = {}
        for item in cookie_dict.items():
            param = ''
            for key in item[1]:
                value = item[1][key]
                if type(value) == str:
                    value = "'" + value + "'"
                if key[0] == '_':
                    key = key[1:]
                param += '{0}={1},'.format(key, value)
            param = param[0:-1]
            evalstr = 'Cookie({0})'.format(param)
            result[item[0]] = eval(evalstr)
        return result
        # return {'.zhihu.com': {'/': result}}

    def getcookies(self):
        expires = 0
        if self.login_cookies:
            for key in self.login_cookies:
                expires = self.login_cookies[key].expires
                break
            return (self.login_cookies, expires)
        if not os.path.exists('login_cookie.json'):
            return (None, 0)
        with open('login_cookie.json', encoding='utf-8') as cookiesfile:
            cookiesstr = cookiesfile.read()
            if cookiesstr == '' or cookiesstr == None:
                return (None, 0)
            cookies = json.loads(cookiesstr)
            self.login_cookies = self.dict2cookie(cookies)
            expires = 0
            if self.login_cookies:
                for key in self.login_cookies:
                    expires = self.login_cookies[key].expires
                    if expires != None:
                        break
            return (self.login_cookies, expires)
        pass

    def parse_page(self, response):
        sel = Selector(response)
        href = sel.xpath('//ul[@id="top-nav-profile-dropdown"]/li[1]/a/@href').extract()[0]
        print('href----->', href)
        # 刷新cookie
        cookie_jar = CookieJar()
        cookie_jar.extract_cookies(response, response.request)
        self.savecookies(self.cookie_jar._cookies)
        request = Request(self.host_url + href, headers=self.headers, meta={'cookie_jar': cookie_jar},
                          callback=self.people_page)
        cookie_jar.add_cookie_header(request)
        return request
        pass

    def people_page(self, response):
        sel = Selector(response)
        # 关注和被关注
        following = sel.xpath('//div[@class="zm-profile-side-following zg-clear"]')
        followees_followers = following.xpath('.//strong/text()').extract()
        count = 0
        for follow in followees_followers:
            count += int(follow)
        if count == 0:
            print('这是一个僵尸号:', response.url.replace(self.host_url + '/people/', ''))
            return
        topics_link = sel.xpath('//a[@class="zg-link-litblue"]/@href').extract()[1]
        print('topics->>>>>>>>>>>', topics_link)
        # cookie_jar = response.meta['cookie_jar']
        # 打开关注的话题
        self.webdriver_addcookies(topics_link)
        browerHeight = self.driver.execute_script('return document.body.scrollHeight;')
        while True:
            # do the scrolling
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)  # 等待加载完成数据
            scrollHeight = self.driver.execute_script('return document.body.scrollHeight;')
            if browerHeight == scrollHeight:
                break
            browerHeight = scrollHeight

        topic_list = self.driver.find_element_by_id('zh-profile-topic-list')
        item = ZhihuItem()
        item['name'] = self.driver.find_element_by_xpath('//span[@class="name"]').text
        item['business'] = self.driver.find_element_by_xpath('//span[@class="business item"]').get_attribute('title')
        item['location'] = self.driver.find_element_by_xpath('//span[@class="location item"]').text
        topics = []
        topic_divs = topic_list.find_elements_by_xpath(
            './/div[@class="zm-profile-section-item zg-clear zm-editable-status-normal"]')
        for topic in topic_divs:
            section = topic.find_element_by_xpath('.//div[@class="zm-profile-section-main"]')
            links = section.find_elements_by_tag_name('a')
            topicdata = links[1]
            topic_id = os.path.basename(topicdata.get_attribute('href'))
            topic_name = topicdata.find_element_by_tag_name('strong').text
            topic_answers = int(links.pop().text.replace(' 个回答', ''))
            topics.append({'topic_id': topic_id, 'topic_name': topic_name, 'topic_answers': topic_answers})
        item['topics'] = topics
        yield item
        # request = Request(self.host_url + topics, headers=self.headers, meta={'cookie_jar': self.cookie_jar},
        #                   callback=self.topics_page)
        # cookie_jar.add_cookie_header(request)
        # yield request

        # todo 递归找出所有有效用户关注的数据
        # followings = following.xpath('.//a/@href').extract()
        # followees = followings[0]  # 关注的链接
        # yield self.cookiejar_addcookies(response, followees, self.followees_page)
        # followers = followings[1]  # 被关注
        # yield self.cookiejar_addcookies(response, followers, self.followees_page)
        pass

    def webdriver_addcookies(self, url):
        for key in self.login_cookies_dict:
            cookie = self.login_cookies_dict[key]
            self.driver.add_cookie({k: cookie[k] for k in ['name', 'value', 'domain', 'path']})
        self.driver.get(self.host_url + url)
        pass

    def cookiejar_addcookies(self, response, url, callback):
        cookie_jar = response.meta['cookie_jar']
        request = Request(self.host_url + url, headers=self.headers, meta={'cookie_jar': cookie_jar},
                          callback=callback)
        cookie_jar.add_cookie_header(request)
        yield request
        pass

    def followees_page(self, response):
        sel = Selector(response)
        peoplelinks = sel.xpath('//a[@class="zm-item-link-avatar"]/@href').extract()
        for link in peoplelinks:
            yield self.cookiejar_addcookies(response, url=link, callback=self.people_page)
        pass
