import unittest
import sys
import os.path
import bcrypt
import pyotp
import json
from pymongo import Connection
from datetime import datetime, timedelta
from time import sleep
import requests


ttl=20
# Allow imports within the same package.
sys.path.append(
    os.path.dirname(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))))

from FlaskApp import app, User, generate_token

class TestFlaskAppHappyPath(unittest.TestCase):
    # Basic TestCase checking whether the site is up
    def test_site_is_up(self):
        self.test_app = app.test_client()
        response = self.test_app.get("/")
        self.assertEquals(response.status, "200 OK")

    # Tests whether a simple user registration without MFA.
    def test_register_successful_user_without_mfa(self):
        self.test_app = app.test_client()
        post_data = {}
        post_data['username'] = "testUser1"
        post_data['email'] = "testUser1@testuser.com"
        post_data['password'] = "supersecretpassword"
        post_data['confirm-password'] = "supersecretpassword"
        response = self.test_app.post('/sign-up', data=post_data)
        self.assertEquals(response.status, "302 FOUND")

    # Tests MFA regsitration.
    def test_register_successful_user_with_mfa(self):
        self.test_app = app.test_client()
        post_data = {}
        post_data['username'] = "testUser2"
        post_data['email'] = "testUser2@testuser.com"
        post_data['password'] = "supersecretpassword"
        post_data['confirm-password'] = "supersecretpassword"
        post_data['enable_mfa'] = True
        response = self.test_app.post('/sign-up', data=post_data)
        self.assertEquals(response.status, "302 FOUND")

    # Tests login on non MFA enabled users
    def test_login_successful_user_without_mfa(self):
        self.test_app = app.test_client()
        # Register
        post_data = {}
        post_data['username'] = "testUser3"
        post_data['email'] = "testUser3@testuser.com"
        post_data['password'] = "supersecretpassword"
        post_data['confirm-password'] = "supersecretpassword"
        post_data['enable_mfa'] = True
        response = self.test_app.post('/sign-up', data=post_data)
        self.assertEquals(response.status, "302 FOUND")

        #Login
        post_data = {}
        post_data['username'] = "testUser3"
        post_data['password'] = "supersecretpassword"
        response = self.test_app.post('/', data=post_data)
        self.assertEquals(response.status, "200 OK")

    # Tests login on MFA enabled users. The actual MFA code validation and QR-Code scanning part is stubbed out.
    def test_login_successful_user_with_mfa(self):
        self.test_app = app.test_client()
        # Register
        post_data = {}
        post_data['username'] = "testUser4"
        post_data['email'] = "testUser4@testuser.com"
        post_data['password'] = "supersecretpassword"
        post_data['confirm-password'] = "supersecretpassword"
        response = self.test_app.post('/sign-up', data=post_data)
        self.assertEquals(response.status, "302 FOUND")

        #Login
        post_data = {}
        post_data['username'] = "testUser4"
        post_data['password'] = "supersecretpassword"
        response = self.test_app.post('/', data=post_data)
        self.assertEquals(response.status, "200 OK")

