## New SnapCloud API v1

import base64
import json
from bs4 import BeautifulSoup
from typing import List
from typing import Optional
from datetime import datetime
from django.utils import timezone
from django.conf import settings
from django.http import HttpResponse
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import check_password

from ninja import NinjaAPI
from ninja import Schema
from ninja.errors import HttpError
from allauth.account.forms import ResetPasswordForm
from allauth.account.utils import send_email_confirmation

from apps.projects.models import Project
from apps.classrooms.models import Group, SelectedProject


api = NinjaAPI(
    title="TurtleNest / SnapCloud API",
    version="1.0.0",
    description="Implements current Snap! and SnapCloud API",
    urls_namespace="api-v1",
)

# TODO
# * API rate lmiting?



###################################
# Schemas
###################################


class CurrentUser(Schema):
    username: str
    verified: bool = False
    id: int = 0
    # verified: bool = Field(None, alias="emailaddress_set.all.0.verified")

    @staticmethod
    def resolve_verified(obj):
        if obj.emailaddress_set.filter(primary=True).exists():
            return obj.emailaddress_set.filter(primary=True).first().verified
        else:
            return False


class ProjectBrief(Schema):
    id: int
    username: str
    projectname: str
    notes: str = None
    ispublic: bool = False
    ispublished: bool = False
    created: datetime
    lastshared: Optional[datetime]
    lastupdated: datetime
    created: datetime


class ProjectList(Schema):
    projects: List[ProjectBrief] = []


class Error(Schema):
    message: str


class Errors(Schema):
    errors: List[str] = []


class Message(Schema):
    message: str = ""


class RedirectMessage(Schema):
    redirect: str = ""


class Info(Schema):
    title: str = ""
    redirect: str = ""
    message: str = ""


###################################
# Endpoints
###################################


@api.post("/init")
def init(request):
    """
    Returns an empty object for now
    """
    return {}


@api.get("/users/c", response={200: CurrentUser, 403: Error})
def current_user(request):
    """
    Get the current user
    """
    if request.user.is_authenticated:
        user = request.user
    else:
        user = CurrentUser(username="")
    return user


@api.post(
    "/users/{username}/login", response={200: Message, 400: Error}, url_name="login"
)
def login_user(request, username: str, persist: bool = True):
    """
    Login a user
    """
    password = request.body
    if isinstance(password, bytes):
        password = password.decode("utf-8")
    password = f"snap${password}"
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        msg = Message(message=f"user {user.username} logged in.")
        return msg
    else:
        return Error(message="Wrong username or password")


@api.post("/users/{username}", response={200: Info, 400: Errors}, url_name="signup")
def signup_user(
    request, username: str, email: str, password: str, password_repeat: str
):
    """
    Signup a user
    """
    User = get_user_model()
    password = f"snap${password}"
    password_repeat = f"snap${password_repeat}"

    if password != password_repeat:
        return Errors(erros=["Passwords do not match"])

    try:
        user = User.objects.get(username=username)
        return 400, Errors(errors=[f"User {username} already exists",])
    except User.DoesNotExist:
        pass

    try:
        user = User.objects.get(email=email)
        return 400, Errors(errors=[f"User with E-mail {email} already exists"])
    except User.DoesNotExist:
        pass

    # form = SignupForm(
    #     {
    #         "username": username,
    #         "email": email,
    #         "password1": password1,
    #         "password2": password2,
    #     })
    # if not form.is_valid():
    #     return 400, Errors(errors=form.errors)
    # form.save(request)
        
    user = User(username=username, email=email, password=password)
    user.set_password(password)
    user.save()
    send_email_confirmation(request, user, user.email)

    return {
        "redirect": "/login",
        "title": "Account created",
        "message": f"User {username} created. Verification email sent to {email}. Please validate your account before logging in.",
    }


