from django import forms
from .models import Review, ReviewReply


class ReviewForm(forms.ModelForm):
    """Form for creating reviews."""

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        self.is_authenticated = self.user and self.user.is_authenticated

        # Add guest_name field only for anonymous users
        if not self.is_authenticated:
            self.fields["guest_name"] = forms.CharField(
                required=False,  # We'll enforce conditionally in clean()
                max_length=100,
                widget=forms.TextInput(
                    attrs={
                        "class": "input input-bordered w-full",
                        "placeholder": "Your name",
                    }
                ),
                label="Your Name",
            )

    def clean(self):
        cleaned_data = super().clean()
        is_anonymous = cleaned_data.get("is_anonymous", False)

        # Assign user to model instance for moderation/uniqueness purposes
        if self.is_authenticated:
            self.instance.user = self.user

        # Assign guest_name if provided
        if "guest_name" in self.fields:
            self.instance.guest_name = cleaned_data.get("guest_name")

            # Guest name is required if not anonymous
            if not is_anonymous and not self.instance.guest_name:
                self.add_error(
                    "guest_name", "Your name is required if not posting anonymously."
                )

        return cleaned_data

    class Meta:
        model = Review
        fields = ["rating", "content", "is_anonymous"]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "textarea textarea-bordered w-full",
                    "rows": "4",
                    "placeholder": "Write your review here...",
                }
            ),
            "is_anonymous": forms.CheckboxInput(attrs={"class": "checkbox"}),
        }
        labels = {"is_anonymous": "Post anonymously"}


class ReviewReplyForm(forms.ModelForm):
    """Form for replying to reviews."""

    class Meta:
        model = ReviewReply
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "textarea textarea-bordered w-full",
                    "rows": "4",
                    "placeholder": "Write your reply here...",
                }
            )
        }
