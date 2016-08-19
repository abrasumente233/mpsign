# -*- coding: utf-8 -
import os
import time
import re
import hashlib
from collections import OrderedDict, namedtuple

import requests
from bs4 import BeautifulSoup
from cached_property import cached_property

from mpsign.crypto import rsa_encrypt
from mpsign.util import select_package
from mpsign.const import *
from mpsign.exceptions import *

# 给 BeautifulSoup 相一个 parser
parser = select_package(('lxml', 'html5lib'))

try:
    os.makedirs(DATA_DIR)
except Exception:
    pass

SignResult = namedtuple('SignResult', ['message', 'exp', 'bar', 'code', 'total_sign', 'rank', 'cont_sign'])
fid_pattern = re.compile(r"(?<=forum_id': ')\d+")
blank_pattern = re.compile(r'\s')


class Captcha:
    def __init__(self, image):
        self.image = image
        self.input = None
        self.path = None

    def as_file(self, path=None):
        if path is None:
            try:
                os.mkdir('{d}{s}www'.format(d=DATA_DIR, s=os.sep))
            except:
                pass

            self.path = '{d}{s}www{s}captcha.gif'.format(d=DATA_DIR, s=os.sep)
        else:
            self.path = path

        with open(self.path, 'wb') as f:
            for chunk in self.image:
                f.write(chunk)

    def get_image(self):
        return self.image

    def fill(self, captcha):
        if not isinstance(captcha, str):
            raise TypeError('Captcha is a string, got {0}'.format(type(captcha).__name__))
        self.input = captcha.strip()

    def destroy(self):
        try:
            if self.path is not None:
                os.remove(self.path)
        except:
            pass

        try:
            self.image.close()
        except:
            pass


class User:
    def __init__(self, bduss):
        if not isinstance(bduss, str) or bduss == '':
            raise InvalidBDUSSException()
        self._bduss = bduss
        self._validation = None

    @property
    def bduss(self):
        return self._bduss

    def sign(self, bar):
        return bar.sign(self)

    @classmethod
    def login(cls, username, password):
        s = requests.Session()

        # 随便访问一个网址来获得一个 SESSION ID (BAIDUID)
        # 否则会提示你 请开启 Cookie
        s.get('http://wappass.baidu.com/passport/?login')

        timestamp = str(int(time.time())) # 当前时间 精确到秒

        payload = {
            'loginmerge': '1',
            'servertime': timestamp,
            'username': username,
            'password': rsa_encrypt(password + timestamp,
                                    RSA_MODULUS, RSA_PUB_KEY),
            'gid': '8578373-26F9-4B83-92EB-CC2BA36C7183'  # 随便取
        }

        r = s.post('http://wappass.baidu.com/wp/api/login?tt={}'.format(timestamp),
                   data=payload)

        # 是否需要验证码
        vcodestr = r.json()['data']['codeString']
        if vcodestr:
            while True:
                r_captcha = s.get('http://wappass.baidu.com/cgi-bin/genimage?{0}&v={1}'.format(vcodestr, timestamp),
                                  stream=True)

                captcha = Captcha(r_captcha.raw)
                user_input = yield captcha
                if user_input is not None:
                    # 支持两种方式填验证码：
                    # 1. captcha.fill(somecaptcha)
                    # 2. gen.send(somecaptcha)
                    # 如果都填有，优先采用第二种
                    captcha.fill(user_input)
                if captcha.input is None:
                    raise InvalidCaptcha(500002, 'You have typed an incorrect captcha')
                elif captcha.input == 'another':
                    continue
                else:
                    break

            payload['vcodestr'] = vcodestr
            payload['verifycode'] = user_input

            r = s.post('http://wappass.baidu.com/wp/api/login?tt={}'.format(timestamp),
                       data=payload)

        data = r.json()
        status = data['errInfo']['no']
        message = data['errInfo']['msg']

        if status == '0':
            yield cls(data['data']['bduss'])
        elif status == '400011':
            raise InvalidPassword(400011, message)
        elif status == '500002':
            raise InvalidCaptcha(500002, message)
        elif status == '50000':
            raise DangerousEnvironment(50000, message)
        elif status == '400010' or status == '230048':
            # 400010 用户不存在
            # 230048 用户名格式错误
            raise InvalidUsername(int(status), message)
        elif status == '400101':
            raise LoginFailure(400101, 'Email auth required. Use BDUSS instead.')
        else:
            raise LoginFailure(status, message)

    @cached_property
    def validation(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.1.2; zh-cn; MB526 Build/JZO54K)'
                          ' AppleWebKit/530.17 (KHTML, like Gecko) FlyFlow/2.4 Version/4.0'
                          ' Mobile Safari/530.17'
                          ' baidubrowser/042_1.8.4.2_diordna_458_084/alorotoM_61_2.1.4_625BM/'
                          '1200a/39668C8F77034455D4DED02169F3F7C7%7C132773740707453/1',
            'Referer': 'http://tieba.baidu.com'
        }
        r = requests.get('http://tieba.baidu.com/dc/common/tbs',
                         headers=headers, cookies={'BDUSS': self.bduss}, timeout=TIMEOUT)

        is_valid = bool(r.json()['is_login'])
        self._validation = is_valid
        return is_valid

    @cached_property
    def tbs(self):
        tbs_r = requests.get('http://tieba.baidu.com/dc/common/tbs',
                             headers={'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.1.2; zh-cn; MB526 Build/JZO54K)'
                                                    ' AppleWebKit/530.17 (KHTML, like Gecko) FlyFlow/2.4'
                                                    ' Version/4.0 Mobile Safari/530.17 baidubrowser/042_1.8.4.2'
                                                    '_diordna_458_084/alorotoM_61_2.1.4_625BM/1200a/39668C8F770'
                                                    '34455D4DED02169F3F7C7%7C132773740707453/1',
                                      'Referer': 'http://tieba.baidu.com/'},
                             cookies={'BDUSS': self.bduss},
                             timeout=TIMEOUT)

        is_valid = bool(tbs_r.json()['is_login'])
        self._validation = is_valid
        if not is_valid:
            raise InvalidBDUSSException()

        self._tbs = tbs_r.json()['tbs']
        return self._tbs

    @cached_property
    def bars(self):
        if parser is None:
            raise ImportError('Please install a parser for BeautifulSoup! either lxml or html5lib.')

        if not self.validation:
            raise InvalidBDUSSException()

        self._bars = []  # 在这里初始化比较好 (｀・ω・´)
        page = 1
        while True:
            r = requests.get('http://tieba.baidu.com/f/like/mylike?&pn={}'.format(page),
                             headers={'Content-Type': 'application/x-www-form-urlencoded'},
                             cookies={'BDUSS': self.bduss},
                             timeout=TIMEOUT)

            r.encoding = 'gbk'

            soup = BeautifulSoup(r.text, parser)
            rows = soup.find_all('tr')[1:]  # 获取除表头外所有行

            for row in rows:
                kw = row.td.a.get_text()  # 吧名
                fid = int(row.find_all('td')[3].span['balvid'])  # 签到时需要的 fid

                self._bars.append(Bar(kw, fid))

            if r.text.find('下一页') == -1:
                break

            page += 1

        return tuple(self._bars)


