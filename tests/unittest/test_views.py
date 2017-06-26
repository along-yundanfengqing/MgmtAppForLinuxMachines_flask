import os
import uuid
import unittest
from application import app
from application.models import MachineData

BASE_DIR = os.getcwd()
LOGIN_FILE_NAME = "test_login.txt"
LOGIN_FILE_PATH = os.path.join(BASE_DIR, "tests/unittest", LOGIN_FILE_NAME)

test_username = "test_user"
test_password = "test_password"

class ViewTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        assert(app.testing)

    @classmethod
    def tearDownClass(cls):
        MachineData.drop_collection()
        with open(LOGIN_FILE_PATH, 'w') as f:
            f.write("")

    def setUp(self):
        self.client = app.test_client()
        self.create_user(test_username, test_password, test_password)
        self.login(test_username, test_password)

    def tearDown(self):
        self.logout()

    def test_signup(self):
        username = test_username + str(uuid.uuid1())
        result = self.create_user(username, test_password, test_password)
        self.assertTrue("Created a user account" in str(result.data))

    def test_login_logout(self):
        self.logout()
        username = test_username + str(uuid.uuid1())
        self.create_user(username, test_password, test_password)
        result = self.login(username, test_password)
        self.assertTrue("Logged in successfully" in str(result.data))

        result = self.logout()
        self.assertTrue("Logged out from a user" in str(result.data))

    def test_login_invalid_user(self):
        self.logout()
        result = self.login('non_exist_user', 'non_exist_password')
        self.assertTrue("Username or password is not correct" in str(result.data))

    def test_register_machine(self):
        result = self.register_machines("1.1.1.1", "test", "test")
        self.assertTrue("Added the new machine" in str(result.data))

    def test_register_machine_no_pass(self):
        result = self.register_machines("2.2.2.2", "test")
        self.assertTrue("Added the new machine" in str(result.data))

    def test_home_page(self):
        result = self.client.get('/portal/home')
        self.assertEqual(result.status_code, 200)

    def test_delete_page(self):
        result = self.client.get('/portal/delete')
        self.assertEqual(result.status_code, 200)

    def test_register_page(self):
        result = self.client.get('/portal/register')
        self.assertEqual(result.status_code, 200)


    def login(self, username, password):
        return self.client.post('/portal/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/portal/logout', follow_redirects=True)

    def create_user(self, username, password, confirm_password):
        return self.client.post('/portal/signup', data=dict(
            username=username,
            password=password,
            confirm=confirm_password
        ), follow_redirects=True)

    def register_machines(self, ip_address, username, password=""):
        return self.client.post('/portal/register', data=dict(
            ip_address=ip_address,
            username=username,
            password=password
        ), follow_redirects=True)


if __name__ == '__main__':
    unittest.main()