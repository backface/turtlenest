import json

from django.test import TestCase, override_settings

from apps.projects.models import Project
from apps.users.test_verification import make_user


class SaveSizeTests(TestCase):
    def setUp(self):
        make_user("alice", verified=True)
        self.client.login(username="alice", password="snap$pw")

    def save(self, padding):
        xml = f'<project name="big"><notes></notes><media>{"x" * padding}</media></project>'
        body = json.dumps({"xml": xml, "notes": "", "thumbnail": ""})
        return self.client.post(
            "/api/v1/projects/alice/big", data=body, content_type="application/json"
        )

    def test_3_mb_project_saves(self):
        response = self.save(3 * 1024 * 1024)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Project.objects.filter(user__username="alice", name="big").exists())

    @override_settings(DATA_UPLOAD_MAX_MEMORY_SIZE=1024 * 1024)
    def test_too_big_returns_snap_error(self):
        response = self.save(2 * 1024 * 1024)
        self.assertEqual(response.status_code, 413)
        self.assertTrue(response.content.startswith(b'{"errors"'))
        self.assertEqual(response.json(), {"errors": ["Project is too big (max 1 MB)"]})
        self.assertFalse(Project.objects.filter(name="big").exists())
