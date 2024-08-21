from django.template import Library
from django.utils.safestring import mark_safe
import re


register = Library()


@register.filter(name="twittify")
def twittify(value):
    """Replace @ and #'s with links to twitter"""
    return mark_safe(
        re.sub(
            r"#(?P<ht>([a-zA-Z0-9_])+)",
            r"#<a href='http://twitter.com/#!/search?q=\g<ht>' target='_blank'>\g<ht></a>",
            re.sub(
                r"@(?P<un>([a-zA-Z0-9_]){1,15})",
                r"@<a href='http://twitter.com/\g<un>' target='_blank'>\g<un></a>",
                value,
            ),
        )
    )
twittify.mark_safe = True


@register.filter(name="linktags")
def linktags(value):
    """Replace #tags with links to tag site using reverse"""
    # regex = "#([a-zA-Z0-9_]+)"
    return mark_safe(
        re.sub(
            # r"#(?P<ht>(\w+))",
            r"#(?P<ht>([a-zA-Z0-9_\-])+)",
            r"<a href='/projects/tag/\g<ht>' class='text-tertiary'>#\g<ht></a>",
            re.sub(
                r"@(?P<ut>(\w+))",
                r"<a href='/user/\g<ut>' class='text-tertiary'>@\g<ut></a>",
                value,
            ),
        )
    )
linktags.mark_safe = True

register.filter(name="removetags")
def removetags(value):
    """Replace #tags with links to tag site using reverse"""
    # regex = "#([a-zA-Z0-9_]+)"
    return mark_safe(
        re.sub(
            # r"#(?P<ht>(\w+))",
            r"#(?P<ht>([a-zA-Z0-9_\-])+)",
            r"",
            value,
        )
    )
removetags.mark_safe = True


@register.filter(name="link_uris")
def link_uris(value):
    """Replace string with http and ftp with links"""

    # regex = "(http|ftp|https)://([^\s]+\.[^\s]+)|(http|ftp)://([\w-]+\.[^\s]+)|(http|ftp)://([\w-]+\.[^\s]+)/?"
    regex = "((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*"
    return mark_safe(
        re.sub(
            regex,
            r"<a target='_blank' href='\g<0>' class='underline text-tertiary''>\g<0></a>",
            value,
        )
    )


@register.simple_tag
def scale_tag(value, min_out, max_out, max_in):
    size = max(min_out, (value / max_in * max_out))
    return f"{size}"
