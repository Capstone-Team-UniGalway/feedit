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

    def __init__(self, *args, **kwargs):
        # Get user from kwargs
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Customize form based on user type
        if self.user and self.user.type == 'employer':
            # Employers can only claim companies, not join them
            self.fields['type'].choices = [
                ('claim', 'Claim')
            ]
            self.fields['type'].initial = 'claim'
            # Use readonly instead of disabled so the value is still submitted
            self.fields['type'].widget.attrs['readonly'] = True
        elif self.user and self.user.type == 'employee':
            # Employees can only join companies, not claim them
            self.fields['type'].choices = [
                ('join', 'Join')
            ]
            self.fields['type'].initial = 'join'
            # Use readonly instead of disabled so the value is still submitted
            self.fields['type'].widget.attrs['readonly'] = True

class RequestReplyForm(forms.ModelForm):
    class Meta:
        model = RequestReply
        fields = ['content']