from django.db import models
from django.utils import timezone

from students.models import Student
from teachers.models import Employee


BEHAVIOUR_TYPE_CHOICES = (
    ("Positive", "Positive"),
    ("Negative", "Negative"),
    ("Neutral", "Neutral"),
)

GRADE_CHOICES = (
    ("Excellent", "Excellent"),
    ("Very Good", "Very Good"),
    ("Good", "Good"),
    ("Average", "Average"),
    ("Needs Improvement", "Needs Improvement"),
)


class BehaviourRecord(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="behaviour_records"
    )

    teacher = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="given_behaviour_records"
    )

    date = models.DateField(default=timezone.now)

    behaviour_type = models.CharField(
        max_length=20,
        choices=BEHAVIOUR_TYPE_CHOICES,
        default="Positive"
    )

    title = models.CharField(max_length=150)

    description = models.TextField(blank=True, null=True)

    points = models.IntegerField(default=0)

    action_taken = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    parent_notified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.student.student_name} - {self.behaviour_type}"


class SkillEvaluation(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="skill_evaluations"
    )

    teacher = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="given_skill_evaluations"
    )

    month = models.CharField(max_length=20)
    year = models.PositiveIntegerField(default=timezone.now().year)

    discipline = models.CharField(
        max_length=30,
        choices=GRADE_CHOICES,
        default="Good"
    )

    punctuality = models.CharField(
        max_length=30,
        choices=GRADE_CHOICES,
        default="Good"
    )

    cleanliness = models.CharField(
        max_length=30,
        choices=GRADE_CHOICES,
        default="Good"
    )

    communication = models.CharField(
        max_length=30,
        choices=GRADE_CHOICES,
        default="Good"
    )

    teamwork = models.CharField(
        max_length=30,
        choices=GRADE_CHOICES,
        default="Good"
    )

    leadership = models.CharField(
        max_length=30,
        choices=GRADE_CHOICES,
        default="Good"
    )

    homework_habit = models.CharField(
        max_length=30,
        choices=GRADE_CHOICES,
        default="Good"
    )

    class_participation = models.CharField(
        max_length=30,
        choices=GRADE_CHOICES,
        default="Good"
    )

    teacher_remarks = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "month", "year")
        ordering = ["-year", "-id"]

    def __str__(self):
        return f"{self.student.student_name} - {self.month} {self.year}"