@api.get("/users/{username}/resendverification")
def resend_verification(request, username: str):
    """
    Resend verification email.
    """
    User = get_user_model()
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        # avoid leaking information about user existence
        # raise HttpError(404, "User not found.")
        return HttpResponse(status=200)

    if not user.is_email_verified():
        send_email_confirmation(request, user, user.email)
    else:
        # return Message(message = f"Email already verified.")
        return HttpResponse(status=200)
    return HttpResponse(status=200)


@api.post(
    "/users/{username}/password_reset",
    response=Message,
)
def request_password_change(request, username: str):
    """
    Request a password change.
    """
    User = get_user_model()
    user = get_object_or_404(User, username=username)

    # TODO What happens if the user is logged in?

    form = ResetPasswordForm(
        data={"email": user.emailaddress_set.filter(primary=True).first().email}
    )
    if form.is_valid():
        form.save(request)

    return Message(message="password reset link is on the way")


@api.post("/users/{username}/newpassword")
def change_password(
    request, username: str, oldpassword: str, password_repeat: str, newpassword: str
):
    """
    Change a User's Password
    """
    User = get_user_model()
    errors = []

    if request.user.is_authenticated and request.user.username == username:
        user = User.objects.get(username=username)
        oldpassword = f"snap${oldpassword}"
        newpassword = f"snap${newpassword}"
        password_repeat = f"snap${password_repeat}"

        if newpassword != password_repeat:
            errors.append("The provided passwords do not match")

        if check_password(oldpassword, user.password):
            user.set_password(newpassword)
            user.save()
            user = authenticate(request, username=username, password=newpassword)
            login(request, user)
            return {
                "redirect": "/profile/",
                "title": "Password changed",
                "message": "Your password has been changed.",
            }
        else:
            errors.append("The provided password is wrong")
    else:
        raise HttpError(401, "Unauthorized. ")

    return {"errors": errors}


@api.post("/logout", response=RedirectMessage, url_name="logout")
def logout_user(request):
    """
    Logout the current user
    """
    logout(request)
    return RedirectMessage(redirect="/")


@api.get("/projects/{username}", response=ProjectList, summary="Get a user's projects.")
def get_users_projects(request, username: str):
    """)
        # for project in 
    Get a user's projects.
    """
    if request.user.is_authenticated and request.user.username == username:
        projects = list(Project.objects.filter(user__username=username))
        # for project in projects:
        #     project.updated = str(project.date_updated).replace(" ", "T")

        return ProjectList(projects=projects)
    else:
        projects = Project.objects.filter(user__username=username, is_public=True)
        return ProjectList(projects=projects)


@api.get("/projects/{username}/{path:projectname}/versions")
def get_project_versions(request, username: str, projectname: str):
    """
    Get a Project's Versions (returns and empty array for now)
    """
    # project = Project.objects.get(user__username=username, name=projectname)
    return []


@api.post("/projects/{username}/{path:projectname}/metadata")
def set_project_visibility(
    request,
    username: str,
    projectname: str,
    ispublic: bool = None,
    ispublished: bool = None,
):
    """
    Change the project's visibility.
    """
    project = Project.objects.get(user__username=username, name=projectname)
    if request.user.is_authenticated and request.user.username == username:
        if ispublic is not None:
            project.is_public = ispublic
            if ispublic:
                project.last_shared = timezone.now()
            else:
                project.last_shared = None
        
        # we set is published but it is ignored for now!
        if ispublished is not None:
            project.is_published = ispublished

        project.save()
        return Message(
            message=f"project {projectname} updated {ispublic}, {ispublished}"
        )
    else:
        raise HttpError(401, "Unauthorized. Note that this project is not public.")


