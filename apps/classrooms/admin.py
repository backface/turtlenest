from django.contrib import admin
from .models import Group, Membership, Unit, SelectedProject, TrainerRequest


class MemberInline(admin.TabularInline):
    model = Membership
    extra = 0
    raw_id_fields = ["user"]
    #can_delete = False
    #has_add_permission = False
    #editable_fields = []    
    #readonly_fields = [field.name for field in model._meta.get_fields()]
    

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "id", "host", "date_created", "current_unit")
    search_fields = ("title", "slug", "host")
    list_filter = ("host",)
    inlines = [MemberInline]
    raw_id_fields = ["host"]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "group")
    search_fields = ("group__title", "user__username")
    raw_id_fields = ["host", "user"]

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
