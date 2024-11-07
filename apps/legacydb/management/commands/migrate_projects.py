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
        migrate_projects()

        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT setval(pg_get_serial_sequence(\'"projects_project"\',\'id\'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "projects_project";'
            )
            # cursor.execute("SELECT setval(pg_get_serial_sequence('projects_project', 'id'), (select max(id) from projects_project) + 1);")

        migrate_likes()

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT setval(pg_get_serial_sequence('projects_like', 'id'), (select max(id) from projects_like) + 1);"
            )

        migrate_comments()
        migrate_project_images()

def migrate_projects():
    print("migrating projects ..")
    projects = OldProject.objects.using("legacydb").order_by("id")
    p = Paginator(projects, 100)    
    print(f"  .. total objects: {p.count} ({p.num_pages})..")
    i = 0
    for page_num in p.page_range:
        page = p.page(page_num)
        for old_project in page:
            i += 1
            progress = (i / p.count) * 100
            print(f"\r  .. {(progress):.1f}% ({i})..", end="", flush=True)

            new_project, created = Project.objects.get_or_create(id=old_project.id)

            if len(old_project.projectname) > 255:
                print(f" - truncating {old_project.projectname} to 255 chars ..")
                old_project.projectname = old_project.projectname[:255]

            # if len(old_project.projectname.strip()) < 1:
            #     print("- setting empty name to noname")
            #     old_project.projectname = "no name - " + shortuuid.uuid()[:6]

            if "\n" in old_project.projectname:
                print(f" - replacing linebreaks with -- in {old_project.projectname} by {old_project.username}")
                old_project.projectname = old_project.projectname.replace("\n", "--")

            # if old_project.projectname.endswith(
            #     " "
            # ) or old_project.projectname.startswith(" "):
            #     if old_project.projectname.startswith(" "):
            #         print(old_project.projectname, " - starts with whitespace")
            #     else:
            #         print(old_project.projectname, " - ends with whitespace")
            #     old_project.projectname = (
            #         old_project.projectname.strip() + " - " + shortuuid.uuid()[:6]
            #     )
            
            # print(f"..{old_project.projectname} by {old_project.username}")
            new_project.name = old_project.projectname

            new_project.slug = slugify(old_project.projectname, allow_unicode=True)
            new_project.notes = old_project.notes
            new_project.date_created = old_project.created or old_project.updated
            new_project.date_updated = old_project.updated or old_project.created

            new_project.is_public = old_project.ispublic
            new_project.is_published = old_project.ispublic
            new_project.image_is_featured = old_project.imageisfeatured or False
            new_project.last_shared = old_project.shared
            new_project.views = old_project.views or 0
            new_project.user = User.objects.get(username=old_project.username)

            # new_project.update_embeddings()
            new_project.project_file.save(
                new_project.slug + ".xml", ContentFile(old_project.contents)
            )
            new_project.date_updated = old_project.updated or old_project.created

            if old_project.thumbnail is not None and old_project.thumbnail != "":
                imgformat, imgstr = old_project.thumbnail.split(";base64,")
                ext = imgformat.split("/")[-1]
                data = ContentFile(base64.b64decode(imgstr))
                file_name = f"{new_project.slug}.{ext}"
                new_project.thumbnail.save(file_name, data, save=True)

            if old_project.origcreator and old_project.origname:
                # new_project.remixed_from = orig_project
                try:
                    orig_project = Project.objects.get(
                        id=OldProject.objects.using("legacydb")
                        .get(
                            projectname=old_project.origname,
                            username=old_project.origcreator,
                        )
                        .id
                    )

                    new_remix, created = Remix.objects.get_or_create(
                        original_project=orig_project,
                        remixed_project=new_project,
                        date_created=old_project.created or old_project.updated,
                    )
                    new_remix.save()
                except ObjectDoesNotExist:
                    # print(
                    #     f"  .. error finding project: {old_project.origname} from {old_project.origcreator}"
                    # )
                    pass

            if old_project.categories:
                tagstr = old_project.categories.replace("undefined", "")
                tagstr = tagstr.replace(";", ",")
                tagstr = tagstr.replace("#", ",")
                categories = tagstr.split(",")

                for c in categories:
                    if c.strip() != "undefined" and len(c.strip()) > 1:
                        name = c.strip().lower().capitalize()
                        cat, created = Category.objects.get_or_create(
                            name=name, slug=slugify(c.strip(), allow_unicode=True)
                        )
                        new_project.categories.add(cat)

            if old_project.tags:
                tagstr = old_project.tags.replace("undefined", "")
                tagstr = tagstr.replace(";", ",")
                tagstr = tagstr.replace("#", ",")
                tags = tagstr.split(",")

                Tag = apps.get_model("taggit", "Tag")
                TaggedItem = apps.get_model("taggit", "TaggedItem")
                ContentType = apps.get_model("contenttypes", "ContentType")
                MyModel = apps.get_model("projects", "project")
                ct = ContentType.objects.get_for_model(MyModel)

                new_tags = ""
                for t in tags:
                    if t.strip() != "undefined" and len(t.strip()) > 1:
                        tag_name = t.strip().lower()
                        tag_slugged = slugify(tag_name, allow_unicode=True)
                        t, created = Tag.objects.get_or_create(
                            # name=tag_name, slug=slugify(tag_name, allow_unicode=True)
                            name=tag_slugged,
                            slug=tag_slugged,
                        )
                        tagged_items, created = TaggedItem.objects.get_or_create(
                            content_type_id=ct.id, object_id=new_project.id, tag=t
                        )
                        new_tags += "#" + tag_slugged + " "
                new_project.notes = new_project.notes + "\n\n\n" + new_tags
            new_project.date_updated = old_project.updated or old_project.created
            new_project.save(no_timestamp=True)
    print("\nDone.")


