from django import forms
from django.core.exceptions import ValidationError

from students.models import Student

from .models import (
    Exam,
    ExamRoutine,
    ExamResult,
    ClassTest,
)


# =========================================================
# SAFE HELPERS
# =========================================================

def get_class_choices():
    choices = []

    try:
        from academics.models import Class

        classes = Class.objects.all().order_by("class_name")

        for c in classes:
            choices.append((c.class_name, c.class_name))

    except Exception:
        pass

    if not choices:
        try:
            old_classes = (
                Student.objects.exclude(school_class__isnull=True)
                .exclude(school_class="")
                .values_list("school_class", flat=True)
                .distinct()
                .order_by("school_class")
            )

            for c in old_classes:
                choices.append((c, c))

        except Exception:
            pass

    return choices


def get_section_choices(selected_class=None):
    choices = [
        ("", "Select Section"),
        ("A", "A"),
        ("B", "B"),
        ("C", "C"),
        ("D", "D"),
    ]

    try:
        from academics.models import Class, Section

        if selected_class:
            class_obj = Class.objects.filter(
                class_name=selected_class
            ).first()

            if class_obj:
                sections = Section.objects.filter(
                    school_class=class_obj
                ).order_by("section_name")

                db_choices = [
                    (s.section_name, s.section_name)
                    for s in sections
                ]

                if db_choices:
                    return [("", "Select Section")] + db_choices

    except Exception:
        pass

    return choices


def get_subject_choices(selected_class=None):
    choices = []

    try:
        from academics.models import Class, ClassSubject

        class_obj = None

        if selected_class:
            class_obj = Class.objects.filter(
                class_name=selected_class
            ).first()

        if class_obj:
            class_subjects = (
                ClassSubject.objects.filter(
                    school_class=class_obj,
                    is_active=True
                )
                .select_related("subject")
                .order_by("subject__subject_name")
            )

            for item in class_subjects:
                subject_obj = getattr(item, "subject", None)

                subject_name = (
                    getattr(subject_obj, "subject_name", None)
                    or getattr(subject_obj, "name", None)
                    or str(subject_obj)
                )

                if subject_name:
                    choices.append((subject_name, subject_name))

    except Exception:
        pass

    if not choices:
        fallback_subjects = [
            "Bengali",
            "English",
            "Mathematics",
            "Science",
            "History",
            "Geography",
        ]

        choices = [(s, s) for s in fallback_subjects]

    return choices


def get_students_by_class(class_name=None, section=None):
    students = Student.objects.all()

    try:
        students = students.select_related(
            "class_assigned",
            "current_session"
        )
    except Exception:
        pass

    if class_name:
        try:
            students = students.filter(
                class_assigned__class_name=class_name
            )
        except Exception:
            try:
                students = students.filter(
                    school_class=class_name
                )
            except Exception:
                pass

    if section:
        try:
            students = students.filter(section=section)
        except Exception:
            pass

    return students.order_by("roll_no", "student_name", "id")


# =========================================================
# EXAM FORM
# =========================================================

class ExamForm(forms.ModelForm):

    class Meta:
        model = Exam

        fields = [
            "name",
            "academic_session",
            "start_date",
            "end_date",
            "is_active",
        ]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Annual Examination"
            }),

            "academic_session": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "2025-26"
            }),

            "start_date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control"
            }),

            "end_date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control"
            }),

            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date < start_date:
            raise ValidationError(
                "End date cannot be before start date."
            )

        return cleaned_data


# =========================================================
# EXAM ROUTINE FORM
# =========================================================

class ExamRoutineForm(forms.ModelForm):

    school_class = forms.ChoiceField(
        choices=[],
        required=True,
        widget=forms.Select(attrs={
            "class": "form-select",
            "id": "id_school_class"
        })
    )

    section = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={
            "class": "form-select",
            "id": "id_section"
        })
    )

    subject = forms.ChoiceField(
        choices=[],
        required=True,
        widget=forms.Select(attrs={
            "class": "form-select",
            "id": "id_subject"
        })
    )

    class Meta:
        model = ExamRoutine

        fields = [
            "exam",
            "school_class",
            "section",
            "subject",
            "date",
            "start_time",
            "end_time",
            "total_marks",
        ]

        widgets = {
            "exam": forms.Select(attrs={
                "class": "form-select"
            }),

            "date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control"
            }),

            "start_time": forms.TimeInput(attrs={
                "type": "time",
                "class": "form-control"
            }),

            "end_time": forms.TimeInput(attrs={
                "type": "time",
                "class": "form-control"
            }),

            "total_marks": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1
            }),
        }

    def __init__(self, *args, **kwargs):
        selected_session = kwargs.pop("selected_session", None)
        super().__init__(*args, **kwargs)

        if selected_session:
            self.fields["exam"].queryset = Exam.objects.filter(
                academic_session=selected_session
            ).order_by("-id")
        else:
            self.fields["exam"].queryset = Exam.objects.all().order_by("-id")

        selected_class = None

        if self.data.get("school_class"):
            selected_class = self.data.get("school_class")
        elif self.initial.get("school_class"):
            selected_class = self.initial.get("school_class")
        elif self.instance and self.instance.pk:
            selected_class = self.instance.school_class

        self.fields["school_class"].choices = [
            ("", "Select Class")
        ] + get_class_choices()

        self.fields["section"].choices = get_section_choices(
            selected_class
        )

        self.fields["subject"].choices = [
            ("", "Select Subject")
        ] + get_subject_choices(
            selected_class
        )

    def clean(self):
        cleaned_data = super().clean()

        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time and end_time <= start_time:
            raise ValidationError(
                "End time must be greater than start time."
            )

        return cleaned_data


