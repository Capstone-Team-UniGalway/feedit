from django import forms

from .models import Request, RequestReply


class RequestForm(forms.ModelForm):
    verification_document = forms.FileField(
        required=False,
        widget=forms.FileInput(
            attrs={"class": "file-input file-input-bordered w-full"}
        ),
    )

    class Meta:
        model = Request
        fields = ["type", "title", "content"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "input input-bordered w-full",
                    "placeholder": "Enter a descriptive title",
                    "required": True,
                }
            ),
            "content": forms.Textarea(attrs={"class": "textarea w-full", "rows": "3"}),
        }

    def __init__(self, *args, **kwargs):
        # Get user and type from kwargs
        self.user = kwargs.pop("user", None)
        request_type = kwargs.pop("request_type", None)
        super().__init__(*args, **kwargs)

        # Restrict type choices to one and make it readonly
        if request_type:
            self.fields["type"].choices = [(request_type, request_type.capitalize())]
            self.fields["type"].initial = request_type
            self.fields["type"].widget.attrs["readonly"] = True


class RequestReplyForm(forms.ModelForm):
    upload_document = forms.FileField(
        required=False,
        widget=forms.FileInput(
            attrs={"class": "file-input file-input-bordered w-full"}
        ),
    )

    class Meta:
        model = RequestReply
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={"class": "textarea w-full", "rows": "3"}),
        }
