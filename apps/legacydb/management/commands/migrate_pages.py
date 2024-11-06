import math
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.core.paginator import Paginator
from django.db import migrations
from django.apps import apps

from apps.pages.models import Page
from apps.users.models import User


class Command(BaseCommand):
    help = "Migrate old accounts "

    def handle(self, **options):
        migrate_data()
        migrations.RunSQL(
            "SELECT setval(pg_get_serial_sequence('pages_page','id'), (select max(id) from classrooms_group) + 1);"
        )


def migrate_data():
    print("Migrating old pages..")
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
            new_object, created = Page.objects.get_or_create(id=old_object.id)
            new_object.title = old_object.title
            new_object.slug = old_object.slug
            new_object.date_created = old_object.last_edit_at or timezone.now()
            new_object.date_modified = old_object.last_edit_at or timezone.now()
            try:
                new_object.last_editor = User.objects.get(
                    username=old_object.last_edit_by
                )
            except User.DoesNotExist:
                new_object.last_editor = None

            new_object.content = old_object.content
            new_object.save()

    print("\nDone.")
