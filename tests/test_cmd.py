import unittest

from docopt import docopt
import json

from mpsign import cmd, __version__


def get_user(name):
    with open(cmd.db_path, 'r') as f:
        json_data = json.loads(f.read())

        for eid, v in json_data['users'].items():
            if v['name'] == name:
                return v

        return None


def remove_user():
    try:
        cmd.delete(cmd.DatabaseUser('mu'))
    except (OSError, cmd.UserNotFound):
        pass


def run_main(arguments):
    cmd.main(docopt(cmd.__doc__, version=__version__, argv=arguments))


# todo: 暂时只有 bad input... 真的BDUSS要等志愿者 QWQ
class TestNewAndSetCommand(unittest.TestCase):

    def test_new_invalid_bduss(self):
        remove_user()
        args = ['new', 'mu', 'invalid_bduss']
        self.assertRaises(cmd.InvalidBDUSSException, run_main, args)

    def test_set_invalid_bduss(self):
        remove_user()
        args_new = ('new', 'mu', 'invalid_bduss', '--without-verifying', '--dont-update')
        args_set = ('set', 'mu', 'another_invalid_bduss', '--dont-update')
        args_set_w = ('set', 'mu', 'another_invalid_bduss', '--without-verifying', '--dont-update')

        run_main(args_new)
        self.assertRaises(cmd.InvalidBDUSSException, run_main, args_set)

        run_main(args_set_w)

    def test_database_created_and_deleted(self):
        remove_user()
        self.assertIs(get_user('mu'), None)
        args_new = ('new', 'mu', 'invalid_bduss', '--without-verifying', '--dont-update')

        run_main(args_new)

        data = get_user('mu')
        self.assertIsInstance(data, dict)
        self.assertEqual(data['name'], 'mu')
        self.assertEqual(data['bduss'], 'invalid_bduss')
        self.assertEqual(data['exp'], 0)

        args_delete = ('delete', 'mu')
        run_main(args_delete)
        self.assertIs(get_user('mu'), None)

    def test_invalid_bduss_updating(self):
        remove_user()
        args_new = ('new', 'mu', 'invalid_bduss', '--without-verifying', '--dont-update')
        args_update = ('update', 'mu')
        run_main(args_new)
        self.assertRaises(cmd.InvalidBDUSSException, run_main, args_update)

    def tearDown(self):
        remove_user()

if __name__ == '__main__':
    unittest.main()