class Bar:
    def __init__(self, kw, fid=None):
        if not isinstance(kw, str):
            raise TypeError('bar name except a string, got {0}'.format(type(kw).__name__))

        if blank_pattern.search(kw) or kw == '':
            raise InvalidBar('there was blank in the bar name')

        if fid is not None:
            if not isinstance(fid, (str, int)):
                raise TypeError('fid except a string or an int, got {0}'.format(type(fid).__name__))
            self._fid = fid.strip() if isinstance(fid, str) else str(fid)
        else:
            self._fid = None

        self.kw = kw

    @cached_property
    def fid(self):
        if self._fid is None:
            r = requests.get('http://tieba.baidu.com/f/like/level?kw={}'.format(self.kw), timeout=TIMEOUT)
            return fid_pattern.search(r.text).group()
        else:
            return self._fid

    def sign(self, user):

        if not user.validation:
            raise InvalidBDUSSException()

        # BY KK!!!! https://ikk.me
        # BY KK!!!! https://ikk.me
        # BY KK!!!! https://ikk.me
        # (=・ω・=)
        post_data = OrderedDict()
        post_data['BDUSS'] = user.bduss
        post_data['_client_id'] = '03-00-DA-59-05-00-72-96-06-00-01-00-04-00-4C-43-01-00-34-F4-02-00-BC-25-09-00-4E-36'
        post_data['_client_type'] = '4'
        post_data['_client_version'] = '1.2.1.17'
        post_data['_phone_imei'] = '540b43b59d21b7a4824e1fd31b08e9a6'
        post_data['fid'] = self.fid
        post_data['kw'] = self.kw
        post_data['net_type'] = '3'
        post_data['tbs'] = user.tbs

        sign_str = []

        for k, v in post_data.items():
            sign_str.append('{0}={1}'.format(k, v))

        sign_str.append('tiebaclient!!!')
        m = hashlib.md5()
        m.update(''.join(sign_str).encode('utf-8'))
        sign_str = m.hexdigest().upper()

        post_data['sign'] = sign_str

        r = requests.post('http://c.tieba.baidu.com/c/c/forum/sign',
                          headers={'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
                                   'User-Agent': 'Mozilla/5.0 (SymbianOS/9.3; Series60/3.2 NokiaE72-1/021.021;'
                                                 ' Profile/MIDP-2.1 Configuration/CLDC-1.1 ) '
                                                 'AppleWebKit/525 (KHTML, like Gecko) Version/3.0 BrowserNG/7.1.16352'},
                          cookies={'BDUSS': user.bduss},
                          data=post_data,
                          timeout=TIMEOUT)

        json_r = r.json()

        if not json_r['error_code'] == '0':
            return SignResult(message=json_r['error_msg'], code=json_r['error_code'],
                              bar=self, exp=0, total_sign=-1, cont_sign=-1, rank=-1)
        else:
            return SignResult(message='ok', code=0, bar=self,
                              exp=int(json_r['user_info']['sign_bonus_point']),
                              total_sign=json_r['user_info']['total_sign_num'],
                              cont_sign=json_r['user_info']['cont_sign_num'],
                              rank=json_r['user_info']['user_sign_rank'])

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            raise TypeError('except {0}, got {1}'.format(type(self).__name__, type(other).__name__))
        return self.kw == other.kw

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return '<Bar: {bar}>'.format(bar=self.kw)

    def __repl__(self):
        return str(self)
