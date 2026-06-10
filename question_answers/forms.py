from django import forms
from .models import StudentQuestion


class StudentQuestionForm(forms.ModelForm):
    class Meta:
        model = StudentQuestion
        fields = ["class_assigned", "subject", "title", "question_text", "attachment"]
        widgets = {
            "class_assigned": forms.Select(attrs={"class": "form-select"}),
            "subject": forms.TextInput(attrs={"class": "form-control", "placeholder": "Subject"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Question title"}),
            "question_text": forms.Textarea(attrs={"class": "form-control", "rows": 5, "placeholder": "Write your question"}),
            "attachment": forms.FileInput(attrs={"class": "form-control"}),
        }


class TeacherAnswerForm(forms.ModelForm):
    class Meta:
        model = StudentQuestion
        fields = ["answer_text", "answer_file", "status", "is_visible_to_parent"]
        widgets = {
            "answer_text": forms.Textarea(attrs={"class": "form-control", "rows": 5, "placeholder": "Write answer / solution"}),
            "answer_file": forms.FileInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "is_visible_to_parent": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
