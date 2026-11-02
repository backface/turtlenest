import csv
import io
from django.shortcuts import render, redirect
from django.urls import reverse
from django.urls import reverse_lazy
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.shortcuts import get_object_or_404
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django_htmx.http import HttpResponseClientRefresh
from apps.projects.models import Project
from apps.users.models import User
from allauth.account.models import EmailAddress
from .models import Group, TrainerRequest, Unit, SelectedProject, Membership
from .forms import TrainerRequestForm, UnitForm, AddMemberForm, BulkAddForm


class HostRequiredMixin(UserPassesTestMixin):
    """Ensure that the current user owns the object."""

    def test_func(self):
        try:
            return self.get_object().host == self.request.user
        except AttributeError:
            try:
                return self.get_object().group.host == self.request.user
            except AttributeError:
                return False


class TeacherRequiredMixin(UserPassesTestMixin):
    """Ensure that the current user is a teacher"""

    def test_func(self):
        try:
            return self.request.user.is_teacher or self.request.user.is_superuser
        except AttributeError:
            return False


class GroupDetailView(LoginRequiredMixin, DetailView):
    model = Group
    # template_name = 'group_detail.html'
    # context_object_name = 'group'

    def get_queryset(self):
        # only members and the host may see a group (roster, units, projects);
        user = self.request.user
        if user.is_superuser:
            return Group.objects.all()
        return Group.objects.filter(Q(members=user) | Q(host=user)).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.request.session["group"] = self.object.id
        context["starters"] = self.object.id
        context["addMemberForm"] = AddMemberForm()
        context["bulkAddForm"] = BulkAddForm()
        return context


class GroupListView(LoginRequiredMixin, ListView):
    model = Group
    paginate_by = 10

    def get_queryset(self):
        return Group.objects.filter(members=self.request.user)


class GroupCreateView(TeacherRequiredMixin, CreateView):
    model = Group
    fields = ["title", "description", "introduction"]

    def form_valid(self, form):
        group = form.save(commit=False)
        group.host = self.request.user
        group.save()
        # form.instance.host = self.request.user
        # form.save()
        group.members.add(self.request.user)
        return super().form_valid(form)


class GroupUpdateView(HostRequiredMixin, UpdateView):
    model = Group
    fields = ["title", "description", "introduction"]


class GroupDeleteView(HostRequiredMixin, DeleteView):
    model = Group
    success_url = reverse_lazy("groups:group_list")
    def form_valid(self, form):
        self.request.session["group"] = 0
        messages.success(self.request, "The group was deleted successfully.")
        return super(GroupDeleteView, self).form_valid(form)
    

    

@login_required
def my_groups(request):
    if request.user.is_authenticated:
        groups = Group.objects.filter(members=request.user)
        return render(request, "classrooms/group_list.html", {"groups": groups})
    else:
        return redirect(reverse("account_login"))


@login_required
def leave(request, group_id=0):
    request.session["group"] = 0
    return redirect("groups:group_list")


## units


class UnitUpdateView(HostRequiredMixin, UpdateView):
    model = Unit
    success_url = reverse_lazy("groups:group_list")


@login_required
def create_unit(request, id):
    group = get_object_or_404(Group, pk=id)
    if not group.is_host(request.user):
        raise (PermissionDenied)
    if request.method == "POST":
        form = UnitForm(request.POST, instance=Unit(group=group))
        if form.is_valid():
            form.save()
            return redirect(reverse("groups:group_detail", args=[id]))
    else:
        form = UnitForm(instance=Unit())
        print(form.instance.pk)
    return render(request, "classrooms/unit_form.html", {"form": form})


