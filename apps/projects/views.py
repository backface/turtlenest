from django.conf import settings
from django.core.paginator import Paginator
from django.core.mail import EmailMessage
from django.core.files.base import ContentFile
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, Http404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.sessions.models import Session
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.template.loader import render_to_string
from django.db.models import Q, Count, Case, Sum, When, IntegerField
from django.db.models.functions import Length
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from pgvector.django import L2Distance, CosineDistance
from bs4 import BeautifulSoup
from apps.pages.models import Page
from apps.users.models import User
from apps.classrooms.models import Group
from .models import (
    Project,
    Category,
    Comment,
    Remix,
    Like,
    FlaggedProject,
    Image,
    create_embeddings,
)
from .forms import (
    ProjectForm,
    CommentForm,
    FlagProjectForm,
    UploadMediaForm,
    CategoriesForm,
)


COLLECTIONS = [
    {"name": _("Featured"), "slug": "featured"},
    {"name": _("Newest"), "slug": "newest"},
    {"name": _("Most Viewed"), "slug": "most_viewed"},
    {"name": _("Most Remixed"), "slug": "most_remixed"},
    {"name": _("Most Commented"), "slug": "most_commented"},
    {"name": _("Most Liked"), "slug": "most_liked"},
    {"name": _("Tags"), "slug": "tags"},
    {"name": _("Categories"), "slug": "categories"},
    {"name": _("Category:"), "slug": "category", "hidden": True},
]

PRIVATE_COLLECTIONS = [
    {"name": _("I Liked"), "slug": "i_liked"},
    {"name": _("I Remixed"), "slug": "i_remixed"},
    {"name": _("I Commented"), "slug": "i_commented"},
]


# @cache_page(60 * 15)
def index(request):
    featured = Project.objects.filter(categories__slug__in=["featured"]).order_by("?")
    try:
        announcement = Page.objects.get(slug='announcement')
    except Page.DoesNotExist:
        announcement = None
        pass
    if featured:
        featured = featured[0]
    else:
        featured = None
    return render(request, "index.html", {"featured": featured, "announcement": announcement})


def list(request):
    return redirect("projects:collection", "newest")


def list_by_tag(request, tag, mine=False):
    return collection(request, "tag", mine=mine, arg=tag)


def my_projects(request, collection="newest"):
    # return collection(request, "My Projects", mine=True)
    return redirect("projects:mycollection")


def collection_redirect(request, collection="newest"):
    return redirect("projects:collection", collection)


