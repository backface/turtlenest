import requests
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from .models import Post, Tag

# def list(request):
#     url = settings.WORDPRESS_API + '/posts'
#     response = requests.get(url)  #
#     posts = response.json()

#     # for post in posts:
#     #     BlogPost.objects.update_or_create(
#     #         title=post['title']['rendered'],  # assuming the API provides 'title' key with rendered HTML content, change according to your WordPress REST API documentation
#     #         content=post['content']['rendered']  # same as above for 'content' field
#     #     )
#     # posts = BlogPost.objects.all()

#     return render(request, 'wp_blog/blog_list.html', {'posts': posts})


def index(request):
    return list(request)

class BlogDetailView(DetailView):
    model = Post
    template_name = "blog/blog_detail.html"

class BlogListView(ListView):
    model = Post
    paginate_by = 9
    template_name = "blog/blog_list.html"

    # def get_queryset(self):
    #     return Post.objects.filter(members=self.request.user)

class TagListView(DetailView):
    model = Tag
    template_name = "blog/tag_list.html"


class TagPostListView(ListView):
    template_name = "blog/blog_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag"] = self.tag
        return context
    
    def get_queryset(self):
        self.tag = get_object_or_404(Tag, slug=self.kwargs["tag"])
        return Post.objects.filter(tags__slug__in=[self.kwargs["tag"]]) 


# def list(request, tag=0):
#     if tag:
#         response = requests.get(f"{settings.WORDPRESS_API}/posts?tags={tag}")
#         tag = requests.get(f"{settings.WORDPRESS_API}/tags/{tag}").json()
#     else:
#         response = requests.get(f"{settings.WORDPRESS_API}/posts")
#     posts = response.json()
#     if response.status_code != 200:
#         posts = []
#     return render(request, "wp_blog/blog_list.html", {"posts": posts, "tag": tag})


# def detail(request, id):
#     # post = BlogPost.objects.get(pk=pk)
#     response = requests.get(f"{settings.WORDPRESS_API}/posts/{id}")
#     post = response.json()
#     try:
#         author = requests.get(f"{settings.WORDPRESS_API}/users/{post['author']}").json()
#     except Exception as e:
#         print(e)
#         author = None
#     try:
#         tags = requests.get(f"{settings.WORDPRESS_API}/tags?post={post['id']}").json()
#     except Exception as e:
#         print(e)
#         tags = None
#     return render(
#         request, "wp_blog/blog_detail.html", {"post": post, "author": author, "tags": tags}
#     )


# def tags(request):
#     response = requests.get(f"{settings.WORDPRESS_API}/tags")
#     tags = response.json()

#     if response.status_code != 200:
#         tags = []

#     return render(request, "wp_blog/blog_tags.html", {"tags": tags})
