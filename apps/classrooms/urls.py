from django.urls import path

from . import views
from .views import (
    GroupListView,
    GroupDetailView,
    GroupUpdateView,
    GroupCreateView,
    GroupDeleteView,
)

app_name = "groups"

urlpatterns = [
    path(r"mygroups", views.my_groups, name="mygroups"),
    path(r"groups", GroupListView.as_view(), name="group_list"),
    path(r"<int:pk>", GroupDetailView.as_view(), name="group_detail"),
    path(r"edit/<int:pk>", GroupUpdateView.as_view(), name="group_update"),
    path(r"delete/<int:pk>", GroupDeleteView.as_view(), name="group_delete"),
    path(r"create", GroupCreateView.as_view(), name="group_create"),
    path(r"leave", views.leave, name="leave"),
    # units
    # path(r"<int:id>/unit/create", UnitCreateView.as_view(), name="unit_create"),
    # path(r"unit/edit/<int:pk>", UnitUpdateView.as_view(), name="unit_update")
    # path(r"unit/delete/<int:pk>", UnitDeleteView.as_view(), name="unit_delete"),
    path(r"<int:id>/unit/create", views.create_unit, name="unit_create"),
    path(r"unit/edit/<int:pk>", views.edit_unit, name="unit_update"),
    path(r"unit/delete/<int:pk>", views.delete_unit, name="unit_delete"),
    path(r"unit/activate/<int:pk>", views.activate_unit, name="unit_activate"),
    path(
        r"addstarter/<int:group_id>/<int:project_id>",
        views.add_starter,
        name="addstarter",
    ),
    path(r"<int:id>/addmember/", views.add_member, name="add_member"),
    path(
        r"<int:id>/remove_member/<str:username>",
        views.remove_member,
        name="remove_member",
    ),
    path(r"<int:id>/bulk_add", views.bulk_add, name="bulk_add"),
    path(r"trainer_request", views.trainer_request, name="trainer_request"),
]
