# -*- coding: utf-8 -*-

"""mpsign

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

"""
import time
import pkgutil
from os import path

from docopt import docopt
from tinydb import TinyDB, where

from mpsign.core import User, Bar

__version__ = pkgutil.get_data(__package__, 'VERSION').decode('ascii').strip()

db = TinyDB(path.expanduser('~') + path.sep + '.mpsign')
user_table = db.table('users', cache_size=10)
bar_table = db.table('bars')


class UserNotFound(Exception):
    pass


class InvalidBDUSSException(Exception):
    pass


def check_user(func):
    def wrapper(*args, **kwargs):
        field_existence = user_table.search(where('name').exists())
        if not field_existence:
            raise UserNotFound

        user_existence = user_table.search(where('name') == kwargs['name'])
        if len(user_existence) == 1:
            return func(*args, **kwargs)
        else:
            raise UserNotFound

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
    print('done, {} users are deleted.'.format(len(users_info)))


@check_user
def delete(*, name):
    user_info = user_table.get(where('name') == name)
    user_table.remove(where('name') == name)
    bar_table.remove(where('user') == user_info.eid)
    print('finish deleting {}'.format(name))


def update_all():
    count = 0
    for user_info in user_table.all():
        count += update(name=user_info['name'])
    print('done, totally {} bars was found!'.format(count))


@check_user
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


@check_user
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


@check_user
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

    print('Name\tEXP\tis bduss valid')

    for user_info in users_info:
        print('{name}\t{exp}\t{valid}'.format(name=user_info['name'], exp=user_info['exp'],
                                              valid=User(user_info['bduss']).verify()))


def new(*, name, bduss):
    user_table.insert({'name': name, 'bduss': bduss, 'exp': 0})


@check_user
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

    except UserNotFound:
        print('User not found.')

    except InvalidBDUSSException:
        print('BDUSS not valid')

    except Exception as e:
        print(e)

    db.close()

if __name__ == '__main__':
    cmd()
