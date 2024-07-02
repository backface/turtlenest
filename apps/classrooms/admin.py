from django.contrib import admin
from .models import Group, Membership, Unit, SelectedProject, TrainerRequest


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "slug", "host", "date_created", "current_unit")
    search_fields = ("title", "slug")


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "group")
    search_fields = ("group__title", "user__username")


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "slug",
        "title",
        "group",
    )
    search_fields = ("title", "slug")


@admin.register(SelectedProject)
class SelectedProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "group", "unit", "is_starter")
    search_fields = ("group__title", "project__name")


@admin.register(TrainerRequest)
class TrainerRequestAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "user",
        "organization",
        "role",
        "phone_number",
        "website",
    )
    search_fields = ("full_name", "organization", "role", "phone_number", "website")
