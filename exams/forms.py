from django import forms
from .models import Exam, ExamRoutine, ExamResult


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'academic_session': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class ExamRoutineForm(forms.ModelForm):
    class Meta:
        model = ExamRoutine
        fields = '__all__'
        widgets = {
            'exam': forms.Select(attrs={'class': 'form-control'}),
            'school_class': forms.TextInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'total_marks': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ExamResultForm(forms.ModelForm):
    class Meta:
        model = ExamResult
        fields = '__all__'
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'exam': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'written_marks': forms.NumberInput(attrs={'class': 'form-control'}),
            'oral_marks': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_marks': forms.NumberInput(attrs={'class': 'form-control'}),
        }