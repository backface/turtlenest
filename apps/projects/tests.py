"""
Unit tests for the `project` module.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from .models import Project


class ProjectTestCase(TestCase):
    """
    Tests for the `Project` model.
    """

    def setUp(self):
        """
        Create a test user and project
        """
        self.UserModel = get_user_model()
        self.user = self.UserModel.objects.create_user(
            username="testuser",
            password="testpassword",
            email="testuser@turtlestitch.org",
        )
        Project.objects.create(
            name="Test Project", slug="test", notes="A test project", user=self.user
        )

    def test_project_creation(self):
        """
        Test that the project was created successfully.
        """
        project = Project.objects.get(name="Test Project")
        self.assertEqual(project.notes, "A test project")
        self.assertEqual(project.user, self.user)
