from django.db import models


class AcademicSession(models.Model):
    session_name = models.CharField(max_length=50, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_date']

    def save(self, *args, **kwargs):
        if self.is_active:
            AcademicSession.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.session_name


class Class(models.Model):
    class_name = models.CharField(max_length=50, unique=True)

    class_teacher = models.ForeignKey(
        'teachers.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_classes'
    )

    class Meta:
        ordering = ['class_name']

    def __str__(self):
        return self.class_name


class Subject(models.Model):
    subject_name = models.CharField(max_length=100, unique=True)
    subject_code = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        ordering = ['subject_name']

    def __str__(self):
        return self.subject_name


class ClassSubject(models.Model):
    school_class = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='class_subjects'
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='subject_classes'
    )

    full_marks = models.PositiveIntegerField(default=100)
    pass_marks = models.PositiveIntegerField(default=35)
    written_marks = models.PositiveIntegerField(default=80)
    oral_marks = models.PositiveIntegerField(default=20)
    practical_marks = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('school_class', 'subject')
        ordering = ['school_class__class_name', 'subject__subject_name']

    def __str__(self):
        return f"{self.school_class} - {self.subject}"