from django import forms
from django.core.exceptions import ValidationError

from .models import Company


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            "name",
            "industry",
            "bio",
            "country",
            "city",
            "date_founded",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "industry": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "bio": forms.Textarea(
                attrs={"class": "textarea textarea-bordered w-full", "rows": 4}
            ),
            "country": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "city": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "date_founded": forms.DateInput(
                attrs={"class": "input input-bordered w-full", "type": "date"}
            ),
        }

    def clean_name(self):
        name = self.cleaned_data.get("name", "")
        if len(name) > 100:
            raise ValidationError("Company name must be 100 characters or less.")
        return name.strip()

    def clean_industry(self):
        industry = self.cleaned_data.get("industry", "")
        return industry.strip()
