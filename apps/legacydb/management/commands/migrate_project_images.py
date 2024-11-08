import os
import math
import base64
from pathlib import Path
from django.conf import settings
from django.db.utils import IntegrityError
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.utils.text import slugify
from django.db import connection
from django.apps import apps

from apps.users.models import User
from apps.legacydb.models import Projects as OldProject
from apps.legacydb.models import Likes as OldLikes
from apps.legacydb.models import Comments as OldComment
from apps.projects.models import Project, Category, Like, Comment, Remix
from apps.projects.models import Image as ProjectImage


class Command(BaseCommand):
    help = "Migrate old project data"

    def handle(self, **options):        
        migrate_project_images()


def migrate_project_images():
    print("migrating project images")
    # count = len(list(Path(  'migrations/projects/images/old/base64' ).rglob( '*.png' )))

    path = settings.MEDIA_ROOT / "projects/images/old/base64"
    for i, filename in enumerate(path.rglob("*.png")):
        # print(i, "import", filename)
        project_id = int(os.path.basename(os.path.dirname(filename)))
        print(i, "import", filename)
        try:
            project = Project.objects.get(id=project_id)
            with open(filename) as f:
                content = f.readlines()
                if content:
                    imgformat, imgstr = content[0].split(";base64,")
                    new_filename = str(filename).replace("base64", "png")

                    Path(os.path.dirname(new_filename)).mkdir(
                        parents=True, exist_ok=True
                    )
                    with open(new_filename, "wb") as o:
                        o.write(base64.b64decode(imgstr))
                    image, created = ProjectImage.objects.get_or_create(
                        project=project,
                        order=0,
                        file=new_filename.replace(str(settings.MEDIA_ROOT) + "/", ""),
                    )
        except ObjectDoesNotExist:
            print("project #", project_id, "does not exist")

    print("\nDone.")
