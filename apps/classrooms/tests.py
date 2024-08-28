# tests.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group as AuthGroup
from .models import Group, Unit, Membership, TrainerRequest

User = get_user_model()


# created with Claude Sonnet
# TODO: unit test for units!

class GroupViewTests(TestCase):
    def setUp(self):
        # Create test users and groups
        self.teacher_group =  AuthGroup.objects.create(name="Teachers")        
        self.teacher = User.objects.create_user(username='teacher', password='password')
        self.teacher_group.user_set.add(self.teacher)
        self.host = User.objects.create_user(username='host', password='password')
        self.member = User.objects.create_user(username='member', password='password')
        self.group = Group.objects.create(title='Test Group', description='Test description', introduction='Test intro', host=self.host)
        self.group.members.add(self.host)

    def test_group_create_view(self):
        self.client.login(username='teacher', password='password')
        response = self.client.post(reverse('groups:group_create'), {
            'title': 'New Group',
            'description': 'New description',
            'introduction': 'New intro'
        })
        self.assertEqual(response.status_code, 302)  # Check for redirect
        self.assertTrue(Group.objects.filter(title='New Group').exists())  # Check if group was created

    def test_group_detail_view(self):
        self.client.login(username='host', password='password')
        response = self.client.get(reverse('groups:group_detail', args=[self.group.id]))
        self.assertEqual(response.status_code, 200)  # Check if the page loads successfully
        self.assertContains(response, self.group.title)  # Check if the group title is in the response

    def test_add_member_view(self):
        self.client.login(username='host', password='password')
        response = self.client.post(reverse('groups:add_member', args=[self.group.id]), {
            'username': 'member'
        })
        self.assertEqual(response.status_code, 302)  # Check for redirect after adding
        self.assertTrue(Membership.objects.filter(group=self.group, user=self.member).exists())  # Check membership

    def test_remove_member_view(self):
        self.client.login(username='host', password='password')
        self.group.members.add(self.member)  # first add the member
        response = self.client.post(reverse('groups:remove_member', args=[self.group.id, 'member']))
        self.assertEqual(response.status_code, 302)  # Check for redirect after removing
        self.assertFalse(Membership.objects.filter(group=self.group, user=self.member).exists())  # Check membership removed

    def test_trainer_request(self):
        response = self.client.post(reverse('groups:trainer_request'), {
            'full_name': 'John Doe',
            'phone_number': '+1234567890',
            'organization': 'Test Org',
            'role': 'Teacher',
            'type': 'Individual',
            'website': 'https://example.com',
            'tos': True,
            'referer': '',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after submitting
        self.assertEqual(TrainerRequest.objects.count(), 1)  # Check if the trainer request is created
        
    def test_bulk_add_view(self):
        self.client.login(username='host', password='password')
        csv_data = "name1,password1\nname2,password2\n"
        response = self.client.post(reverse('groups:bulk_add', args=[self.group.id]), {
            'data': csv_data
        })
        self.assertEqual(response.status_code, 302)  # Check for redirect
        self.assertTrue(User.objects.filter(username='group{}name1'.format(self.group.id)).exists())  # Check if users were created
        self.assertTrue(User.objects.filter(username='group{}name2'.format(self.group.id)).exists())

    def test_leave_view(self):
        self.client.login(username='member', password='password')
        response = self.client.get(reverse('groups:leave'))
        self.assertEqual(response.status_code, 302)  # Check for redirect
        self.assertFalse(self.group.members.filter(username='member').exists())  # Check if member left

    def tearDown(self):
        User.objects.all().delete()
        Group.objects.all().delete()
