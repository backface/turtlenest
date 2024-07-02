from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "migrate all legacy data"

    def handle(self, *args, **options):
        self.stdout.write("migrate all legacy data")
        call_command(
            "migrate_accounts",
        )
        call_command(
            "migrate_projects",
        )
        call_command(
            "migrate_classrooms",
        )
        # call_command(
        #     "migrate_pages",
        # )
        call_command(
            "migrate_pages2wagtail",
        )