# =========================================================
# EXAM RESULT FORM
# =========================================================

class ExamResultForm(forms.ModelForm):

    subject = forms.ChoiceField(
        choices=[],
        required=True,
        widget=forms.Select(attrs={
            "class": "form-select",
            "id": "id_subject"
        })
    )

    class Meta:
        model = ExamResult

        fields = [
            "student",
            "exam",
            "subject",
            "written_marks",
            "oral_marks",
            "max_marks",
            "remarks",
        ]

        widgets = {
            "student": forms.Select(attrs={
                "class": "form-select",
                "id": "id_student"
            }),

            "exam": forms.Select(attrs={
                "class": "form-select",
                "id": "id_exam"
            }),

            "written_marks": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 0
            }),

            "oral_marks": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 0
            }),

            "max_marks": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1
            }),

            "remarks": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Good / Excellent / Need Improvement"
            }),
        }

    def __init__(self, *args, **kwargs):
        class_name = kwargs.pop("class_name", None)
        section = kwargs.pop("section", None)
        selected_session = kwargs.pop("selected_session", None)

        super().__init__(*args, **kwargs)

        if selected_session:
            self.fields["exam"].queryset = Exam.objects.filter(
                academic_session=selected_session
            ).order_by("-id")
        else:
            self.fields["exam"].queryset = Exam.objects.all().order_by("-id")

        self.fields["student"].queryset = get_students_by_class(
            class_name=class_name,
            section=section
        )

        self.fields["subject"].choices = [
            ("", "Select Subject")
        ] + get_subject_choices(
            class_name
        )

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

        if student and exam and subject:
            exists = ExamResult.objects.filter(
                student=student,
                exam=exam,
                subject=subject
            )

            if self.instance and self.instance.pk:
                exists = exists.exclude(pk=self.instance.pk)

            if exists.exists():
                raise ValidationError(
                    "This student's subject marks already exist for this exam."
                )

        return cleaned_data


# =========================================================
# CLASS TEST FORM
# =========================================================

class ClassTestForm(forms.ModelForm):

    subject = forms.ChoiceField(
        required=False,
        choices=[],
        widget=forms.Select(attrs={
            "class": "form-control",
            "id": "id_subject"
        })
    )

    class Meta:
        model = ClassTest

        fields = [
            "class_name",
            "section",
            "test_name",
            "subject",
            "exam_date",
            "total_marks",
        ]

        widgets = {
            "class_name": forms.Select(attrs={
                "class": "form-control",
                "id": "id_class_name"
            }),

            "section": forms.Select(attrs={
                "class": "form-control",
                "id": "id_section"
            }),

            "test_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Unit Test 1 / Unit Test 2"
            }),

            "exam_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),

            "total_marks": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1
            }),
        }

    def __init__(self, *args, **kwargs):
        selected_session = kwargs.pop("selected_session", None)
        super().__init__(*args, **kwargs)

        selected_class = None

        if self.data.get("class_name"):
            selected_class = self.data.get("class_name")
        elif self.initial.get("class_name"):
            selected_class = self.initial.get("class_name")
        elif self.instance and self.instance.pk:
            selected_class = self.instance.class_name

        self.fields["class_name"].choices = [
            ("", "Select Class")
        ] + get_class_choices()

        self.fields["section"].choices = get_section_choices(
            selected_class
        )

        subject_choices = [("All Subjects", "All Subjects")]

        if selected_class:
            subject_choices += get_subject_choices(selected_class)

        self.fields["subject"].choices = subject_choices

        if selected_session and not self.instance.pk:
            self.initial["academic_session"] = selected_session


# =========================================================
# CLASS TEST RESULT FORM
# =========================================================

class ClassTestResultForm(forms.Form):

    class_test = forms.ModelChoiceField(
        queryset=ClassTest.objects.all().order_by("-id"),
        required=True,
        widget=forms.Select(attrs={
            "class": "form-control",
            "id": "id_class_test",
            "onchange": "this.form.submit()"
        })
    )

    student = forms.ModelChoiceField(
        queryset=Student.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            "class": "form-control",
            "id": "id_student",
            "onchange": "this.form.submit()"
        })
    )

    def __init__(self, *args, **kwargs):
        selected_test_id = kwargs.pop("selected_test_id", None)

        super().__init__(*args, **kwargs)

        self.fields["student"].queryset = Student.objects.none()

        if selected_test_id:
            try:
                class_test = ClassTest.objects.get(
                    id=selected_test_id
                )

                students = Student.objects.filter(
                    class_assigned__class_name=str(class_test.class_name).strip()
                )

                section_name = str(getattr(class_test, "section", "") or "").strip()

                if section_name:
                    students = students.filter(
                        section=section_name
                    )

                students = students.order_by(
                    "roll_no",
                    "student_name",
                    "id"
                )

                self.fields["student"].queryset = students

            except Exception:
                self.fields["student"].queryset = Student.objects.all().order_by(
                    "student_name"
                )