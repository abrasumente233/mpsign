MPSIGN |Build Status|
=====================

用 Python 实现的贴吧签到助手

需求
----

| MPSIGN 在 Python 3.5 的环境下开发，对 Python 3.x
  其他版本的运行状况未知。1.5.2 的工作就是兼容测试。
| 暂时没有兼容 2.x 的计划。

安装
----

.. code:: bash

    $ sudo pip install mpsign

API
---

MPSIGN 的所有核心功能均在 ``mpsign.core`` 模块下。以下是一些示例。

-  登录

   -  通过账号密码

      .. code:: python

          from mpsign.core import User, Captcha, LoginFailure

          user_gen = User.login('USERNAME', 'PASSWORD')  # 登陆的接口是用 generator 实现的

          try:
              result = user_gen.send(None)  # 启动 generator
              if isinstance(result, Captcha):  # 是否需要验证码
                  result.as_file('captcha.gif')  # 验证码图片保存到 captcha.gif
                  your_input = input('captcha: ')  # 获取用户输入
                  user = user_gen.send(your_input)  # 发送验证码给 generator
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

   -  通过 BDUSS

      .. code:: python

          >>> from mpsign.core import User
          >>> user = User('YOUR BDUSS')  # 此处的 BDUSS 可从 baidu.com 域下的 Cookies 找到

-  获取喜欢的吧

   .. code:: python

       >>> user.bars[0].kw
       'chrome'

-  签到

   .. code:: python

       >>> from mpsign.core import User, Bar
       >>> user = ...get User instance
       >>> bar = Bar(kw='python')
       >>> bar.sign(user)
       SignResult(message='ok', exp=8, bar=<mpsign.core.Bar object at 0x7f7648d35e48>, code=0, total_sign='41', rank='3249', cont_sign='4')

   注: ``user.sign(bar)`` 与 ``bar.sign(user)`` 等价。

   .. code:: python

       >>> [user.sign(bar) for bar in user.bars]
       ...a list of SignResult

   注: 签到需要四样东西：BDUSS，tbs，吧名和\ **对应贴吧的 fid**.
   ``mpsign.core.Bar`` 有两种实例化的方法: Bar(kw, fid) 或 Bar(kw).
   如果使用后者，访问 ``bar.fid`` 的时候会去单独获取该贴吧的
   fid，贴吧多了之后流量消耗相当可观. 所以除非真的不知道 fid，
   否则请使用第一种构造方法。有一种批量获取用户喜欢的吧 fid 的方法是使用
   ``user.bars``\ ，返回的是一个由前者构造成的 Bar 的 tuple.

-  检验 BDUSS 是否合法

   .. code:: python

       >>> from mpsign.core import User
       >>> User('AN INVALID BDUSS').validation
       False

-  TBS

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

MPSIGN
提供一个现成的命令行工具，自带一个轻量的用户管理系统。所有的用户信息都会被储存在
``~/.mpsign/.mpsigndb`` 之下。你可以配合 Linux Crontab
与此工具快速设置一个全自动的签到系统。

基本用法
~~~~~~~~

.. code:: bash

    $ mpsign --help
    Usage:
      mpsign login <username>
      mpsign (new|set) <user> <bduss> [--without-verifying]
      mpsign (delete|update) [<user>]
      mpsign sign [<user>] [--delay=<second>]
      mpsign info [<user>]
      mpsign -h | --help
      mpsign -v | --version

    Options:
      -h --help             Show this screen.
      -v --version          Show version.
      --without-verifying   Do not verify BDUSS.
      --bduss               Your Baidu BDUSS.
      --username            Your Baidu ID
      --user                Your mpsign ID.
      --delay=<second>      Delay for every single bar [default: 3].

.. |Build Status| image:: https://travis-ci.org/abrasumente233/mpsign.svg?branch=master
   :target: https://travis-ci.org/abrasumente233/mpsign
