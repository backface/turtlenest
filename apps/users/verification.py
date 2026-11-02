"""E-mail verification for the API: a grace period for new accounts, and
saving a project counts as verification."""

import math

from allauth.account.models import EmailAddress
from django.conf import settings
from django.utils import timezone


def grace_days():
    return getattr(settings, "UNVERIFIED_GRACE_DAYS", 3)


def days_left(user):
    """Whole days (rounded up) left in the grace period, 0 when it is over."""
    end = user.date_joined + timezone.timedelta(days=grace_days())
    seconds = (end - timezone.now()).total_seconds()
    return max(0, math.ceil(seconds / 86400))


def mark_verified(user):
    """Mark the user's current e-mail address as verified (and primary if
    the user has no primary address yet). Returns True if anything changed."""
    if not user.email:
        return False
    address, created = EmailAddress.objects.get_or_create(
        user=user,
        email__iexact=user.email,
        defaults={"email": user.email.lower()},  # allauth stores and looks up lowercase
    )
    changed = created
    if not address.verified:
        address.verified = True
        changed = True
    if not address.primary and not user.emailaddress_set.filter(primary=True).exists():
        address.primary = True
        changed = True
    if changed:
        address.save()
    return changed
