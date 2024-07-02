from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

from .models import TrainerRequest, Unit
from apps.users.models import User


def validate_tos(value):
    if not value:
        raise ValidationError(
            _("You must agree to our Terms of Service!"),
            params={"value": value},
        )


def is_valid_user(value):
    try:
        return User.objects.get(username=value)
    except User.DoesNotExist:
        raise ValidationError(
            _(f"User with username {value} does not exist!"),
            params={"value": value},
        )


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ["number", "title", "description"]


class TrainerRequestForm(forms.ModelForm):
    website = forms.CharField(validators=[URLValidator])
    tos = forms.BooleanField(validators=[validate_tos])
    referer = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = TrainerRequest
        fields = [
            "full_name",
            "phone_number",
            "organization",
            "role",
            "type",
            "website",
            "tos",
        ]


class AddMemberForm(forms.Form):
    username = forms.CharField(
        label="Username", max_length=250, validators=[is_valid_user]
    )


class BulkAddForm(forms.Form):
    data = forms.CharField(
        label="Provide a comma seperated list of user and password",
        widget=forms.Textarea(attrs={"placeholder": "user1, 1234\nuser2, 4321"}),
    )
