"""Remove stale unverified accounts.

Dry run by default; pass --commit to change anything. Meant to run daily,
e.g. from cron on the deploy host:

    docker compose exec -T django python manage.py cleanup_unverified \\
        --verify-with-projects --commit
"""

from allauth.account.models import EmailAddress
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Exists, OuterRef
from django.utils import timezone

from apps.users.models import User
from apps.users.verification import mark_verified

BATCH = 500


def unverified_users():
    verified = EmailAddress.objects.filter(user=OuterRef("pk"), verified=True)
    return User.objects.filter(~Exists(verified))


def without_related_rows(qs):
    """Exclude users that anything else points at (projects, comments,
    groups they host, pupils they mentor, ...). Deleting such a user would
    cascade into other data; only the e-mail address rows are expendable."""
    for rel in User._meta.related_objects:
        model = rel.related_model
        if model is EmailAddress:
            continue
        if rel.many_to_many:
            through = rel.through
            fk = next(
                f.name
                for f in through._meta.get_fields()
                if getattr(f, "related_model", None) is User
            )
            rows = through.objects.filter(**{fk: OuterRef("pk")})
        else:
            rows = model.objects.filter(**{rel.field.name: OuterRef("pk")})
        qs = qs.filter(~Exists(rows))
    return qs


class Command(BaseCommand):
    help = (
        "Delete unverified accounts that never logged in and own nothing; "
        "optionally mark unverified accounts with projects as verified. "
        "Dry run unless --commit is given."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="only delete accounts that joined more than DAYS ago (default 30)",
        )
        parser.add_argument(
            "--verify-with-projects",
            action="store_true",
            help="mark unverified accounts that own at least one project as verified",
        )
        parser.add_argument(
            "--commit", action="store_true", help="actually change the database"
        )

    def handle(self, *args, days, verify_with_projects, commit, verbosity, **options):
        mode = "" if commit else "[dry run] "

        if verify_with_projects:
            with_projects = unverified_users().filter(project__isnull=False).distinct()
            count = with_projects.count()
            if verbosity > 1:
                for user in with_projects:
                    self.stdout.write(f"  verify {user.username} <{user.email}>")
            if commit:
                count = sum(mark_verified(user) for user in with_projects)
            self.stdout.write(f"{mode}verified {count} account(s) with projects")

        cutoff = timezone.now() - timezone.timedelta(days=days)
        stale = without_related_rows(
            unverified_users().filter(
                date_joined__lt=cutoff,
                last_login__isnull=True,
                is_staff=False,
                is_superuser=False,
                groups__isnull=True,  # no Teachers/Puppets/Editors/... role
            )
        )
        ids = list(stale.values_list("pk", flat=True))
        if verbosity > 1:
            for user in User.objects.filter(pk__in=ids).order_by("date_joined"):
                self.stdout.write(f"  delete {user.username} (joined {user.date_joined:%Y-%m-%d})")
        if commit:
            for i in range(0, len(ids), BATCH):
                with transaction.atomic():
                    User.objects.filter(pk__in=ids[i : i + BATCH]).delete()
        self.stdout.write(
            f"{mode}deleted {len(ids)} unverified account(s) older than {days} days "
            "that never logged in and own nothing"
        )
