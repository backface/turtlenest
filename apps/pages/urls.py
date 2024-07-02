from django.urls import path

from . import views

app_name = "pages"
urlpatterns = [
    path("<slug>", views.view_page, name="view"),
]
