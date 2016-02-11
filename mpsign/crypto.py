# -*- coding: utf-8 -*-

from Crypto.PublicKey.RSA import RSAImplementation

"""
由移植 RSA.js 到 Python3.
原 JavaScript 实现: https://github.com/abrasumente233/pajhome/blob/c6f893af589f6ed122bf5b308faafe650827fd65/crypt/md5/rsa/RSA.js
想要阅读可以直接找 JavaScript 原实现阅读，不建议阅读本移植版的.
RSA.js 依赖的 BigInt.js 可以在 RSA.js 的同级目录下找到.
"""


def dec2hex(n):
    return hex(n)[2:]  # remove prefix 0x


def encrypt_string(key, string):
    char_list = [ord(char) for char in string]
    n_in_hex = dec2hex(key.n)

    # TODO: 这条语句的意思待解
    # TODO: else 后面的表达式是不是有效的也待检...
    chunk_size = int((len(n_in_hex) / 2)) - 2 if len(n_in_hex) % 4 is 0 else \
        int(len(n_in_hex) / 2) + 1 - 2

    # 让 char_list 的长度变成 chunk_size 的倍数
    while len(char_list) % chunk_size is not 0:
        char_list.append(0)

    char_list_length = len(char_list)
    result = []  # 16进制表示的结果, 稍后再拼接成字符串

    i = j = 0
    while i < char_list_length:
        while j < (i + chunk_size):
            current_number = char_list[j] + (char_list[j + 1] << 8)
            result.insert(0, dec2hex(current_number))
            j += 2

        # 原 RSA.js 实现中每个 chunk 后面都有一个空格
        # 即在这里 result += ' '
        # 但为了简化设计，这里没加，而且密码那点长度也不会破出一个 chunk (似乎是126)
        i += chunk_size

    return int(''.join(result), 16)  # 把16进制表示的 result 转换成 int


def rsa_encrypt(text, n, e):
    impl = RSAImplementation()
    n = int(n, 16) if isinstance(n, str) else n
    e = int(e, 16) if isinstance(e, str) else e
    private_key = impl.construct((n, e))

    # 这里的2其实是随便填的，pycrypto 会忽略掉。他这样做是为了兼容性考虑
    # 还有[0]是因为 encrypt() 返回的是一个 tuple，第一个元素为结果，第二个始终为 None, 具体看 pycrypto 的文档
    result = private_key.encrypt(encrypt_string(private_key, text), 2)[0]

    return dec2hex(result)
