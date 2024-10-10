from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.projects.models import Project


class Group(models.Model):
    """
    A Group of learners. Formerly called 'classrooms'
    """

    host = models.ForeignKey(
        settings.AUTH_USER_MODEL, models.CASCADE, related_name="host"
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, editable=False, db_index=True)
    description = models.TextField(blank=True, null=True)
    #image = models.TextField(blank=True, null=True)
    current_unit = models.IntegerField(default=0)
    # current_unit = models.ForeignKey("Unit", on_delete=models.SET_NULL, blank=True, null=True, related_name="current_unit")
    introduction = models.TextField(blank=True, null=True)

    date_modified = models.DateTimeField(default=timezone.now, editable=False)
    date_created = models.DateTimeField(default=timezone.now, editable=False)

    members = models.ManyToManyField(settings.AUTH_USER_MODEL, through="Membership")
    projects = models.ManyToManyField(Project, through="SelectedProject", blank=True)

    class Meta:
        ordering = ("-date_modified",)

    def __str__(self):
        return f"{self.title}"

    def save(self, *args, **kwargs):
        self.date_modified = timezone.now()
        self.slug = slugify(self.title, allow_unicode=True)
        super(Group, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            "groups:group_detail",
            kwargs={"pk": self.pk},
        )

    def is_host(self, user):
        return self.host == user

    @property
    def get_starters(self):
        return self.projects.filter(selectedproject__is_starter=True, unit=None)

    @property
    def get_projects(self):
        return self.projects.filter(selectedproject__is_starter=False, unit=None)

    def addProject(self, project):
        return self.projects.add(project)


class Membership(models.Model):
    """
    Group Memberships.
    """

    group = models.ForeignKey("Group", models.CASCADE)
    is_hosting = models.BooleanField(default=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, models.CASCADE, related_name="membership"
    )

    date_modified = models.DateTimeField(default=timezone.now, editable=False)
    date_created = models.DateTimeField(default=timezone.now, editable=False)

    def save(self, *args, **kwargs):
        self.date_created = timezone.now()
        self.date_modified = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = (("group", "user"),)
        ordering = ("-date_modified",)

    def __str__(self):
        return f"{self.user}"


class Unit(models.Model):
    """
    A Unit of content. Formerly called 'lesson'
    """

    group = models.ForeignKey("Group", models.CASCADE, related_name="units")
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=200, editable=False, db_index=True)
    number = models.IntegerField(default=0)
    description = models.TextField(blank=True, null=True)

    projects = models.ManyToManyField(Project, through="SelectedProject", blank=True)

    date_modified = models.DateTimeField(default=timezone.now, editable=False)
    date_created = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ("number",)

    def save(self, *args, **kwargs):
        self.date_modified = timezone.now()
        self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title}"

    def is_host(self, user):
        return self.group.host == user

    @property
    def get_starters(self):
        return self.projects.filter(selectedproject__is_starter=True)

    @property
    def get_projects(self):
        return self.projects.filter(selectedproject__is_starter=False)


class SelectedProject(models.Model):
    """
    A selection of projects for a group or unit
    """

    group = models.ForeignKey("Group", models.CASCADE, blank=True, null=True)
    unit = models.ForeignKey("Unit", models.CASCADE, blank=True, null=True)
    project = models.ForeignKey(Project, models.CASCADE)
    is_starter = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    date_modified = models.DateTimeField(default=timezone.now, editable=False)
    date_created = models.DateTimeField(default=timezone.now, editable=False)

    def save(self, *args, **kwargs):
        self.date_modified = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ("order",)

    def __str__(self):
        return f"{self.project}"


class TrainerRequest(models.Model):
    """
    A request to become a trainer.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255, verbose_name=_("Full Name"))
    phone_number = models.CharField(
        max_length=255, blank=True, verbose_name=_("Phone Number")
    )
    organization = models.CharField(max_length=255, verbose_name=_("Organization"))
    role = models.CharField(max_length=255, verbose_name=_("Role"))
    type = models.CharField(max_length=255, verbose_name=_("Type of organization"))
    website = models.URLField(max_length=255, verbose_name=_("Website"))
    tos = models.BooleanField(
        default=False, verbose_name=_("I agree to the terms of service (stated below)")
    )

    date_created = models.DateTimeField(default=timezone.now, editable=False)
    date_modified = models.DateTimeField(default=timezone.now, editable=False)
    approved = models.BooleanField(default=False)
