from django import forms

from teachers.models import Employee

from .models import (
    AcademicSession,
    Class,
    Section,
    Subject,
    ClassSubject,
    ClassRoutine,
)


# =========================
# ACADEMIC SESSION FORM
# =========================

class AcademicSessionForm(forms.ModelForm):

    class Meta:
        model = AcademicSession

        fields = [
            "session_name",
            "start_date",
            "end_date",
            "is_active",
        ]

        widgets = {
            "session_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Example: 2026-27",
            }),
            "start_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "end_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }


# =========================
# CLASS FORM
# =========================

class ClassForm(forms.ModelForm):

    class_teacher = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            "class": "form-select",
        }),
        label="Class Teacher"
    )

    class Meta:
        model = Class

        fields = [
            "class_name",
            "class_teacher",
            "is_active",
        ]

        widgets = {
            "class_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Example: Class X",
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }


# =========================
# SECTION FORM
# =========================

class SectionForm(forms.ModelForm):

    class Meta:
        model = Section

        fields = [
            "school_class",
            "section_name",
            "is_active",
        ]

        widgets = {
            "school_class": forms.Select(attrs={
                "class": "form-select",
            }),
            "section_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Example: A",
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }


# =========================
# SUBJECT FORM
# =========================

class SubjectForm(forms.ModelForm):

    class Meta:
        model = Subject

        fields = [
            "subject_name",
            "subject_code",
            "is_active",
        ]

        widgets = {
            "subject_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Example: Mathematics",
            }),
            "subject_code": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Example: MATH",
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }


# =========================
# CLASS SUBJECT ASSIGN FORM
# =========================

class ClassSubjectAssignForm(forms.Form):

    school_class = forms.ModelChoiceField(
        queryset=Class.objects.filter(is_active=True).order_by("class_name"),
        required=True,
        widget=forms.Select(attrs={
            "class": "form-select",
        }),
        label="Select Class"
    )

    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.filter(is_active=True).order_by("subject_name"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Select Subjects"
    )

    full_marks = forms.IntegerField(
        initial=100,
        min_value=1,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
        }),
        label="Full Marks"
    )

    pass_marks = forms.IntegerField(
        initial=35,
        min_value=0,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
        }),
        label="Pass Marks"
    )

    written_marks = forms.IntegerField(
        initial=80,
        min_value=0,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
        }),
        label="Written Marks"
    )

    oral_marks = forms.IntegerField(
        initial=20,
        min_value=0,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
        }),
        label="Oral Marks"
    )

    practical_marks = forms.IntegerField(
        initial=0,
        min_value=0,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
        }),
        label="Practical Marks"
    )

    def clean(self):
        cleaned_data = super().clean()

        full_marks = cleaned_data.get("full_marks") or 0
        pass_marks = cleaned_data.get("pass_marks") or 0
        written_marks = cleaned_data.get("written_marks") or 0
        oral_marks = cleaned_data.get("oral_marks") or 0
        practical_marks = cleaned_data.get("practical_marks") or 0

        if pass_marks > full_marks:
            raise forms.ValidationError(
                "Pass marks cannot be greater than full marks."
            )

        if written_marks + oral_marks + practical_marks > full_marks:
            raise forms.ValidationError(
                "Written + Oral + Practical marks cannot be greater than Full Marks."
            )

        return cleaned_data


# =========================
# CLASS SUBJECT FORM
# =========================

