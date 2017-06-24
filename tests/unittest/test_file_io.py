import logging
import os
import unittest
from application.modules.file_io import FileIO
from application.modules.validation import Validation

BASE_DIR = os.getcwd()
LOGIN_FILE_NAME = "test_login.txt"
LOGIN_FILE_PATH = os.path.join(BASE_DIR, "tests/unittest", LOGIN_FILE_NAME)

test_data='''###############
172.30.0.1,user1,password1
172.30.0.2,user2,password2
172.30.0.3,user3
# 172.30.0.4,user4
1.1.1,user5
'''

class FileIOTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        assert(Validation.check_internet_connection())

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        logging.disable(logging.CRITICAL)
        with open(LOGIN_FILE_PATH, 'w') as f:
            f.write(test_data)

    def tearDown(self):
        with open(LOGIN_FILE_PATH, 'w') as f:
            f.write("")

    def test_get_login_list(self):
        test_login_data = [(u'172.30.0.1', u'user1', u'password1'),
                           (u'172.30.0.2', u'user2', u'password2'),
                           (u'172.30.0.3', u'user3', None)]

        self.assertEqual(FileIO.get_login_list(), test_login_data)


    def test_get_username(self):
        self.assertEquals(FileIO.get_username('172.30.0.1'), 'user1')


    def test_exists_in_file(self):
        self.assertTrue(FileIO.exists_in_file('172.30.0.1'))
        self.assertFalse(FileIO.exists_in_file('172.30.0.11'))

    def test_add_vm_to_file(self):
        FileIO.add_vm_to_file("10.0.0.1", "user10", "password10")
        self.assertTrue(('10.0.0.1', 'user10', 'password10') in FileIO.get_login_list())

    def test_del_vm_from_file(self):
        del_ip_list = ['172.30.0.2', '172.30.0.3']
        FileIO.del_vm_from_file(del_ip_list)
        self.assertFalse(FileIO.exists_in_file('172.30.0.2'))
        self.assertFalse(FileIO.exists_in_file('172.30.0.3'))



if __name__ == '__main__':
    unittest.main()