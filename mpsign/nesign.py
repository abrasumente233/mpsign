#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import json
import random
import math
import base64
import requests

from Crypto.Cipher import AES
from Crypto.PublicKey.RSA import RSAImplementation

'''
A module for helping you to finish the daily task on Neteasy Music
'''

__author__ = 'abrasumente'

# 常量
PUBKEY = '010001'
MODULES = '00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17' \
          'a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114a' \
          'f6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d5' \
          '46b8e289dc6935b3ece0462db0a22b8e7'
NONCE = '0CoJUm6Qyw8W8jud'
IV = '0102030405060708'

TYPE_WEBPC = 1
TYPE_ANDROID = 0

# 关闭 urllib3 的 logging
urllib3_logger = logging.getLogger('urllib3')
urllib3_logger.setLevel(logging.CRITICAL)


def _config_log(echo, filename=None):
    if echo:
        if filename:
            logging.basicConfig(level=logging.INFO,
                                format='%(asctime)s %(message)s',
                                datefmt='[%Y-%m-%d %H:%M:%S]',
                                filename=filename,
                                filemode='w')
        else:
            logging.basicConfig(level=logging.INFO,
                                format='%(asctime)s %(message)s',
                                datefmt='[%Y-%m-%d %H:%M:%S]')


def log_from_code(result, platform, name):
    code = result['code']
    if code == -2:
        logging.info('{0}: {1} failed. had done the task today'.format(name, platform))
    elif code == 200:
        logging.info('{0}: {1} ok. point +{2}'.format(name, platform, result['point']))
    else:
        logging.info('{0}: {1} failed. {2}({3})'.format(name, platform,
                                                        code, result['msg']))

# 封印开始 -- 千万别看这段，自己都感觉浪费人生

block_size = AES.block_size
pad = lambda s: s + (block_size - len(s) % block_size) * chr(block_size - len(s) % block_size)


def hex2bi(s):
    result = []
    s_len = len(s)

    i = s_len
    while i > 0:
        start = max(i - 4, 0)
        length = start + min(i, 4)
        result.append(int(s[start:length], 16))
        i -= 4
    return result


def bi_high_index(x):
    result = len(x) - 1
    while result > 0 and x[result] == 0:
        result -= 1
    return result


def bi2hex(x):
    result = ''
    i = bi_high_index(x)
    while i > -1:
        result += hex(x[i])[2:]
        i -= 1
    return result


def ne_str2int(key, s):
    a = []
    s_len = len(s)
    i = 0
    chunk_size = 2 * bi_high_index(hex2bi(hex(key.n)[2:]))
    while i < s_len:
        a.append(ord(s[i]))
        i += 1

    while len(a) % chunk_size != 0:
        a.append(0)
        i += 1
    i = k = 0
    block = []
    while k < i + chunk_size:
        block.append(a[k] + (a[k + 1] << 8))
        k += 2
    return int(bi2hex(block), 16)


def create_secret_key(size):
    keys = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    key = ''
    i = 0
    while i < size:
        pos = math.floor(random.random() * len(keys))
        key += keys[pos]
        i += 1
    return key


def aes_encrypt(text, sec_key, byte=False):
    cipher = AES.new(sec_key, AES.MODE_CBC, IV=IV)
    return base64.b64encode(cipher.encrypt(pad(text))) if not byte else base64.b64encode(
        cipher.encrypt(pad(str(text, 'utf-8'))))


def rsa_encrypt(text, pub_key, modules):
    impl = RSAImplementation()
    keys = impl.construct((int(modules, 16), int(pub_key, 16)))
    result = keys.encrypt(ne_str2int(keys, text), 2)[0]
    return hex(result)[2:]  # 移除前缀 0x


def aes_rsa_encrypt(text, pubkey, modulus, nonce, *, sec_key=None):
    result = {}
    sec_key = create_secret_key(16) if sec_key is None else sec_key
    result['enc_text'] = aes_encrypt(text, nonce)
    result['enc_text'] = aes_encrypt(result['enc_text'], sec_key, byte=True)
    print(sec_key, pubkey, modulus)
    result['enc_sec_key'] = rsa_encrypt(sec_key, pubkey, modulus)
    return result


# 封印结束

def get_form_data(csrf, signtype):
    unencrypted = {'csrf_token': csrf, 'type': signtype}
    plaintext = json.dumps(unencrypted).replace(' ', '')
    encrypted = aes_rsa_encrypt(plaintext, PUBKEY, MODULES, NONCE)
    return encrypted


def nesign(music_u, csrf, log=True, log_filename=None, display_name='anonymous'):
    _config_log(log, log_filename)

    cookies = {'MUSIC_U': music_u, '__csrf': csrf}
    headers = {'Referer': 'http://music.163.com/'}

    url = 'http://music.163.com/weapi/point/dailyTask?csrf_token={}'.format(csrf)

    # web 和 pc 客户端
    encrypted = get_form_data(csrf, TYPE_WEBPC)

    data = {
        'params': encrypted['enc_text'],
        'encSecKey': encrypted['enc_sec_key']
    }

    response = requests.post(url, cookies=cookies,
                             headers=headers, data=data)

    log_from_code(response.json(), 'web & pc', display_name)

    # web 和 pc 客户端结束

    # android
    encrypted = get_form_data(csrf, TYPE_ANDROID)

    data = {
        'params': encrypted['enc_text'],
        'encSecKey': encrypted['enc_sec_key']
    }

    response = requests.post(url, cookies=cookies,
                             headers=headers, data=data)

    log_from_code(response.json(), 'android', display_name)

    # android 结束
