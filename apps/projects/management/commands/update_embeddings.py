import math
from django.core.management.base import BaseCommand
from django.conf import settings
from bs4 import BeautifulSoup

from apps.projects.models import Project
from apps.projects.models import create_embeddings


class Command(BaseCommand):
    help = "Update/create project embeddings"

    def add_arguments(self, parser):
        parser.add_argument("--replace", action="store_true")
        parser.add_argument("--target", type=str)

    def handle(self, **options):
        replace = False
        if options["replace"]:
            replace = True

        if not options["target"] or (options["target"] and options["target"] == "meta"):
            update_embeddings(replace)

def update_embeddings(replace=False):
    print("updating  project embedding.")

    if replace:
        objects = Project.objects.all()
    else:
        objects = Project.objects.filter(embedding_project_meta__isnull=True)

    count = objects.count()
    pages = math.ceil(count / 100)

    print(f"  .. total objects: {count} ({pages})..")
    for ii in range(0, pages + 1):
        for i, project in enumerate(
            objects.order_by("id")[(ii * 100) : ((ii + 1) * 100)]
        ):
            progress = ((ii * 100 + i) / count) * 100
            counter = (ii * 100 + i) + 1
            print(f"\r  .. {(progress):.1f}% ({counter})..", end="", flush=True)

            project.update_embeddings()
            project.save(no_timestamp=True)

    print("\nDone.")