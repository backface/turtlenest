"""Social signup must not trust an unverified provider e-mail address."""

from allauth.core import context
from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.helpers import complete_social_login
from allauth.socialaccount.models import SocialApp
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core import mail
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.users.models import User


class SocialSignupVerificationTests(TestCase):
    def setUp(self):
        SocialApp.objects.create(provider="github", name="GitHub", client_id="id", secret="s")

    def social_login(self, email, verified):
        request = RequestFactory().get("/accounts/github/login/callback/")
        SessionMiddleware(lambda r: None).process_request(request)
        MessageMiddleware(lambda r: None).process_request(request)
        request.user = AnonymousUser()
        response = {
            "id": 4711,
            "login": "octo",
            "email": email,
            "emails": [{"email": email, "primary": True, "verified": verified}],
        }
        with context.request_context(request):
            provider = get_adapter().get_provider(request, "github")
            sociallogin = provider.sociallogin_from_response(request, response)
            return request, complete_social_login(request, sociallogin)

    def test_unverified_provider_email_requires_verification(self):
        request, response = self.social_login("victim@example.com", verified=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("account_email_verification_sent"))
        self.assertNotIn("_auth_user_id", request.session)
        user = User.objects.get(email="victim@example.com")
        self.assertFalse(user.is_email_verified())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["victim@example.com"])

    def test_verified_provider_email_logs_in(self):
        request, response = self.social_login("octo@example.com", verified=True)
        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", request.session)
        self.assertTrue(User.objects.get(email="octo@example.com").is_email_verified())
