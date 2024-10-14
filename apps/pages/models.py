from django.db import models
from django.utils import timezone
from django.conf import settings
from django.utils.text import slugify
import uuid
import shortuuid


class Page(models.Model):
    """
    A (flat) page
    """

    title = models.CharField(max_length=200)
    slug = models.CharField(max_length=200, unique=True, blank=True)
    content = models.TextField(blank=True, null=True)
    last_editor = models.ForeignKey(
        settings.AUTH_USER_MODEL, models.CASCADE, blank=True, null=True
    )
    date_modified = models.DateTimeField(default=timezone.now, editable=False)
    date_created = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ("-date_created",)

    def __str__(self):
        return f"{self.title}"
    
    def save(self, *args, **kwargs):
        self.date_modified = timezone.now()
        if self.slug == "":
            self.slug = slugify(self.title, allow_unicode=True)
        try:
            Page.objects.get(slug=self.slug)
            s = shortuuid.encode(uuid.uuid4())[:5]
            self.slug = slugify(self.title, allow_unicode=True) + "-" + s
        except Page.DoesNotExist:
            pass

        super().save(*args, **kwargs)
