from django.test import SimpleTestCase, override_settings


class HealthCheckTests(SimpleTestCase):
    def test_alive(self):
        response = self.client.get("/alive", HTTP_HOST="127.0.0.1:8000")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")

    @override_settings(ALLOWED_HOSTS=["turtlestitch.org"])
    def test_unknown_host_rejected(self):
        response = self.client.get("/alive", HTTP_HOST="evil.example")
        self.assertEqual(response.status_code, 400)
