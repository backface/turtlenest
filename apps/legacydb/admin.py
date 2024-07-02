from django.contrib import admin
from .models import Users, Projects, Comments, Likes
from .models import Classrooms, ClassroomMembers, ClassroomProjects, ClassroomUnits


@admin.register(Users)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "email", "location", "joined")
    search_fields = ("username", "email")


@admin.register(Projects)
class ProjectsAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "projectname", "created", "updated")
    search_fields = ("username", "projectname")


admin.site.register(Comments)
admin.site.register(Likes)
admin.site.register(Classrooms)
admin.site.register(ClassroomMembers)
admin.site.register(ClassroomProjects)
admin.site.register(ClassroomUnits)
