from django.conf import settings
from django.test import SimpleTestCase
from django.urls import resolve


class LegacyDbDisabledTests(SimpleTestCase):
    def test_not_configured(self):
        self.assertNotIn("apps.legacydb", settings.INSTALLED_APPS)
        self.assertNotIn("legacydb", settings.DATABASES)
        self.assertEqual(settings.DATABASE_ROUTERS, [])


class LegacyApiNotServedTests(SimpleTestCase):
    def test_routes_gone(self):
        for path in ["/api/users/alice/projects/p", "/api/projects/save", "/api/users/c"]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_v1_still_served(self):
        self.assertEqual(resolve("/api/v1/init").namespace, "api-v1")
