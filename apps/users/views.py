from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.core.exceptions import PermissionDenied


# from django.template.response import TemplateResponse
# from django.views import View

from .forms import ProfileForm


def profile(request):
    user = request.user
    if not user.is_authenticated:
        raise (PermissionDenied)
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Your profile has been updated."))
            return render(request, "users/profile.html", {"user": user, "form": form})
        else:
            messages.error(request, _("Please correct the following errors:"))
            return render(request, "users/profile.html", {"user": user, "form": form})
    else:
        form = ProfileForm(instance=user)
    return render(request, "users/profile.html", {"user": user, "form": form})