class ClassSubjectForm(forms.ModelForm):

    class Meta:
        model = ClassSubject

        fields = [
            "school_class",
            "subject",
            "subject_rank",
            "full_marks",
            "pass_marks",
            "written_marks",
            "oral_marks",
            "practical_marks",
            "is_active",
        ]

        widgets = {
            "school_class": forms.Select(attrs={
                "class": "form-select",
            }),
            "subject": forms.Select(attrs={
                "class": "form-select",
            }),
            "subject_rank": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
            "full_marks": forms.NumberInput(attrs={
                "class": "form-control",
            }),
            "pass_marks": forms.NumberInput(attrs={
                "class": "form-control",
            }),
            "written_marks": forms.NumberInput(attrs={
                "class": "form-control",
            }),
            "oral_marks": forms.NumberInput(attrs={
                "class": "form-control",
            }),
            "practical_marks": forms.NumberInput(attrs={
                "class": "form-control",
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }


# =========================
# CLASS ROUTINE FORM
# =========================

class ClassRoutineForm(forms.ModelForm):

    class_select = forms.ModelChoiceField(
        queryset=Class.objects.filter(is_active=True).order_by("class_name"),
        required=True,
        label="Class",
        widget=forms.Select(attrs={
            "class": "form-select",
        })
    )

    section_select = forms.ModelChoiceField(
        queryset=Section.objects.filter(is_active=True).select_related("school_class").order_by(
            "school_class__class_name",
            "section_name"
        ),
        required=False,
        label="Section",
        widget=forms.Select(attrs={
            "class": "form-select",
        })
    )

    subject_select = forms.ModelChoiceField(
        queryset=Subject.objects.filter(is_active=True).order_by("subject_name"),
        required=True,
        label="Subject",
        widget=forms.Select(attrs={
            "class": "form-select",
        })
    )

    teacher_select = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True).order_by("name"),
        required=False,
        label="Teacher",
        widget=forms.Select(attrs={
            "class": "form-select",
        })
    )

    class Meta:
        model = ClassRoutine

        fields = [
            "class_select",
            "section_select",
            "day",
            "period",
            "start_time",
            "end_time",
            "subject_select",
            "teacher_select",
            "room",
            "is_active",
        ]

        widgets = {
            "day": forms.Select(attrs={
                "class": "form-select",
            }),
            "period": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Example: Period 1",
            }),
            "start_time": forms.TimeInput(attrs={
                "class": "form-control",
                "type": "time",
            }),
            "end_time": forms.TimeInput(attrs={
                "class": "form-control",
                "type": "time",
            }),
            "room": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Example: Room 101",
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["class_select"].empty_label = "-- Select Class --"
        self.fields["section_select"].empty_label = "-- Select Section --"
        self.fields["subject_select"].empty_label = "-- Select Subject --"
        self.fields["teacher_select"].empty_label = "-- Select Teacher --"

        if self.instance and self.instance.pk:
            class_obj = Class.objects.filter(
                class_name=self.instance.class_name
            ).first()

            section_obj = Section.objects.filter(
                section_name=self.instance.section,
                school_class=class_obj
            ).first() if class_obj else None

            subject_obj = Subject.objects.filter(
                subject_name=self.instance.subject
            ).first()

            teacher_obj = Employee.objects.filter(
                name=self.instance.teacher
            ).first()

            if class_obj:
                self.initial["class_select"] = class_obj

            if section_obj:
                self.initial["section_select"] = section_obj

            if subject_obj:
                self.initial["subject_select"] = subject_obj

            if teacher_obj:
                self.initial["teacher_select"] = teacher_obj

    def save(self, commit=True):
        routine = super().save(commit=False)

        class_obj = self.cleaned_data.get("class_select")
        section_obj = self.cleaned_data.get("section_select")
        subject_obj = self.cleaned_data.get("subject_select")
        teacher_obj = self.cleaned_data.get("teacher_select")

        routine.class_name = class_obj.class_name if class_obj else ""

        routine.section = section_obj.section_name if section_obj else ""

        routine.subject = subject_obj.subject_name if subject_obj else ""

        if teacher_obj:
            if hasattr(teacher_obj, "name") and teacher_obj.name:
                routine.teacher = teacher_obj.name
            elif hasattr(teacher_obj, "employee_name") and teacher_obj.employee_name:
                routine.teacher = teacher_obj.employee_name
            else:
                routine.teacher = str(teacher_obj)
        else:
            routine.teacher = ""

        if commit:
            routine.save()

        return routine