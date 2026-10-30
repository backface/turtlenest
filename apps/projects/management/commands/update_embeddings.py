import math
from django.core.management.base import BaseCommand

from apps.projects.models import Project


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

    # fetch ids up front: saving removes projects from the isnull filter,
    # so offset-based paging over the queryset would skip projects
    ids = list(objects.order_by("id").values_list("id", flat=True))
    count = len(ids)
    pages = math.ceil(count / 100)

    print(f"  .. total objects: {count} ({pages})..")
    for ii in range(pages):
        page_ids = ids[(ii * 100) : ((ii + 1) * 100)]
        for i, project in enumerate(Project.objects.filter(id__in=page_ids).order_by("id")):
            counter = ii * 100 + i + 1
            progress = (counter / count) * 100
            print(f"\r  .. {(progress):.1f}% ({counter})..", end="", flush=True)

            project.update_embeddings()
            project.save(no_timestamp=True)

    print("\nDone.")
