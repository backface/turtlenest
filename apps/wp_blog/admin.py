from django.contrib import admin
from .models import Post, Author, Tag, Media, Category

admin.site.register(Post)
admin.site.register(Author)
admin.site.register(Tag)
admin.site.register(Category)
admin.site.register(Media)
