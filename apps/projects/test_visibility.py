import importlib
import json

from django.apps import apps
from django.contrib.auth.models import Group as AuthGroup
from django.test import TestCase
from django.urls import reverse

from apps.classrooms.models import Group, SelectedProject
from apps.users.test_verification import make_user

from .models import Category, Project


class VisibilityTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = make_user("owner", verified=True)
        cls.other = make_user("other", verified=True)
        cls.moderator = make_user("mod", verified=True)
        cls.moderator.groups.add(AuthGroup.objects.create(name="Moderators"))

    def make_project(self, name, public=True, published=True, user=None):
        return Project.objects.create(
            name=name, user=user or self.owner, is_public=public, is_published=published
        )


class InvariantTests(VisibilityTestCase):
    def test_private_project_cannot_be_published(self):
        project = self.make_project("p", public=False, published=True)
        project.refresh_from_db()
        self.assertFalse(project.is_published)

    def test_unlisted_project_stays_unlisted(self):
        project = self.make_project("p", public=True, published=False)
        project.refresh_from_db()
        self.assertTrue(project.is_public)
        self.assertFalse(project.is_published)

    def test_migration_unpublishes_private_projects(self):
        project = self.make_project("p")
        Project.objects.filter(pk=project.pk).update(is_public=False)  # bypasses save()
        migration = importlib.import_module(
            "apps.projects.migrations.0009_unpublish_private_projects"
        )
        migration.unpublish_private(apps, None)
        project.refresh_from_db()
        self.assertFalse(project.is_published)


class ListingTests(VisibilityTestCase):
    def setUp(self):
        self.featured = Category.objects.create(name="Featured", slug="featured")

    def test_index_never_features_unlisted_project(self):
        unlisted = self.make_project("unlisted", published=False)
        unlisted.categories.add(self.featured)
        self.assertIsNone(self.client.get("/").context["featured"])

    def test_index_features_published_project(self):
        listed = self.make_project("listed")
        listed.categories.add(self.featured)
        self.assertEqual(self.client.get("/").context["featured"], listed)

    def test_category_list_hides_unlisted_and_private(self):
        shown = self.make_project("shown")
        for project in (shown, self.make_project("u", published=False), self.make_project("x", public=False)):
            project.categories.add(self.featured)
        response = self.client.get(reverse("projects:categories"))
        category = next(c for c in response.context["categories"] if c.pk == self.featured.pk)
        self.assertEqual([p for p in category.page_obj], [shown])

    def test_project_stats_private_is_404(self):
        private = self.make_project("x", public=False)
        url = reverse("projects:project_stats", args=[private.id])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(url).status_code, 200)


class ShareAndPublishTests(VisibilityTestCase):
    def test_moderator_cannot_share_or_publish(self):
        private = self.make_project("x", public=False)
        unlisted = self.make_project("u", published=False)
        self.client.force_login(self.moderator)
        self.assertEqual(self.client.get(reverse("projects:share", args=[private.id])).status_code, 403)
        self.assertEqual(self.client.get(reverse("projects:publish", args=[unlisted.id])).status_code, 403)
        private.refresh_from_db()
        unlisted.refresh_from_db()
        self.assertFalse(private.is_public)
        self.assertFalse(unlisted.is_published)

    def test_moderator_can_unshare_and_unpublish(self):
        a, b = self.make_project("a"), self.make_project("b")
        self.client.force_login(self.moderator)
        self.client.get(reverse("projects:unshare", args=[a.id]))
        self.client.get(reverse("projects:unpublish", args=[b.id]))
        a.refresh_from_db()
        b.refresh_from_db()
        self.assertFalse(a.is_public)
        self.assertFalse(b.is_published)

    def test_owner_publishing_private_project_shares_it(self):
        private = self.make_project("x", public=False)
        self.client.force_login(self.owner)
        self.client.get(reverse("projects:publish", args=[private.id]))
        private.refresh_from_db()
        self.assertTrue(private.is_public)
        self.assertTrue(private.is_published)
        self.assertIsNotNone(private.last_shared)


class ApiVisibilityTests(VisibilityTestCase):
    def setUp(self):
        self.client.login(username="owner", password="snap$pw")

    def save(self, name):
        data = {"xml": f'<project name="{name}"><notes></notes></project>', "notes": "", "thumbnail": ""}
        return self.client.post(
            f"/api/v1/projects/owner/{name}", data=json.dumps(data), content_type="application/json"
        )

    def test_save_new_project_is_published(self):
        self.assertEqual(self.save("new").status_code, 200)
        project = Project.objects.get(name="new")
        self.assertTrue(project.is_public and project.is_published)

    def test_save_keeps_private_project_private(self):
        self.make_project("secret", public=False)
        self.assertEqual(self.save("secret").status_code, 200)
        project = Project.objects.get(name="secret")
        self.assertFalse(project.is_public or project.is_published)

    def test_save_keeps_unlisted_project_unlisted(self):
        self.make_project("unl", published=False)
        self.save("unl")
        project = Project.objects.get(name="unl")
        self.assertTrue(project.is_public)
        self.assertFalse(project.is_published)

    def test_metadata_publish_shares_private_project(self):
        self.make_project("p", public=False)
        response = self.client.post("/api/v1/projects/owner/p/metadata?ispublished=true")
        self.assertEqual(response.status_code, 200)
        project = Project.objects.get(name="p")
        self.assertTrue(project.is_public and project.is_published)

    def test_metadata_unshare_unpublishes(self):
        self.make_project("p")
        self.client.post("/api/v1/projects/owner/p/metadata?ispublic=false&ispublished=false")
        project = Project.objects.get(name="p")
        self.assertFalse(project.is_public or project.is_published)


class StarterProjectTests(VisibilityTestCase):
    def setUp(self):
        self.group = Group.objects.create(title="Class", host=self.other)
        self.client.force_login(self.other)

    def add(self, project):
        return self.client.get(reverse("groups:addstarter", args=[self.group.id, project.id]))

    def test_cannot_add_someone_elses_private_project(self):
        private = self.make_project("x", public=False)
        self.assertEqual(self.add(private).status_code, 404)
        self.assertFalse(SelectedProject.objects.exists())

    def test_can_add_shared_project(self):
        self.assertEqual(self.add(self.make_project("s", published=False)).status_code, 302)
        self.assertTrue(SelectedProject.objects.filter(group=self.group).exists())
