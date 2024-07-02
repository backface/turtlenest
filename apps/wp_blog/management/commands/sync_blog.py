import requests
from django.conf import settings
from django.core.management.base import BaseCommand


from apps.wp_blog.models import Post, Tag, Media, Author, Category


class Command(BaseCommand):
    help = "Sync wordpress blog"

    def handle(self, **options):
        print("Syncing WP Authors..")
        sync_authors()
        print("Syncing WP Tags..")
        sync_tags()
        print("Syncing WP Categories..")
        sync_categories()
        print("Syncing WP Media..")
        sync_media()        
        print("Syncing WP Blog post..")
        sync_posts()



def sync_authors():    
    response = requests.get(f"{settings.WORDPRESS_API}/users")
    for i in range(1, int(response.headers['x-wp-total'])+1):
        if i > 1:
            response = requests.get(f"{settings.WORDPRESS_API}/users?page={i}")
        objects = response.json()
        for obj in objects:
            author, created = Author.objects.get_or_create(
                id=int(obj["id"]),
            )
            author.name = obj["name"]
            author.save()


def sync_tags():    
    response = requests.get(f"{settings.WORDPRESS_API}/tags")
    for i in range(1, int(response.headers["X-WP-TotalPages"])+1):
        if i > 1:
            response = requests.get(f"{settings.WORDPRESS_API}/tags?page={i}")
        objects = response.json()
        for obj in objects:
            tag, created = Tag.objects.get_or_create(
                id=int(obj["id"]),
            )
            tag.name = obj["name"]
            tag.slug = obj["slug"]
            tag.count = obj["count"]
            tag.description = obj["description"]
            tag.save()


def sync_categories():    
    response = requests.get(f"{settings.WORDPRESS_API}/categories")
    for i in range(1, int(response.headers["X-WP-TotalPages"])+1):
        if i > 1:
            response = requests.get(f"{settings.WORDPRESS_API}/categories?page={i}")
        objects = response.json()
        for obj in objects:
            cat, created = Category.objects.get_or_create(
                id=int(obj["id"]),
            )
            cat.name = obj["name"]
            cat.slug = obj["slug"]
            cat.count = obj["count"]
            cat.description = obj["description"]
            cat.save()


def sync_media():    
    response = requests.get(f"{settings.WORDPRESS_API}/media")
    for i in range(1, int(response.headers["X-WP-TotalPages"])+1):
        if i > 1:
            response = requests.get(f"{settings.WORDPRESS_API}/media?page={i}")
        objects = response.json()
        if response.status_code == 200:
            for obj in objects:
                media, created = Media.objects.get_or_create(
                    id=int(obj["id"]),
                )
                media.guid = obj["guid"]["rendered"]
                media.title = obj["title"]["rendered"]
                media.slug = obj["slug"]
                media.description = obj["description"]["rendered"]
                media.caption = obj["caption"]["rendered"]
                media.alt_text = obj["alt_text"]
                media.media_type = obj["media_type"]
                media.mime_type = obj["mime_type"]
                media.media_details = obj["media_details"]
                media.save()
        else:
            print(response.status_code, objects)


def sync_posts():    
    response = requests.get(f"{settings.WORDPRESS_API}/posts")
    for i in range(1, int(response.headers["X-WP-TotalPages"])+1):
        if i > 1:
            response = requests.get(f"{settings.WORDPRESS_API}/posts?page={i}")
        objects = response.json()
        for obj in objects:
            post, created = Post.objects.get_or_create(
                id=int(obj["id"]),
            )
            post.title = obj["title"]["rendered"]
            post.slug = obj["slug"]
            post.content = obj["content"]["rendered"]
            post.excerpt = obj["excerpt"]["rendered"]
            post.date = obj["date"]
            post.status = obj["status"]
            post.modified = obj["modified"]
            post.featured_media_id = obj["featured_media"]
            post.author_id = obj["author"]
            post.save()

            post.tags.clear()
            print(obj["tags"])
            for tag_id in obj["tags"]:
                print(tag_id)
                tag = Tag.objects.get(id=tag_id)
                post.tags.add(tag.name)