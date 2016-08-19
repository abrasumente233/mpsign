MPSIGN |Build Status|
=====================

用 Python 实现的贴吧签到助手

安装
----

.. code:: bash

    $ sudo pip install mpsign

API
---

MPSIGN 的所有核心功能均在 ``mpsign.core``
模块下(很快就不在了)。以下是一些示例。

-  登录

   -  通过 BDUSS

      .. code:: python

          >>> from mpsign.core import User
          >>> user = User('YOUR BDUSS')  # 此处的 BDUSS 可从 *.baidu.com 域下的 Cookies 找到

   -  通过账号密码 (复活！！)

      .. code:: python

          from mpsign.core import User, Captcha, LoginFailure

          get_my_user = User.login('USERNAME', 'PASSWORD')  # 登陆的接口是用 generator 实现的

          try:
              result = get_my_user.send(None)  # 启动 generator
              if isinstance(result, Captcha):  # 是否需要验证码
                  result.as_file('captcha.gif')  # 验证码图片保存到 captcha.gif
                  user = get_my_user.send(input('captcha: '))  # 发送验证码给 generator
              else:
                  user = result  # 不需要验证码的话，result 即是新建的 User 实例
          except LoginFailure as ex:
              raise ex

      注: ``LoginFailure`` 还有如下子异常: ``InvalidPassword``,
      ``InvalidCaptcha``, ``InvalidUsername``, ``DangerousEnvironment``

      注: ``user = user_gen.send(your_input)`` 也等价与以下代码:

      .. code:: python

          result.fill(your_input)  # result 是一个 Captcha 对象
          user_gen.send(None)

-  获取喜欢的吧

   .. code:: python

       >>> user.bars[0].kw
       'chrome'

-  签到

   .. code:: python

       >>> from mpsign.core import User, Bar
       >>> user = ...获取 User 实例
       >>> bar = Bar(kw='python')
       >>> bar.sign(user)
       SignResult(message='ok', exp=8, bar=<Bar: python>, code=0, total_sign='41', rank='3249', cont_sign='4')

   注: ``user.sign(bar)`` 与 ``bar.sign(user)`` 等价。

   .. code:: python

       >>> [user.sign(bar) for bar in user.bars]
       ...a list of SignResult

   注: 签到需要贴吧的 fid。最好不要用 Bar(kw) 这个构造方法，会单独获取
   fid。请权衡用 ``user.bars`` 批量获取和单独获取的利弊再用

-  BDUSS 吼不吼啊？

   .. code:: python

       >>> from mpsign.core import User
       >>> User('已过期或滚键盘出来的 BDUSS').validation
       False

-  tbs

   .. code:: python

       >>> user.tbs
       ...

-  fid

   .. code:: python

       >>> from mpsign.core import Bar
       >>> Bar('chrome').fid
       '1074587'

命令行工具
----------

MPSIGN 自带一个命令行工具！配合 Cron 食用效！果！更！佳！(〜￣△￣)〜

我不想看用法！
~~~~~~~~~~~~~~

.. code:: bash

    $ mpsign login 用户名
    ...按步骤走(･∀･)
    $ mpsign sign
    ...

用法
~~~~

.. code:: bash

    $ mpsign --help
    Usage:
      mpsign login <username> [--dont-update]
      mpsign (new|set) <user> <bduss> [--without-verifying] [--dont-update]
      mpsign (delete|update) [<user>]
      mpsign sign [<user>] [--delay=<second>]
      mpsign info [<user>]
      mpsign -h | --help
      mpsign -v | --version

    Options:
      -h --help             Show this screen.
      -v --version          Show version.
      --without-verifying   Do not verify BDUSS.
      --dont-update         Do not update your favorite bars after binding user
      --bduss               Your Baidu BDUSS.
      --username            Your Baidu ID
      --user                Your mpsign ID.
      --delay=<second>      Delay for every single bar [default: 3].

.. |Build Status| image:: https://travis-ci.org/abrasumente233/mpsign.svg?branch=master
   :target: https://travis-ci.org/abrasumente233/mpsign
