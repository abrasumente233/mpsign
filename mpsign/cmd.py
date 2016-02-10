# -*- coding: utf-8 -*-

"""mpsign

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

"""
import time
import threading
import http.server
import sys
from os import path
from getpass import getpass

from docopt import docopt
from tinydb import TinyDB, where

from .core import *
from . import __version__

db = TinyDB(data_directory + path.sep + '.mpsigndb')
user_table = db.table('users', cache_size=10)
bar_table = db.table('bars')


class UserDuplicated(Exception):
    pass


class UserNotFound(Exception):
    pass


class InvalidBDUSSException(Exception):
    pass


class CaptchaRequestHandler(http.server.SimpleHTTPRequestHandler):

    def log_message(self, format, *args):
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
        raise UserNotFound

    user_existence = user_table.search(where('name') == name)
    return True if len(user_existence) is 1 else False


def check_user_duplicated(name):
    if is_user_existed(name):
        raise UserDuplicated()


def is_user_existed_dec(func):
    def wrapper(*args, **kwargs):
        if is_user_existed(kwargs['name']):
            return func(*args, **kwargs)
        else:
            raise UserNotFound()

    return wrapper


def sure(message, default):
    decision = input(message).strip()
    if decision == '':
        return default
    else:
        return True if decision.lower() in ['y', 'yes', 'ok', 'ye'] \
            else False


def delete_all():
    is_continue = sure('Are you sure delete all accounts in the database? y/N:', False)
    if not is_continue:
        return
    users_info = user_table.all()
    for user_info in user_table.all():
        delete(name=user_info['name'])
    print('done, {0} users are deleted.'.format(len(users_info)))


@is_user_existed_dec
def delete(*, name):
    user_info = user_table.get(where('name') == name)
    user_table.remove(where('name') == name)
    bar_table.remove(where('user') == user_info.eid)
    print('finished deleting {0}'.format(name))


def update_all():
    count = 0
    for user_info in user_table.all():
        count += update(name=user_info['name'])
    print('done, totally {0} bars was found!'.format(count))


@is_user_existed_dec
def update(*, name):
    user_info = user_table.get(where('name') == name)

    bars = User(user_info['bduss']).bars
    bars_in_list = []

    # convert Bar objects to a list of dict that contains kw, fid, and user's eid
    for bar in bars:
        print('found {name}\'s bar {bar}'.format(bar=bar.kw, name=name))
        bars_in_list.append({'kw': bar.kw, 'fid': bar.fid, 'user': user_info.eid})

    print('{name} has {count} bars.'.format(name=name, count=len(bars)))
    bar_table.remove(where('user') == user_info.eid)  # clean old bars
    bar_table.insert_multiple(bars_in_list)
    return len(bars)


def sign_all(delay=None):
    names = [user_info['name'] for user_info in user_table.all()]
    exp = 0
    for name in names:
        exp += sign(name=name, delay=delay)

    print('done. totally {exp} exp was got.'.format(exp=exp))
    return exp


@is_user_existed_dec
def sign(*, name, delay=None):
    user_info = user_table.get(where('name') == name)
    bars_info = bar_table.search(where('user') == user_info.eid)
    exp = 0

    for bar_info in bars_info:
        exp += sign_bar(name=name, kw=bar_info['kw'], fid=bar_info['fid'])
        if delay is not None:
            time.sleep(delay)

    print('{name}\'s {count} bars was signed, exp +{exp}.'.format(name=name, count=len(bars_info),
                                                                  exp=exp))
    return exp


@is_user_existed_dec
def sign_bar(*, name, kw, fid):
    user_info = user_table.get(where('name') == name)
    user_obj = User(user_info['bduss'])
    r = Bar(kw, fid).sign(user_obj)
    if r.code == 0:
        print('{name} - {bar}: exp +{exp}'.format(name=name, bar=r.bar.kw, exp=r.exp))
    else:
        print('{name} - {bar}:{code}: {msg}'.format(name=name, bar=r.bar.kw, code=r.code,
                                                    msg=r.message))

    old_exp = user_table.get(where('name') == name)['exp']
    user_table.update({'exp': old_exp + r.exp}, where('name') == name)
    return r.exp


def info(*, name=None):
    if name is None:
        users_info = user_table.all()
    else:
        users_info = [user_table.get(where('name') == name)]

    if len(users_info) == 0:
        print('No user yet.')
        return

    if users_info[0] is None:
        raise UserNotFound

    row_format = '{:>15}{:>15}{:>20}'

    print(row_format.format('Name', 'EXP', 'is BDUSS valid'))

    for user_info in users_info:
        print(row_format.format(user_info['name'],
                                user_info['exp'],
                                str(User(user_info['bduss']).verify())))


def new(*, name, bduss):
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


def login(username, password):
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

                    user_input = selections[int(choice)-1][1](result).strip()  # pass the Captcha object

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
                    new(name=user_id, bduss=user.bduss)
                    break
                except UserDuplicated:
                    print('duplicated username {0}, please pick another one.'.format(user_id))

            print('Fetching your favorite bars...')
            update(name=user_id)
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


@is_user_existed_dec
def modify(*, name, bduss):
    user_table.update({'bduss': bduss}, where('name') == name)


def cmd():
    arguments = docopt(__doc__, version=__version__)
    if arguments['--delay'] is None:
        arguments['--delay'] = 3

    try:

        if arguments['new']:
            if not arguments['--without-verifying']:
                if not User(arguments['<bduss>']).verify():
                    raise InvalidBDUSSException
            new(name=arguments['<user>'], bduss=arguments['<bduss>'])
            update(name=arguments['<user>'])
        elif arguments['login']:
            password = getpass()
            login(arguments['<username>'], password)
        elif arguments['set']:
            if not arguments['--without-verifying']:
                if not User(arguments['<bduss>']).verify():
                    raise InvalidBDUSSException
            modify(name=arguments['<user>'], bduss=arguments['<bduss>'])
            print('ok')
        elif arguments['delete']:
            if arguments['<user>'] is None:
                delete_all()
            else:
                delete(name=arguments['<user>'])
        elif arguments['update']:
            if arguments['<user>'] is None:
                update_all()
            else:
                update(name=arguments['<user>'])
        elif arguments['sign']:
            if arguments['<user>'] is None:
                sign_all(delay=float(arguments['--delay']))
            else:
                sign(name=arguments['<user>'], delay=float(arguments['--delay']))

        elif arguments['info']:
            info(name=arguments['<user>'])
    except ImportError as e:
        # lxml or html5lib not found
        print(e.msg)
        print('Please try again by using `mpsign update [user]`')
    except UserNotFound:
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
