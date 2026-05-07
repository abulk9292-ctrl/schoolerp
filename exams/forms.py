from django import forms
from django.core.exceptions import ValidationError

from students.models import Student
from .models import Exam, ExamRoutine, ExamResult


# =========================
# HELPERS
# =========================

def get_class_choices():
    classes = []

    try:
        from academics.models import Class

        classes = list(
            Class.objects.all()
            .order_by("class_name")
            .values_list("class_name", "class_name")
        )

    except Exception:
        pass

    if not classes:
        try:
            unique_classes = Student.objects.exclude(
                school_class__isnull=True
            ).exclude(
                school_class=""
            ).values_list(
                "school_class",
                flat=True
            ).distinct()

            classes = [(c, c) for c in unique_classes]

        except Exception:
            pass

    return classes

# =========================
# EXAM FORM
# =========================

class ExamForm(forms.ModelForm):

    class Meta:
        model = Exam

        fields = [
            'name',
            'academic_session',
            'start_date',
            'end_date',
            'is_active',
        ]

        widgets = {

            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Annual Examination'
            }),

            'academic_session': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '2025-26'
            }),

            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),

            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),

            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError(
                    "End date cannot be before start date."
                )

        return cleaned_data


# =========================
# EXAM ROUTINE FORM
# =========================

class ExamRoutineForm(forms.ModelForm):

    school_class = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_school_class'
        })
    )

    subject = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_subject'
        })
    )

    class Meta:
        model = ExamRoutine

        fields = [
            'exam',
            'school_class',
            'subject',
            'date',
            'start_time',
            'end_time',
            'total_marks',
        ]

        widgets = {

            'exam': forms.Select(attrs={
                'class': 'form-select'
            }),

            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),

            'start_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control'
            }),

            'end_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control'
            }),

            'total_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        class_choices = get_class_choices()

        self.fields['school_class'].choices = [
            ('', 'Select Class')
        ] + class_choices

        self.fields['subject'].choices = [
            ('', 'Select Subject')
        ]

        selected_class = None

        # POST
        if self.data.get('school_class'):
            selected_class = self.data.get('school_class')

        # GET INITIAL DATA
        elif self.initial.get('school_class'):
            selected_class = self.initial.get('school_class')

        # EDIT MODE
        elif self.instance.pk:
            selected_class = self.instance.school_class

        # LOAD SUBJECTS
        if selected_class:
            try:
                from academics.models import (
                    Class,
                    ClassSubject
                )

                class_obj = Class.objects.filter(
                    class_name=selected_class
                ).first()

                if class_obj:

                    subjects = ClassSubject.objects.filter(
                        school_class=class_obj,
                        is_active=True
                    ).select_related('subject')

                    self.fields['subject'].choices += [

                        (
                            s.subject.subject_name,
                            s.subject.subject_name
                        )

                        for s in subjects
                    ]

            except Exception:
                pass

    def clean(self):
        cleaned_data = super().clean()

        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time:
            if end_time <= start_time:
                raise ValidationError(
                    "End time must be greater than start time."
                )

        return cleaned_data

# =========================
# EXAM RESULT FORM
# =========================

class ExamResultForm(forms.ModelForm):

    subject = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_subject'
        })
    )

    class Meta:
        model = ExamResult

        fields = [
            'student',
            'exam',
            'subject',
            'written_marks',
            'oral_marks',
            'max_marks',
            'remarks',
        ]

        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'exam': forms.Select(attrs={'class': 'form-select'}),

            'written_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),

            'oral_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),

            'max_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),

            'remarks': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Good / Excellent / Need Improvement'
            }),
        }

    def __init__(self, *args, **kwargs):
        class_name = kwargs.pop('class_name', None)
        super().__init__(*args, **kwargs)

        students = Student.objects.all().order_by('id')

        if class_name:
            try:
                students = students.filter(class_assigned__class_name=class_name)
            except Exception:
                pass

            try:
                students = students.filter(school_class=class_name)
            except Exception:
                pass

        self.fields['student'].queryset = students

        self.fields['subject'].choices = [
            ('', 'Select Subject')
        ]

        if class_name:
            try:
                from academics.models import Class, ClassSubject

                class_obj = Class.objects.filter(class_name=class_name).first()

                if class_obj:
                    class_subjects = ClassSubject.objects.filter(
                        school_class=class_obj,
                        is_active=True
                    ).select_related('subject')

                    self.fields['subject'].choices += [
                        (
                            cs.subject.subject_name,
                            cs.subject.subject_name
                        )
                        for cs in class_subjects
                    ]

            except Exception:
                pass

    def clean(self):
        cleaned_data = super().clean()

        student = cleaned_data.get("student")
        exam = cleaned_data.get("exam")
        subject = cleaned_data.get("subject")

        written_marks = cleaned_data.get("written_marks") or 0
        oral_marks = cleaned_data.get("oral_marks") or 0
        max_marks = cleaned_data.get("max_marks") or 0

        if written_marks + oral_marks > max_marks:
            raise ValidationError(
                "Written + Oral marks cannot be greater than Max Marks."
            )

        exists = ExamResult.objects.filter(
            student=student,
            exam=exam,
            subject=subject
        )

        if self.instance.pk:
            exists = exists.exclude(pk=self.instance.pk)

        if exists.exists():
            raise ValidationError(
                "This student's subject marks already exist for this exam."
            )

        return cleaned_data