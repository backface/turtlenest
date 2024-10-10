from django.contrib import admin
from django.db import models
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
    list_display = ("title", "host", "date_created", "current_unit", "num_users")
    search_fields = ("title", "slug", "host")
    list_filter = ("host",)
    inlines = [MemberInline]
    raw_id_fields = ["host"]

    def get_queryset(self, request):
        qs = super(GroupAdmin, self).get_queryset(request)
        qs = qs.annotate(models.Count('members'))
        return qs
    
    @admin.display(description="Users")
    def num_users(self, obj):
        return obj.members.count()
    num_users.admin_order_field = 'members__count' 


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "group")
    search_fields = ("group__title", "user__username")
    raw_id_fields = ["user"]

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
