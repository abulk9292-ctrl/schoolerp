from django.db import models

from teachers.models import Employee
from students.models import Student


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


class HomeworkSubmission(models.Model):
    STATUS_CHOICES = (
        ("Submitted", "Submitted"),
        ("Reviewed", "Reviewed"),
        ("Late", "Late"),
        ("Rejected", "Rejected"),
    )

    homework = models.ForeignKey(
        Homework,
        on_delete=models.CASCADE,
        related_name="submissions"
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="homework_submissions"
    )

    answer_text = models.TextField(
        blank=True,
        null=True
    )

    submitted_file = models.FileField(
        upload_to="homework_submissions/",
        blank=True,
        null=True
    )

    submitted_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Submitted"
    )

    marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )

    teacher_remarks = models.TextField(
        blank=True,
        null=True
    )

    reviewed_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="reviewed_homework_submissions"
    )

    reviewed_at = models.DateTimeField(
        blank=True,
        null=True
    )

    class Meta:
        unique_together = ("homework", "student")
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.student} - {self.homework}"