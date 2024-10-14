from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from allauth.account.forms import SignupForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset
from crispy_tailwind.tailwind import CSSContainer

from .models import User


helper = FormHelper()
helper.label_class = "inline"
helper.css_container = CSSContainer(
    {
        "base": "base",
        "text": "mt-4 mb-10",
        "textarea": "mt-2 mb-4 h-24 w-full",
        # "checkbox": "accent-primary mr-4 ml-1"
    }
)


class TurtleStitchSignupForm(SignupForm):
    class Meta:
        model = User

    toc = forms.BooleanField(
        label='Terms of Service', 
        help_text='I have read and agree to the <a href="/page/tos" class="underline">Terms of Service</a>'
        )
    dmca = forms.BooleanField(
        label='DMCA Disclaimer', 
        help_text='I have read and agree to the <a href="/page/dmca" class="underline">DMCA Disclaimer</a>'
        )    
    age_confirm = forms.BooleanField(
        label='Age and Privacy Policy',
        help_text=mark_safe(_("By signing up, you confirm that you are at least 16 years old (or the minimum age required by your country’s laws) and consent to the processing of your personal \
            data in accordance with our <a href=\"/page/privacy\" class=\"underline\">Privacy Policy</a>. \
            If you are under the required age, a parent or legal guardian must create and manage the account on your behalf."))
    )
    # def save(self, user):
    #     user.gender = self.cleaned_data['gender']
    #     user.save()


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["about", "location", "notify_comment", "notify_like"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = helper
        self.helper.layout = Layout(
            Fieldset(
                None,
                "location",
                "about",
            ),
            Fieldset(
                "Notifications:",
                "notify_comment",
                "notify_like",
                css_class="border border-gray-300 border-rounded p-4",
            ),
            # Row(
            #     'notify_comment',
            #     'notify_like',
            #     css_class='flex flex-row',
            # ),
        )

        # self.helper.form_id = 'id-exampleForm'
        # self.helper.form_class = 'blueForms'
        # self.helper.form_method = 'post'
        # self.helper.form_action = 'submit_survey'
        # self.helper.add_input(Submit('submit', 'Submit'))
