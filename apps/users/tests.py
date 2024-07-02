from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
import hashlib


class PasswordHasherTest(TestCase):
    def setUp(self):
        self.UserModel = get_user_model()
        self.password = "tsetpassword123"
        self.password_hashed = hashlib.sha256(self.password.encode("utf-8")).hexdigest()
        self.user = self.UserModel.objects.create_user(
            username="testuser",
        )
        self.user.set_password(self.password)
        self.user.save()

    def test_password_hasher(self):
        print(self.user.password)
        # Check if the password was hashed correctly
        self.assertTrue(check_password(self.password, self.user.password))
        # self.assertTrue(check_password(self.password_hashed, self.user.password))
        self.assertTrue(
            check_password(
                "dc53da91af0a00ef627dd54a81693a1ba8b22f0341e81ebeb4230f8f87c17adc697d62e6318d26ae4a6a68a9d0ef96c2109ddb15d917a115a8327ee7d1ef7c34",
                self.user.password,
            )
        )
