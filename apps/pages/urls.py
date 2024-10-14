from django.urls import path

from . import views

app_name = "pages"

urlpatterns = [
    path("<str:slug>/", views.view_page, name="view"),
]
