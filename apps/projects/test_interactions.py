from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Comment, FlaggedProject, Like, Project

User = get_user_model()


class ProjectInteractionTests(TestCase):
    """Comments, likes and flags only reach projects the user may see."""

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(username="owner", password="pw", email="o@example.com")
        cls.other = User.objects.create_user(username="other", password="pw", email="x@example.com")
        cls.public = Project.objects.create(name="Public", user=cls.owner)
        cls.private = Project.objects.create(name="Private", user=cls.owner, is_public=False, is_published=False)

    def setUp(self):
        self.client.force_login(self.other)

    def comment(self, target, **data):
        return self.client.post(
            reverse("projects:add_comment", args=[target.id]), {"contents": "hello", **data}
        )

    # comments

    def test_comment_on_public_project(self):
        response = self.comment(self.public)
        self.assertEqual(response.status_code, 200)
        comment = Comment.objects.get()
        self.assertEqual((comment.project, comment.author), (self.public, self.other))

    def test_comment_on_private_project_is_404(self):
        self.assertEqual(self.comment(self.private).status_code, 404)
        self.assertFalse(Comment.objects.exists())

    def test_comment_ignores_posted_project_and_author(self):
        response = self.comment(self.public, project=self.private.id, author=self.owner.id)
        self.assertEqual(response.status_code, 200)
        comment = Comment.objects.get()
        self.assertEqual((comment.project, comment.author), (self.public, self.other))

    def test_owner_can_comment_on_own_private_project(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.comment(self.private).status_code, 200)
        self.assertEqual(Comment.objects.get().project, self.private)

    def test_empty_comment_is_400(self):
        self.assertEqual(self.comment(self.public, contents="").status_code, 400)
        self.assertFalse(Comment.objects.exists())

    def test_comment_on_missing_project_is_404(self):
        response = self.client.post(reverse("projects:add_comment", args=[999999]), {"contents": "x"})
        self.assertEqual(response.status_code, 404)

    # likes

    def test_like_public_project(self):
        response = self.client.get(reverse("projects:like", args=[self.public.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Like.objects.filter(project=self.public, liker=self.other).exists())

    def test_like_private_project_is_404(self):
        response = self.client.get(reverse("projects:like", args=[self.private.id]))
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Like.objects.exists())

    def test_like_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("projects:like", args=[self.public.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Like.objects.exists())

    # flags

    def test_flag_public_project(self):
        response = self.client.post(reverse("projects:flag", args=[self.public.id]), {"reason": "spam"})
        self.assertEqual(response.status_code, 302)
        flag = FlaggedProject.objects.get()
        self.assertEqual((flag.project, flag.flagged_by), (self.public, self.other))

    def test_flag_private_project_is_404(self):
        url = reverse("projects:flag", args=[self.private.id])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, {"reason": "spam"}).status_code, 404)
        self.assertFalse(FlaggedProject.objects.exists())
