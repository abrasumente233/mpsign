# -*- coding: utf-8 -*-

"""mpsign

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

"""
import http.server
import sys
import threading
from getpass import getpass
from os import path

from docopt import docopt
from tinydb import TinyDB, where

from mpsign import __version__
from mpsign.core import *

db_path = data_directory + path.sep + '.mpsigndb'
db = TinyDB(db_path)
user_table = db.table('users', cache_size=10)
bar_table = db.table('bars')


class UserDuplicated(Exception):
    pass


class UserNotFound(Exception):
    pass


class DatabaseUser:
    def __init__(self, name):
        if not is_user_existed(name):
            raise UserNotFound()
        user_row = user_table.get(where('name') == name)
        self.eid = user_row.eid
        self.name = user_row['name']
        self.exp = user_row['exp']
        self.obj = User(user_row['bduss'])


class CaptchaRequestHandler(http.server.SimpleHTTPRequestHandler):

    def log_message(self, log_format, *args):
        pass

    def do_GET(self):
        """Serve a GET request."""
        captcha_file = open('{d}{sep}www{sep}captcha.gif'.format(d=data_directory, sep=path.sep),
                                 'rb')
        self.send_response(200)
        self.send_header("Content-type", 'image/gif')
        fs = os.fstat(captcha_file.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        self.copyfile(captcha_file, self.wfile)
        captcha_file.close()


def is_user_existed(name):
    field_existence = user_table.search(where('name').exists())
    if not field_existence:
        return False

    user_existence = user_table.search(where('name') == name)
    return True if len(user_existence) is 1 else False


def check_user_duplicated(name):
    if is_user_existed(name):
        raise UserDuplicated()


def make_sure(message, default):
    y = 'Y' if default else 'y'
    n = 'N' if not default else 'n'
    message = '{msg} {y}/{n}: '.format(msg=message, y=y, n=n)
    while True:

        decision = input(message).strip()
        if decision == '':
            return default
        elif decision.lower() in ['y', 'yes', 'ok', 'yea']:
            return True
        elif decision.lower() in ['n', 'no', 'nope']:
            return False


def delete_all():
    is_continue = make_sure('Are you sure delete all accounts in the database?', False)
    if not is_continue:
        return
    user_rows = user_table.all()
    for user_row in user_rows:
        delete(user=DatabaseUser(user_row['name']))
    print('done, {0} users are deleted.'.format(len(user_rows)))


def delete(user):
    user_table.remove(where('name') == user.name)
    bar_table.remove(where('user') == user.eid)
    print('finished deleting {0}'.format(user.name))


def update_all():
    count = 0
    for user_row in user_table.all():
        count += update(DatabaseUser(user_row['name']))
    print('done, totally {0} bars was found!'.format(count))


def update(user):
    bars = User(user.obj.bduss).bars
    bars_as_list = []

    # 把 Bar 对象转换成一个含有多个 {kw: str, fid: str, eid: int} dict 的 list
    for bar in bars:
        print('found {name}\'s bar {bar}'.format(bar=bar.kw, name=user.name))
        bars_as_list.append({'kw': bar.kw, 'fid': bar.fid, 'user': user.eid})

    print('{name} has {count} bars.'.format(name=user.name, count=len(bars)))
    bar_table.remove(where('user') == user.eid)  # 删除以前的贴吧
    bar_table.insert_multiple(bars_as_list)
    return len(bars)


def sign_all(delay=None):
    user_instances = [DatabaseUser(user_row['name']) for user_row in user_table.all()]
    exp = 0
    for instance in user_instances:
        exp += sign(instance, delay=delay)

    print('done. totally {exp} exp was got.'.format(exp=exp))
    return exp


def sign(user, delay=None):
    bar_rows = bar_table.search(where('user') == user.eid)
    exp = 0

    for bar_row in bar_rows:
        exp += sign_bar(user, Bar(bar_row['kw'], bar_row['fid']))
        if delay is not None:
            time.sleep(delay)

    print('{name}\'s {count} bars was signed, exp +{exp}.'.format(name=user.name, count=len(bar_rows),
                                                                  exp=exp))
    return exp


def sign_bar(user, bar):
    r = bar.sign(user.obj)
    if r.code == 0:
        print('{name} - {bar}: exp +{exp}'.format(name=user.name, bar=r.bar.kw, exp=r.exp))
    else:
        print('{name} - {bar}:{code}: {msg}'.format(name=user.name, bar=r.bar.kw, code=r.code,
                                                    msg=r.message))

    past_exp = user_table.get(where('name') == user.name)['exp']
    user_table.update({'exp': past_exp + r.exp}, where('name') == user.name)
    return r.exp


def info(name=None):
    if name is None:
        user_rows = user_table.all()
    else:
        user_rows = [user_table.get(where('name') == name)]

    if len(user_rows) == 0:
        print('No user yet.')
        return

    if user_rows[0] is None:
        raise UserNotFound

    row_format = '{:>15}{:>15}{:>20}'

    print(row_format.format('Name', 'EXP', 'is BDUSS valid'))

    for user_row in user_rows:
        print(row_format.format(user_row['name'],
                                user_row['exp'],
                                str(User(user_row['bduss']).validation)))


def new(name, bduss):
    check_user_duplicated(name)
    user_table.insert({'name': name, 'bduss': bduss, 'exp': 0})


def get_captcha():
    print('Enter the captcha you see. (left the input empty to change the captcha)')
    return input('Captcha: ')


def caca(captcha):
    print('Launching cacaview, press key q to exit caca.')
    captcha.as_file()
    caca_r = os.system('cacaview {}'.format(captcha.path))

    if caca_r == 32512:
        # cacaview not found
        print('Seems you have not installed caca yet.')
        print('On Ubuntu, you could use \'sudo apt-get install caca-utils\'')
        sys.exit(0)
    else:
        return get_captcha()


def xdgopen(captcha):
    print('Launching your desktop image viewer.')
    captcha.as_file()
    xdg_r = os.system('xdg-open {}'.format(captcha.path))

    if xdg_r == 32512:
        # not found
        print('Seems you have not installed a desktop image viewer yet.')
        print('Try caca or http instead.')
        sys.exit(0)
    else:
        return get_captcha()


class HTTPThread(threading.Thread):
    def __init__(self, port, captcha):
        super().__init__()
        self.captcha = captcha
        self.port = port
        self.httpd = None

    def run(self):
        print('Running http server at 127.0.0.1:{0}'.format(self.port))
        self.httpd = http.server.HTTPServer(('', self.port), CaptchaRequestHandler)
        self.httpd.serve_forever()


def via_http(captcha):
    try:
        os.mkdir('{d}{sep}www'.format(d=data_directory, sep=path.sep))
    except Exception:
        pass

    captcha.as_file('{d}{sep}www{sep}captcha.gif'.format(d=data_directory, sep=path.sep))

    t = HTTPThread(8823, captcha)
    t.start()

    user_input = get_captcha()

    print('Shutting down the http server, please wait...')
    t.httpd.server_close()
    t.httpd.shutdown()
    print('Finished shutting down the httpd.')
    return user_input


def login(username, password, need_update=True):
    while True:
        user_gen = User.login(username, password)

        try:
            result = user_gen.send(None)
            if isinstance(result, Captcha):

                selections = (('caca', caca, 'a command line image viewer'),
                              ('xdg-open', xdgopen, 'view it on your Linux desktop'),
                              ('via http', via_http, 'serve the captcha image via http'))

                while True:
                    print('Captcha is needed, how do you want to view it?')

                    for i, sel in enumerate(selections):
                        print('  {no}) {name} -- {desc}'.format(no=i+1, name=sel[0], desc=sel[2]))
                    choice = input('Your choice(1-{0}): '.format(len(selections)))

                    user_input = selections[int(choice)-1][1](result)  # pass the Captcha object

                    result.destroy()

                    if user_input == 'another' or user_input == '':
                        result = user_gen.send('another')
                        continue
                    else:
                        break

                user = user_gen.send(user_input)
            else:
                user = result

            print('Only a few things left to do...')
            while True:
                try:
                    user_id = input('Pick up a username(only saved in mpsign\'s local database) you like: ')
                    new(user_id, user.bduss)
                    break
                except UserDuplicated:
                    print('{0} is already EXISTED in the database!!!'.format(user_id))
                    override = make_sure('Do you hope to override it?', False)
                    if override:
                        modify(DatabaseUser(user_id), user.bduss)
                        break

            if need_update:
                print('Fetching your favorite bars...')
                update(DatabaseUser(user_id))
            print('It\'s all done!')
            break

        except InvalidPassword:
            print('You have entered the wrong password. Please try again.')
            password = getpass()
        except InvalidUsername:
            print('You have entered the wrong username. Please try again.')
            break
        except InvalidCaptcha:
            print('You have got the captcha wrong. Please try again')
            continue
        except LoginFailure as e:
            print('Unknown exception.\nerror code:{0}\nmessage: {1}'.format(e.code, e.message))
            break


def modify(user, bduss):
    user_table.update({'bduss': bduss}, where('name') == user.name)


def main(arguments):

    if arguments['--delay'] is None:
        arguments['--delay'] = 3

    if arguments['new']:
        if not arguments['--without-verifying']:
            if not User(arguments['<bduss>']).validation:
                raise InvalidBDUSSException
        new(arguments['<user>'], arguments['<bduss>'])
        if not arguments['--dont-update']:
            print('Fetching your favorite bars...')
            update(user=DatabaseUser(arguments['<user>']))
    elif arguments['login']:
        password = getpass()
        login(arguments['<username>'], password, not arguments['--dont-update'])
    elif arguments['set']:

        # 验证 BDUSS
        if not arguments['--without-verifying']:
            if not User(arguments['<bduss>']).validation:
                raise InvalidBDUSSException

        user = DatabaseUser(arguments['<user>'])
        modify(user, arguments['<bduss>'])

        # 更新贴吧
        if not arguments['--dont-update']:
            print('Fetching your favorite bars...')
            update(user)

        print('ok')
    elif arguments['delete']:
        if arguments['<user>'] is None:
            delete_all()
        else:
            delete(user=DatabaseUser(arguments['<user>']))
    elif arguments['update']:
        if arguments['<user>'] is None:
            update_all()
        else:
            update(user=DatabaseUser(arguments['<user>']))
    elif arguments['sign']:
        if arguments['<user>'] is None:
            sign_all(delay=float(arguments['--delay']))
        else:
            sign(user=DatabaseUser(arguments['<user>']), delay=float(arguments['--delay']))

    elif arguments['info']:
        info(arguments['<user>'])


def cmd():
    try:
        main(docopt(__doc__, version=__version__))
    except ImportError as e:
        # lxml or html5lib not found
        print(e.msg)
        print('Please try again by using `mpsign update [user]`')
    except UserNotFound as e:
        print('User not found.')
    except InvalidBDUSSException:
        print('BDUSS not valid')
    except KeyboardInterrupt:
        print('Operation cancelled by user.')
    except Exception as e:
        raise e

    db.close()

if __name__ == '__main__':
    cmd()
