from django.db import models
from modelcluster.fields import ParentalKey
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.fields import RichTextField, StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Orderable, Page
from wagtail.search import index

# import MultiFieldPanel:
from wagtail.admin.panels import MultiFieldPanel
from apps.content.blocks import CaptionBlock


def _get_default_block_types():
    return [
        ("paragraph", blocks.RichTextBlock()),
        ("image", ImageChooserBlock()),
        ("caption", CaptionBlock()),
        ("html", blocks.RawHTMLBlock()),
    ]


class HomePage(Page):
    # add the Feature section to home page
    feature_code_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Code feature image",
    )
    feature_code_text = models.CharField(
        blank=True, max_length=255, help_text="Write an brief intro for the code feature block"
    )
    feature_code_link = models.CharField(
        blank=True, max_length=255, help_text="Link for the code feature block"
    )

    feature_make_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Make feature image",
    )
    feature_make_text = models.CharField(
        blank=True, max_length=255, help_text="Write an brief intro for the Make feature block"
    )
    feature_make_link = models.CharField(
        blank=True, max_length=255, help_text="Link to make feature "
    )

    feature_project_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Make feature image",
    )
    feature_project_text = models.CharField(
        blank=True, max_length=255, help_text="Write an brief intro for the featured project"
    )    
    feature_project_link = models.CharField(
        blank=True, max_length=255, help_text="Link to featured project"
    )

    body = RichTextField(blank=True)

    # modify your content_panels:
    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("feature_code_image"),
                FieldPanel("feature_code_text"),
                FieldPanel("feature_code_link"),

                FieldPanel("feature_make_image"),
                FieldPanel("feature_make_text"),
                FieldPanel("feature_make_link"),

                FieldPanel("feature_project_image"),
                FieldPanel("feature_project_text"),
                FieldPanel("feature_project_link"),
            ],

            heading="Feature Blocks",
        ),
        FieldPanel("body"),
    ]


class BaseContentPage(Page):
    social_image = models.ImageField(null=True, blank=True)
    promote_panels = Page.promote_panels + [
        FieldPanel("social_image"),
    ]

    def get_social_image_url(self):
        return self.social_image.url or ""

    class Meta:
        abstract = True


class ContentPage(BaseContentPage):
    """
    A page of generic content.
    """

    body = StreamField(_get_default_block_types(), use_json_field=True)
    content_panels = Page.content_panels + [
        FieldPanel("body", classname="full"),
        InlinePanel("gallery_images", label="Gallery images"),
    ]

    @property
    def main_image(self):
        gallery_item = self.gallery_images.first()
        if gallery_item:
            return gallery_item.image
        else:
            return None



class PageGalleryImage(Orderable):
    page = ParentalKey(
        ContentPage, on_delete=models.CASCADE, related_name="gallery_images"
    )
    image = models.ForeignKey(
        "wagtailimages.Image", on_delete=models.CASCADE, related_name="+"
    )
    caption = models.CharField(blank=True, max_length=250)

    panels = [
        FieldPanel("image"),
        FieldPanel("caption"),
    ]
