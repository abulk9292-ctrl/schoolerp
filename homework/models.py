from django.db import models
from teachers.models import Employee


class Homework(models.Model):
    STATUS_CHOICES = (
        ("Active", "Active"),
        ("Closed", "Closed"),
    )

    title = models.CharField(max_length=200)

    school_class = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    subject = models.CharField(max_length=100)

    description = models.TextField()

    given_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    assigned_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)

    attachment = models.FileField(
        upload_to="homework/",
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Active"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.school_class}"