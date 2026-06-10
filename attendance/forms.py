from django import forms

from .models import Holiday


# =========================================================
# HOLIDAY FORM
# =========================================================

class HolidayForm(forms.ModelForm):
    class Meta:
        model = Holiday

        fields = [
            "title",
            "date",
            "holiday_type",
            "is_half_day",
            "is_active",
            "note",
        ]

        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Holiday Title",
            }),

            "date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),

            "holiday_type": forms.Select(attrs={
                "class": "form-select",
            }),

            "is_half_day": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),

            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),

            "note": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Optional Note",
            }),
        }