@api.get(
    "/projects/{username}/{path:projectname}/thumbnail",
    description="returns a base64 encoded image string",
)
def get_project_thumbnail(request, username: str, projectname: str):
    """
    Get a project's thumbnail.
    """
    project = Project.objects.get(user__username=username, name=projectname)
    if (
        request.user.is_authenticated and request.user.username == username
    ) or project.is_public:
        with open(f"{settings.MEDIA_ROOT}/{project.thumbnail}", "rb") as image_file:
            encoded_thumbnail = base64.b64encode(image_file.read()).decode("utf-8")
        return HttpResponse(
            f"data:image/png;base64,{encoded_thumbnail}", content_type="text/html"
        )
    else:
        raise HttpError(401, "Unauthorized. Note that this project is not public.")


@api.delete("/projects/{username}/{path:projectname}")
def delete_project(request, username: str, projectname: str):
    """
    Delete a Project
    """
    project = Project.objects.get(user__username=username, name=projectname)
    if request.user.is_authenticated and request.user.username == username:
        project.delete()
        return {
            "redirect": "",
            "message": f"project {projectname} has been deleted",
            "title": "Project deleted",
        }
    else:
        raise HttpError(401, "Unauthorized. Note that this project is not public.")


@api.get(
    "/projects/{username}/{path:projectname}",
    description="returns XML project file",
)
def get_project(request, username: str, projectname: str, updatingnotes: bool = True):
    """
    Load a project.
    """
    project = Project.objects.get(user__username=username, name=projectname)
    if (
        request.user.is_authenticated and request.user.username == username
    ) or project.is_public:
        project.views = project.views + 1
        project.save(no_timestamp=True)
        with open(f"{settings.MEDIA_ROOT}/{project.project_file}", "r") as project_file:
            contents = project_file.read()
        return HttpResponse(
            f'<snapdata>{contents}<media name="{project.name}" app="Snap! 4.2, http://snap.berkeley.edu" version="1"/></snapdata>',
            content_type="text/xml",
        )
    else:
        raise HttpError(401, "Unauthorized. Note that this project is not public.")


@api.post(
    "/projects/{username}/{path:projectname}",
    description="saves a project",
)
def save_project(request, username: str, projectname: str):
    """
    Save a Project
    """
    # are we the same user who requested to save the project?
    if not (request.user.is_authenticated and request.user.username == username):
        raise HttpError(403, "Not Allowed.")

    # print(type(request.body))
    data = json.loads(request.body.decode("ISO-8859-1"))
    # return {}
    # string = f"{request.body}"
    # print(json.loads(string))
    # print(json.loads(str(request.body, encoding="utf-8")))
    # print("------------------------------")

    contents = data["xml"]

    # print(contents)
    notes = data["notes"]
    thumbnail = data["thumbnail"]
    soup = BeautifulSoup(contents, "xml")

    # # we look for the first instances (less elegant but it might be nested)
    # thumbnail = soup.find_all("thumbnail")[0].text if soup.find_all("thumbnail") else thumbnail
    thumbnail = soup.find_all("pentrails")[0].text if soup.find_all("pentrails") else thumbnail
          
    # notes = soup.find_all("notes")[0].text if soup.find_all("notes") else None
    # # tag = soup.find_all("tags")[0].text if soup.find_all("notes") else None

    project, created = Project.objects.get_or_create(
        user=request.user, name=projectname
    )
    project.is_public = True
    project.is_published = True
    project.notes = notes
    project.update_tags_from_notes()
    project.update_embeddings()
    project.date_updated = timezone.now()
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
    project.save()

    # are we logged into a group? add a reference there as well
    try:
        if "group" in request.session:
            if request.session["group"]:
                group = Group.objects.get(id=request.session["group"])
                if group.current_unit:
                    selected_project = SelectedProject.objects.get_or_create(
                        group=group,
                        project=project,
                        is_starter=False,
                        unit_id=group.current_unit,
                    )
                else:
                    selected_project = SelectedProject.objects.get_or_create(
                        group=group,
                        project=project,
                        is_starter=False
                    )                    
    except Group.DoesNotExist:
        del request.session["group"]
        pass

    return Message(message=f"project {projectname} saved")
