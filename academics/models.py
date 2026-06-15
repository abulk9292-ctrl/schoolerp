from django.db import models


class AcademicSession(models.Model):
    session_name = models.CharField(max_length=50, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ["-start_date"]
        verbose_name = "Academic Session"
        verbose_name_plural = "Academic Sessions"

    def save(self, *args, **kwargs):
        if self.is_active:
            AcademicSession.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.session_name


class Class(models.Model):
    class_name = models.CharField(max_length=50, unique=True)

    class_teacher = models.ForeignKey(
        "teachers.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_classes"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["class_name"]
        verbose_name = "Class"
        verbose_name_plural = "Classes"

    def __str__(self):
        return self.class_name

    def save(self, *args, **kwargs):

        old_teacher = None

        if self.pk:
            try:
                old_teacher = Class.objects.get(
                    pk=self.pk
                ).class_teacher
            except Class.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        # Remove old teacher assignment
        if (
            old_teacher and
            old_teacher != self.class_teacher
        ):
            old_teacher.assigned_class = None
            old_teacher.assigned_section = ""
            old_teacher.save(
                update_fields=[
                    "assigned_class",
                    "assigned_section"
                ]
            )

        # Assign new teacher
        if self.class_teacher:
            self.class_teacher.assigned_class = self
            self.class_teacher.save(
                update_fields=[
                    "assigned_class"
                ]
            )

class Section(models.Model):
    school_class = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name="sections"
    )

    section_name = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["school_class__class_name", "section_name"]
        unique_together = ("school_class", "section_name")
        verbose_name = "Section"
        verbose_name_plural = "Sections"

    def __str__(self):
        return f"{self.school_class.class_name} - {self.section_name}"


class Subject(models.Model):
    subject_name = models.CharField(max_length=100, unique=True)
    subject_code = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["subject_name"]
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"

    def __str__(self):
        return self.subject_name

# =========================
# CLASS SUBJECT
# =========================
class ClassSubject(models.Model):
    school_class = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name="class_subjects"
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="subject_classes"
    )

    # =========================
    # SUBJECT ORDER / RANK
    # =========================
    subject_rank = models.PositiveIntegerField(
        default=0,
        verbose_name="Subject Rank"
    )

    full_marks = models.PositiveIntegerField(default=100)
    pass_marks = models.PositiveIntegerField(default=35)
    written_marks = models.PositiveIntegerField(default=80)
    oral_marks = models.PositiveIntegerField(default=20)
    practical_marks = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("school_class", "subject")
        ordering = [
            "school_class__class_name",
            "subject_rank",
            "subject__subject_name"
        ]
        verbose_name = "Class Subject"
        verbose_name_plural = "Class Subjects"

    def __str__(self):
        return f"{self.subject_rank}. {self.school_class} - {self.subject}"


class ClassRoutine(models.Model):
    DAY_CHOICES = [
        ("Saturday", "Saturday"),
        ("Sunday", "Sunday"),
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
    ]

    class_name = models.CharField(max_length=50)
    section = models.CharField(max_length=20, blank=True, null=True)

    day = models.CharField(max_length=20, choices=DAY_CHOICES)
    period = models.CharField(max_length=50)

    start_time = models.TimeField()
    end_time = models.TimeField()

    subject = models.CharField(max_length=100)
    teacher = models.CharField(max_length=100, blank=True, null=True)
    room = models.CharField(max_length=50, blank=True, null=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["class_name", "section", "day", "start_time"]
        verbose_name = "Class Routine"
        verbose_name_plural = "Class Routines"

    def __str__(self):
        if self.section:
            return f"{self.class_name} - {self.section} - {self.day} - {self.period}"
        return f"{self.class_name} - {self.day} - {self.period}"