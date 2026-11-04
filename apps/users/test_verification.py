"""Grace period for unverified API logins, verify on save, cleanup."""

import json
from io import StringIO
from unittest import skip

from allauth.account.models import EmailAddress
from django.contrib.auth.models import Group as AuthGroup
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.classrooms.models import Group
from apps.projects.models import Comment, Project
from apps.users.models import User
from apps.users.verification import days_left, mark_verified

DAY = timezone.timedelta(days=1)


def make_user(username, joined_days_ago=0, verified=False, **extra):
    user = User.objects.create_user(
        username=username, email=f"{username}@example.com", password="snap$pw", **extra
    )
    user.date_joined = timezone.now() - joined_days_ago * DAY
    user.save()
    EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=verified)
    return user


@override_settings(UNVERIFIED_GRACE_DAYS=3)
class GraceLoginTests(TestCase):
    def login(self, username):
        return self.client.post(
            f"/api/v1/users/{username}/login", data="pw", content_type="text/plain"
        )

    def test_verified_user_gets_no_days_left(self):
        make_user("ver", joined_days_ago=100, verified=True)
        response = self.login("ver")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("days_left", response.json())
        self.assertIn("_auth_user_id", self.client.session)

    def test_new_unverified_user_gets_days_left(self):
        make_user("fresh")
        response = self.login("fresh")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["days_left"], 3)
        self.assertIn("_auth_user_id", self.client.session)

    def test_days_left_rounds_up(self):
        user = make_user("mid")
        user.date_joined = timezone.now() - 2.5 * DAY
        user.save()
        self.assertEqual(days_left(user), 1)
        self.assertEqual(self.login("mid").json()["days_left"], 1)

    def test_expired_unverified_user_is_refused(self):
        make_user("old", joined_days_ago=4)
        response = self.login("old")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(response.content.startswith(b'{"errors"'))
        self.assertIn("Resend Verification Email", response.json()["errors"][0])
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_wrong_password_unchanged(self):
        make_user("old", joined_days_ago=4)
        response = self.client.post(
            "/api/v1/users/old/login", data="nope", content_type="text/plain"
        )
        self.assertEqual(response.json(), {"message": "Wrong username or password"})

    def test_signup_then_login_works_immediately(self):
        response = self.client.post(
            "/api/v1/users/newbie?email=newbie@example.com&password=pw&password_repeat=pw"
        )
        self.assertIn("within 3 days", response.json()["message"])
        self.assertEqual(self.login("newbie").json()["days_left"], 3)


class VerifyOnSaveTests(TestCase):
    def setUp(self):
        self.user = make_user("saver", joined_days_ago=1)
        self.client.login(username="saver", password="snap$pw")

    def test_v1_save_verifies(self):
        data = {"xml": '<project name="p"><notes></notes></project>', "notes": "", "thumbnail": ""}
        response = self.client.post(
            "/api/v1/projects/saver/p", data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user.is_email_verified())

    @skip("legacy API is deprecated and not routed")
    def test_legacy_save_verifies(self):
        response = self.client.post(
            "/api/projects/save?username=saver&projectname=P&tags=&ispublic=true",
            content_type="application/json",
            data="<xml><notes>n</notes></xml>",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user.is_email_verified())

    def test_refused_save_does_not_verify(self):
        make_user("other")
        self.client.post(
            "/api/v1/projects/other/p",
            data=json.dumps({"xml": "<project/>", "notes": "", "thumbnail": ""}),
            content_type="application/json",
        )
        self.assertFalse(User.objects.get(username="other").is_email_verified())

    def test_mark_verified_handles_missing_address_and_case(self):
        user = User.objects.create_user(username="bare", email="Bare@Example.com")
        self.assertTrue(mark_verified(user))
        self.assertTrue(user.is_email_verified())
        self.assertFalse(mark_verified(user))  # nothing left to change
        EmailAddress.objects.filter(user=user).update(email="bare@example.com", verified=False)
        mark_verified(user)
        self.assertEqual(EmailAddress.objects.filter(user=user).count(), 1)


class CleanupUnverifiedTests(TestCase):
    def run_cmd(self, *args):
        out = StringIO()
        call_command("cleanup_unverified", *args, stdout=out)
        return out.getvalue()

    def setUp(self):
        self.stale = make_user("stale", joined_days_ago=60)
        self.recent = make_user("recent", joined_days_ago=10)
        self.verified = make_user("verified", joined_days_ago=60, verified=True)
        self.logged_in = make_user("loggedin", joined_days_ago=60)
        self.logged_in.last_login = timezone.now() - 50 * DAY
        self.logged_in.save()
        self.staff = make_user("staff", joined_days_ago=60, is_staff=True)
        self.with_project = make_user("maker", joined_days_ago=60)
        Project.objects.create(user=self.with_project, name="x")
        self.teacher = make_user("teacher", joined_days_ago=60)
        self.teacher.groups.add(AuthGroup.objects.create(name="Teachers"))
        self.host = make_user("host", joined_days_ago=60)
        Group.objects.create(title="g", host=self.host)
        self.mentor = make_user("mentor", joined_days_ago=60)
        make_user("pupil", joined_days_ago=60, verified=True, mentor=self.mentor)
        self.member = make_user("member", joined_days_ago=60)
        Group.objects.create(title="h", host=self.verified).members.add(self.member)
        self.commenter = make_user("commenter", joined_days_ago=60)
        Comment.objects.create(
            project=Project.objects.create(user=self.verified, name="y"),
            author=self.commenter,
            contents="hi",
        )

    def remaining(self):
        return set(User.objects.values_list("username", flat=True))

    def test_dry_run_changes_nothing(self):
        before = self.remaining()
        out = self.run_cmd("--verify-with-projects")
        self.assertIn("[dry run] deleted 1 ", out)
        self.assertIn("[dry run] verified 1 ", out)
        self.assertEqual(self.remaining(), before)
        self.assertFalse(self.with_project.is_email_verified())

    def test_commit_deletes_only_stale_unowned_accounts(self):
        before = self.remaining()
        self.run_cmd("--commit")
        self.assertEqual(before - self.remaining(), {"stale"})
        self.assertFalse(EmailAddress.objects.filter(email="stale@example.com").exists())
        # without the option, project owners stay unverified
        self.assertFalse(self.with_project.is_email_verified())

    def test_verify_with_projects(self):
        out = self.run_cmd("--verify-with-projects", "--commit")
        self.assertIn("verified 1 ", out)
        self.assertTrue(self.with_project.is_email_verified())
        self.assertTrue(User.objects.filter(username="maker").exists())

    def test_days_option(self):
        self.run_cmd("--days", "5", "--commit")
        self.assertNotIn("recent", self.remaining())
        self.assertIn("mentor", self.remaining())
        self.assertIn("pupil", self.remaining())
