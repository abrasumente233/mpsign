import unittest

from mpsign import crypto

RSA_PUB_KEY = '010001'
RSA_MODULUS = 'B3C61EBBA4659C4CE3639287EE871F1F48F7930EA977991C7AFE3CC442FEA49643212' \
              'E7D570C853F368065CC57A2014666DA8AE7D493FD47D171C0D894EEE3ED7F99F6798B7F' \
              'FD7B5873227038AD23E3197631A8CB642213B9F27D4901AB0D92BFA27542AE89085539' \
              '6ED92775255C977F5C302F1E7ED4B1E369C12CB6B1822F'


class TestCrypto(unittest.TestCase):

    def test_dec2hex(self):
        r = crypto.dec2hex(255)
        self.assertEqual(r, 'ff')

    def test_rsa_encryption(self):
        # TODO: test string which its length is larger than 126 (a chunk size in Baidu's case)
        cases = (
            ('tetetetetetetetetetetetetetetetete', '617758987d012eb47b4b61498472e2d3ae96f891512bf130c6b42d724ec81b21f6e9cbbbc17cf2f260b5c76feaebc99615f5df5c5a88ddf4b859c0dbf1daba476af4f55f4502a0ce84e6adcf397909a9933f093be08381ac2ceb4b1e4d48f2e5eb87fdac2f259bc3b85cd674a0c9ef2e8b3debba1043c7af8ab378db0123463e'),
            ('testdata', '1d49d809c48d14444cd0bcd739f50a86fee8df6a6c3c73ffd57c55c0124c89816b2e3d7a8d5ffd1d5d1ba5fac092590ad20be7b3a3c22284074027f4b99af04fc98ffebe5a82ae161675fd7bfbe6f54c3d3425465d62c9cff013ea861f5a6c222fd735e92c0d4acda0b0a103a83f45b1a7d2bfd2458501b89ca4c08d61715af3')
        )
        for string, result in cases:
            self.assertEqual(crypto.rsa_encrypt(string, RSA_MODULUS, RSA_PUB_KEY), result)

if __name__ == '__main__':
    unittest.main()