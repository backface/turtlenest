import uuid
import hashlib
from django.utils.translation import gettext_lazy as _
from django.contrib import admin
from django.contrib.auth.models import AbstractUser
from django.db import models
#from allauth.account.models import EmailAddress
from django.contrib.auth.models import Group


def _get_avatar_filename(instance, filename):
    """Use random filename prevent overwriting existing files & to fix caching issues."""
    return f'profile-pictures/{uuid.uuid4()}.{filename.split(".")[-1]}'


# class Preferences(models.Model):
#    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#    timezone = models.CharField(max_length=100, blank=True, default="")
#    language = models.CharField(max_length=10, blank=True, null=True)
#    notify_comment = models.BooleanField(blank=True, null=True)
#    notify_like = models.BooleanField(blank=True, null=True)


class User(AbstractUser):
    """
    A Custom User.
    Add additional fields to Django's User model
    """

    password = models.CharField(max_length=255)
    verified = models.BooleanField(default=False)

    # from turtleCloud/Snapcloud
    location = models.TextField(blank=True, null=True)
    about = models.TextField(blank=True, null=True)

    avatar = models.ImageField(upload_to=_get_avatar_filename, blank=True)
    timezone = models.CharField(max_length=100, blank=True, default="")
    language = models.CharField(max_length=10, default="en")

    # from turtleCloud/
    notify_comment = models.BooleanField(
        default=True, verbose_name=_("Notify me when someone comments on my project")
    )
    notify_like = models.BooleanField(
        default=True, verbose_name=_("Notify me when someone likes my project")
    )

    # is teacher in snap
    is_mentor = models.BooleanField(default=False)

    mentor = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)

    bad_flags = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.get_display_name() }"

    def get_display_name(self) -> str:
        if self.get_full_name().strip():
            return self.get_full_name()
        return self.username

    @property
    def avatar_url(self) -> str:
        if self.avatar:
            return self.avatar.url
        else:
            return "https://www.gravatar.com/avatar/{}?s=128&d=identicon".format(
                self.gravatar_id
            )

    @property
    def gravatar_id(self) -> str:
        # https://en.gravatar.com/site/implement/hash/
        return hashlib.md5(self.email.lower().strip().encode("utf-8")).hexdigest()

    @property
    @admin.display(boolean=True)
    def is_moderator(self):
        return self.groups.filter(name="Moderators").exists()

    @property
    @admin.display(boolean=True)
    def is_teacher(self):
        return self.groups.filter(name="Teachers").exists()

    @property
    @admin.display(boolean=True)
    def is_puppet(self):
        return self.groups.filter(name="Puppets").exists()

    @property
    @admin.display(boolean=True)
    def is_editor(self):
        return self.groups.filter(name="Editors").exists()

    def is_email_verified(self):
        """
        returns True if EmailAddress exists and is already verified, otherwise returns False
        """
        result = False
        try:
            emailaddress = EmailAddress.objects.get_for_user(self, self.email)
            result = emailaddress.verified
        except EmailAddress.DoesNotExist:
            pass
        return result

    class Meta:
        indexes = [
            models.Index(fields=["username"], name="username_idx"),
        ]

    def get_superusers(self):
        return [user.email for user in User.objects.filter(is_superuser=True)]

    def get_superusers_emails(self):
        # return User.objects.filter(is_superuser=True).values("email")
        return [
            email.email
            for email in EmailAddress.objects.filter(user__is_superuser=True).values(
                "email"
            )
        ]

    def get_moderator_emails(self):
        # return User.objects.filter(groups__name__in=["Moderators"]).values("email")
        return [
            user.email for user in User.objects.filter(groups__name__in=["Moderators"])
        ]

    def add_to_group(self, name):
        self.groups.add(Group.objects.get(name=name))


class Token(models.Model):
    user = models.ForeignKey(User, related_name="tokens", on_delete=models.CASCADE)
    value = models.TextField()
    purpose = models.CharField(max_length=255, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
