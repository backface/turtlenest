from django.db import models
from django.utils import timezone
from django.conf import settings
from django.utils.html import strip_tags
from django.utils.html import mark_safe
from django.utils.text import slugify
from taggit.managers import TaggableManager
import markdown


class Post(models.Model):
    """
    A Blog Post
    """

    title = (models.CharField(max_length=200, unique=True),)
    slug = models.SlugField(editable=False, unique=True, db_index=True)
    summary = models.TextField()
    body = models.TextField()
    image = models.ImageField(
        blank=True, null=True, help_text="image for social media cards"
    )

    authors = models.ManyToManyField(settings.AUTH_USER_MODEL, through="Authorship")

    is_draft = models.BooleanField(default=False)

    date_created = models.DateTimeField(default=timezone.now, editable=False)
    date_updated = models.DateTimeField(default=timezone.now, editable=False)

    tags = TaggableManager()

    class Meta:
        verbose_name_plural = "posts"

    def save(self):
        self.date_updated = timezone.now()
        if not self.slug or self.slug == "":
            self.slug = slugify(self.title, allow_unicode=True)
        super(Post, self).save()

    def get_absolute_url(self):
        return "/blog/%d/%s/" % (self.created.year, self.slug)

    def __str__(self):
        return self.title

    @property
    def summary_rendered(self):
        return mark_safe(markdown.markdown(self.summary, output_format="html5"))

    @property
    def summary_text(self):
        return strip_tags(markdown.markdown(self.summary, output_format="html5"))

    @property
    def body_rendered(self):
        return mark_safe(markdown.markdown(self.body, output_format="html5"))


class Authorship(models.Model):
    """
    A Blog Post's Authorships
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]
