from django import forms
from .models import Admission


class AdmissionForm(forms.ModelForm):

    class Meta:
        model = Admission

        fields = [
            "student_name",
            "father_name",
            "mother_name",
            "date_of_birth",
            "gender",
            "student_class",
            "aadhaar_no",
            "mobile",
            "guardian_mobile",
            "address",
            "previous_school",
            "transport_required",
            "hostel_required",
            "student_photo",
        ]

        widgets = {

            "student_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "father_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "mother_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "date_of_birth": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date"
                }
            ),

            "gender": forms.Select(
                attrs={"class": "form-select"}
            ),

            "student_class": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "aadhaar_no": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "mobile": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "guardian_mobile": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2
                }
            ),

            "previous_school": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "transport_required": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),

            "hostel_required": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),

            "student_photo": forms.FileInput(
                attrs={"class": "form-control"}
            ),

        }