import re

from django.template import Library
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe


register = Library()


@register.filter(name="twittify", needs_autoescape=True)
def twittify(value, autoescape=None):
    """Replace @ and #'s with links to twitter"""
    if autoescape:
        value = conditional_escape(value)
    return mark_safe(
        re.sub(
            r"(?<!&)#(?P<ht>([a-zA-Z0-9_])+)",
            r"#<a href='http://twitter.com/#!/search?q=\g<ht>' target='_blank'>\g<ht></a>",
            re.sub(
                r"@(?P<un>([a-zA-Z0-9_]){1,15})",
                r"@<a href='http://twitter.com/\g<un>' target='_blank'>\g<un></a>",
                value,
            ),
        )
    )


@register.filter(name="linktags", needs_autoescape=True)
def linktags(value, autoescape=None):
    """Replace @mentions and #tags with links"""
    if autoescape:
        value = conditional_escape(value)
    return mark_safe(
        re.sub(
            r"(?<!&)#(?P<ht>([a-zA-Z0-9_\-])+)",
            r"<a href='/projects/tag/\g<ht>' class='text-tertiary'>#\g<ht></a>",
            re.sub(
                r"@(?P<ut>[a-zA-Z0-9_\-]+)",
                r"<a href='/user/\g<ut>' class='text-tertiary'>@\g<ut></a>",
                value,
            ),
        )
    )


@register.filter(name="removetags", needs_autoescape=True)
def removetags(value, autoescape=None):
    """Remove #tags from text (used before computing embeddings)"""
    if autoescape:
        value = conditional_escape(value)
    return mark_safe(
        re.sub(
            r"(?<!&)#(?P<ht>([a-zA-Z0-9_\-])+)",
            "",
            value,
        )
    )


@register.filter(name="link_uris", needs_autoescape=True)
def link_uris(value, autoescape=None):
    """Replace http(s) URLs with links"""
    if autoescape:
        value = conditional_escape(value)
    regex = r"https?://[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\%\:@\-_=#])*"
    return mark_safe(
        re.sub(
            regex,
            r"<a target='_blank' href='\g<0>' class='underline text-tertiary'>\g<0></a>",
            value,
        )
    )


@register.simple_tag
def scale_tag(value, min_out, max_out, max_in):
    size = max(min_out, (value / max_in * max_out))
    return f"{size}"
