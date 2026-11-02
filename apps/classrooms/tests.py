# tests.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group as AuthGroup
from .models import Group, Membership, TrainerRequest


User = get_user_model()

# created with Claude Sonnet
# TODO: unit test for units!


class GroupViewTests(TestCase):
    def setUp(self):
        # Create test users and groups
        self.teacher_group =  AuthGroup.objects.create(name="Teachers")        
        self.teacher = User.objects.create_user(username='teacher', password='password')
        self.teacher_group.user_set.add(self.teacher)
        # bulk_add expects the 'Puppets' auth group to exist (seeded in prod by migrate_accounts)
        AuthGroup.objects.get_or_create(name="Puppets")
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
        self.client.login(username='host', password='password')
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


class GroupAccessTests(TestCase):
    """only members and the host may open a group."""

    def setUp(self):
        self.host = User.objects.create_user(username="host", password="password")
        self.member = User.objects.create_user(username="member", password="password")
        self.outsider = User.objects.create_user(username="outsider", password="password")
        self.group = Group.objects.create(title="Secret Class", host=self.host)
        self.group.members.add(self.host, self.member)
        self.url = reverse("groups:group_detail", args=[self.group.id])

    def test_host_can_open_group(self):
        self.client.login(username="host", password="password")
        self.assertContains(self.client.get(self.url), "Secret Class")

    def test_host_who_is_not_a_member_can_open_group(self):
        self.group.members.remove(self.host)
        self.client.login(username="host", password="password")
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_member_can_open_group(self):
        self.client.login(username="member", password="password")
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_outsider_gets_404_and_no_session_group(self):
        self.client.login(username="outsider", password="password")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)
        self.assertNotContains(response, "Secret Class", status_code=404)
        self.assertNotIn("group", self.client.session)

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("account_login"), response["Location"])

    def test_superuser_can_open_group(self):
        User.objects.create_superuser(username="admin", password="password")
        self.client.login(username="admin", password="password")
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_member_of_two_groups_sees_group_once(self):
        # the Q(members) | Q(host) join must not duplicate the row
        other = Group.objects.create(title="Other", host=self.member)
        other.members.add(self.member)
        self.group.host = self.member
        self.group.save()
        self.client.login(username="member", password="password")
        self.assertEqual(self.client.get(self.url).status_code, 200)


