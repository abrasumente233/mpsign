# -*- coding: utf-8 -
import re
import hashlib
from collections import OrderedDict, namedtuple

import requests
from bs4 import BeautifulSoup
from cached_property import cached_property

SignResult = namedtuple('SignResult', ['message', 'exp', 'bar', 'code'])
fid_pattern = re.compile(r"(?<=forum_id': ')\d+")


class User:
    def __init__(self, bduss):
        self.bduss = bduss
        self._tbs = ''
        self._bars = []

    def sign(self, bar):
        return bar.sign(self)

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
                             cookies={'BDUSS': self.bduss}
                             )

        self._tbs = tbs_r.json()['tbs']
        return self._tbs

    @cached_property
    def bars(self):
        page = 1
        while True:
            r = requests.get('http://tieba.baidu.com/f/like/mylike?&pn={}'.format(page),
                             headers={'Content-Type': 'application/x-www-form-urlencoded', },
                             cookies={'BDUSS': self.bduss}
                             )

            r.encoding = 'gbk'

            soup = BeautifulSoup(r.text, "lxml")
            rows = soup.find_all('tr')[1:]  # find all rows except the table header

            for row in rows:
                kw = row.td.a.get_text()  # bar name
                fid = int(row.find_all('td')[3].span['balvid'])  # a bar's fid used for signing

                self._bars.append(Bar(kw, fid))

            if r.text.find('下一页') == -1:
                break

            page += 1

        return self._bars


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
                              bar=self, exp=0)
        else:
            return SignResult(message='ok', code=0, bar=self,
                              exp=int(json_r['user_info']['sign_bonus_point']))
