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
        fix_features()

def fix_features():
    """
    Fix feature images
    """

    projects = Project.objects.filter(image_is_featured=1)
    for project in projects:
        if len(project.image_set.all()) == 1:
            #print(project.image_set.all()[0].id)
            print("updating", project.name, "image:", project.image_set.all()[0].id)
            project.image_is_featured = project.image_set.all()[0].id
            project.save(no_timestamp=True)