def collection(request, collection="newest", mine=False, arg=None):
    """returns a collection of projects"""
    arg_str = arg or ""

    # check if collection is valid
    INTERNAL_COLLECTIONS = [
        {"name": _("Tag"), "slug": "tag"},
        {"user": _("User"), "slug": "user"}
    ]
    collections = COLLECTIONS + INTERNAL_COLLECTIONS + PRIVATE_COLLECTIONS if mine else COLLECTIONS + INTERNAL_COLLECTIONS
    if not [item for item in collections if item.get('slug')==collection]:
        raise Http404("Collection not found")
    
    # pre-filter
    if mine:
        if request.user.is_authenticated:
            projects = Project.objects.filter(user=request.user)
        else:
            messages.error(request, _("You have to login first!"))
            return redirect("account_login")
    else:
        projects = Project.objects.filter(is_published=True)

    projects = projects.select_related("user")

    if collection == "category" and arg is None:
        collection = "categories"

    # build collection
    if collection == "newest":
        projects = projects.order_by("-date_created")
    elif collection == "featured":
        projects = projects.filter(categories__slug__in=["featured"]).order_by(
            "-date_created"
        )
    elif collection == "user":
        projects = projects.filter(user__username=arg)
    elif collection == "most_viewed":
        projects = projects.order_by("-views")
    elif collection == "most_remixed":
        projects = (
            projects.annotate(num_remixes=Count("remixed_from"))
            .order_by("-num_remixes")
            .distinct()
        )
    elif collection == "most_commented":
        projects = (
            projects.annotate(num_comments=Count("comment__id"))
            .order_by("-num_comments")
            .distinct()
        )
    elif collection == "most_liked":
        projects = (
            projects.prefetch_related("likes")
            .annotate(num_likes=Count("likes__id"))
            .order_by("-num_likes")
        ).distinct()
    elif collection == "i_liked":
        projects = (
            Project.objects.filter(is_published=True)
            .filter(likes__liker=request.user)
            .distinct()
        )
    elif collection == "i_commented":
        projects = (
            Project.objects.filter(is_published=True)
            .filter(comment__author=request.user)
            .distinct()
        )
    elif collection == "i_remixed":
        projects = (
            Project.objects.filter(is_published=True)
            .filter(remixed_to__remixed_project__user=request.user)
            .distinct()
        )
    elif collection == "tag":
        projects = projects.filter(
            tags__slug__in=[
                arg,
            ]
        )
        if projects:
            arg_str = f"#{Project.tags.filter(slug=arg).first().name}"
        else: 
            arg_str = f"#{arg}"
    elif collection == "category":
        projects = projects.filter(categories__slug__in=[arg])
        if projects:
            arg_str = Category.objects.filter(slug=arg).first().name
        else:
           arg_str = f"{arg}" 
    elif collection == "categories":
        return category_list(request)

    # paginate
    paginator = Paginator(projects, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # choose template
    if request.META.get("HTTP_HX_REQUEST") or request.htmx:
        template = "projects/_project_list.html"
    else:
        template = "projects/project_list.html"

    collections = COLLECTIONS + PRIVATE_COLLECTIONS if mine else COLLECTIONS

    if mine:
        for i, c in enumerate(COLLECTIONS):
            if c["slug"] == "categories":
                del COLLECTIONS[i]

    # render
    return render(
        request,
        template,
        {
            "projects": paginator,
            "collection": collection,
            "collection_str": next(
                (x["name"] for x in collections if x["slug"] == collection), ""
            ),
            "page_obj": page_obj,
            "arg": arg,
            "arg_str": arg_str,
            "mine": mine,
            "collections": collections,
            "private_collections": PRIVATE_COLLECTIONS,
            "baseurl": "myprojects" if mine else "projects",
            "basename": "projects:mycollection" if mine else "projects:collection",
        },
    )


def user_detail(request, username):
    """returns a collection of projects"""
    user = get_object_or_404(User, username=username)
    projects = Project.objects.filter(user__username=username, is_published=True)

    # paginate
    paginator = Paginator(projects, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # choose template
    if request.META.get("HTTP_HX_REQUEST") or request.htmx:
        template = "projects/_project_list.html"
    else:
        template = "projects/user_detail.html"

    # render
    return render(
        request,
        template,
        {
            "user": user,
            "projects": paginator,
            "page_obj": page_obj,
            "collection": "user",
            "arg": username,
            "basename": "projects:collection",
        },
    )


def tags(request, mine=False):
    if mine:
        projects = Project.tags.annotate(count_all=Count("project")).annotate(
            count=Sum(
                Case(When(project__user=request.user, then=1)),
                output_field=IntegerField(),
            )
        )
        projects = projects.filter(count__gte=1).order_by("-count")
    else:
        projects = Project.tags.annotate(count_all=Count("project")).annotate(
            count=Sum(
                Case(When(project__is_published=True, then=1)),
                output_field=IntegerField(),
            )
        )
        projects = projects.filter(count__gte=2).order_by("-count")

    maxima = projects.first().count if projects.first() else 1

    return render(
        request,
        "projects/tags.html",
        {
            #'tags': Project.tags.annotate(count=Count('project')).order_by("-count")
            "tags": projects,
            "scale": 100 / maxima,
            "maxima": maxima,
            "mine": mine,
            "collections": COLLECTIONS,
            "collection": "tags",
            "baseurl": "myprojects" if mine else "projects",
            "basename": "projects:mycollection" if mine else "projects:collection",
        },
    )


def detail(request, username, projectname):
    """show project detail page by username and projectname"""
    project = get_object_or_404(Project, user__username=username, name=projectname)
    return detail_by_id(request, project.id)


def detail_by_id(request, id):
    """show project detail page by id"""
    project = get_object_or_404(Project, id=id)

    # check permissons
    if not project.is_published and not project.user == request.user:
        raise PermissionDenied

    # get remixes and similar projects
    remixed_to = Remix.objects.filter(original_project=project).filter(
        remixed_project__is_published=True
    )
    remixed_from = Remix.objects.filter(remixed_project=project).filter(
        original_project__is_published=True
    )
    similar_projects = (
        Project.objects.filter(is_published=True)
        .exclude(id=id)
        .order_by(CosineDistance("embedding_project_meta", project.embedding_project_meta))[:6]
        # .annotate(
        #     l2_distance=L2Distance(
        #         "embedding_project_meta", project.embedding_project_meta
        #     )
        # )
        # .annotate(
        #     cos_distance=CosineDistance(
        #         "embedding_project_meta", project.embedding_project_meta
        #     )
        #)
    )

    # increment view counter
    project.views = project.views + 1
    project.save(no_timestamp=True)

    group = None
    if "group" in request.session:
        if request.session["group"]:
            group = Group.objects.get(pk=request.session["group"])

    return render(
        request,
        "projects/project_detail.html",
        {
            "project": project,
            "group": group,
            "comment_form": CommentForm({"project": project, "author": request.user}),
            "categories_form": CategoriesForm(instance=project),
            "remixed_from": remixed_from,
            "remixed_to": remixed_to,
            "similar_projects": similar_projects,
            "ilike": project.ilike(request.user)
            if request.user.is_authenticated
            else None,
        },
    )


@cache_page(60 * 15)
def project_stats(request, id):
    project = get_object_or_404(Project, pk=id)
    return render(
        request,
        "projects/_project_stats.html",
        {"project": project, "ilike": project.ilike(request.user)},
    )


def search(request, target="all"):
    q = request.GET.get("q") or ""
    if len(q) > 1:
        if target == "users":
            objects = User.objects.filter(
                Q(username__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
            ).order_by("-username")

        elif target == "semantic":
            q_vector = create_embeddings(q)
            objects = (
                Project.objects.filter(is_published=True)
                .select_related("user")
                .order_by(
                    # L2Distance('embedding_project_meta', q_vector )
                    CosineDistance("embedding_project_meta", q_vector)
                )
                .annotate(l2_distance=L2Distance("embedding_project_meta", q_vector))
                .annotate(
                    cos_distance=CosineDistance("embedding_project_meta", q_vector)
                )
            )
            # objects = objects.filter(cos_distance__lte=0.5).distinct()
            objects = objects.distinct()

        elif target == "projects":
            objects = (
                Project.objects.filter(is_published=True)
                .filter(Q(name__icontains=q) | Q(notes__icontains=q))
                .select_related("user")
            )

        elif target == "pg_search":
            vector = SearchVector("name", "notes")
            query = SearchQuery(q)
            objects = (
                Project.objects.filter(is_published=True)
                .annotate(
                    rank=SearchRank(vector, query),
                    search=vector,
                )
                .order_by("-rank")
                .select_related("user")
                .filter(search=q)
            )
        else:
            objects = (
                Project.objects.filter(is_published=True)
                .filter(
                    Q(name__icontains=q) | Q(notes__icontains=q)
                ).select_related("user")
            )
            users = User.objects.filter(
                Q(username__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
            ).order_by("-username")

        if "users" in locals():  # search for uses
            user_paginator = Paginator(users, 6)
            user_page_obj = user_paginator.get_page(1)
            paginator = Paginator(objects, 6)
            page_obj = paginator.get_page(1)
        else:  # search for projects
            user_page_obj = None
            paginator = Paginator(objects, 12)
            page_number = request.GET.get("page")
            page_obj = paginator.get_page(page_number)
    else:
        page_obj = None
        user_page_obj = None

    if request.htmx:
        if request.htmx.target == "searchresult":
            template = "projects/_search_result.html"
        else:
            template = "projects/_search_result_list.html"
    else:
        template = "projects/search.html"

    return render(
        request,
        template,
        {
            "q": q,
            "count": paginator.count if page_obj else 0,
            "page_obj": page_obj,
            "target": target,
            "user_page_obj": user_page_obj if user_page_obj else None,
        },
    )


def category_list(request):
    # subqry = Subquery(Category.objects \
    #     .filter(projects__id=OuterRef('id')) \
    #     .values_list('id', flat=True)[:5])

    # categories = Category.objects.prefetch_related(
    #     Prefetch('projects', queryset=Project.objects.filter(id__in=subqry)))
    categories = Category.objects.all()
    for cat in categories:
        cat.paginator = Paginator(cat.projects.all()[:6], 6)
        cat.page_obj = cat.paginator.get_page(1)
    return render(
        request,
        "projects/categories.html",
        {
            "categories": categories,
            "target": "category",
            "collections": COLLECTIONS,
            "collection_str": _("Categories"),
            "private_collections": PRIVATE_COLLECTIONS,
            "basename": "projects:collection",
        },
    )


def stats(request):
    stats_data = {
        "total": {
            "projects total": Project.objects.count(),
            "users total": User.objects.count(),
        },
        "project interactions I": {
            "projects with notes": Project.objects.annotate(text_len=Length("notes"))
            .filter(text_len__gt=0)
            .count(),
            "projects with tags": Project.objects.filter(tags__isnull=False).count(),
            "projects with likes": Project.objects.filter(likes__isnull=False).count(),
            "projects with comments": Project.objects.filter(
                comment__isnull=False
            ).count(),
        },
        "project interactions II": {
            "categories": Category.objects.count(),
            "tags": Project.tags.count(),
            "likes": Like.objects.count(),
            "views": Project.objects.aggregate(Sum("views"))["views__sum"],
            "comments": Comment.objects.count(),
            "remixes": Remix.objects.count(),
        },
        "project creations": {
            "projects created last 24h": Project.objects.filter(
                date_created__gte=timezone.now() - timezone.timedelta(hours=24)
            ).count(),
            "projects created this week": Project.objects.filter(
                date_created__gte=timezone.now() - timezone.timedelta(days=7)
            ).count(),
            "projects created last 30 days": Project.objects.filter(
                date_created__gte=timezone.now() - timezone.timedelta(days=30)
            ).count(),
            "projects created last year": Project.objects.filter(
                date_created__gte=timezone.now() - timezone.timedelta(weeks=52)
            ).count(),
        },
        "project updates": {
            "projects updated last 24h": Project.objects.filter(
                date_updated__gte=timezone.now() - timezone.timedelta(hours=24)
            ).count(),
            "projects updated this week": Project.objects.filter(
                date_updated__gte=timezone.now() - timezone.timedelta(days=7)
            ).count(),
            "projects updated last 30 days": Project.objects.filter(
                date_updated__gte=timezone.now() - timezone.timedelta(days=30)
            ).count(),
            "projects updated last year": Project.objects.filter(
                date_updated__gte=timezone.now() - timezone.timedelta(weeks=52)
            ).count(),
        },
        "project sharing": {
            "projects shared last 24h": Project.objects.filter(
                last_shared__gte=timezone.now() - timezone.timedelta(hours=24)
            ).count(),
            "projects shared this week": Project.objects.filter(
                last_shared__gte=timezone.now() - timezone.timedelta(days=7)
            ).count(),
            "projects shared last 30 days": Project.objects.filter(
                last_shared__gte=timezone.now() - timezone.timedelta(days=30)
            ).count(),
            "projects shared last year": Project.objects.filter(
                last_shared__gte=timezone.now() - timezone.timedelta(weeks=52)
            ).count(),
        },
        "users joined": {
            "users joined last 24h": User.objects.filter(
                date_joined__gte=timezone.now() - timezone.timedelta(hours=24)
            ).count(),
            "users joined this week": User.objects.filter(
                date_joined__gte=timezone.now() - timezone.timedelta(days=7)
            ).count(),
            "users joined last 30 days": User.objects.filter(
                date_joined__gte=timezone.now() - timezone.timedelta(days=30)
            ).count(),
            "users joined last year": User.objects.filter(
                date_joined__gte=timezone.now() - timezone.timedelta(weeks=52)
            ).count(),
            "users currently active": Session.objects.filter(
                expire_date__gte=timezone.now()
            ).count(),
        },
        "users signed in": {
            "users signed in this week": User.objects.filter(
                last_login__gte=timezone.now() - timezone.timedelta(days=7)
            ).count(),
            "users signed in last 30 days": User.objects.filter(
                last_login__gte=timezone.now() - timezone.timedelta(days=30)
            ).count(),
            "users signed in last year": User.objects.filter(
                last_login__gte=timezone.now() - timezone.timedelta(weeks=52)
            ).count(),
        },
    }
    stats = []
    for key, value in stats_data.items():
        sub_items = []
        for k, v in value.items():
            sub_items.append({"label": k, "value": v})
        stats.append({"label": key, "items": sub_items})
    return render(request, "projects/stats.html", {"stats": stats})


@login_required
def edit(request, id):
    project = get_object_or_404(Project, pk=id)
    if not request.user == project.user:
        raise (PermissionDenied)
    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            project.update_tags_from_notes()
            project.update_embeddings()
            project.save()
            if settings.SYNC_NOTES_ON_SAVE and project.notes:
                with open(
                    f"{settings.MEDIA_ROOT}/{project.project_file}", "r"
                ) as project_file:
                    projectfile = project_file.read()
                    soup = BeautifulSoup(projectfile, "xml")
                    for note in soup.find_all("notes"):
                        if note.contents:
                            note.contents[0].replace_with(project.notes)
                        else:
                            note.contents = [project.notes]
                    content = str(soup).replace(
                        '<?xml version="1.0" encoding="utf-8"?>\n', ""
                    )
                    project.project_file.save(
                        project.slug + ".xml", ContentFile(content)
                    )
            messages.success(request, _("The project's details have been updated."))
            return redirect(
                reverse(
                    "projects:detail",
                    kwargs={
                        "username": project.user.username,
                        "projectname": project.name,
                    },
                )
            )
        else:
            messages.error(request, _("Please correct the following errors:"))
            return render(
                request,
                "projects/project_edit.html",
                {
                    "project": project,
                    "form": form,
                    "uploadMediaForm": UploadMediaForm(),
                },
            )
    else:
        form = ProjectForm(instance=project)
    return render(
        request,
        "projects/project_edit.html",
        {"project": project, "form": form, "uploadMediaForm": UploadMediaForm()},
    )


@login_required
def update_categories(request, id):
    project = get_object_or_404(Project, pk=id)
    if not request.user.is_superuser and not request.user.editor:
        raise (PermissionDenied)

    if request.method == "POST":
        categories_form = CategoriesForm(request.POST, instance=project)
        if categories_form.is_valid():
            categories_form.save()
            messages.success(request, _("Project categories updated"))
            return redirect(reverse("projects:detail_by_id", args=(project.id,)))
    else:
        categories_form = CategoriesForm(instance=project)
        return redirect(reverse("projects:detail_by_id", args=(project.id,)))


@login_required
def upload_media(request, id):
    project = get_object_or_404(Project, pk=id)
    if not request.user == project.user:
        raise (PermissionDenied)

    if request.method == "POST":
        uploadMediaForm = UploadMediaForm(
            request.POST,
            request.FILES,
            instance=Image(project=Project.objects.get(pk=id)),
        )
        if uploadMediaForm.is_valid():
            # instance = Image(file=request.FILES["file"], project=Project.objects.get(pk=id))
            # instance.save()
            uploadMediaForm.save()
            messages.success(request, _("Image uploaded"))
            return redirect(reverse("projects:edit", args=(project.id,)))
    else:
        uploadMediaForm = UploadMediaForm()
    return render(
        request,
        "projects/project_edit.html",
        {
            "project": project,
            "form": ProjectForm(instance=project),
            "uploadMediaForm": uploadMediaForm,
        },
    )


@login_required
def delete_media(request, id):
    print("delete media")
    image = get_object_or_404(Image, pk=id)
    project = image.project
    if image.project.user != request.user:
        raise (PermissionDenied)
    if project.image_is_featured == image.id:
        project.image_is_fetures = 0
        project.save()
    image.delete()
    messages.success(request, _("Image deleted"))
    return redirect(reverse("projects:edit", args=(project.id,)))


@login_required
def feature_media(request, id):
    image = get_object_or_404(Image, pk=id)
    project = image.project
    if image.project.user != request.user:
        raise (PermissionDenied)

    project.image_is_featured = image.id
    project.save()
    messages.success(request, _("Set Image as featured"))

    return redirect(reverse("projects:edit", args=(project.id,)))


@login_required
def delete(request, id):
    project = get_object_or_404(Project, pk=id)
    if (
        not request.user == project.user
        or request.user.is_superuser
        or request.user.is_moderator
    ):
        raise (PermissionDenied)

    messages.success(request, _("Project successfully deleted"))

    if request.headers.get("HX-Request"):
        response = HttpResponse()
        response["HX-Redirect"] = reverse("projects:my_projects")
        return response
    else:
        return redirect(reverse("projects:my_projects"))


@login_required
def like(request, id):
    like, created = Like.objects.get_or_create(project_id=id, liker=request.user)
    if not created:
        like.delete()
    else:
        if like.project.user != request.user and like.project.user.notify_like:
            message = EmailMessage(
                _("Someone liked your project!"),
                render_to_string("emails/notify_like.txt", {"like": like}),
                settings.EMAIL_FROM_ADDRESS,
                [
                    like.project.user.email,
                ],
                [],  # bcc
                # reply_to=[],
            )
            message.send()
    return project_stats(request, id)


@login_required
@require_http_methods(["DELETE"])
def delete_comment(request, id):
    comment = get_object_or_404(Comment, pk=id)
    if (
        not request.user == comment.author
        and not request.user.is_moderator
        and not request.user.is_superuser
    ):
        raise (PermissionDenied)
    else:
        comment.delete()
        messages.error(request, "Comment deleted")
        return HttpResponse("")


@login_required
def share_project(request, id):
    project = get_object_or_404(Project, pk=id)
    if (
        not request.user == project.user
        and not request.user.is_moderator
        and not request.user.is_superuser
    ):
        raise (PermissionDenied)
    else:
        project.is_public = True
        project.is_published = True
        project.last_shared = timezone.now()
        project.save()
        messages.success(request, "Project shared")
        if request.META.get("HTTP_HX_REQUEST") or request.htmx:
            return render(request, "projects/_is_shared.html", {"project": project})
        else:
            return redirect("projects:detail_by_id", id=project.id)


@login_required
def unshare_project(request, id):
    project = get_object_or_404(Project, pk=id)
    if (
        not request.user == project.user
        and not request.user.is_moderator
        and not request.user.is_superuser
    ):
        raise (PermissionDenied)
    else:
        project.is_public = False
        project.is_published = False
        project.last_shared = None
        project.save()
        messages.success(request, "Project unshared")
        if request.META.get("HTTP_HX_REQUEST") or request.htmx:
            return render(request, "projects/_is_unshared.html", {"project": project})
        else:
            return redirect("projects:detail_by_id", id=project.id)


@login_required
def add_comment(request, id):
    if request.method == "POST":
        if not request.user.id == int(request.POST["author"]):
            raise (PermissionDenied)

        form = CommentForm(request.POST)
        if form.is_valid():
            form.author = request.user
            comment = form.save()
            messages.success(request, "Comment posted!")
            if (
                comment.project.user != request.user
                and comment.project.user.notify_comment
            ):
                message = EmailMessage(
                    _("Someone commented on your project!"),
                    render_to_string("emails/notify_comment.txt", {"comment": comment}),
                    settings.EMAIL_FROM_ADDRESS,
                    [
                        comment.project.user.email,
                    ],
                    [],  # bcc
                    # reply_to=[],
                )
                message.send()
            return render(request, "projects/_comment.html", {"comment": comment})
        else:
            # error_str = " ".join(
            #     [" ".join(x for x in l) for l in list(form.errors.values())]
            # )
            # print(error_str)
            # print(form.errors)
            # print("invalid comment!")
            messages.error(request, "Invalid comment!")
            return HttpResponse("error", status=500)
    else:
        raise (PermissionDenied)


@login_required
def flag(request, id):
    if request.method == "POST":
        project = get_object_or_404(Project, pk=id)
        form = FlagProjectForm(
            request.POST,
            instance=FlaggedProject(flagged_by=request.user, project=project),
        )
        if form.is_valid():
            flagged_project = form.save()
            message = EmailMessage(
                _("A project has been flagged!"),
                render_to_string(
                    "emails/flag_project.txt",
                    {"flag": flagged_project, "request": request},
                ),
                settings.EMAIL_FROM_ADDRESS,
                request.user.get_moderator_emails(),
            )
            message.send()
            messages.success(
                request, _("Thanks for your report. Moderators have been notified!")
            )
            return redirect(
                reverse(
                    "projects:detail",
                    kwargs={
                        "username": flagged_project.project.user.username,
                        "projectname": flagged_project.project.name,
                    },
                )
            )
        else:
            messages.error(request, _("Please correct the following errors:"))
            return render(
                request,
                "projects/project_flag.html",
                {"form": form, "project": project},
            )
    else:
        project = get_object_or_404(Project, pk=id)
        form = FlagProjectForm(instance=FlaggedProject())
    return render(
        request, "projects/project_flag.html", {"form": form, "project": project}
    )


@xframe_options_exempt
def run(request):
    return render(request, "run.html")
