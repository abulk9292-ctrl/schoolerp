from django import forms
from .models import OnlineAdmission


class OnlineAdmissionForm(forms.ModelForm):
    class Meta:
        model = OnlineAdmission
        fields = [
            "student_name",
            "father_name",
            "mother_name",
            "date_of_birth",
            "class_applied",
            "phone",
            "address",
            "aadhaar_number",
            "photo",
        ]

        widgets = {
            "student_name": forms.TextInput(attrs={"class": "form-control"}),
            "father_name": forms.TextInput(attrs={"class": "form-control"}),
            "mother_name": forms.TextInput(attrs={"class": "form-control"}),
            "date_of_birth": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "class_applied": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "aadhaar_number": forms.TextInput(attrs={"class": "form-control"}),
            "photo": forms.FileInput(attrs={"class": "form-control"}),
        }