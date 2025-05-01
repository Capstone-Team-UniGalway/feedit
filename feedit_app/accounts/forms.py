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
        # Override the login field to use email
        self.fields["login"].widget = forms.EmailInput(
            attrs={
                "placeholder": "Email address",
                "class": "input input-bordered w-full",
            }
        )
        self.fields["login"].label = "Email"
        # Style the password field
        self.fields["password"].widget = forms.PasswordInput(
            attrs={"placeholder": "Password", "class": "input input-bordered w-full"}
        )
        # Style the remember field
        self.fields["remember"].widget = forms.CheckboxInput(
            attrs={"class": "checkbox"}
        )

    def clean(self):
        cleaned_data = super().clean()

        user = getattr(self, "user", None)

        if user and getattr(user, "is_deleted", False):
            self.add_error("login", "This account has been closed.")
            raise forms.ValidationError("Login blocked due to deleted status.")

        return cleaned_data


class CustomSignupForm(AllauthSignupForm):
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(
            attrs={"placeholder": "First name", "class": "input input-bordered w-full"}
        ),
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(
            attrs={"placeholder": "Last name", "class": "input input-bordered w-full"}
        ),
    )
    type = forms.ChoiceField(
        choices=User.UserType.choices,
        widget=forms.Select(attrs={"class": "select select-bordered w-full"}),
    )

    def __init__(self, *args, **kwargs):
        initial_role = kwargs.pop("initial_role", None)
        super().__init__(*args, **kwargs)
        if initial_role:
            self.fields["type"].initial = initial_role

        # Style the email field
        self.fields["email"].widget = forms.EmailInput(
            attrs={
                "placeholder": "Email address",
                "class": "input input-bordered w-full",
            }
        )
        # Style the password fields
        self.fields["password1"].widget = forms.PasswordInput(
            attrs={"placeholder": "Password", "class": "input input-bordered w-full"}
        )
        self.fields["password2"].widget = forms.PasswordInput(
            attrs={
                "placeholder": "Confirm password",
                "class": "input input-bordered w-full",
            }
        )

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.type = self.cleaned_data["type"]
        user.save()
        return user


class UserProfileForm(forms.ModelForm):
    # Override the model fields to make them required in the form
    job_title = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"class": "input input-bordered w-full"}),
        help_text="Your current role or position",
    )
    bio = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={"class": "textarea textarea-bordered w-full"}),
        help_text="Tell us about yourself",
        min_length=20,
    )

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
            "privacy": forms.Select(attrs={"class": "select select-bordered w-full"}),
        }
        help_texts = {
            "privacy": (
                "Public: any user can view; Private: nobody can view; "
                "Internal: users within company can view"
            ),
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
