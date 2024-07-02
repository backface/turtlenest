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
        if not options["target"] or (
            options["target"] and options["target"] == "files"
        ):
            update_file_embeddings(replace)


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
            if not type(project.embedding_project_meta) == type(None):
                if len(project.embedding_project_meta) == 1024:
                    continue

            progress = ((ii * 100 + i) / count) * 100
            counter = (ii * 100 + i) + 1
            print(f"\r  .. {(progress):.1f}% ({counter})..", end="", flush=True)

            project.update_embeddings()
            project.save(no_timestamp=True)

    print("\nDone.")


def update_file_embeddings(replace=False):
    print("updating project file embeddings.")

    if replace:
        objects = Project.objects.all()
    else:
        objects = Project.objects.filter(embedding_project_file__isnull=True)

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

            with open(
                str(settings.MEDIA_ROOT) + "/" + project.project_file.name, "r"
            ) as f:
                contents = f.read()
                soup = BeautifulSoup(contents, "xml")
                for th in soup.find_all("thumbnail"):
                    th.replaceWith("")
                for th in soup.find_all("pentrails"):
                    th.replaceWith("")
                for th in soup.find_all("costumes"):
                    th.replaceWith("")

                cleaned_project_str = soup.prettify()

                project.embedding_project_fil = get_embeddings(
                    cleaned_project_str, "mxbai-embed-large"
                )
                project.save()
    print("\nDone.")
