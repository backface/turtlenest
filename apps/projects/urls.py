from django.urls import path
from ..projects import views


app_name = "projects"

urlpatterns = [
    path("", views.index, name="index"),
    path("run", views.run, name="run"),
    path("run/", views.run),
    path("beta", views.beta, name="beta"),
    path("beta/", views.beta),
    path("categories/", views.category_list, name="categories"),
    path("categories/<str:arg>", views.collection, { "collection" : "category" }),
    path("tag/<str:tag>", views.list_by_tag, name="list_by_tag"),
    path("tags", views.tags),

    path("myprojects", views.my_projects, name="my_projects"),
    
    path("stats", views.stats, name="stats"),
   
    path("search", views.search),
    path("search/<str:target>/", views.search, name="search"),

    path("users/search", views.search, { "target": "users"}),
    path(
        "users/<str:username>/projects/<path:projectname>", views.detail, name="detail"
    ),  # old style
    path("users/<str:username>", views.user_detail, name="user_detail"),
    path("user/<str:username>", views.user_detail),
    
    path("project/<int:id>", views.detail_by_id, name="detail_by_id"),
    path("project/stats/<int:id>", views.project_stats, name="project_stats"),
    path("project/edit/<int:id>", views.edit, name="edit"),
    path("project/delete/<int:id>", views.delete, name="delete"),
    path("project/delete_media/<int:id>", views.delete_media, name="delete_media"),
    path("project/upload_media/<int:id>", views.upload_media, name="upload_media"),
    path("project/feature_media/<int:id>", views.feature_media, name="feature_media"),
    path("project/unfeature_media/<int:id>", views.unfeature_media, name="unfeature_media"),
    path(
        "project/update_categories/<int:id>",
        views.update_categories,
        name="update_categories",
    ),
    path("project/flag/<int:id>", views.flag, name="flag"),
    path("project/like/<int:id>", views.like, name="like"),
    path("project/<int:id>/comment/add", views.add_comment, name="add_comment"),
    path("project/<int:id>/share", views.share_project, name="share"),
    path("project/<int:id>/unshare", views.unshare_project, name="unshare"),
    path("project/comment/delete/<id>", views.delete_comment, name="delete_comment"),
    
    path("projects", views.list, name="list"),
    path("projects/search", views.search),
    path("projects/g/<str:collection>", views.collection_redirect),
    path("projects/tag/<str:tag>", views.list_by_tag, name="list_by_tag"),
    path("projects/tags", views.tags, name="list_tags"),
    path("projects/tags/<str:tag>", views.list_by_tag),
    path("projects/<str:collection>", views.collection, name="collection"),
    path("projects/<str:collection>/<str:arg>", views.collection, name="collection"),
    path("myprojects/tags", views.tags, {"mine": True}, name="mycollection"),
    
    path("myprojects/tags/<str:collection>", views.tags, name="list_tags"),
    path(
        "myprojects/tag/<str:tag>",
        views.list_by_tag,
        {"mine": True},
        name="mycollection",
    ),
    path("myprojects/", views.collection, {"mine": True}, name="mycollection"),
    path(
        "myprojects/<str:collection>",
        views.collection,
        {"mine": True},
        name="mycollection",
    ),
    path(
        "myprojects/<str:collection>/<str:arg>",
        views.collection,
        {"mine": True},
        name="mycollection",
    ),
]
