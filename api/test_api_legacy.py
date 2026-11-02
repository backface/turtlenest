import base64
import os

from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.projects.models import Project
from apps.users.models import User


class LegacyAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.project = Project.objects.create(
            user=self.user,
            name="Test Project",
            is_public=True,
            notes="Test notes",
            project_file=SimpleUploadedFile(
                "test_project.xml", b"<xml><notes>Test notes</notes></xml>"
            ),
            thumbnail=SimpleUploadedFile("test_thumbnail.png", b"dummy thumbnail data"),
        )

    def test_current_user(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(reverse("api-legacy:current_user"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "testuser")

    def test_get_users_projects(self):
        response = self.client.get(
            reverse("api-legacy:get_users_projects", args=["testuser"])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["projectname"], "Test Project")
        self.assertEqual(response.json()[0]["ispublic"], True)

    def test_get_project(self):
        response = self.client.get(
            reverse("api-legacy:get_project", args=["testuser", "Test Project"])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["projectname"], "Test Project")
        self.assertEqual(response.json()["notes"], "Test notes")

    def test_get_project_thumbnail(self):
        response = self.client.get(
            reverse(
                "api-legacy:get_project_thumbnail", args=["testuser", "Test Project"]
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("data:image/png;base64,", response.content.decode("utf-8"))

    def test_set_project_visibility(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(
            reverse(
                "api-legacy:set_project_visibility", args=["testuser", "Test Project"]
            ),
            {"ispublic": False},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["ispublic"])

        self.client.logout()
        response = self.client.get(
            reverse("api-legacy:get_users_projects", args=["testuser"])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

    def test_set_project_visibility_non_owner(self):
        other = User.objects.create_user(username="other", password="otherpass")
        self.client.force_login(other)
        response = self.client.get(
            reverse(
                "api-legacy:set_project_visibility", args=["testuser", "Test Project"]
            ),
            {"ispublic": False},
        )
        self.assertEqual(response.status_code, 403)
        self.project.refresh_from_db()
        self.assertTrue(self.project.is_public)
        self.assertTrue(self.project.is_published)

    def test_delete_project(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(
            reverse("api-legacy:delete_project", args=["testuser", "Test Project"])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertFalse(Project.objects.filter(name="Test Project").exists())

    def test_delete_project_non_owner(self):
        other = User.objects.create_user(username="other", password="otherpass")
        self.client.force_login(other)
        response = self.client.get(
            reverse("api-legacy:delete_project", args=["testuser", "Test Project"])
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Project.objects.filter(name="Test Project").exists())

    def test_save_project(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.post(
            "/api/projects/save?username=testuser&projectname=Test&tags=&ispublic=true",
            content_type="application/json",
            data="<xml><notes>some notes #tagged</notes></xml>",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["text"], "project Test created")
        response = self.client.get("/api/users/testuser/projects/Test")
        self.assertEqual(
            response.json()["contents"], "<xml><notes>some notes #tagged</notes></xml>"
        )

        response = self.client.get(
            reverse("api-legacy:get_users_projects", args=["testuser"])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

    def test_save_project_drops_html_thumbnail(self):
        self.client.login(username="testuser", password="testpassword")
        payload = base64.b64encode(b'<script>alert(1)</script>').decode()
        xml = (
            f"<xml><thumbnail>data:text/html;base64,{payload}</thumbnail>"
            "<notes>n</notes></xml>"
        )
        response = self.client.post(
            "/api/projects/save?username=testuser&projectname=Evil&tags=&ispublic=true",
            content_type="application/json",
            data=xml,
        )
        # the project is saved, the invalid thumbnail is dropped
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Project.objects.get(user__username="testuser", name="Evil").thumbnail
        )
        found = []
        thumbs_root = os.path.join(settings.MEDIA_ROOT, "projects", "thumbs")
        if os.path.isdir(thumbs_root):
            for root, _, files in os.walk(thumbs_root):
                found.extend(f for f in files if f.lower().endswith(".html"))
        self.assertEqual(found, [])        
