from django.urls import path
from apps.projects import views as project_views
from . import views


app_name = "users"

urlpatterns = [
    path("profile", views.profile, name="profile"),
    path("users/<str:username>", project_views.user_detail, name="detail"),
    path("delete_my_account", views.delete_account, name="delete_account")
]
