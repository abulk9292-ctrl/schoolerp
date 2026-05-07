from django import forms
from .models import Notice


CLASS_CHOICES = [
    ("", "Select Class"),
    ("Nursery", "Nursery"),
    ("LKG", "LKG"),
    ("UKG", "UKG"),
    ("Class I", "Class I"),
    ("Class II", "Class II"),
    ("Class III", "Class III"),
    ("Class IV", "Class IV"),
    ("Class V", "Class V"),
    ("Class VI", "Class VI"),
    ("Class VII", "Class VII"),
    ("Class VIII", "Class VIII"),
    ("Class IX", "Class IX"),
    ("Class X", "Class X"),
]


class NoticeForm(forms.ModelForm):
    school_class = forms.ChoiceField(
        choices=CLASS_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-control"})
    )

    class Meta:
        model = Notice
        fields = [
            "title",
            "notice_type",
            "target",
            "school_class",
            "description",
            "attachment",
            "published_by",
            "expiry_date",
            "status",
            "is_pinned",
        ]

        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "notice_type": forms.Select(attrs={"class": "form-control"}),
            "target": forms.Select(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "attachment": forms.FileInput(attrs={"class": "form-control"}),
            "published_by": forms.Select(attrs={"class": "form-control"}),
            "expiry_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "is_pinned": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }