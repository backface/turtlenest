from django import forms
from .models import Project, Comment, FlaggedProject, Image, Category
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row
from crispy_tailwind.tailwind import CSSContainer


helper = FormHelper()
helper.label_class = "inline"  # "text-gray-700 text-sm font-bold mb-2"
helper.css_container = CSSContainer(
    {
        "base": "base",
        "text": "mt-4 mb-10",
        "textarea": "mt-2 mb-4 w-full",
        # "checkbox": "accent-primary mr-4 ml-1"
    }
)


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["is_public", "is_published", "notes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = helper
        self.helper.layout = Layout(
            "notes",
            Fieldset(
                "Privacy Settings",
                Row(
                    "is_public",
                    "is_published",
                    css_class="border border-gray-300 border-rounded p-4 pb-2 flex flex-row mb-4",
                ),
            ),
        )
        # self.helper.add_input(Submit('submit', 'Submit'))


class CommentForm(forms.ModelForm):
    # contents = MarkdownxFormField(min_length=1)
    class Meta:
        model = Comment
        fields = ["contents", "project", "author"]
        widgets = {"project": forms.HiddenInput(), "author": forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.label_class = "hidden"


class CategoriesForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["categories"]

    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(), widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.label_class = "hidden"


class FlagProjectForm(forms.ModelForm):
    reason = forms.CharField(
        widget=forms.Textarea(
            attrs={"placeholder": "State the reason for reporting the project here ..."}
        )
    )

    class Meta:
        model = FlaggedProject
        fields = [
            "reason",
        ]
        widgets = {"project": forms.HiddenInput(), "user": forms.HiddenInput()}


class UploadMediaForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ["file", "title", "caption"]
