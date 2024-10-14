from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import check_password


# from django.template.response import TemplateResponse
# from django.views import View

from .forms import ProfileForm, AccountDeletionForm


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


@login_required
def delete_account(request):
    user = request.user
    if not user.is_authenticated:
        raise (PermissionDenied)    
    if request.method == "POST":
        form = AccountDeletionForm(request.POST)
        if form.is_valid():
            if user.email != form.cleaned_data["email"]:
                messages.error(request, _("Please enter your valid email address to confirm."))
                return render(request, "users/delete_account.html", {"form": form})
            if check_password(form.cleaned_data["password"], user.password):
                messages.error(request, _("Please enter your valid password to confirm."))
                return render(request, "users/delete_account.html", {"form": form})      
            #user.delete()
            user.is_active = False
            user.save()
            message = EmailMessage(
                _("User Account Deletetion Request"),
                render_to_string(
                    "emails/delete_account.txt",
                    {
                        "request": request
                    },
                ),
                settings.EMAIL_FROM_ADDRESS,
                request.user.get_superusers(),
                [],  # bcc
                # reply_to=[],
            )
            message.send()
            messages.success(request, _("Your request has been sent. Please wait for a response."))
            return render(request, "users/delete_account.html", {"done":True})
        else:
            messages.error(request, _("Please correct the following errors:"))
            return render(request, "users/delete_account.html", {"form": form})
    else:
        form = AccountDeletionForm()
        form.referer = request.META.get("HTTP_REFERER")
    return render(request, "users/delete_account.html", {"form": form})