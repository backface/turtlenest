from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings
from .models import Project, Category, Comment
from .templatetags.tags import linktags, link_uris, removetags

# TODO: test for comments, 

User = get_user_model()

class ProjectViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.project = Project.objects.create(name='Test Project', user=self.user)
        self.category = Category.objects.create(name='Test Category')

    def test_index_view(self):
        response = self.client.get(reverse('projects:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    def test_detail_view(self):
        response = self.client.get(reverse('projects:detail', args=[self.user.username, self.project.name]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/project_detail.html')

    def test_detail_view_escapes_xss_in_notes(self):
        self.project.notes = '<img src=x onerror=alert(1)> http://example.com #tag'
        self.project.save()
        response = self.client.get(reverse('projects:detail', args=[self.user.username, self.project.name]))
        self.assertEqual(response.status_code, 200)
        content = response.content
        self.assertNotIn(b'<img src=x onerror=alert(1)>', content)
        self.assertIn(b'&lt;img src=x onerror=alert(1)&gt;', content)

    def test_user_detail_view_escapes_xss_in_profile(self):
        self.user.about = '<script>alert(1)</script>'
        self.user.location = "<img src=x onerror='alert(2)'>"
        self.user.save()
        response = self.client.get(reverse('projects:user_detail', args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        content = response.content
        self.assertNotIn(b'<script>alert(1)</script>', content)
        self.assertNotIn(b"<img src=x onerror='alert(2)'>", content)
        self.assertIn(b'&lt;script&gt;alert(1)&lt;/script&gt;', content)

    def test_collection_view(self):
        response = self.client.get(reverse('projects:collection', args=['newest']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/project_list.html')

    def test_search_view(self):
        response = self.client.get(reverse('projects:search', args=['projects']), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/search.html')

    def test_search_users_view(self):
        response = self.client.get(reverse('projects:search', args=['users']), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/search.html')

    def test_search_semantic_view(self):
        response = self.client.get(reverse('projects:search', args=['semantic']), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/search.html')

    def test_category_list_view(self):
        response = self.client.get(reverse('projects:categories'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/categories.html')

    def test_tags_view(self):
        response = self.client.get(reverse('projects:list_tags'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/tags.html')

    def test_myprojects_view(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('projects:mycollection'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/project_list.html')


class ProjectEditViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.project = Project.objects.create(name='Test Project', user=self.user)
        settings.SYNC_NOTES_ON_SAVE = False

    def test_edit_view(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('projects:edit', args=[self.project.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/project_edit.html')

    def test_edit_project(self):
        self.client.login(username='testuser', password='testpassword')
        url = reverse('projects:edit', args=[self.project.id])
        data = {
            'notes': 'Updated project notes',
            'is_public': True,
            'is_published': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Expecting a redirect after successful edit

        # Refresh the project from the database
        self.project.refresh_from_db()
        self.assertEqual(self.project.notes, 'Updated project notes')
        self.assertTrue(self.project.is_public)
        self.assertTrue(self.project.is_published)

    def test_add_comment(self):
        self.client.login(username='testuser', password='testpassword')
        url = reverse('projects:add_comment', args=[self.project.id])
        data = {
            'contents': 'This is a test comment',
            'project': self.project.id,
            'author': self.user.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)  # Expecting a successful response

        # Check if the comment was added to the database
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.contents, 'This is a test comment')
        self.assertEqual(comment.project, self.project)
        self.assertEqual(comment.author, self.user)

    def test_add_comment_unauthenticated(self):
        url = reverse('projects:add_comment', args=[self.project.id])
        data = {
            'contents': 'This is a test comment',
            'project': self.project.id,
            'author': self.user.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Expecting a redirect to login page
        self.assertEqual(Comment.objects.count(), 0)  # No comment should be added

    def test_add_invalid_comment(self):
        self.client.login(username='testuser', password='testpassword')
        url = reverse('projects:add_comment', args=[self.project.id])
        data = {
            'contents': '',  # Invalid: empty comment
            'project': self.project.id,
            'author': self.user.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 500)  # Expecting an error response
        self.assertEqual(Comment.objects.count(), 0)  # No comment should be added


class TemplateFilterTests(TestCase):
    """The filters inject HTML, so they must escape user text first (stored XSS)."""

    def test_linktags_escapes_html_and_links_tags(self):
        out = linktags('<img src=x onerror=alert(1)> #tag @user', autoescape=True)
        self.assertNotIn("<img", out)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", out)
        self.assertIn("<a href='/projects/tag/tag' class='text-tertiary'>#tag</a>", out)
        self.assertIn("<a href='/user/user' class='text-tertiary'>@user</a>", out)

    def test_linktags_escapes_quote_injection(self):
        out = linktags("#a' onclick='alert(1)", autoescape=True)
        self.assertNotIn("' onclick='", out)
        self.assertIn("&#x27;", out)

    def test_link_uris_escapes_html_and_links_http_urls(self):
        out = link_uris("<script>alert(1)</script> see http://example.com/a?b=1", autoescape=True)
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", out)
        self.assertIn("<a target='_blank' href='http://example.com/a?b=1'", out)
        self.assertNotIn("''", out)

    def test_link_uris_escapes_quote_injection(self):
        out = link_uris("http://example.com/' onclick='alert(1)", autoescape=True)
        self.assertNotIn("' onclick='", out)
        self.assertIn("&#x27;", out)

    def test_link_uris_does_not_link_urls_without_scheme(self):
        out = link_uris("example.com is here", autoescape=True)
        self.assertNotIn("<a", out)

    def test_removetags_still_strips_tags(self):
        out = removetags("hello #world and @user")
        self.assertNotIn("#", out)

