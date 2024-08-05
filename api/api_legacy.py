## Legacy turtlecloud API

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.utils import timezone
from django.core.files.base import ContentFile
from ninja.errors import HttpError
from ninja.security import django_auth
from ninja import NinjaAPI
from ninja import Field, Schema
from typing import List
from datetime import datetime
from bs4 import BeautifulSoup
import base64

from apps.projects.models import Project
from apps.classrooms.models import Group, SelectedProject


# TODO:
# * Rate limiting
# TODO
# @api.get("/users/{username}/projects/{projectname}/delete")


api = NinjaAPI(
    title="TurtleCloud Legacy API",
    version="0.1",
    description="legacy API compatible with TurtleStitch v2.x",
    urls_namespace="api-legacy",
)

###################################
# Schemas
###################################


class CurrentUser(Schema):
    username: str = ""


class Username(Schema):
    username: str


class ProjectBrief(Schema):
    projectname: str = Field(None, alias="name")
    notes: str = None
    ispublic: bool = Field(None, alias="is_public")
    updated: datetime = Field(None, alias="date_updated")


###################################
# Endpoints
###################################


@api.get("/user", response=CurrentUser, summary="Get the current user.")
def current_user(request):
    """
    Get the current user.
    """
    user = request.user
    return CurrentUser(username=user.username)


@api.get(
    "/users/{username}/projects",
    response=List[ProjectBrief],
    summary="Get a user's projects.",
)
def get_users_projects(request, username: str):
    """
    Get a user's projects.
    """
    if request.user.is_authenticated and request.user.username == username:
        projects = Project.objects.filter(user__username=username)
        return projects
    else:
        projects = Project.objects.filter(user__username=username, is_public=True)
        return projects


@api.get(
    "/users/{username}/projects/{projectname}", summary="Get a Project's full details."
)
def get_project(request, username: str, projectname: str):
    """
    Get a project's full details
    """
    project = Project.objects.get(user__username=username, name=projectname)

    if (
        request.user.is_authenticated and request.user.username == username
    ) or project.is_public:
        if project.thumbnail:
            with open(f"{settings.MEDIA_ROOT}/{project.thumbnail}", "rb") as image_file:
                encoded_thumbnail = encoded_thumbnail = base64.b64encode(
                    image_file.read()
                ).decode("utf-8")
        else:
            encoded_thumbnail = ""
        with open(f"{settings.MEDIA_ROOT}/{project.project_file}", "r") as project_file:
            projectfile = project_file.read()

        project.views = project.views + 1
        project.save()

        return {
            "projectname": project.name,
            "username": project.user.username,
            "notes": project.notes,
            "thumbnail": f"data:image/png;base64,{encoded_thumbnail}",
            "contents": f"{projectfile}",
            "ispublic": project.is_public,
            "updated": project.date_updated,
            "id": project.id,
            "views": project.views,
        }
    else:
        raise HttpError(401, "Unauthorized. Note that this project is not public.")


@api.get("/users/{username}/projects/{projectname}/image")
def get_project_thumbnail(request, username: str, projectname: str):
    """
    Get a project's thumbnail.
    """
    project = Project.objects.get(user__username=username, name=projectname)
    # check permission
    if (
        request.user.is_authenticated and request.user.username == username
    ) or project.is_public:
        # read file and return the encoded images
        with open(f"{settings.MEDIA_ROOT}/{project.thumbnail}", "rb") as image_file:
            encoded_thumbnail = base64.b64encode(image_file.read()).decode("utf-8")
        return HttpResponse(
            f"data:image/png;base64,{encoded_thumbnail}", content_type="text/html"
        )
    else:
        raise HttpError(401, "Unauthorized. Note that this project is not public.")


@api.get("/users/{username}/projects/{projectname}/visibility", auth=django_auth)
def set_project_visibility(
    request, username: str, projectname: str, ispublic: bool = True
):
    """
    Change the project's visibility.
    """
    project = Project.objects.get(user__username=username, name=projectname)
    if (
        request.user.is_authenticated and request.user.username == username
    ) or project.is_public:
        project.is_public = ispublic
        project.is_published = ispublic
        if ispublic:
            project.last_shared = timezone.now()
        else:
            project.last_shared = None
        project.save()
        return {
            "ispublic": project.is_public,
            "text": f"project {projectname} is now {'public' if ispublic else 'private'}",
            "success": True,
        }
    else:
        raise HttpError(401, "Unauthorized. Note that this project is not public.")


@api.get("/users/{username}/projects/{projectname}/delete", auth=django_auth)
def delete_project(request, username: str, projectname: str):
    """
    Delete a Project
    """
    project = Project.objects.get(user__username=username, name=projectname)

    if (
        request.user.is_authenticated and request.user.username == username
    ) or project.is_public:
        project.delete()
        return {
            "text": f"project {projectname} is removed",
            "success": True,
        }
    else:
        raise HttpError(401, "Unauthorized. Note that this project is not public.")


@api.post("/projects/save")
@csrf_exempt
def save_project(
    request, username: str, projectname: str, tags: str, visibility: bool = True
):
    """
    Save a Project
    """
    # are we the same user who requested to save the project?
    if not (request.user.is_authenticated and request.user.username == username):
        raise HttpError(403, "Not Allowed.")

    # parse the body which contains the project file for thumbnail and notes
    contents = request.body
    soup = BeautifulSoup(contents, "xml")
    # we look for the first instances (less elegant but it might be nested)
    thumbnail = (
        soup.find_all("thumbnail")[0].text if soup.find_all("thumbnail") else None
    )
    notes = soup.find_all("notes")[0].text if soup.find_all("notes") else None
    # tag = soup.find_all("tags")[0].text if soup.find_all("notes") else None

    project, created = Project.objects.get_or_create(
        user=request.user, name=projectname
    )
    project.is_public = visibility
    project.is_published = visibility
    project.notes = notes
    project.date_updated = timezone.now()
    project.update_tags_from_notes()
    project.update_embeddings()
    project.save()

    if tags:
        for tag in tags.split(","):
            project.tags.add(tag.strip())
    project.save()

    # save project file
    project.project_file.save(project.slug + ".xml", ContentFile(contents))

    # parse thumbnail and save to file
    if thumbnail:
        imgformat, imgstr = thumbnail.split(";base64,")
        ext = imgformat.split("/")[-1]
        project.thumbnail.save(
            f"{project.slug}.{ext}", ContentFile(base64.b64decode(imgstr)), save=True
        )

    if "group" in request.session:
        group = Group.objects.get(id=request.session["group"])
        newproject = SelectedProject(
            group=group,
            project=project,
            is_starter=False,
            unit_id=group.current_unit or "",
        )
        newproject.save()
        # if group.current_unit:
        #     unit = Unit.objects.get(id=group.current_unit)
        #     unit.projects.add(project)
        #     unit.save()
        # else:
        #     group.projects.add(project)
        #     group.save()

    return {"text": f"project {projectname} {'created' if created else 'updated'}"}
