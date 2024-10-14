import json
import math
from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder
from django.apps import apps
from wagtail.models import Page, Site

from apps.content.models import ContentPage


def _text_to_stream_value(text):
    return json.dumps([{"type": "paragraph", "value": text}], cls=DjangoJSONEncoder)


def save_page(index_page, page):
    index_page.add_child(instance=page)
    page.save()
    revision = page.save_revision()
    revision.publish()


class Command(BaseCommand):
    help = "Migrate old accounts "

    def handle(self, **options):
        migrate_pages()


def migrate_pages():
    print("Migrating old pages..")

    root_page = Page.objects.get(slug="root").specific
    try:
        landing_page = ContentPage.objects.get(slug="content")
        print("Using existing content homepage...")
    except ContentPage.DoesNotExist:
        print("Creating your content homepage...")
        landing_page = ContentPage(
            slug="content",
            title="Welcome to your content area!",
            body=_text_to_stream_value(
                "This is where your content pages will live. You can create more pages here. "
                'Everything here can be edited in <a href="/cms">the content admin</a>.'
            ),
        )
        root_page.add_child(instance=landing_page)
        landing_page.save()

    site = Site.objects.get()
    site.root_page = landing_page
    site.save()

    OldPage = apps.get_model("legacydb", "Pages")
    count = OldPage.objects.using("legacydb").count()
    pages = math.ceil(count / 100)
    print(f"  .. total objects: {count} ({pages})..", end="\n")

    for ii in range(0, pages + 1):
        for i, old_object in enumerate(
            OldPage.objects.using("legacydb")[(ii * 100) : ((ii + 1) * 100)]
        ):
            progress = ((ii * 100 + i + 1) / count) * 100
            counter = (ii * 100 + i) + 1
            print(f"\r  .. {(progress):.1f}% ({counter})..", end="")

            try:
                new_page = ContentPage.objects.get(slug=old_object.slug)
            except ContentPage.DoesNotExist:
                print("Creating new page...")
                new_page = ContentPage(
                    slug=old_object.slug,
                    title=old_object.title,
                    body=_text_to_stream_value(old_object.content),
                )

                save_page(landing_page, new_page)

    print("\nDone.")
