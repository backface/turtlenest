from django.urls import path
from . import views

app_name = "blog"


urlpatterns = [
    #path("", views.index, name="list"),
    # path("<int:id>/", views.detail, name="detail"),
    # path("tag/<int:tag>/", views.list, name="tag"),
    # path("tags", views.tags, name="tags"),

    path("", views.BlogListView.as_view(), name="post_list"),
    path("<str:slug>", views.BlogDetailView.as_view(), name="post_detail"), 
    path("tag/<str:tag>", views.TagPostListView.as_view(), name="post_tag"),   
]
