"""Rate limits on the API auth endpoints and web write views."""

from unittest import mock

from allauth.account.models import EmailAddress
from django.core import mail
from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings

from apps.projects.models import Project
from apps.users.models import User
from turtlenest import ratelimit
from turtlenest.ratelimit import TOO_MANY, client_ip

LOW_LIMITS = {
    **ratelimit.LIMITS,
    "api-login": [("ip", "6/h"), ("username", "3/h")],
    "api-signup": [("ip", "2/h")],
    "api-password-reset": [("ip", "50/h"), ("username", "2/h")],
    "api-resend-verification": [("ip", "50/h"), ("username", "2/h")],
    "api-newpassword": [("ip", "50/h"), ("username", "2/h")],
    "web-search": [("ip", "3/m")],
    "web-semantic-search": [("ip", "1/m")],
    "web-comment": [("user", "2/m")],
    "web-like": [("user", "4/m")],
    "web-flag": [("user", "1/h")],
}


@override_settings(RATELIMIT_ENABLE=True, TRUSTED_PROXY_COUNT=1)
class RateLimitTestCase(TestCase):
    def setUp(self):
        patcher = mock.patch.dict(ratelimit.LIMITS, LOW_LIMITS)
        patcher.start()
        self.addCleanup(patcher.stop)
        cache.clear()
        self.addCleanup(cache.clear)


class ClientIpTests(TestCase):
    def setUp(self):
        self.rf = RequestFactory()

    def ip(self, xff=None, remote="172.18.0.1"):
        meta = {"REMOTE_ADDR": remote}
        if xff is not None:
            meta["HTTP_X_FORWARDED_FOR"] = xff
        return client_ip(self.rf.get("/", **meta))

    @override_settings(TRUSTED_PROXY_COUNT=1)
    def test_uses_hop_written_by_our_proxy(self):
        # the client can prepend anything; nginx appends the real peer
        self.assertEqual(self.ip("6.6.6.6, 203.0.113.7"), "203.0.113.7")

    @override_settings(TRUSTED_PROXY_COUNT=2)
    def test_two_proxies(self):
        self.assertEqual(self.ip("6.6.6.6, 203.0.113.7, 10.0.0.2"), "203.0.113.7")

    @override_settings(TRUSTED_PROXY_COUNT=1)
    def test_without_header_falls_back_to_remote_addr(self):
        self.assertEqual(self.ip(), "172.18.0.1")

    @override_settings(TRUSTED_PROXY_COUNT=0)
    def test_header_ignored_without_trusted_proxy(self):
        self.assertEqual(self.ip("203.0.113.7"), "172.18.0.1")

    @override_settings(TRUSTED_PROXY_COUNT=1)
    def test_garbage_and_ipv6(self):
        self.assertEqual(self.ip("not-an-ip"), "unknown")
        self.assertEqual(self.ip("2001:db8:1:2:3:4:5:6"), "2001:db8:1:2::/64")


class ApiRateLimitTests(RateLimitTestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="snap$testpass"
        )
        EmailAddress.objects.create(
            user=self.user, email="test@example.com", primary=True, verified=True
        )

    def login(self, username="testuser", password="wrong", ip="203.0.113.1"):
        return self.client.post(
            f"/api/v1/users/{username}/login",
            data=password,
            content_type="text/plain",
            HTTP_X_FORWARDED_FOR=ip,
        )

    def assertLimited(self, response):
        self.assertEqual(response.status_code, 429)
        self.assertTrue(response.content.startswith(b'{"errors"'))
        self.assertEqual(response.json(), {"errors": [TOO_MANY]})

    def test_login_limited_per_username_across_ips(self):
        for i in range(3):
            self.assertEqual(self.login(ip=f"203.0.113.{i}").status_code, 200)
        self.assertLimited(self.login(ip="203.0.113.99"))
        # even the right password is refused while limited
        self.assertLimited(self.login(password="testpass", ip="203.0.113.98"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_limit_is_case_insensitive(self):
        for name in ("testuser", "TestUser", "TESTUSER"):
            self.login(username=name)
        self.assertLimited(self.login(username="tEsTuSeR"))

    def test_login_limited_per_ip_across_usernames(self):
        for i in range(6):
            self.assertEqual(self.login(username=f"user{i}").status_code, 200)
        self.assertLimited(self.login(username="other"))
        # another IP is unaffected
        self.assertEqual(self.login(username="other2", ip="198.51.100.1").status_code, 200)

    def test_spoofed_forwarded_for_does_not_bypass(self):
        for i in range(3):
            self.login(ip=f"10.9.9.{i}, 203.0.113.1")
        self.assertLimited(self.login(ip="10.9.9.200, 203.0.113.1"))

    def test_signup_limited_per_ip(self):
        for i in range(2):
            response = self.client.post(
                f"/api/v1/users/new{i}?email=new{i}@example.com"
                "&password=pw&password_repeat=pw"
            )
            self.assertEqual(response.status_code, 200)
        response = self.client.post(
            "/api/v1/users/new9?email=new9@example.com&password=pw&password_repeat=pw"
        )
        self.assertLimited(response)
        self.assertFalse(User.objects.filter(username="new9").exists())

    def test_password_reset_limited_per_username(self):
        for _ in range(2):
            self.client.post("/api/v1/users/testuser/password_reset")
        sent = len(mail.outbox)
        self.assertLimited(self.client.post("/api/v1/users/testuser/password_reset"))
        self.assertEqual(len(mail.outbox), sent)

    def test_resend_verification_limited_per_username(self):
        for _ in range(2):
            self.client.get("/api/v1/users/testuser/resendverification")
        self.assertLimited(self.client.get("/api/v1/users/testuser/resendverification"))

    def test_newpassword_limited_per_username(self):
        self.client.login(username="testuser", password="snap$testpass")
        url = "/api/v1/users/testuser/newpassword?oldpassword=x&newpassword=y&password_repeat=y"
        for _ in range(2):
            self.client.post(url)
        self.assertLimited(self.client.post(url))

    @override_settings(RATELIMIT_ENABLE=False)
    def test_disabled_setting_turns_limits_off(self):
        for _ in range(10):
            self.assertEqual(self.login().status_code, 200)


class WebRateLimitTests(RateLimitTestCase):
    def setUp(self):
        super().setUp()
        self.owner = User.objects.create_user(
            username="owner", email="owner@example.com", password="pw", notify_like=True
        )
        self.liker = User.objects.create_user(username="liker", password="pw")
        self.project = Project.objects.create(
            user=self.owner, name="p", is_public=True, is_published=True
        )
        self.client.login(username="liker", password="pw")

    def test_search_limited_per_ip(self):
        for _ in range(3):
            self.assertEqual(self.client.get("/search/all/?q=").status_code, 200)
        response = self.client.get("/search/all/?q=")
        self.assertEqual(response.status_code, 429)

    def test_like_limited_and_mail_sent_once(self):
        url = f"/project/like/{self.project.id}"
        for _ in range(4):
            self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.get(url).status_code, 429)
        # liked, unliked, liked, unliked: only the first like mails the owner
        self.assertEqual(len(mail.outbox), 1)

    def test_comment_limited_per_user(self):
        url = f"/project/{self.project.id}/comment/add"
        data = {"author": self.liker.id, "project": self.project.id, "body": "hi"}
        for _ in range(2):
            self.assertNotEqual(self.client.post(url, data).status_code, 429)
        self.assertEqual(self.client.post(url, data).status_code, 429)

    def test_flag_post_limited_per_user(self):
        url = f"/project/flag/{self.project.id}"
        self.assertNotEqual(self.client.post(url, {}).status_code, 429)
        self.assertEqual(self.client.post(url, {}).status_code, 429)
        # the form itself (GET) stays reachable
        self.assertEqual(self.client.get(url).status_code, 200)
