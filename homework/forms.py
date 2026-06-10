from django import forms

from .models import Homework, HomeworkSubmission


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


class HomeworkForm(forms.ModelForm):
    school_class = forms.ChoiceField(
        choices=CLASS_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"})
    )

    class Meta:
        model = Homework
        fields = [
            "title",
            "school_class",
            "subject",
            "description",
            "given_by",
            "due_date",
            "attachment",
            "status",
        ]

        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "subject": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5
            }),
            "given_by": forms.Select(attrs={"class": "form-control"}),
            "due_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
            "attachment": forms.FileInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
        }


class HomeworkSubmissionForm(forms.ModelForm):
    class Meta:
        model = HomeworkSubmission
        fields = [
            "answer_text",
            "submitted_file",
        ]

        widgets = {
            "answer_text": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Write your homework answer here..."
            }),
            "submitted_file": forms.FileInput(attrs={
                "class": "form-control"
            }),
        }


class HomeworkReviewForm(forms.ModelForm):
    class Meta:
        model = HomeworkSubmission
        fields = [
            "status",
            "marks",
            "teacher_remarks",
        ]

        widgets = {
            "status": forms.Select(attrs={"class": "form-control"}),
            "marks": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01"
            }),
            "teacher_remarks": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Write teacher review..."
            }),
        }