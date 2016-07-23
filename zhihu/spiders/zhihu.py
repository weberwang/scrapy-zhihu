import zhihu.settings as projectsetting

import scrapy
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher
from scrapy.selector import Selector
from scrapy.http import Request, FormRequest
from scrapy.http.cookies import CookieJar
from scrapy.spiders import CrawlSpider, Rule

import os
import json

from http.cookiejar import Cookie

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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
        self.driver = _driver
        _driver.implicitly_wait(12)
        _driver.get("https://www.zhihu.com/#signin")
        # wait = WebDriverWait(driver, 12)  # 等待
        _xsrf = _driver.find_element_by_xpath('//input[@name="_xsrf"]')
        _xsrf = _xsrf.get_attribute('value')
        print('_xsrf------->', _xsrf)
        cookies = self.getcookies()
        print(cookies)
        if cookies:
            self.cookie_jar = CookieJar()
            self.cookie_jar.set_cookie(cookies)
            for url in self.start_urls:
                requset = Request(url, headers=self.headers,
                                  meta={'dont_merge_cookies': True, 'cookie_jar': self.cookie_jar},
                                  callback=self.parse_page)
                self.cookie_jar.add_cookie_header(requset)
            return
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
                    'remember_me': 'false',
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
        print('cookies----->', self.cookie_jar._cookies)
        self.savecookies(self.cookie_jar._cookies)
        for url in self.start_urls:
            requset = Request(url, headers=self.headers,
                              meta={'dont_merge_cookies': True, 'cookie_jar': self.cookie_jar},
                              callback=self.parse_page)
            self.cookie_jar.add_cookie_header(requset)
            yield requset
        pass

    def savecookies(self, cookies):
        with open('login_cookie.json', 'w') as cookiesfile:
            def convterall(cookies):
                for key in cookies.keys():
                    value = cookies.get(key)
                    print(type(value))
                    if isinstance(value, Cookie):
                        cookies[key] = self.class2str(value)
                    elif isinstance(value, dict):
                        convterall(value)

            convterall(cookies)
            cookiesfile.write(json.dumps(cookies))
        pass

    def class2str(self, dictdata):
        dic = {}
        dic.update(dictdata.__dict__)
        return dic
        pass

    def dict2cookie(self, cookie_dict):
        for key in cookie_dict.keys():
            for nextkey in cookie_dict[key].keys():
                if nextkey == '/':
                    cookies = cookie_dict[key][nextkey]
                    result = {}
                    for item in cookies.items():
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

        return {'.zhihu.com': {'/': result}}

    def getcookies(self):
        if not os.path.exists('login_cookie.json'):
            return None
        with open('login_cookie.json') as cookiesfile:
            cookiesstr = cookiesfile.read()
            if cookiesstr == '' or cookiesstr == None:
                return None
            cookies = cookiesfile.read()
            cookies = json.loads(cookies, encoding='utf-8')
            return self.dict2cookie(cookies)
        pass

    def parse_page(self, response):
        sel = Selector(response)
        href = sel.xpath('//a[@class="top-nav-profile-dropdown"]/li[1]/a/@href').extract()[0]
        print('href----->', href)
        cookie_jar = response.meta['cookie_jar']
        request = Request(self.host_url + href, headers=self.headers, meta={'cookie_jar': self.cookie_jar},
                          callback=self.people_page)
        cookie_jar.add_cookie_header(request)
        pass

    def people_page(self, response):
        sel = Selector(response)
        # 关注和被关注
        following = sel.xpath('//div{@class="zm-profile-side-following zg-clear"]')
        followees_followers = following.xpath('.//strong/text()').extract()
        count = 0
        for follow in followees_followers:
            count += int(follow)
        if count == 0:
            print('这是一个僵尸号:', response.url.replace(self.host_url + '/people/'))
            return
        topics = sel.xpath('//a[@class="zg-link-litblue"]/@href').extract()[0]
        print('topics->>>>>>>>>>>', topics)
        cookie_jar = response.meta['cookie_jar']
        # 打开关注的话题
        request = Request(self.host_url + topics, headers=self.headers, meta={'cookie_jar': self.cookie_jar},
                          callback=self.topics_page)
        cookie_jar.add_cookie_header(request)
        yield request

        # todo 递归找出所有有效用户关注的数据
        followings = following.xpath('.//div/@href').extract()
        followees = followings[0]  # 关注的链接
        followers = followings[1]  # 被关注
        pass

    def topics_page(self, response):
        sel = Selector(response)
        topic_items = sel.xpath('//div[@class="zm-profile-section-item zg-clear zm-editable-status-normal"]')
        for item in topic_items:
            topic = item.xpath('.//a/[@data-hovercard]')[0]
            topic_id = topic.xpath('./@href').extract()[0].replace('/topic/')
            topic_name = topic.xpath('.//strong').extract()[0]
            print(topic_name, topic_id)
        pass
