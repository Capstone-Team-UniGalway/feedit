from django import forms
from django.contrib.auth import get_user_model
from allauth.account.forms import (
    LoginForm as AllauthLoginForm,
    SignupForm as AllauthSignupForm,
)

User = get_user_model()


class CustomLoginForm(AllauthLoginForm):
    # remember = forms.BooleanField(required=False, initial=False, label="Remember Me")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class CustomSignupForm(AllauthSignupForm):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    type = forms.ChoiceField(choices=User.UserType.choices)

    def __init__(self, *args, **kwargs):
        initial_role = kwargs.pop("initial_role", None)
        super().__init__(*args, **kwargs)
        if initial_role:
            self.fields["type"].initial = initial_role

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.type = self.cleaned_data["type"]
        user.save()
        return user


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "job_title", "bio", "privacy"]
        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "input input-bordered w-full"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "input input-bordered w-full"}
            ),
            "job_title": forms.TextInput(
                attrs={"class": "input input-bordered w-full"}
            ),
            "bio": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full"}),
            "privacy": forms.Select(attrs={"class": "select select-bordered w-full"}),
        }
