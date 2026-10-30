import hashlib

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password

from apps.users.hashers import SnapPBKDF2PasswordHasher

User = get_user_model()


class SnapPBKDF2PasswordHasherTest(TestCase):
    password = "tsetpassword123"
    # Snap! clients send the password pre-hashed: snap$<sha512hex>
    snap_prehashed = "snap$" + hashlib.sha512(password.encode("utf-8")).hexdigest()

    def setUp(self):
        self.user = User.objects.create_user(username="testuser")
        self.user.set_password(self.password)
        self.user.save()

    def test_default_hasher_is_snap_pbkdf2(self):
        self.assertTrue(self.user.password.startswith("pbkdf2_snapped_sha512$"))

    def test_verify_plain_password(self):
        self.assertTrue(check_password(self.password, self.user.password))
        self.assertFalse(check_password("wrong", self.user.password))

    def test_verify_snap_prehashed_password(self):
        # stored from the plain password, verified from the Snap! app's pre-hashed form
        self.assertTrue(check_password(self.snap_prehashed, self.user.password))

    def test_encode_plain_and_prehashed_match(self):
        # encoding with a fixed salt, plain and snap$-pre-hashed input must produce
        # the same digest, so both login paths work against one stored hash
        hasher = SnapPBKDF2PasswordHasher()
        salt = hasher.salt()
        self.assertEqual(
            hasher.encode(self.password, salt),
            hasher.encode(self.snap_prehashed, salt),
        )

    def test_verify_legacy_double_hashed(self):
        # legacy stored format: PBKDF2(sha512(sha512(password)))
        hasher = SnapPBKDF2PasswordHasher()
        legacy = hasher.encode(
            hashlib.sha512(self.password.encode("utf-8")).hexdigest(),
            hasher.salt(),
        )
        self.assertTrue(check_password(self.password, legacy))

    def test_legacy_hash_upgrades_on_check(self):
        # a legacy stored hash must verify and be re-encoded with the default
        # (snapped) hasher when checked through the user, as login does
        self.user.password = make_password(self.password, hasher="sha512")
        self.user.save()
        self.assertTrue(self.user.check_password(self.password))
        self.user.refresh_from_db()
        self.assertTrue(self.user.password.startswith("pbkdf2_snapped_sha512$"))
        self.assertTrue(self.user.check_password(self.password))
