# -*- coding: utf-8 -
import os
import time
import re
import hashlib
from collections import OrderedDict, namedtuple

import requests
from bs4 import BeautifulSoup
from cached_property import cached_property

from .crypto import rsa_encrypt

RSA_PUB_KEY = '010001'
RSA_MODULUS = 'B3C61EBBA4659C4CE3639287EE871F1F48F7930EA977991C7AFE3CC442FEA49643212' \
              'E7D570C853F368065CC57A2014666DA8AE7D493FD47D171C0D894EEE3ED7F99F6798B7F' \
              'FD7B5873227038AD23E3197631A8CB642213B9F27D4901AB0D92BFA27542AE89085539' \
              '6ED92775255C977F5C302F1E7ED4B1E369C12CB6B1822F'

data_directory = os.path.expanduser('~' + os.path.sep + '.mpsign')

# detect parser for BeautifulSoup
try:
    import lxml
    parser = 'lxml'
    del lxml
except ImportError:
    try:
        import html5lib
        parser = 'html5lib'
        del html5lib
    except ImportError:
        parser = None

try:  # move old files
    if os.path.isfile(data_directory):  # 1.4 -- 1.5
        os.rename(data_directory, os.path.expanduser('~') + os.sep + '.mpsignbak')
        try:
            os.mkdir(data_directory)
        except Exception:
            pass
        os.rename(os.path.expanduser('~') + os.sep + '.mpsignbak',
                  data_directory + os.sep + '.mpsigndb')
    else:  # new to mpsign 1.5
        try:
            os.mkdir(data_directory)
        except Exception:
            pass
except:
    pass


SignResult = namedtuple('SignResult', ['message', 'exp', 'bar', 'code', 'total_sign', 'rank', 'cont_sign'])
fid_pattern = re.compile(r"(?<=forum_id': ')\d+")


