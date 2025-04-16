from django import forms
from django.contrib.auth import get_user_model
from allauth.account.forms import (
    LoginForm as AllauthLoginForm,
    SignupForm as AllauthSignupForm,
    ResetPasswordForm,
)

User = get_user_model()


class CustomLoginForm(AllauthLoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        user = getattr(self, "user", None)

        if user and getattr(user, "is_deleted", False):
            self.add_error("login", "This account has been closed.")
            raise forms.ValidationError("Login blocked due to deleted status.")

        return cleaned_data


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


class CustomResetPasswordForm(ResetPasswordForm):
    def clean_email(self):
        email = (
            super().clean_email()
        )  # ✅ Important: preserve Allauth behavior (sets self.users)

        # Run soft-delete check against each resolved user
        for user in getattr(self, "users", []):
            if user.is_deleted:
                raise forms.ValidationError("This account has been closed.")

        return email
