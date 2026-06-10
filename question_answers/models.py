from django.db import models
from django.conf import settings
from django.utils import timezone

from academics.models import Class


class StudentQuestion(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("ANSWERED", "Answered"),
        ("CLOSED", "Closed"),
    ]

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="questions"
    )
    class_assigned = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="student_questions"
    )
    subject = models.CharField(max_length=150, blank=True, null=True)
    title = models.CharField(max_length=255)
    question_text = models.TextField()
    attachment = models.FileField(upload_to="question_answers/questions/", blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    asked_at = models.DateTimeField(auto_now_add=True)

    answered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="answered_questions"
    )
    answer_text = models.TextField(blank=True, null=True)
    answer_file = models.FileField(upload_to="question_answers/answers/", blank=True, null=True)
    answered_at = models.DateTimeField(blank=True, null=True)

    is_visible_to_parent = models.BooleanField(default=True)

    class Meta:
        ordering = ["-asked_at"]
        verbose_name = "Student Question"
        verbose_name_plural = "Student Questions"

    def __str__(self):
        return f"{self.student} - {self.title}"

    def mark_answered(self, user):
        self.status = "ANSWERED"
        self.answered_by = user
        self.answered_at = timezone.now()
        self.save()
