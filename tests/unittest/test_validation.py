import unittest
from application.modules.validation import Validation


class ValidationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        assert(Validation.check_internet_connection())

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_is_valid_ipv4(self):
        valid_ip_list = ['10.0.0.1', '10.0.0.254', '172.30.0.1', '172.30.0.254', '192.168.0.1', '192.168.0.254']
        invalid_ip_list = ['a', 'a.b.c.d', '0.1.1.1', '1.1.1', '172.30.0.256', '172.30.0.-1']
        for ip in valid_ip_list:
            self.assertTrue(Validation.is_valid_ipv4(ip))

        for ip in invalid_ip_list:
            self.assertFalse(Validation.is_valid_ipv4(ip))


    def test_is_valid_username(self):
        invalid_chars = ['~', '`', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '+', '=',
                         '{', '[', '}', ']', '|', '\\', ':', ';', '"', '\'', '<', ',', '>', '?', '/']

        valid_chars = ['.', '-', '_']

        valid_username_base = 'test_user'

        for char in invalid_chars:
            invalid_username1 = valid_username_base + char
            invalid_username2 = char + valid_username_base
            self.assertFalse(Validation.is_valid_username(invalid_username1))
            self.assertFalse(Validation.is_valid_username(invalid_username2))

        for char in valid_chars:
            valid_username = valid_username_base + char
            invalid_username = char + valid_username_base
            self.assertTrue(Validation.is_valid_username(valid_username))
            self.assertFalse(Validation.is_valid_username(invalid_username))


    def test_is_valid_password(self):
        valid_password = 'password~`!@#$%^&*()_-+={[}]|\\:;\"\'<,>.?/'

        self.assertTrue(Validation.is_valid_password(None))
        self.assertTrue(Validation.is_valid_password(valid_password))
        self.assertFalse(Validation.is_valid_password(" "))
        self.assertFalse(Validation.is_valid_password(valid_password + " "))

    def test_is_aws(self):
        aws_ip = '52.52.224.126'
        non_aws_ip = '172.30.0.1'

        self.assertTrue(Validation.is_aws(aws_ip))
        self.assertFalse(Validation.is_aws(non_aws_ip))


if __name__ == '__main__':
    unittest.main()