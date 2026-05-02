from django.db import models


class AcademicSession(models.Model):
    session_name = models.CharField(max_length=50, unique=True)  # Example: 2026-2027
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
    class_name = models.CharField(max_length=50)

    def __str__(self):
        return self.class_name


class Subject(models.Model):
    subject_name = models.CharField(max_length=100)

    def __str__(self):
        return self.subject_name