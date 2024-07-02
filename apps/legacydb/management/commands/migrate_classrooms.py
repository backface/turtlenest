import math
from django.utils import timezone
from django.db.utils import IntegrityError
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.db import migrations
from django.db import connection
from django.apps import apps

from apps.users.models import User


class Command(BaseCommand):
    help = "Migrate classrooms "

    def handle(self, **options):
        migrate_classrooms()
        with connection.cursor() as cursor:
            cursor.execute("SELECT setval(pg_get_serial_sequence('classrooms_group', 'id'), (select max(id) from classrooms_group) + 1);")
        migrate_members()
        with connection.cursor() as cursor:
            cursor.execute("SELECT setval(pg_get_serial_sequence('classrooms_membership', 'id'), (select max(id) from classrooms_membership) + 1);")
        migrate_units()
        with connection.cursor() as cursor:
            cursor.execute("SELECT setval(pg_get_serial_sequence('classrooms_unit', 'id'), (select max(id) from classrooms_unit) + 1);")
        migrate_projects()
        with connection.cursor() as cursor:
            cursor.execute("SELECT setval(pg_get_serial_sequence('classrooms_selectedproject', 'id'), (select max(id) from classrooms_selectedproject) + 1);")


def migrate_classrooms():
    print("migrating classrooms ..", end="\n")
    OldClass = apps.get_model("legacydb", "Classrooms")
    Group = apps.get_model("classrooms", "Group")

    count = OldClass.objects.using("legacydb").count()
    pages = math.ceil(count / 100)
    print(f"  .. total objects: {count} ({pages})..", end="\n")

    for ii in range(0, pages):
        for i, old_object in enumerate(
            OldClass.objects.using("legacydb")[(ii * 100) : ((ii + 1) * 100)]
        ):
            progress = ((ii * 100 + i) / count) * 100
            counter = (ii * 100 + i) + 1
            print(f"\r  .. {(progress):.1f}% ({counter})..", end="")

            new_object, created = Group.objects.get_or_create(
                id=old_object.id, host=User.objects.get(username=old_object.host)
            )
            new_object.title = old_object.title
            new_object.slug = slugify(old_object.title, allow_unicode=True)
            new_object.current_unit = old_object.current_unit
            new_object.description = old_object.description
            new_object.introduction = old_object.introduction
            new_object.date_created = old_object.created_at or timezone.now()
            new_object.date_modified = old_object.updated_at or timezone.now()
            new_object.save()
    print("\ndone")


def migrate_members():
    print("migrating members..", end="\n")
    OldObject = apps.get_model("legacydb", "ClassroomMembers")
    Group = apps.get_model("classrooms", "Group")
    MemberShip = apps.get_model("classrooms", "MemberShip")

    count = OldObject.objects.using("legacydb").count()
    pages = math.ceil(count / 100)
    print(f"  .. total objects: {count} ({pages})..", end="\n")

    for ii in range(0, pages):
        for i, old_object in enumerate(
            OldObject.objects.using("legacydb")[(ii * 100) : ((ii + 1) * 100)]
        ):
            progress = ((ii * 100 + i) / count) * 100
            counter = (ii * 100 + i) + 1
            print(f"\r  .. {(progress):.1f}% ({counter})..", end="")

            new_object, created = MemberShip.objects.get_or_create(
                id=old_object.id,
                user=User.objects.get(username=old_object.username),
                is_hosting=old_object.is_teaching,
                group=Group.objects.get(id=old_object.classroom_id),
            )
            new_object.date_created = old_object.created_at or timezone.now()
            new_object.date_modified = old_object.updated_at or timezone.now()
            new_object.save()
    print("\ndone")


def migrate_units():
    print("migrating units..", end="\n")
    OldObject = apps.get_model("legacydb", "ClassroomUnits")
    Group = apps.get_model("classrooms", "Group")
    Unit = apps.get_model("classrooms", "Unit")

    count = OldObject.objects.using("legacydb").count()
    pages = math.ceil(count / 100)
    print(f"  .. total objects: {count} ({pages})..", end="\n")

    for ii in range(0, pages):
        for i, old_object in enumerate(
            OldObject.objects.using("legacydb")[(ii * 100) : ((ii + 1) * 100)]
        ):
            progress = ((ii * 100 + i) / count) * 100
            counter = (ii * 100 + i) + 1
            print(f"\r  .. {(progress):.1f}% ({counter})..", end="")

            try:
                new_object, created = Unit.objects.get_or_create(
                    id=old_object.id, group=Group.objects.get(id=old_object.classroom_id)
                )
                new_object.title = old_object.title
                new_object.slug = slugify(old_object.title, allow_unicode=True)
                new_object.number = old_object.number
                new_object.date_created = old_object.created_at or timezone.now()
                new_object.date_modified = old_object.updated_at or timezone.now()
                new_object.save()
            except IntegrityError:
                print("error: duplicate entry?")                
            except Group.DoesNotExist:
                print("error: group does not exist")   

    print("\ndone")


def migrate_projects():
    print("migrating project selections..", end="\n")
    OldObject = apps.get_model("legacydb", "ClassroomProjects")
    Group = apps.get_model("classrooms", "Group")
    ProjectSelection = apps.get_model("classrooms", "SelectedProject")
    Unit = apps.get_model("classrooms", "Unit")

    count = OldObject.objects.using("legacydb").count()
    pages = math.ceil(count / 100)
    print(f"  .. total objects: {count} ({pages})..", end="\n")

    for ii in range(0, pages):
        for i, old_object in enumerate(
            OldObject.objects.using("legacydb")[(ii * 100) : ((ii + 1) * 100)]
        ):
            progress = ((ii * 100 + i) / count) * 100
            counter = (ii * 100 + i) + 1
            print(f"\r  .. {(progress):.1f}% ({counter})..", end="")

            try:
                new_object, created = ProjectSelection.objects.get_or_create(
                    id=old_object.id,
                    project_id=old_object.project_id,
                    is_starter=old_object.is_starter,
                    group=Group.objects.get(id=old_object.classroom_id)
                    if old_object.classroom_id
                    else None,
                    unit=Unit.objects.get(id=old_object.unit) if old_object.unit else None,
                )
                new_object.date_created = old_object.created_at or timezone.now()
                new_object.date_modified = old_object.updated_at or timezone.now()
                new_object.save()
            except IntegrityError:
                print("error: duplicate entry?")                
            except Group.DoesNotExist:
                print("error: group does not exist")   
            except Unit.DoesNotExist:
                print("error: unit does not exist") 

    print("\nDone.")
