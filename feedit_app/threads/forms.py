# forms.py
from django import forms

from django_ckeditor_5.widgets import CKEditor5Widget
from utils.sanitizers import sanitize_html
from .models import Thread


class ThreadForm(forms.ModelForm):

    def __init__(self, *args, mention_feed=None, **kwargs):
        super().__init__(*args, **kwargs)
        if mention_feed:
            self.fields["content"].widget.config.setdefault("mention", {})["feeds"] = [
                {
                    "marker": "@",
                    "feed": mention_feed,
                    "minimumCharacters": 0,
                }
            ]

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

    def clean_content(self):
        return sanitize_html(self.cleaned_data.get("content", ""))


class ThreadReplyForm(forms.ModelForm):

    def __init__(self, *args, mention_feed=None, **kwargs):
        super().__init__(*args, **kwargs)
        if mention_feed:
            self.fields["content"].widget.config.setdefault("mention", {})["feeds"] = [
                {
                    "marker": "@",
                    "feed": mention_feed,
                    "minimumCharacters": 0,
                }
            ]

    class Meta:
        model = Thread
        fields = ["content"]
        widgets = {
            "content": CKEditor5Widget(
                attrs={"class": "django_ckeditor_5 w-full textarea"},
                config_name="extends",
            ),
        }

    def clean_content(self):
        return sanitize_html(self.cleaned_data.get("content", ""))
