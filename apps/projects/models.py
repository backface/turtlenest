import re
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.html import mark_safe
from taggit.managers import TaggableManager
from django.template.defaultfilters import truncatechars
from django.utils.translation import gettext_lazy as _
from fastembed import TextEmbedding as Embedding
from markdownx.utils import markdownify
from pgvector.django import VectorField
from .templatetags.tags import removetags


def create_embeddings(text):
    text = removetags(text)
    cache_dir = settings.MEDIA_ROOT / "models"
    embedding_model = Embedding(
        model_name=settings.TEXT_EMBEDDING_MODEL,
        max_length=512,
        cache_dir=str(cache_dir),
    )
    embeddings_generator = embedding_model.embed(text)  # reminder this is a generator
    return list(embeddings_generator)[0]


class Project(models.Model):
    """
    A TurtleStitch cloud project
    """

    def project_upload_handler(instance, filename):
        """upload handler for project files"""
        date = instance.date_updated or instance.date_created
        return "projects/files/{Y}/{m}/{d}/{uid}/{fn}".format(
            uid=instance.user.id,
            Y=date.strftime("%Y"),
            m=date.strftime("%m"),
            d=date.strftime("%d"),
            fn=filename,
        )

    def thumbs_upload_handler(instance, filename):
        """upload handler for thumbnails"""
        date = instance.date_updated or instance.date_created
        return "projects/thumbs/{Y}/{m}/{d}/{uid}/{fn}".format(
            uid=instance.user.id,
            Y=date.strftime("%Y"),
            m=date.strftime("%m"),
            d=date.strftime("%d"),
            fn=filename,
        )

    name = models.CharField(max_length=255, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, models.CASCADE, blank=True, null=True, db_index=True
    )
    slug = models.SlugField(max_length=255, editable=False, db_index=True)
    notes = models.TextField(
        blank=True,
        null=True,
        default="",
        verbose_name="Project notes",
        help_text="You can add hashtags here!",
    )

    project_file = models.FileField(
        upload_to=project_upload_handler, blank=True, null=True
    )
    thumbnail = models.ImageField(
        upload_to=thumbs_upload_handler, blank=True, null=True
    )
    image_is_featured = models.IntegerField(default=0)

    is_public = models.BooleanField(default=True, verbose_name="is_shared")
    is_active = models.BooleanField(default=True, verbose_name="is_active")
    is_published = models.BooleanField(default=True, verbose_name="is_published")

    last_shared = models.DateTimeField(blank=True, null=True)
    first_published = models.DateTimeField(blank=True, null=True)

    views = models.IntegerField(default=0)

    embedding_project_meta = VectorField(blank=True, null=True, dimensions=384)

    categories = models.ManyToManyField("Category", blank=True, related_name="projects")

    # moved remixes to additional table
    # orig_creator = models.CharField(max_length=255, blank=True, null=True)
    # orig_name = models.CharField(max_length=255, blank=True, null=True)
    # remixhistory = models.TextField(blank=True, null=True)

    date_updated = models.DateTimeField(default=timezone.now, editable=False)
    date_created = models.DateTimeField(default=timezone.now, editable=False)

    tags = TaggableManager(blank=True)

    class Meta:
        unique_together = (("user", "name"),)
        ordering = ("-date_updated",)
        indexes = [
            models.Index(fields=["user", "name"], name="user_project_idx"),
            # HnswIndex(
            #     name='embedding_project_meta_index',
            #     fields=['embedding_project_meta'],
            #     m=16,
            #     ef_construction=64,
            #     opclasses=['vector_l2_ops']
            # ),
        ]

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        if not kwargs.get("no_timestamp", False):
            self.date_updated = timezone.now()
            if "no_timestamp" in kwargs:
                del kwargs["no_timestamp"]
        else:
            del kwargs["no_timestamp"]
        self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def image_tag(self):
        return mark_safe('<img src="/media/%s" width="150" />' % (self.thumbnail))

    image_tag.short_description = "Image"

    def ilike(self, user):
        return self.likes.filter(liker=user).count() > 0

    def get_absolute_url(self):
        if (self.name):
            return reverse(
                "projects:detail",
                kwargs={
                    "username": self.user.username if self.user else "",
                    "projectname": self.name,
                },
            )
        else:
            return reverse(
                "projects:detail_by_id",
                kwargs={
                    "id": self.id,
                },
            )

    def update_tags_from_notes(self):
        # remove all tags
        current_tags = self.tags.all()
        for tag in current_tags:
            self.tags.remove(tag)
        # ... and add new ones
        regex = "#(\w+)"
        hashtag_list = re.findall(regex, self.notes)
        for hashtag in hashtag_list:
            self.tags.add(hashtag)

    def update_embeddings(self):
        self.embedding_project_meta = create_embeddings(f"{self.name} \n{self.notes}")

    def description_as_markdown(self):
        return mark_safe(markdownify(self.description or ""))

    @property
    def featured_image(self):
        if self.image_is_featured:
            try:
                return self.image_set.get(id=self.image_is_featured).file
            except Exception:
                try:
                    return self.image_set.first().file
                except Exception:
                    return self.thumbnail or None
        else:
            return self.thumbnail or None

    def featured_caption(self):
        if self.image_is_featured:
            try:
                return (
                    self.image_set.get(id=self.image_is_featured).caption or self.name
                )
            except Exception:
                try:
                    return self.image_set.first().caption or self.name
                except Exception:
                    return self.name
        else:
            return self.name

    @property
    def ispublic(self):
        return self.is_public

    @property
    def ispublished(self):
        return self.is_published

    @property
    def lastshared(self):
        return self.last_shared

    @property
    def lastupdated(self):
        return self.date_updated

    @property
    def created(self):
        return self.date_created

    @property
    def projectname(self):
        return self.name

    @property
    def username(self):
        return self.user.username

    @property
    def name_short(self):
        return truncatechars(self.name, 23)
    

