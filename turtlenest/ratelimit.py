"""Rate limiting for the APIs and web views. Counters live in the default cache.

Per-IP limits are generous because a school class often shares one IP;
the tight limits are per username or per user.
"""

import ipaddress

from django.conf import settings
from django_ratelimit.core import is_ratelimited

# group -> list of (key, rate). key is "ip", "user" or "username" (the
# username the request targets, passed in by the caller).
LIMITS = {
    # API
    "api-login": [("ip", "100/10m"), ("username", "10/10m")],
    "api-signup": [("ip", "20/h")],
    "api-password-reset": [("ip", "20/h"), ("username", "5/h")],
    "api-resend-verification": [("ip", "20/h"), ("username", "5/h")],
    "api-newpassword": [("ip", "30/h"), ("username", "10/h")],
    # web
    "web-search": [("ip", "300/m")],
    "web-semantic-search": [("ip", "60/m")],
    "web-comment": [("user", "10/m"), ("user", "100/d")],
    "web-like": [("user", "60/10m")],
    "web-flag": [("user", "10/h")],
}

# like notification mails per liker and project
LIKE_NOTIFY_RATE = "1/d"

TOO_MANY = "Too many attempts. Please wait a few minutes and try again."


def client_ip(request):
    """Client IP from X-Forwarded-For behind ``TRUSTED_PROXY_COUNT`` proxies
    (same rule as allauth's ``ALLAUTH_TRUSTED_PROXY_COUNT``)."""
    count = getattr(settings, "TRUSTED_PROXY_COUNT", 0)
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    ip = None
    if count > 0 and xff:
        hops = [h.strip() for h in xff.split(",")]
        if len(hops) >= count:
            ip = hops[-count]
    if not ip:
        ip = request.META.get("REMOTE_ADDR", "")
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return "unknown"
    if addr.version == 6:
        # one subscriber usually owns a whole /64
        return str(ipaddress.ip_network(f"{addr}/64", strict=False))
    return str(addr)


def _key_func(kind, value):
    if kind == "ip":
        return lambda group, request: client_ip(request)
    if kind == "user":
        return lambda group, request: (
            f"user:{request.user.pk}" if request.user.is_authenticated else client_ip(request)
        )
    return lambda group, request: f"name:{(value or '').lower()}"


def is_limited(request, group, username=None):
    """Count the request against all limits of ``group``; True if any is exceeded."""
    limited = False
    for i, (kind, rate) in enumerate(LIMITS[group]):
        if kind == "username" and not username:
            continue
        if is_ratelimited(
            request,
            group=f"{group}:{i}",
            key=_key_func(kind, username),
            rate=rate,
            increment=True,
        ):
            limited = True
    return limited


def allow_once(request, group, key, rate):
    """True the first time within ``rate`` for ``key``, then False."""
    return not is_ratelimited(
        request, group=group, key=lambda g, r: key, rate=rate, increment=True
    )
