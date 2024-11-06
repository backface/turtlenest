from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.db import migrations
from django.core.paginator import Paginator
import math

from apps.users.models import User
from apps.legacydb.models import Users as OldUser
from allauth.account.models import EmailAddress


class Command(BaseCommand):
    help = "Migrate old accounts "

    def handle(self, **options):
        create_groups()
        migrate_userdata()
        migrations.RunSQL(
            'SELECT setval(pg_get_serial_sequence(\'"users_user"\',\'id\'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "users_user";'
        )

def create_groups():
    for g in [
        "Teachers",
        "Moderators",
        "Puppets",
    ]:
        obj, created = Group.objects.get_or_create(name=g)


def migrate_userdata():
    print("migrating user data ..", end="\n")
    oldusers = OldUser.objects.order_by("joined", "id").using("legacydb")
    p = Paginator(oldusers, 100)    
    print(f"  .. total objects: {p.count} ({p.num_pages})..")
    i = 0
    for page_num in p.page_range:
        page = p.page(page_num)
        for person in page:
            i += 1
            progress = (i / p.count) * 100
            print(f"\r  .. {(progress):.1f}% ({i})..", end="", flush=True)

            new_user, created = User.objects.get_or_create(
                username=person.username,
                email=person.email if person.email else f"{person.username}@turtlestitch.org"
            )
            # new_user.email = (
            #     person.email if person.email else f"{person.username}@turtlestitch.org"
            # )

            if person.username == "group13tobyh":
                print(f"\n{person.username}")
            
            # password is hashed in the legacy database, so we need to add 'crypt$21$' prefix for Django to recognize it as a bcrypt hash. 
            # This might be different depending on your setup and how you handle passwords in Django.
            new_user.password = "crypt$21$" + person.password
            new_user.date_joined = person.joined
            new_user.last_login = person.last_active
            new_user.about = person.about
            new_user.location = person.location.replace("Click to edit your location.", "") if person.location else ""
            new_user.notify_comment = person.notify_comment
            new_user.notify_like = person.notify_like
            new_user.verified = person.confirmed
            new_user.is_mentor = person.is_teacher
            new_user.save()

            new_account, created = EmailAddress.objects.get_or_create(
                user=new_user,
                email=new_user.email
            )
            new_account.verified = person.confirmed
            new_account.primary = True
            new_account.save()

            if person.has_teacher:
                try: 
                    teacher = User.objects.get(username=person.has_teacher)
                except User.DoesNotExist:
                    print("Teacher not found", person.has_teacher, "for", person.username)
                    raise Exception("Teacher not found")
                else:
                    new_user.mentor = (
                        User.objects.get(username=person.has_teacher)
                        if person.has_teacher
                        else None
                    )
            if person.isadmin:
                new_user.is_staff = True
            if person.ismoderator:
                new_user.groups.add(Group.objects.get(name="Moderators").id)
            if person.is_teacher:
                new_user.groups.add(Group.objects.get(name="Teachers").id)
            if person.is_puppet:
                new_user.groups.add(Group.objects.get(name="Puppets").id)

            if new_user.username == "mash":
                new_user.is_superuser = True
            if new_user.username == "chmod":
                new_user.is_superuser = True

            new_user.save()


            # if person.username == "group13tobyh":
            #     print(f"\n{person.username}")

    print("\nDone.")
