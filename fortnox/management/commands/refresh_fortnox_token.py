from django.conf import settings
from django.core.management.base import BaseCommand

from fortnox import FortnoxAPIClient
from fortnox.django import retrieve_or_refresh_token
from fortnox.models import APIUser


class Command(BaseCommand):
    help = "Refresh the Fortnox service account access token."

    def handle(self, *args, **options):
        if not APIUser.objects.exists():
            self.stdout.write(self.style.WARNING("No Fortnox service account configured; nothing to refresh."))
            return

        client = FortnoxAPIClient(
            client_id=settings.FORTNOX_CLIENT_ID,
            client_secret=settings.FORTNOX_CLIENT_SECRET,
            scope=settings.FORTNOX_SCOPE,
        )
        token = retrieve_or_refresh_token(client)
        if token is None:
            self.stderr.write(self.style.ERROR("Failed to refresh Fortnox token; tokens may be expired."))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS("Fortnox token refreshed."))
