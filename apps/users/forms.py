from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from allauth.account.forms import SignupForm
from crispy_forms.helper import FormHelper
from django.utils.html import format_html
from crispy_forms.layout import Layout, Fieldset, HTML
from crispy_tailwind.tailwind import CSSContainer
from django.core.exceptions import ValidationError
from PIL import Image
import io
from django.core.files.uploadedfile import InMemoryUploadedFile
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

def validate_confirmation(value):
    if not value:
        raise ValidationError(
            _("You must agree to this!"),
            params={"value": value},
        )


class TurtleStitchSignupForm(SignupForm):
    class Meta:
        model = User

    toc = forms.BooleanField(
        label='Terms of Service and Privacy Agreement', 
        help_text='I have read and agree to the <a href="/page/tos">Terms of Service</a> and the \
            <a href="/page/privacy">Privacy Policy</a>'
        )
    # dmca = forms.BooleanField(
    #     label='DMCA Disclaimer', 
    #     help_text='I have read and agree to the <a href="/page/dmca" class="underline">DMCA Disclaimer</a>'
    #     )    
    age_confirm = forms.BooleanField(
        label='Age confirmation',
        help_text=mark_safe(_("I confirm that I am at least 16 years old, or I am being signed in by \
            an adult or teacher who is supervising my use of Turtlestitch.org."))
    )
    # def save(self, user):
    #     user.gender = self.cleaned_data['gender']
    #     user.save()


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["avatar", "about", "location", "notify_comment", "notify_like"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

         # Create HTML for current avatar preview
        current_avatar = ''
        if self.instance and self.instance.avatar_url:
            current_avatar = format_html(
                '<div class="mb-4"><img src="{}" alt="Current avatar" '
                'class="w-24 h-24 rounded-full object-cover border-2 border-gray-200"/></div>',
                self.instance.avatar_url
            )
            
        self.helper = helper
        self.helper.layout = Layout(
            Fieldset(
                "Avatar",  
                HTML(current_avatar),          
                "avatar",
                css_class="border border-gray-300 border-rounded p-4",
            ),
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


    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            # Open image using PIL
            img = Image.open(avatar)
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Calculate dimensions for center crop to square
            width, height = img.size
            size = min(width, height)
            left = (width - size) // 2
            top = (height - size) // 2
            right = left + size
            bottom = top + size
            
            # Crop and resize
            img = img.crop((left, top, right, bottom))
            img = img.resize((256, 256), Image.LANCZOS)
            
            # Save the processed image
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85)
            output.seek(0)
            
            # Return the processed image as InMemoryUploadedFile
            return InMemoryUploadedFile(
                output,
                'ImageField',
                f"{avatar.name.split('.')[0]}.jpg",
                'image/jpeg',
                output.getbuffer().nbytes,
                None
            )
        return avatar

class AccountDeletionForm(forms.Form):
    class Meta:
        model = User

    sure = forms.BooleanField(
        label='Are you sure, you want to delete your account?', 
        help_text='I confirm I want to delete my account and all associated data.',
        required=True,
        validators=[validate_confirmation]
        )

    email = forms.EmailField(
        label="E-mail",
        help_text='Please confirm and enter your e-mail address.',
        required=True,
    )  

    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Password",
        help_text='Please confirm your password.',
        required=True,
    )    
    