class LoginFailure(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message


class InvalidPassword(LoginFailure):
    pass


class InvalidCaptcha(LoginFailure):
    pass


class InvalidUsername(LoginFailure):
    pass


class DangerousEnvironment(LoginFailure):
    pass


class Captcha:
    def __init__(self, image):
        self.image = image
        self.input = None
        self.path = None

    def as_file(self, path=None):
        if path is None:
            try:
                os.mkdir('{d}{sep}www'.format(d=data_directory, sep=os.sep))
            except:
                pass

            self.path = '{d}{sep}www{sep}captcha.gif'.format(d=data_directory, sep=os.sep)
        else:
            self.path = path

        with open(self.path, 'wb') as f:
            for chunk in self.image:
                f.write(chunk)

    def get_image(self):
        return self.image

    def fill(self, captcha):
        self.input = captcha

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
        self.bduss = bduss
        self._tbs = ''
        self._bars = []

    def sign(self, bar):
        return bar.sign(self)

    @classmethod
    def login(cls, username, password):
        s = requests.Session()

        # get a BAIDUID or it will present me "Please enable cookies"
        s.get('http://wappass.baidu.com/passport/?login')

        timestamp = str(int(time.time()))

        payload = {
            'loginmerge': '1',
            'servertime': timestamp,
            'username': username,
            'password': rsa_encrypt(password + timestamp,
                                    RSA_MODULUS, RSA_PUB_KEY),
            'gid': '8578373-26F9-4B83-92EB-CC2BA36C7183'
        }

        r = s.post('http://wappass.baidu.com/wp/api/login?tt={}'.format(timestamp),
                   data=payload)

        # see if captcha is needed
        vcodestr = r.json()['data']['codeString']
        if not vcodestr == '':
            while True:
                r_captcha = s.get('http://wappass.baidu.com/cgi-bin/genimage?{0}&v={1}'.format(vcodestr, timestamp),
                                  stream=True)

                captcha = Captcha(r_captcha.raw)
                user_input = yield captcha
                user_input = user_input or captcha.input
                if user_input is None:
                    raise InvalidCaptcha(500002, 'Your captcha is wrong.')
                elif user_input == 'another':
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
            # 400010 unexisting user
            # 230048 just invalid because of the format
            raise InvalidUsername(int(status), message)
        elif status == '400101':
            raise LoginFailure(400101, 'Email authentication is needed. Use BDUSS instead.')
        else:
            raise LoginFailure(status, message)

    def verify(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.1.2; zh-cn; MB526 Build/JZO54K)'
                          ' AppleWebKit/530.17 (KHTML, like Gecko) FlyFlow/2.4 Version/4.0'
                          ' Mobile Safari/530.17'
                          ' baidubrowser/042_1.8.4.2_diordna_458_084/alorotoM_61_2.1.4_625BM/'
                          '1200a/39668C8F77034455D4DED02169F3F7C7%7C132773740707453/1',
            'Referer': 'http://tieba.baidu.com'
        }
        r = requests.get('http://tieba.baidu.com/dc/common/tbs',
                         headers=headers, cookies={'BDUSS': self.bduss})

        return bool(r.json()['is_login'])

    @cached_property
    def tbs(self):
        tbs_r = requests.get('http://tieba.baidu.com/dc/common/tbs',
                             headers={'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.1.2; zh-cn; MB526 Build/JZO54K)'
                                                    ' AppleWebKit/530.17 (KHTML, like Gecko) FlyFlow/2.4'
                                                    ' Version/4.0 Mobile Safari/530.17 baidubrowser/042_1.8.4.2'
                                                    '_diordna_458_084/alorotoM_61_2.1.4_625BM/1200a/39668C8F770'
                                                    '34455D4DED02169F3F7C7%7C132773740707453/1',
                                      'Referer': 'http://tieba.baidu.com/'},
                             cookies={'BDUSS': self.bduss})

        self._tbs = tbs_r.json()['tbs']
        return self._tbs

    @cached_property
    def bars(self):
        if parser is None:
            raise ImportError('Please install a parser for BeautifulSoup! either lxml or html5lib.')

        page = 1
        while True:
            r = requests.get('http://tieba.baidu.com/f/like/mylike?&pn={}'.format(page),
                             headers={'Content-Type': 'application/x-www-form-urlencoded'},
                             cookies={'BDUSS': self.bduss})

            r.encoding = 'gbk'

            soup = BeautifulSoup(r.text, parser)
            rows = soup.find_all('tr')[1:]  # find all rows except the table header

            for row in rows:
                kw = row.td.a.get_text()  # bar name
                fid = int(row.find_all('td')[3].span['balvid'])  # a bar's fid used for signing

                self._bars.append(Bar(kw, fid))

            if r.text.find('下一页') == -1:
                break

            page += 1

        return tuple(self._bars)


class Bar:
    def __init__(self, kw, fid=None):
        self.kw = kw
        self._fid = fid

    @cached_property
    def fid(self):
        if self._fid is None:
            r = requests.get('http://tieba.baidu.com/f/like/level?kw={}'.format(self.kw))
            return fid_pattern.search(r.text).group()
        else:
            return self._fid

    def sign(self, user):

        # BY KK!!!! https://ikk.me
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

        sign_str = ''

        for k, v in post_data.items():
            sign_str += '%s=%s' % (k, v)

        sign_str += 'tiebaclient!!!'
        m = hashlib.md5()
        m.update(sign_str.encode('utf-8'))
        sign_str = m.hexdigest().upper()

        post_data['sign'] = sign_str

        r = requests.post('http://c.tieba.baidu.com/c/c/forum/sign',
                          headers={'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
                                   'User-Agent': 'Mozilla/5.0 (SymbianOS/9.3; Series60/3.2 NokiaE72-1/021.021;'
                                                 ' Profile/MIDP-2.1 Configuration/CLDC-1.1 ) '
                                                 'AppleWebKit/525 (KHTML, like Gecko) Version/3.0 BrowserNG/7.1.16352'},
                          cookies={'BDUSS': user.bduss},
                          data=post_data)

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
