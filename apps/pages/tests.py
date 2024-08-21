# Create your tests here.
from django.test import TestCase, Client
from django.urls import reverse
from .models import Page

class PageViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.page = Page.objects.create(title='Test Page', content='Test Content')

    def test_view_page(self):
        url = reverse('pages:view', args=[self.page.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Content')
