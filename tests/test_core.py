import unittest
import os

from mpsign import core

captcha_path = os.path.join(os.path.dirname(__file__) + os.sep + 'captcha.gif')

if captcha_path == '\\captcha.gif':
    captcha_path = 'captcha.gif'


class TestCaptcha(unittest.TestCase):

    def test_release_properly(self):
        captcha = core.Captcha(open(captcha_path, 'rb'))
        captcha.as_file()
        self.assertTrue(os.path.exists(core.data_directory + os.sep + 'www' + os.sep + 'captcha.gif'))
        captcha.destroy()
        self.assertFalse(os.path.exists(core.data_directory + os.sep + 'www' + os.sep + 'captcha.gif'))
        self.assertTrue(captcha.get_image().closed)

    def test_custom_path_release_properly(self):
        captcha = core.Captcha(open(captcha_path, 'rb'))
        captcha.as_file('a.gif')
        self.assertTrue(os.path.exists('a.gif'))
        captcha.destroy()
        self.assertFalse(os.path.exists('a.gif'))
        self.assertTrue(captcha.get_image().closed)

    def test_fill(self):
        captcha = core.Captcha(open(captcha_path, 'rb'))
        captcha.fill('2szx')
        self.assertTrue(captcha.input, '2szx')
        captcha.destroy()


class TestCaptchaBadInput(unittest.TestCase):

    def test_not_str(self):
        captcha = core.Captcha(open(captcha_path, 'rb'))
        for case in (1, 2312, 239.2):
            self.assertRaises(TypeError, captcha.fill, (case,))
        captcha.destroy()


class TestBar(unittest.TestCase):

    def test_fid_pattern(self):
        bar = core.Bar('chrome')
        self.assertIsInstance(bar.fid, str)
        self.assertEqual(bar.fid, '1074587')

    def test_eq(self):
        bar1 = core.Bar('python')
        bar2 = core.Bar('chrome')
        bar3 = core.Bar('chrome')

        self.assertIsNot(bar2, bar3)
        self.assertEqual(bar2, bar3)
        self.assertNotEqual(bar1, bar2)


class TestBarBadInput(unittest.TestCase):

    def test_empty_bar_name(self):
        for blank in ('', ' '):
            with self.assertRaises(core.InvalidBar):
                core.Bar(blank)

    def test_bar_with_spaces(self):
        for case in ('s 9', 'a9923\n', '\r', 'ras\r', 'sd\r\n', ' abc\n '):
            with self.assertRaises(core.InvalidBar):
                core.Bar(case)

    def test_type(self):
        for case in (1, 1.3):
            with self.assertRaises(TypeError):
                core.Bar(case)

        for case in (999.3,):
            with self.assertRaises(TypeError):
                core.Bar('chrome', case)


class TestUserBadInput(unittest.TestCase):

    def test_invalid_bduss_when_creation(self):
        for bad in ('', 23122312, 0xff, 23.3):
            with self.assertRaises(core.InvalidBDUSSException):
                core.User(bad)

    def test_invalid_bduss_getting_tbs(self):
        u = core.User('invalid_bduss')
        with self.assertRaises(core.InvalidBDUSSException):
            tbs = u.tbs

    def test_invalid_bduss_getting_bars(self):
        u = core.User('invalid_bduss')
        with self.assertRaises(core.InvalidBDUSSException):
            bars = u.bars

    def test_invalid_bduss_sign(self):
        bar = core.Bar('chrome', 1074587)
        u = core.User('invalid_bduss')
        with self.assertRaises(core.InvalidBDUSSException):
            u.sign(bar)

if __name__ == '__main__':
    unittest.main()