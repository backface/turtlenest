from urllib.parse import urlencode

from allauth.account.adapter import get_adapter
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.users.test_verification import make_user

User = get_user_model()


class SignupTests(TestCase):
    def signup(self, username, email="new@example.com", password="pw", repeat="pw"):
        query = urlencode({"email": email, "password": password, "password_repeat": repeat})
        return self.client.post(f"/api/v1/users/{username}?{query}")

    def assertRejected(self, response, text):
        self.assertEqual(response.status_code, 400)
        errors = response.json()["errors"]
        self.assertTrue(any(text in e for e in errors), errors)

    def test_valid_signup(self):
        response = self.signup("newuser")
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username="newuser")
        self.assertEqual(user.email, "new@example.com")
        self.assertTrue(user.check_password("snap$pw"))

    def test_password_mismatch(self):
        response = self.signup("newuser", repeat="other")
        self.assertRejected(response, "Passwords do not match")
        self.assertTrue(response.content.startswith(b'{"errors"'))
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_username_taken_case_insensitive(self):
        make_user("alice")
        response = self.signup("Alice")
        self.assertRejected(response, "username already exists")
        self.assertEqual(User.objects.filter(username__iexact="alice").count(), 1)

    def test_reserved_username(self):
        for name in ["admin", "Admin", "moderator"]:
            with self.subTest(name=name):
                self.assertRejected(self.signup(name), "can not be used")
        self.assertFalse(User.objects.filter(username__iexact="admin").exists())

    def test_current_user_route_name_reserved(self):
        # /users/c is the current-user route; also blocked for web signup
        with self.assertRaises(ValidationError):
            get_adapter().clean_username("C")

    def test_invalid_username(self):
        self.assertRejected(self.signup("bad name!"), "valid username")

    def test_invalid_email(self):
        for email in ["", "not-an-email", "a@b@c"]:
            with self.subTest(email=email):
                self.assertRejected(self.signup("newuser", email=email), "valid e-mail")
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_email_taken_case_insensitive(self):
        make_user("alice")
        response = self.signup("bob", email="ALICE@Example.com")
        self.assertRejected(response, "already exists")
        self.assertFalse(User.objects.filter(username="bob").exists())

    def test_email_is_normalised(self):
        self.signup("newuser", email=" New@Example.COM ")
        self.assertEqual(User.objects.get(username="newuser").email, "new@example.com")


class ChangePasswordTests(TestCase):
    def setUp(self):
        self.user = make_user("alice", verified=True)
        self.client.login(username="alice", password="snap$pw")

    def change(self, old="pw", new="new", repeat="new", username="alice"):
        query = urlencode({"oldpassword": old, "newpassword": new, "password_repeat": repeat})
        return self.client.post(f"/api/v1/users/{username}/newpassword?{query}")

    def assertPassword(self, raw):
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(f"snap${raw}"))

    def test_change(self):
        response = self.change()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "Password changed")
        self.assertPassword("new")

    def test_mismatch_keeps_password(self):
        response = self.change(repeat="typo")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"errors": ["The provided passwords do not match"]})
        self.assertPassword("pw")

    def test_wrong_old_password(self):
        response = self.change(old="wrong")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"errors": ["The provided password is wrong"]})
        self.assertPassword("pw")

    def test_other_user(self):
        make_user("bob")
        response = self.change(username="bob")
        self.assertEqual(response.status_code, 401)

    def test_anonymous(self):
        self.client.logout()
        self.assertEqual(self.change().status_code, 401)
        self.assertPassword("pw")
