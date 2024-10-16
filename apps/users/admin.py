from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from .models import User
from apps.projects.models import Project

class ProjectInline(admin.TabularInline):
    model = Project
    max_num = 0
    can_delete = False
    fields = ["name", "is_published", "is_public", "date_created"]   
    readonly_fields =["name", "is_published", "is_public", "date_created"] 


class IsModerator(admin.SimpleListFilter):
    title = "is moderator"
    # Parameter for the filter that will be used in the URL query.
    parameter_name = "is_moderator"

    def lookups(self, request, model_admin):
        return ((1, "yes"), (0, "no"))

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(groups__in=Group.objects.filter(name="moderator"))
        elif self.value() == "0":
            return queryset.exclude(groups__in=Group.objects.filter(name="moderator"))
        return queryset


class IsTeacher(admin.SimpleListFilter):
    title = "is teacher"
    # Parameter for the filter that will be used in the URL query.
    parameter_name = "is_teacher"

    def lookups(self, request, model_admin):
        return ((1, "yes"), (0, "no"))

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(groups__in=Group.objects.filter(name="teacher"))
        elif self.value() == "0":
            return queryset.exclude(groups__in=Group.objects.filter(name="teacher"))
        return queryset


class IsPuppet(admin.SimpleListFilter):
    title = "is puppet"
    # Parameter for the filter that will be used in the URL query.
    parameter_name = "is_puppet"

    def lookups(self, request, model_admin):
        return ((1, "yes"), (0, "no"))

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(groups__in=Group.objects.filter(name="puppet"))
        elif self.value() == "0":
            return queryset.exclude(groups__in=Group.objects.filter(name="puppet"))
        return queryset


@admin.register(User)
class UserAdmin(UserAdmin):
    # list_display = UserAdmin.list_display + ("location", "is_moderator", "is_teacher", "is_puppet", "is_active", "date_joined", "last_login",)
    list_display = (
        "username",
        "email",
        "location",
        "about",
        "mentor",
        "is_teacher",
        "is_puppet",
        "is_active",
        "date_joined",
        "last_login",
        "num_projects"
    )
    list_filter = UserAdmin.list_filter + (
        "date_joined",
        IsModerator,
        IsTeacher,
        IsPuppet,
        "is_staff",
    )
    search_fields = ("first_name", "last_name", "email", "username")
    fieldsets = UserAdmin.fieldsets + (
        (
            "Additional Infos",
            {"fields": ("avatar", "language", "location", "about", "mentor")},
        ),
    )
    raw_id_fields = ("mentor",)
    inlines = (ProjectInline,)
    ordering = ("-date_joined",)

    # def get_queryset(self, request):
    #     qs = super(UserAdmin, self).get_queryset(request)
    #     qs = qs.annotate(UserAdmin.Count('projects'))
    #     return qs
    
    @admin.display(description="Projects")
    def num_projects(self, obj):
        return obj.project_set.all().count()
    #num_projects.admin_order_field = 'project__count'     