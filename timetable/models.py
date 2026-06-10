from django.db import models
from django.utils import timezone


class Period(models.Model):
    name = models.CharField(max_length=80)
    start_time = models.TimeField()
    end_time = models.TimeField()
    order = models.PositiveIntegerField(default=1)
    is_break = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "start_time"]

    def __str__(self):
        return f"{self.name} ({self.start_time}-{self.end_time})"


class TimetableHoliday(models.Model):
    DAY_CHOICES = [
        ("MONDAY", "Monday"),
        ("TUESDAY", "Tuesday"),
        ("WEDNESDAY", "Wednesday"),
        ("THURSDAY", "Thursday"),
        ("FRIDAY", "Friday"),
        ("SATURDAY", "Saturday"),
        ("SUNDAY", "Sunday"),
    ]

    day = models.CharField(max_length=20, choices=DAY_CHOICES, unique=True)
    title = models.CharField(max_length=150, default="Weekly Holiday")
    is_holiday = models.BooleanField(default=True)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["day"]

    def __str__(self):
        return f"{self.get_day_display()} - {self.title}"


class ClassTimetable(models.Model):
    DAY_CHOICES = [
        ("MONDAY", "Monday"),
        ("TUESDAY", "Tuesday"),
        ("WEDNESDAY", "Wednesday"),
        ("THURSDAY", "Thursday"),
        ("FRIDAY", "Friday"),
        ("SATURDAY", "Saturday"),
        ("SUNDAY", "Sunday"),
    ]

    class_assigned = models.ForeignKey(
        "academics.Class",
        on_delete=models.CASCADE,
        related_name="timetable_entries"
    )
    section = models.CharField(max_length=50, blank=True, null=True)
    day = models.CharField(max_length=20, choices=DAY_CHOICES)
    period = models.ForeignKey(
        Period,
        on_delete=models.CASCADE,
        related_name="class_entries"
    )
    subject = models.ForeignKey(
        "academics.Subject",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="timetable_entries"
    )
    teacher = models.ForeignKey(
        "teachers.Employee",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="timetable_entries"
    )
    room_no = models.CharField(max_length=50, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["day", "period__order"]
        unique_together = ("class_assigned", "section", "day", "period")

    def __str__(self):
        return f"{self.class_assigned} {self.section or ''} - {self.day} - {self.period}"
