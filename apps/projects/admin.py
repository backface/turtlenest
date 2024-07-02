from django.contrib import admin
from .models import Project, Category, Image, Like, Comment, Remix, FlaggedProject


class ImageInline(admin.TabularInline):
    model = Image
    max_num = 1
    can_delete = False


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):  # MarkdownxModelAdmin):
    list_display = (
        "id",
        "image_tag",
        "name",
        "user",
        "tag_list",
        "is_public",
        "views",
        "date_created",
        "date_updated",
        "last_shared",
    )
    search_fields = ["name", "user__username", "tags__name"]
    raw_id_fields = ["user"]
    list_filter = ["is_public", "is_published"]
    inlines = [ImageInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("tags")

    def tag_list(self, obj):
        return ", ".join(o.name for o in obj.tags.all())


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "date_updated")
    search_fields = [
        "name",
    ]


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("project", "liker", "date_created")
    search_fields = ["liker__username", "project__name"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "author", "contents", "date_created")
    search_fields = ["author__username", "contents", "project__name"]


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ("id", "preview_tag", "file", "project", "date_created")


@admin.register(Remix)
class RemixAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "original_project",
        "remixed_project",
    )


@admin.register(FlaggedProject)
class FlaggedProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "flagged_by", "reason", "date_created")
    search_fields = ("project__title", "flagged_by__username")
