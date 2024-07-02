from django.db import models
from django.utils import timezone
from django.conf import settings
from taggit.managers import TaggableManager


class Author(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name


class Media(models.Model):
    guid = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    caption = models.TextField(blank=True, null=True)
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    mime_type = models.CharField(max_length=255, blank=True, null=True)
    media_type = models.CharField(max_length=255, blank=True, null=True)
    media_details = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.title


class Post(models.Model):
    title = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    excerpt = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    date = models.DateTimeField(default=timezone.now, editable=False)
    modified = models.DateTimeField(default=timezone.now, editable=False)
    status = models.CharField(max_length=200)
    featured_media = models.ForeignKey("Media", on_delete=models.SET_NULL, null=True)
    author = models.ForeignKey("Author", on_delete=models.SET_NULL, null=True)

    tags = TaggableManager(blank=True)

    def __str__(self):
        return self.title


class Tag(models.Model):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    count = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    count = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "categories"
        
    def __str__(self):
        return self.name
