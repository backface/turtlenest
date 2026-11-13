import re


def parse_allowed_hosts(value):
    """Split on commas/whitespace; accept "*.example.org" as Django's ".example.org"."""
    hosts = []
    for host in re.split(r"[\s,]+", value.strip()):
        if host.startswith("*."):
            host = host[1:]
        if host:
            hosts.append(host)
    return hosts
