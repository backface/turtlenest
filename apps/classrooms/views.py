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

# from django.template.response import TemplateResponse
# from django.views import View
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from apps.projects.models import Project
from apps.users.models import User
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
            return self.request.user.is_teacher
        except AttributeError:
            return False


class GroupDetailView(LoginRequiredMixin, DetailView):
    model = Group
    # template_name = 'group_detail.html'
    # context_object_name = 'group'

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
    print(group)
    print(group.membership_set.all)
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
def bulk_add(request, id):
    group = get_object_or_404(Group, pk=id)
    if not group.is_host(request.user):
        raise (PermissionDenied)
    if request.method == "POST":
        bulkAddForm = BulkAddForm(request.POST)
        if bulkAddForm.is_valid():
            try:
                csv_data = bulkAddForm.cleaned_data["data"]
                reader = csv.reader(io.StringIO(csv_data))
                for line in reader:
                    if len(line) == 2:
                        username = f"group{group.id}{line[0].strip()}"
                        password = line[1].strip()
                        if username and password:
                            u, created = User.objects.get_or_create(
                                username=username,
                            )
                            u.mentor = request.user
                            u.set_password(password)
                            u.add_to_group("Puppets")
                            u.save()
                            group.members.add(u)
                    else:
                        raise (Exception("Invalid CSV data"))
            except Exception as e:
                messages.error(request, f"Error adding members: {e}")
            else:
                messages.success(request, "Members added")
        # if request.htmx:
        #    return render(request, "classrooms/_members_bulkadd.html", { "group": group, "bulkAddForm": bulkAddForm })
        # else:
        return redirect(reverse("groups:group_detail", args=[group.id]))
    else:
        bulkAddForm = BulkAddForm()
    # if request.htmx:
    #    return render(request, "classrooms/_members_bulkadd.html", { "group": group, "bulkAddForm": bulkAddForm })
    # else:
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
                    {"trainer_request": trainer_request, "request": request},
                ),
                settings.EMAIL_FROM_ADDRESS,
                request.user.get_superusers(),
                [],  # bcc
                # reply_to=[],
            )
            message.send()
            messages.success(request, _("Your trainer request has been sent."))
            return redirect(request.META["HTTP_REFERER"])
        else:
            messages.error(request, _("Please correct the following errors:"))
            return render(request, "classrooms/trainer_request.html", {"form": form})
    else:
        form = TrainerRequestForm()
        form.referer = request.META.get("HTTP_REFERER")
    return render(request, "classrooms/trainer_request.html", {"form": form})
