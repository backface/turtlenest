from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class ProjectNotFoundTests(TestCase):
    def setUp(self):
        User.objects.create_user(username="alice", password="snap$pw")
        self.client.login(username="alice", password="snap$pw")

    def assertNotFound(self, response):
        self.assertEqual(response.status_code, 404)
        self.assertTrue(response.content.startswith(b'{"errors"'))
        self.assertEqual(response.json(), {"errors": ["Project missing not found"]})

    def test_get(self):
        self.assertNotFound(self.client.get("/api/v1/projects/alice/missing"))

    def test_get_unknown_user(self):
        response = self.client.get("/api/v1/projects/nobody/missing")
        self.assertEqual(response.status_code, 404)

    def test_thumbnail(self):
        self.assertNotFound(self.client.get("/api/v1/projects/alice/missing/thumbnail"))

    def test_metadata(self):
        response = self.client.post("/api/v1/projects/alice/missing/metadata?ispublic=true")
        self.assertNotFound(response)

    def test_delete(self):
        self.assertNotFound(self.client.delete("/api/v1/projects/alice/missing"))

    def test_anonymous(self):
        self.client.logout()
        self.assertNotFound(self.client.get("/api/v1/projects/alice/missing"))
