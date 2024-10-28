from django.urls import path
from . import views

app_name = "blog"


urlpatterns = [
    # path("", views.index, name="list"),
    # path("<int:id>/", views.detail, name="detail"),
    # path("tag/<int:tag>/", views.list, name="tag"),
    # path("tags", views.tags, name="tags"),
    path("", views.BlogListView.as_view(), name="post_list"),
    path("tags", views.tag_list, name="tags"),
    path("tag/<str:tag>", views.TagPostListView.as_view(), name="tag"),
    #path("category/<str:category>", views.CategoryPostListView.as_view(), name="category"),
    path("categories", views.category_list, name="categories"),    
    path("<str:slug>", views.BlogDetailView.as_view(), name="post_detail"),
]