class Category(models.Model):
    """
    A Project Category
    """

    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.TextField(null=True, blank=True)
    order = models.IntegerField(default=0)
    date_created = models.DateTimeField(default=timezone.now, editable=False)
    date_updated = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["order", "name"]

    def save(self, *args, **kwargs):
        self.date_updated = timezone.now()
        self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        # return reverse('projects:detail', kwargs={
        #     'projectname': self.name,
        #     'username': self.user.username
        # })
        return reverse(
            "projects:collection", kwargs={"collection": "category", "arg": self.slug}
        )

    def __str__(self):
        return f"{self.name}"


class Image(models.Model):
    """
    A Project's Images
    """

    project = models.ForeignKey("Project", on_delete=models.CASCADE)
    file = models.ImageField(upload_to="projects/images/%Y/%m/%d/")
    title = models.CharField(max_length=255, blank=True, null=True)
    caption = models.CharField(max_length=255, blank=True, null=True, default="")
    order = models.IntegerField(default=0)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def preview_tag(self):
        return mark_safe('<img src="/media/%s" width="150" />' % (self.file))

    preview_tag.short_description = "preview"

    def __str__(self):
        return f"{self.title}"


class Like(models.Model):
    """
    Likes for a project
    """

    liker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True
    )
    project = models.ForeignKey(
        "Project", on_delete=models.CASCADE, related_name="likes", blank=True, null=True
    )
    date_created = models.DateTimeField(
        default=timezone.now, editable=False, blank=True, null=True
    )

    class Meta:
        unique_together = ("liker", "project")


class Comment(models.Model):
    """
    Comments for projects
    """

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey("Project", on_delete=models.CASCADE)
    contents = models.TextField()

    date_created = models.DateTimeField(default=timezone.now, editable=False)
    date_updated = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["-date_created"]

    @property
    def truncated(self):
        return truncatechars(self.contents, 50)


    def save(self, *args, **kwargs):
        self.date_updated = timezone.now()
        super().save(*args, **kwargs)


class Remix(models.Model):
    original_project = models.ForeignKey(
        "Project", on_delete=models.CASCADE, related_name="remixed_from"
    )
    remixed_project = models.ForeignKey(
        "Project", on_delete=models.CASCADE, related_name="remixed_to"
    )
    date_created = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        verbose_name_plural = "remixes"
        verbose_name = "remix"


class FlaggedProject(models.Model):
    """
    A project that has been flagged by a user
    """

    project = models.ForeignKey("Project", on_delete=models.CASCADE)
    flagged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reason = models.TextField(verbose_name=_("Reason"))

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.name} flagged by {self.flagged_by.username}"
