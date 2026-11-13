from django.conf import settings
from django.http.request import validate_host
from django.test import SimpleTestCase, override_settings

from turtlenest.hosts import parse_allowed_hosts


class ParseAllowedHostsTests(SimpleTestCase):
    def test_separators(self):
        expected = ["a.org", "b.org", "c.org"]
        for value in ["a.org b.org c.org", "a.org,b.org,c.org", " a.org, b.org\tc.org "]:
            with self.subTest(value=value):
                self.assertEqual(parse_allowed_hosts(value), expected)

    def test_star_subdomain_becomes_dot(self):
        hosts = parse_allowed_hosts("example.org *.example.org")
        self.assertEqual(hosts, ["example.org", ".example.org"])
        self.assertTrue(validate_host("staging.example.org", hosts))
        self.assertTrue(validate_host("example.org", hosts))
        self.assertFalse(validate_host("evil.org", hosts))

    def test_plain_star_kept(self):
        self.assertEqual(parse_allowed_hosts("*"), ["*"])

    def test_default_covers_subdomains(self):
        for host in ["turtlestitch.org", "staging.turtlestitch.org", "x.backface.net"]:
            with self.subTest(host=host):
                self.assertTrue(validate_host(host, settings.ALLOWED_HOSTS))
        self.assertFalse(validate_host("evil.org", settings.ALLOWED_HOSTS))


@override_settings(ALLOWED_HOSTS=parse_allowed_hosts("*.example.org"))
class SubdomainRequestTests(SimpleTestCase):
    def test_subdomain_served(self):
        self.assertEqual(self.client.get("/alive", HTTP_HOST="staging.example.org").status_code, 200)

    def test_other_host_rejected_and_logged(self):
        with self.assertLogs("django.security.DisallowedHost", "ERROR"):
            response = self.client.get("/alive", HTTP_HOST="evil.org")
        self.assertEqual(response.status_code, 400)
