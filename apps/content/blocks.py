from django.utils.html import format_html
from django.utils.safestring import mark_safe
from wagtail.blocks import TextBlock


class CaptionBlock(TextBlock):
    """
    A block for generating <figcaptions> that can also use html characters (so you can add, e.g. links).
    """

    def render_basic(self, value, context=None):
        if value:
            return format_html("<figcaption>{0}</figcaption>", mark_safe(value))
        else:
            return ""

    class Meta:
        icon = "info-circle"