def migrate_likes():
    print("migrating likes")
    likes = OldLikes.objects.using("legacydb").order_by("id")
    p = Paginator(likes, 100)    
    print(f"  .. total objects: {p.count} ({p.num_pages})..")
    i = 0
    for page_num in p.page_range:
        page = p.page(page_num)
        for old_object in page:
            i += 1
            progress = (i / p.count) * 100
            print(f"\r  .. {(progress):.1f}% ({i})..", end="", flush=True)

            try:
                new_object, created = Like.objects.get_or_create(
                    id=old_object.id,
                    liker=User.objects.get(username=old_object.liker),
                    project=Project.objects.get(
                        name=old_object.projectname,
                        user=User.objects.get(username=old_object.projectowner),
                    ),
                )
            except IntegrityError:
                print("error: duplicate like?")
            except Project.DoesNotExist:
                print("error: project does not exist")

            new_object.liker = User.objects.get(username=old_object.liker)

    print("\nDone.")


def migrate_comments():
    print("migrating comments ..", end="\n")
    comments = OldComment.objects.using("legacydb").order_by("id")
    p = Paginator(comments, 100)    
    print(f"  .. total objects: {p.count} ({p.num_pages})..")
    i = 0
    for page_num in p.page_range:
        page = p.page(page_num)
        for old_object in page:
            i += 1
            progress = (i / p.count) * 100
            print(f"\r  .. {(progress):.1f}% ({i})..", end="", flush=True)

            try:
                new_object, created = Comment.objects.get_or_create(
                    author=User.objects.get(username=old_object.author),
                    project=Project.objects.get(
                        name=old_object.projectname,
                        user=User.objects.get(username=old_object.projectowner),
                    ),
                )
                new_object.contents = old_object.contents
                new_object.date_created = old_object.date
                new_object.date_modified = old_object.date
                new_object.save()
            except IntegrityError:
                print("error: duplicate comment?")
            except Project.DoesNotExist:
                print("error: project does not exist")

    print("\nDone.")


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
