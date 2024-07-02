from django.test import TestCase, Client
from django.urls import reverse
from apps.users.models import User
from apps.projects.models import Project


class APITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.project = Project.objects.create(
            user=self.user, name="testproject", slug="testproject", notes="testproject"
        )

    def test_current_user(self):
        response = self.client.get(reverse("api-v1:current_user"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "")
        self.client.login(username="testuser", password="testpassword")
        # response = self.client.get("/api/v1/users/c")
        response = self.client.get(reverse("api-v1:current_user"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "testuser")

    def test_logout(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.post(reverse("api-v1:logout"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["redirect"], "/")

    def test_get_users_projects(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(
            reverse("api-v1:get_users_projects", args=["testuser"])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["projects"]), 1)
