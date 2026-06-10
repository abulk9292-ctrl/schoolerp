from django.db import models
from django.conf import settings
from django.utils import timezone

from academics.models import Class
try:
    from academics.models import Section
except Exception:
    Section = None


class LiveClass(models.Model):
    STATUS_CHOICES = [
        ("UPCOMING", "Upcoming"),
        ("RUNNING", "Running"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    title = models.CharField(max_length=200)
    class_assigned = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name="live_classes"
    )

    # If your academics app has Section model, migration will work.
    # If not, change this to CharField or remove it.
    section = models.CharField(max_length=50, blank=True, null=True)

    subject = models.CharField(max_length=150, blank=True, null=True)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="created_live_classes"
    )

    meeting_link = models.URLField(max_length=500)
    meeting_id = models.CharField(max_length=100, blank=True, null=True)
    passcode = models.CharField(max_length=100, blank=True, null=True)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="UPCOMING")
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="live_classes_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_time"]
        verbose_name = "Live Class"
        verbose_name_plural = "Live Classes"

    def __str__(self):
        return f"{self.title} - {self.class_assigned}"

    def auto_status(self):
        now = timezone.now()
        if self.status == "CANCELLED":
            return "CANCELLED"
        if self.end_time and now > self.end_time:
            return "COMPLETED"
        if self.start_time <= now and (not self.end_time or now <= self.end_time):
            return "RUNNING"
        return "UPCOMING"


class LiveClassAttendance(models.Model):
    live_class = models.ForeignKey(
        LiveClass,
        on_delete=models.CASCADE,
        related_name="attendances"
    )
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="live_class_attendances"
    )
    joined_at = models.DateTimeField(default=timezone.now)
    remarks = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ("live_class", "student")
        ordering = ["-joined_at"]

    def __str__(self):
        return f"{self.student} - {self.live_class}"
