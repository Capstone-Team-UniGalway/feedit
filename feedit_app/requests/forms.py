from django import forms
from .models import Request, RequestReply

class RequestForm(forms.ModelForm):
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