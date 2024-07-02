from django.contrib.syndication.views import Feed
from django.shortcuts import render, get_object_or_404
from django.utils.feedgenerator import Atom1Feed
from .models import Post


ENTRIES_ON_HOMEPAGE = 5


def index(request):
    entries = list(
        Post.objects.filter(is_draft=False).order_by("-created")[
            : ENTRIES_ON_HOMEPAGE + 1
        ]
    )
    has_more = False
    if len(entries) > ENTRIES_ON_HOMEPAGE:
        has_more = True
        entries = entries[:ENTRIES_ON_HOMEPAGE]
    return render(request, "blog/index.html", {"posts": entries, "has_more": has_more})


def post(request, year, slug):
    post = get_object_or_404(Post, created__year=year, slug=slug)
    return render(
        request,
        "blog/entry.html",
        {"post": post},
    )


def year(request, year):
    entries = Post.objects.filter(created__year=year, is_draft=False).order_by(
        "-date_created"
    )
    return render(request, "blog/year.html", {"posts": entries, "year": year})


def archive(request):
    entries = Post.objects.filter(is_draft=False).order_by("-date_created")
    return render(request, "blog/archive.html", {"posts": entries})


class BlogFeed(Feed):
    title = "TurtleStitch Cloud"
    link = "/blog/"
    feed_type = Atom1Feed

    def items(self):
        return Post.objects.filter(is_draft=False).order_by("-date_created")[:5]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.summary_rendered + "\n" + item.body_rendered

    def item_link(self, item):
        return "/blog/%d/%s/" % (item.created.year, item.slug)

    def item_author_name(self, item):
        return (
            ", ".join([a.get_full_name() or str(a) for a in item.authors.all()]) or None
        )

    def get_feed(self, obj, request):
        feedgen = super().get_feed(obj, request)
        feedgen.content_type = "application/xml; charset=utf-8"
        return feedgen
