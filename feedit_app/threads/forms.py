from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import Thread


class ThreadForm(forms.ModelForm):
    """Form for creating and updating threads."""

    class Meta:
        model = Thread
        fields = ["title", "content", "type", "visibility"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "input input-bordered w-full",
                    "placeholder": "Enter a descriptive title",
                    "required": True,
                }
            ),
            "content": CKEditor5Widget(
                attrs={"class": "django_ckeditor_5 w-full textarea"},
                config_name="extends",
            ),
            "type": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "visibility": forms.Select(
                attrs={"class": "select select-bordered w-full"}
            ),
        }
        help_texts = {
            "type": "Forum threads allow replies; announcements don't.",
            "visibility": (
                "Internal: visible to all. Private: visible to employees only."
            ),
        }


class ThreadReplyForm(forms.ModelForm):
    """Form for creating replies to threads."""

    class Meta:
        model = Thread
        fields = ["content"]
        widgets = {
            "content": CKEditor5Widget(
                attrs={"class": "django_ckeditor_5 w-full textarea"},
                config_name="extends",
            )
        }