# Handles corner cases in the application
class TestFlaskAppCornerCases(unittest.TestCase):
    # Test empty username registration. Expect 400
    def test_username_empty(self):
        self.test_app = app.test_client()
        post_data = {}
        post_data['username'] = ""
        post_data['email'] = "testUser5@testuser.com"
        post_data['password'] = "supersecretpassword"
        post_data['confirm-password'] = "supersecretpassword"
        response = self.test_app.post('/sign-up', data=post_data)
        self.assertEquals(response.status, "400 BAD REQUEST")

    # test username < 4 characters. Expect 400
    def test_username_less_than_4_chars(self):
        self.test_app = app.test_client()
        post_data = {}
        post_data['username'] = "123"
        post_data['email'] = "testUser6@testuser.com"
        post_data['password'] = "supersecretpassword"
        post_data['confirm-password'] = "supersecretpassword"
        response = self.test_app.post('/sign-up', data=post_data)
        self.assertEquals(response.status, "400 BAD REQUEST")

    # Tests empty password registration. Expect 400
    def test_password_empty(self):
        self.test_app = app.test_client()
        post_data = {}
        post_data['username'] = "testUser6"
        post_data['email'] = "testUser6@testuser.com"
        post_data['password'] = ""
        post_data['confirm-password'] = "supersecretpassword"
        response = self.test_app.post('/sign-up', data=post_data)
        self.assertEquals(response.status, "400 BAD REQUEST")

    # Tests password < 8 characters. Expect 400
    def test_password_less_than_8_chars(self):
        self.test_app = app.test_client()
        post_data = {}
        post_data['username'] = "testUser7"
        post_data['email'] = "testUser7@testuser.com"
        post_data['password'] = "supersecretpassword"
        post_data['confirm-password'] = "1234567"
        response = self.test_app.post('/sign-up', data=post_data)
        self.assertEquals(response.status, "400 BAD REQUEST")

    # Tests emtpu email registration. Expect 400
    def test_email_empty(self):
        self.test_app = app.test_client()
        post_data = {}
        post_data['username'] = "testUser8"
        post_data['email'] = ""
        post_data['password'] = "supersecretpassword"
        post_data['confirm-password'] = "12345678"
        response = self.test_app.post('/sign-up', data=post_data)
        self.assertEquals(response.status, "400 BAD REQUEST")

    # Tests invalid email format. Expect 400
    def test_email_invalid(self):
        self.test_app = app.test_client()
        post_data = {}
        post_data['username'] = "testUser9"
        post_data['email'] = "email_without_at_symbol"
        post_data['password'] = "supersecretpassword"
        post_data['confirm-password'] = "supersecretpassword"
        response = self.test_app.post('/sign-up', data=post_data)
        self.assertEquals(response.status, "400 BAD REQUEST")

    # Tests mismatched password and confirm password. Expect 400
    def test_password_mismatch(self):
        self.test_app = app.test_client()
        post_data = {}
        post_data['username'] = "testUser10"
        post_data['email'] = "testUser10@testuser.com"
        post_data['password'] = "supersecretpassword"
        post_data['confirm-password'] = "password_that_doesnt_match"
        response = self.test_app.post('/sign-up', data=post_data)
        self.assertEquals(response.status, "400 BAD REQUEST")

    # Tests failed login. Expect 401
    def test_invalid_login(self):
        # Register
        self.test_app = app.test_client()
        post_data = {}
        post_data['username'] = "testUser11"
        post_data['email'] = "testUser11@testuser.com"
        post_data['password'] = "supersecretpassword"
        post_data['confirm-password'] = "supersecretpassword"
        response = self.test_app.post('/sign-up', data=post_data)
        self.assertEquals(response.status, "302 FOUND")

        #Login with bad password
        post_data = {}
        post_data['username'] = "testUser11"
        post_data['password'] = "invalidpassword"
        response = self.test_app.post('/', data=post_data)
        self.assertEquals(response.status, "401 UNAUTHORIZED")

class PythonRESTServerTest(unittest.TestCase):
    # Test Python API Server POST call with a valid token. Expect 200 and a valid greeting
    def test_py_rest_server(self):
        # POST a valid user
        self.test_app = app.test_client()
        post_data = {}
        post_data['username'] = "testUser12"
        post_data['email'] = "testUser12@testuser.com"
        post_data['password'] = "supersecretpassword"
        post_data['confirm-password'] = "supersecretpassword"
        response = self.test_app.post('/sign-up', data=post_data)
        self.assertEquals(response.status, "302 FOUND")

        # Access DB to find the accessToken
        mongo_url = os.environ["MONGO_URL"]
        connection = Connection(mongo_url)
        db = connection.auth.users
        found_user = db.find_one()

        post_data = {}
        post_data['token'] = found_user['token']
        r = requests.post("https://localhost:8000", data = json.dumps(post_data), verify=False)
        self.assertEquals(r.status_code, 200)
        found = "Hello testuser12! Python is pleased to meet you!" in r.text
        self.assertEquals(found, True)

    # Test invalid token python REST call. Fake update expiry to be 10 seconds from
    # start of the test. Expects 401
    def test_py_rest_server_timeout(self):
        self.test_app = app.test_client()

        # Access DB to find the accessToken
        mongo_url = os.environ["MONGO_URL"]
        connection = Connection(mongo_url)
        db = connection.auth.users
        found_user = db.find_one()

	post_data = {}
        post_data['token'] = found_user['token']
        r = requests.post("https://localhost:8000", data = json.dumps(post_data), verify=False)
        self.assertEquals(r.status_code, 200)

	# Update expiry in the database to 10 seconds from now
	found_user['expires_at'] = datetime.utcnow() + timedelta(seconds=10)
	db.save(found_user)
	sleep(10)
	r = requests.post("https://localhost:8000", data = json.dumps(post_data), verify=False)
        self.assertEquals(r.status_code, 401)

if __name__ == '__main__':
    unittest.main()
