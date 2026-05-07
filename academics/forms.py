from django import forms

from .models import Class, Subject, ClassSubject
from teachers.models import Employee


class ClassForm(forms.ModelForm):

    class_teacher = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Class Teacher"
    )

    class Meta:
        model = Class

        fields = [
            'class_name',
            'class_teacher',
        ]

        widgets = {
            'class_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Example: Class X'
            }),
        }


class SubjectForm(forms.ModelForm):

    class Meta:
        model = Subject

        fields = [
            'subject_name',
            'subject_code',
        ]

        widgets = {
            'subject_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Example: Mathematics'
            }),

            'subject_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Example: MATH'
            }),
        }


class ClassSubjectAssignForm(forms.Form):

    school_class = forms.ModelChoiceField(
        queryset=Class.objects.all().order_by('class_name'),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label="Select Class"
    )

    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all().order_by('subject_name'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Select Subjects"
    )

    full_marks = forms.IntegerField(
        initial=100,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        }),
        label="Full Marks"
    )

    pass_marks = forms.IntegerField(
        initial=35,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        }),
        label="Pass Marks"
    )

    written_marks = forms.IntegerField(
        initial=80,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        }),
        label="Written Marks"
    )

    oral_marks = forms.IntegerField(
        initial=20,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        }),
        label="Oral Marks"
    )

    practical_marks = forms.IntegerField(
        initial=0,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        }),
        label="Practical Marks"
    )

    def clean(self):
        cleaned_data = super().clean()

        full_marks = cleaned_data.get('full_marks') or 0
        pass_marks = cleaned_data.get('pass_marks') or 0
        written_marks = cleaned_data.get('written_marks') or 0
        oral_marks = cleaned_data.get('oral_marks') or 0
        practical_marks = cleaned_data.get('practical_marks') or 0

        if pass_marks > full_marks:
            raise forms.ValidationError(
                "Pass marks cannot be greater than full marks."
            )

        if written_marks + oral_marks + practical_marks > full_marks:
            raise forms.ValidationError(
                "Written + Oral + Practical marks cannot be greater than Full Marks."
            )

        return cleaned_data