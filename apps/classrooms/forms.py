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
    tos = forms.BooleanField(validators=[validate_tos], 
        required=True,
        label='I agree to the Terms of Service',
        help_text='As a host of a group and regular registered user you have accepted our \
        <a href="/page/tos"> Terms of Service</a> It is in your responsibility that your \
        group members follow this TOS during the period of this’ group’s activities. \
        If you are aware of offensive content in one of your member projects \
        and you need help to handle it, we are happy to assist. \
        We reserve the right to revoke the shared status of anything that, \
        in our sole judgment, is offensive to our community standards.'
    )
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
