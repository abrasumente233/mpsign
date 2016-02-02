
# MPSIGN


## 安装


```bash
$ sudo pip install mpsign
```

## API


MPSIGN 的所有核心功能均在 `mpsign.core` 模块下。以下是一些示例。

* 获取喜欢的吧

	```python
	>>> from mpsign.core import User
	>>> user = User('YOUR BDUSS')  # 此处的 BDUSS 可从 baidu.com 域下的 Cookies 找到
	>>> (user.bars[0].kw, user.bars[0].fid)
	('chrome', '1074587')
	```
* 签到

	```python
	>>> from mpsign.core import User, Bar
	>>> user = User('YOUR BDUSS')
	>>> bar = Bar(kw='python')
	>>> bar.sign(user)
	SignResult(message='ok', exp=8, bar=<mpsign.core.Bar object at 0x7f7648d35e48>, code=0, total_sign='41', rank='3249', cont_sign='4')
	```
	注: `user.sign(bar)` 与 `bar.sign(user)` 等价。
	```python
	>>> [user.sign(bar) for bar in user.bars]
	...a list of SignResult
	```
	注: 使用 `user.bars` 获取一群贴吧的 fid 比让 `core.Bar` 单独获取快非常多。一个贴吧的 fid 通常是不变的，所以第一次最好把 fid 存起来，日后使用 `Bar('name', 'fid')` 获取 Bar 实例签到会省不少流量。MPSIGN 自带的命令行工具已经这么做了。

* 检验 BDUSS 是否合法

	```python
	>>> from mpsign.core import User
	>>> User('AN INVALID BDUSS').verify()
	False
	```
* TBS

	```python
	>>> from mpsign.core import User
	>>> user = User('YOUR BDUSS')
	>>> user.tbs
	...
	```
* fid

	```python
	>>> from mpsign.core import Bar
	>>> Bar('chrome').fid
	'1074587'
	```

## 命令行工具


MPSIGN 提供一个现成的命令行工具，自带一个轻量的用户管理系统。所有的用户信息都会被储存在 `~/.mpsign` 之下。你可以配合 Linux Crontab 与此工具快速设置一个全自动的签到系统。

### 基本用法

```bash
$ mpsign --help
Usage:
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
  --user                Your convenient use ID.
  --delay=<second>      Delay for every single bar [default: 3].
```
