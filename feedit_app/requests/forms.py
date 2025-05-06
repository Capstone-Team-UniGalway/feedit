from django import forms
from django.contrib.contenttypes.models import ContentType
from .models import Request, RequestReply

class RequestForm(forms.ModelForm):
    verification_document = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'file-input file-input-bordered w-full'})
    )

    class Meta:
        model = Request
        fields = ['type', 'title', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'textarea'})
        }

class RequestReplyForm(forms.ModelForm):
    class Meta:
        model = RequestReply
        fields = ['content']