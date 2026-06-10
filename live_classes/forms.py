from django import forms
from .models import LiveClass


class LiveClassForm(forms.ModelForm):
    class Meta:
        model = LiveClass
        fields = [
            "title",
            "class_assigned",
            "section",
            "subject",
            "teacher",
            "meeting_link",
            "meeting_id",
            "passcode",
            "start_time",
            "end_time",
            "description",
            "status",
            "is_active",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Live class title"}),
            "class_assigned": forms.Select(attrs={"class": "form-select"}),
            "section": forms.TextInput(attrs={"class": "form-control", "placeholder": "Section"}),
            "subject": forms.TextInput(attrs={"class": "form-control", "placeholder": "Subject"}),
            "teacher": forms.Select(attrs={"class": "form-select"}),
            "meeting_link": forms.URLInput(attrs={"class": "form-control", "placeholder": "Zoom / Google Meet / YouTube Live link"}),
            "meeting_id": forms.TextInput(attrs={"class": "form-control"}),
            "passcode": forms.TextInput(attrs={"class": "form-control"}),
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