@login_required
def edit_unit(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    if not unit.group.is_host(request.user):
        raise (PermissionDenied)
    if request.method == "POST":
        form = UnitForm(request.POST, instance=unit)
        if form.is_valid():
            form.save()
            return redirect(reverse("groups:group_detail", args=[unit.group.id]))
    else:
        form = UnitForm(instance=unit)
    return render(request, "classrooms/unit_form.html", {"form": form})


@login_required
def delete_unit(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    if not unit.group.is_host(request.user):
        raise (PermissionDenied)
    if unit.group.current_unit == pk:
        unit.group.current_unit = 0
        unit.group.save()
    unit.delete()

    return redirect(reverse("groups:group_detail", args=[unit.group.id]))


@login_required
def activate_unit(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    if not unit.group.is_host(request.user):
        raise (PermissionDenied)
    unit.group.current_unit = unit.id
    unit.group.save()
    return redirect(reverse("groups:group_detail", args=[unit.group.id]))


@login_required
def deactivate_unit(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    if not unit.group.is_host(request.user):
        raise (PermissionDenied)
    unit.group.current_unit = 0
    unit.group.save()
    return redirect(reverse("groups:group_detail", args=[unit.group.id]))


@login_required
def add_starter(request, group_id, project_id):
    group = get_object_or_404(Group, id=group_id)
    project = get_object_or_404(Project, id=project_id)
    if not group.is_host(request.user):
        raise (PermissionDenied)
    newproject = SelectedProject(
        group=group, project=project, is_starter=True, unit_id=group.current_unit or ""
    )
    newproject.save()
    return redirect(reverse("groups:group_detail", args=[group.id]))


@login_required
def add_member(request, id):
    group = get_object_or_404(Group, pk=id)
    if not group.is_host(request.user):
        raise (PermissionDenied)
    if request.method == "POST":
        addMemberForm = AddMemberForm(request.POST)
        if addMemberForm.is_valid():
            addMemberForm.cleaned_data["username"]
            membership, created = Membership.objects.get_or_create(
                group=group,
                user=User.objects.get(username=addMemberForm.cleaned_data["username"]),
            )
            if created:
                messages.success(request, "Member added")
            else:
                messages.error(request, "Member already exists")
        if request.htmx:
            return render(
                request,
                "classrooms/_members.html",
                {"group": group, "addMemberForm": addMemberForm},
            )
        else:
            return redirect(reverse("groups:group_detail", args=[group.id]))
    else:
        addMemberForm = AddMemberForm()
    return redirect(reverse("groups:group_detail", args=[group.id]))


@login_required
def remove_member(request, id, username):
    group = get_object_or_404(Group, pk=id)
    if not group.is_host(request.user):
        raise (PermissionDenied)
    membership = Membership.objects.get(group=group, user__username=username)
    membership.delete()
    messages.success(request, "Member removed")
    if request.htmx:
        return render(
            request,
            "classrooms/_members.html",
            {"group": group, "addMemberForm": AddMemberForm()},
        )
    else:
        return redirect(reverse("groups:group_detail", args=[group.id]))


@login_required
def remove_project(request, id, project_id):
    group = get_object_or_404(Group, pk=id)
    if not group.is_host(request.user):
        raise  (PermissionDenied)
    project = SelectedProject.objects.get(group=group, pk=project_id)
    project.delete()
    messages.success(request, "Project removed")
    return HttpResponseClientRefresh()
    

BULK_ADD_MAX_ROWS = 200


def _parse_bulk_add(csv_data, group, host):
    """Validate every CSV row before anything is written.

    Returns ``(rows, errors)``; ``rows`` holds ``(username, password, user)``
    with ``user`` None for accounts to create. Usernames keep the historic
    ``group<id><name>`` scheme, so an existing account may only be updated
    when it is a pupil account created by this host (``mentor``). That stops
    a host from resetting the password of anybody else's account whose name
    happens to match (e.g. group 30 + "1a" and group 3 + "01a").
    """
    rows, errors, seen = [], [], set()
    lines = [line for line in csv.reader(io.StringIO(csv_data)) if any(f.strip() for f in line)]
    if len(lines) > BULK_ADD_MAX_ROWS:
        return [], [_("Too many rows (at most %(max)s).") % {"max": BULK_ADD_MAX_ROWS}]
    for number, line in enumerate(lines, start=1):
        if len(line) != 2 or not line[0].strip() or not line[1].strip():
            errors.append(_("Line %(n)s: expected 'name, password'.") % {"n": number})
            continue
        name, password = line[0].strip(), line[1].strip()
        username = f"group{group.id}{name}"
        try:
            User.username_validator(username)
            if len(username) > User._meta.get_field("username").max_length:
                raise ValidationError("too long")
        except ValidationError:
            errors.append(_("Line %(n)s: invalid name '%(name)s'.") % {"n": number, "name": name})
            continue
        if username.lower() in seen:
            errors.append(_("Line %(n)s: '%(name)s' is listed twice.") % {"n": number, "name": name})
            continue
        seen.add(username.lower())
        user = User.objects.filter(username__iexact=username).first()
        if user is not None and not (user.is_puppet and user.mentor_id == host.id):
            errors.append(_("Line %(n)s: the name '%(name)s' is already taken.") % {"n": number, "name": name})
            continue
        rows.append((username, password, user))
    return rows, errors


@login_required
def bulk_add(request, id):
    group = get_object_or_404(Group, pk=id)
    if not group.is_host(request.user):
        raise (PermissionDenied)
    if request.method == "POST":
        bulkAddForm = BulkAddForm(request.POST)
        if bulkAddForm.is_valid():
            rows, errors = _parse_bulk_add(
                bulkAddForm.cleaned_data["data"], group, request.user
            )
            if errors:
                # all or nothing: report every problem, change nothing
                for error in errors:
                    messages.error(request, error)
            else:
                with transaction.atomic():
                    for username, password, user in rows:
                        if user is None:
                            user = User(
                                username=username,
                                # fake email, the pupil has none
                                email=f"{username}@turtlestitch.org",
                                mentor=request.user,
                                notify_comment=False,
                                notify_like=False,
                            )
                        # re-importing an own pupil resets the password
                        user.set_password(password)
                        user.save()
                        user.add_to_group("Puppets")
                        group.members.add(user)

                        # add allauth email account
                        EmailAddress.objects.update_or_create(
                            user=user,
                            email=user.email,
                            defaults={"verified": True, "primary": True},
                        )
                messages.success(request, _("Members added"))
        # if request.htmx:
        #    return render(request, "classrooms/_members_bulkadd.html", { "group": group, "bulkAddForm": bulkAddForm })
        # else:
        return redirect(reverse("groups:group_detail", args=[group.id]))
    return redirect(reverse("groups:group_detail", args=[group.id]))


@login_required
def trainer_request(request):
    if request.method == "POST":
        trainer_request = TrainerRequest(user=request.user)
        form = TrainerRequestForm(request.POST, instance=trainer_request)
        if form.is_valid():
            form.save()
            message = EmailMessage(
                _("New Trainer Request!"),
                render_to_string(
                    "emails/trainer_request.txt",
                    {
                        "trainer_request": trainer_request, 
                        "request": request
                    },
                ),
                settings.EMAIL_FROM_ADDRESS,
                request.user.get_superusers(),
                [],  # bcc
                # reply_to=[],
            )
            message.send()
            messages.success(request, _("Your trainer request has been sent."))
            return redirect("users:profile")
        else:
            messages.error(request, _("Please correct the following errors:"))
            return render(request, "classrooms/trainer_request.html", {"form": form})
    else:
        form = TrainerRequestForm()
        form.referer = request.META.get("HTTP_REFERER")
    return render(request, "classrooms/trainer_request.html", {"form": form})
