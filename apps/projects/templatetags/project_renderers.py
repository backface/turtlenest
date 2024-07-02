from django import template
from django.db.models import Count, Sum, Case, When, IntegerField
from django.template.loader import render_to_string

from apps.projects.models import Project


register = template.Library()


@register.inclusion_tag("tags/tagcloud.html", takes_context=True)
def render_tagcloud(context):
    # try:
    #     queryset = queryset.annotate(num_times=Count('taggeditem_items'))
    # except FieldError:
    #     queryset = queryset.annotate(num_times=Count('taggit_taggeditem_items'))
    # num_times = queryset.values_list('num_times', flat=True)
    # weight_fun = get_weight_fun(T_MIN, T_MAX, min(num_times), max(num_times))
    # queryset = queryset.order_by('name')
    # for tag in queryset:
    #     tag.weight = weight_fun(tag.num_times)

    projects = Project.tags.annotate(count_all=Count("project")).annotate(
        count=Sum(
            Case(When(project__is_published=True, then=1)),
            output_field=IntegerField(),
        )
    )
    projects = projects.filter(count__gte=2).order_by("-count")
    maxima = projects.first().count if projects.count else 1

    return {"tags": projects, "scale": 100 / maxima, "basename": "projects:collection"}


@register.simple_tag(takes_context=True)
def render_collection(context, collection="newest"):
    projects = Project.objects.filter(is_published=True)

    if collection == "newest":
        projects = projects.order_by("-date_created")
    elif collection == "featured":
        projects = projects.filter(categories__slug__in=["featured"]).order_by(
            "-date_created"
        )
    elif collection == "most_viewed":
        projects = projects.order_by("-views")
    elif collection == "most_remixed":
        projects = projects.annotate(num_remixes=Count("remixed_from")).order_by(
            "-num_remixes"
        )
    elif collection == "most_commented":
        projects = projects.annotate(num_comments=Count("comment__id")).order_by(
            "-num_comments"
        )
    elif collection == "most_liked":
        projects = (
            projects.prefetch_related("likes")
            .annotate(num_likes=Count("likes__id"))
            .order_by("-num_likes")
        )

    template = "projects/_project_list.html"

    # template_string = "<!DOCTYPE html><html><body><h1>hello {{ name }}!</h1></body></html>"
    return render_to_string(
        template,
        {
            "page_obj": projects[:6],
            "collection": collection,
            "basename": "projects:collection",
        },
    )
