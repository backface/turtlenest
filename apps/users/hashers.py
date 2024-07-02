from django.contrib.auth.hashers import BasePasswordHasher, mask_hash
from django.utils.crypto import constant_time_compare, get_random_string
from django.utils.translation import gettext_noop as _
from django.contrib.auth.hashers import PBKDF2PasswordHasher
import hashlib

# copied from django.contrib.auth.hashers (Django 3.2)
# Need for reading and upgrading legacy passwords (crypt)


class SnapPBKDF2PasswordHasher(PBKDF2PasswordHasher):
    algorithm = "pbkdf2_snapped_sha512"

    def encode_sha512_hash(self, sha512_hash, salt, iterations=None):
        return super().encode(sha512_hash, salt, iterations)

    def encode(self, password, salt, iterations=None):
        # password from Snap! comes pre-hashed
        # post-hash again when not from snap!
        if password[:5] == "snap$":
            sha512_hash = password[5:]
        else:
            sha512_hash = hashlib.sha512(password.encode("utf-8")).hexdigest()
        return self.encode_sha512_hash(sha512_hash, salt, iterations)

    def verify(self, password, encoded):
        decoded = self.decode(encoded)
        # password from Snap! comes pre-hashed
        # so we verify both pre-hashed and post-hashed passwords
        # for legacy
        encoded_2 = self.encode(password, decoded["salt"], decoded["iterations"])
        encoded_prehash = self.encode(
            hashlib.sha512(password.encode("utf-8")).hexdigest(),
            decoded["salt"],
            decoded["iterations"],
        )
        if constant_time_compare(encoded, encoded_prehash):
            return True
        else:
            return constant_time_compare(encoded, encoded_2)


# def mask_hash(hash, show=6, char="*"):
#     """
#     Return the given hash, with only the first ``show`` number shown. The
#     rest are masked with ``char`` for security reasons.
#     """
#     masked = hash[:show]
#     masked += char * len(hash[show:])
#     return masked


class CryptPasswordHasher(BasePasswordHasher):
    """
    Password hashing using UNIX crypt (not recommended)
    copied and modified from an older version of Django.

    Needed for reading and upgrading legacy passwords

    The crypt module is not supported on all platforms.
    """

    algorithm = "crypt"
    library = "crypt"

    def salt(self):
        return get_random_string(2)

    def encode(self, password, salt):
        crypt = self._load_library()
        assert len(salt) == 2
        hash = crypt.crypt(password, salt)
        assert hash is not None  # A platform like OpenBSD with a dummy crypt module.
        # we don't need to store the salt, but Django used to do this
        return "%s$%s$%s" % (self.algorithm, "", hash)

    def decode(self, encoded):
        algorithm, salt, hash = encoded.split("$", 2)
        assert algorithm == self.algorithm
        return {
            "algorithm": algorithm,
            "hash": hash,
            "salt": salt,
        }

    def verify(self, password, encoded):
        crypt = self._load_library()
        decoded = self.decode(encoded)
        data = crypt.crypt(password, decoded["hash"])
        return constant_time_compare(decoded["hash"], data)

    def safe_summary(self, encoded):
        decoded = self.decode(encoded)
        return {
            _("algorithm"): decoded["algorithm"],
            _("salt"): decoded["salt"],
            _("hash"): mask_hash(decoded["hash"], show=3),
        }

    def harden_runtime(self, password, encoded):
        pass


class SHA512PasswordHasher(BasePasswordHasher):
    """
    SHA512 password hasher.
    """

    algorithm = "sha512"

    def salt(self):
        return get_random_string(2)

    def encode(self, password, salt):
        salt = ""
        hash = hashlib.sha512(password.encode("UTF-8")).hexdigest()
        return "%s$%s$%s" % (self.algorithm, salt, hash)

    def decode(self, encoded):
        algorithm, salt, hash = encoded.split("$", 2)
        assert algorithm == self.algorithm
        return {
            "algorithm": algorithm,
            "hash": hash,
            "salt": salt,
        }

    def verify(self, password, encoded):
        decoded = self.decode(encoded)
        data = hashlib.sha512(password.encode("UTF-8")).hexdigest()
        return constant_time_compare(decoded["hash"], data)

    def safe_summary(self, encoded):
        decoded = self.decode(encoded)
        return {
            _("algorithm"): decoded["algorithm"],
            _("salt"): decoded["salt"],
            _("hash"): mask_hash(decoded["hash"], show=3),
        }

    def harden_runtime(self, password, encoded):
        pass
