from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import Thread


class ThreadForm(forms.ModelForm):
    """Form for creating and updating threads."""

    class Meta:
        model = Thread
        fields = ["title", "content", "type", "visibility"]
        widgets = {
            "content": CKEditor5Widget(
                attrs={"class": "django_ckeditor_5"}, config_name="extends"
            )
        }


class ThreadReplyForm(forms.ModelForm):
    """Form for creating replies to threads."""

    class Meta:
        model = Thread
        fields = ["content"]
        widgets = {
            "content": CKEditor5Widget(
                attrs={"class": "django_ckeditor_5"}, config_name="extends"
            )
        }