class BulkAddTests(TestCase):
    """Audit #5: bulk add must not take over accounts it did not create."""

    def setUp(self):
        AuthGroup.objects.get_or_create(name="Puppets")
        self.host = User.objects.create_user(username="host", password="password")
        self.other_host = User.objects.create_user(username="other", password="password")
        # ids chosen so that group 30 + "1a" == group 3 + "01a" == "group301a"
        self.group3 = Group.objects.create(id=3, title="Three", host=self.other_host)
        self.group30 = Group.objects.create(id=30, title="Thirty", host=self.host)
        self.client.login(username="host", password="password")

    def bulk_add(self, group, data):
        return self.client.post(
            reverse("groups:bulk_add", args=[group.id]), {"data": data}, follow=True
        )

    def make_pupil(self, username, mentor, group):
        pupil = User.objects.create_user(username=username, password="original", mentor=mentor)
        pupil.add_to_group("Puppets")
        group.members.add(pupil)
        return pupil

    def test_creates_pupils(self):
        self.bulk_add(self.group30, "anna, pw1\nben, pw2\n")
        for name, pw in [("anna", "pw1"), ("ben", "pw2")]:
            pupil = User.objects.get(username=f"group30{name}")
            self.assertTrue(pupil.check_password(pw))
            self.assertTrue(pupil.is_puppet)
            self.assertEqual(pupil.mentor, self.host)
            self.assertFalse(pupil.notify_comment)
            self.assertFalse(pupil.notify_like)
            self.assertTrue(self.group30.members.filter(pk=pupil.pk).exists())
            self.assertTrue(pupil.emailaddress_set.get(email=f"group30{name}@turtlestitch.org").verified)

    def test_other_teachers_pupil_is_not_taken_over(self):
        victim = self.make_pupil("group301a", self.other_host, self.group3)
        response = self.bulk_add(self.group30, "1a, hijacked")
        victim.refresh_from_db()
        self.assertTrue(victim.check_password("original"))
        self.assertEqual(victim.mentor, self.other_host)
        self.assertFalse(self.group30.members.filter(pk=victim.pk).exists())
        self.assertContains(response, "already taken")

    def test_pupil_added_to_own_group_by_username_is_still_protected(self):
        # add_member lets a host add any existing user; that must not grant
        # password control over another teacher's pupil
        victim = self.make_pupil("group30x", self.other_host, self.group3)
        self.group30.members.add(victim)
        self.bulk_add(self.group30, "x, hijacked")
        victim.refresh_from_db()
        self.assertTrue(victim.check_password("original"))

    def test_regular_user_with_matching_name_is_not_touched(self):
        real = User.objects.create_user(username="group30bob", password="original")
        self.bulk_add(self.group30, "bob, hijacked")
        real.refresh_from_db()
        self.assertTrue(real.check_password("original"))
        self.assertFalse(real.is_puppet)
        self.assertFalse(self.group30.members.filter(pk=real.pk).exists())

    def test_name_match_is_case_insensitive(self):
        real = User.objects.create_user(username="Group30Bob", password="original")
        self.bulk_add(self.group30, "bob, hijacked")
        real.refresh_from_db()
        self.assertTrue(real.check_password("original"))
        self.assertFalse(User.objects.filter(username="group30bob").exists())

    def test_reimporting_own_pupil_resets_password(self):
        pupil = self.make_pupil("group30anna", self.host, self.group30)
        self.bulk_add(self.group30, "anna, newpass")
        pupil.refresh_from_db()
        self.assertTrue(pupil.check_password("newpass"))
        self.assertEqual(User.objects.filter(username="group30anna").count(), 1)

    def test_one_bad_row_changes_nothing(self):
        victim = self.make_pupil("group301a", self.other_host, self.group3)
        response = self.bulk_add(self.group30, "anna, pw1\n1a, hijacked\nben, pw2")
        self.assertFalse(User.objects.filter(username__in=["group30anna", "group30ben"]).exists())
        victim.refresh_from_db()
        self.assertTrue(victim.check_password("original"))
        self.assertNotContains(response, "Members added")

    def test_malformed_rows_are_reported(self):
        response = self.bulk_add(self.group30, "anna\nben, pw, extra\n, pw\ncarl,  ")
        self.assertEqual(User.objects.filter(username__startswith="group30").count(), 0)
        for n in (1, 2, 3, 4):
            self.assertContains(response, f"Line {n}:")

    def test_invalid_and_duplicate_names_are_rejected(self):
        response = self.bulk_add(self.group30, "bad name, pw\nanna, pw\nANNA, pw2")
        self.assertContains(response, "invalid name")
        self.assertContains(response, "listed twice")
        self.assertFalse(User.objects.filter(username__startswith="group30").exists())

    def test_blank_lines_are_ignored(self):
        self.bulk_add(self.group30, "\nanna, pw1\n\n  \n")
        self.assertTrue(User.objects.filter(username="group30anna").exists())

    def test_row_cap(self):
        from apps.classrooms.views import BULK_ADD_MAX_ROWS
        data = "\n".join(f"p{i}, pw" for i in range(BULK_ADD_MAX_ROWS + 1))
        response = self.bulk_add(self.group30, data)
        self.assertContains(response, "Too many rows")
        self.assertFalse(User.objects.filter(username__startswith="group30").exists())

    def test_non_host_cannot_bulk_add(self):
        response = self.bulk_add(self.group3, "anna, pw1")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username="group3anna").exists())
