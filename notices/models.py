from django.db import models
from teachers.models import Employee


class Notice(models.Model):
    NOTICE_TYPE_CHOICES = (
        ("General", "General"),
        ("Urgent", "Urgent"),
        ("Exam", "Exam"),
        ("Holiday", "Holiday"),
        ("Homework", "Homework"),
    )

    TARGET_CHOICES = (
        ("All", "All"),
        ("Students", "Students"),
        ("Teachers", "Teachers"),
        ("Parents", "Parents"),
        ("Class Wise", "Class Wise"),
    )

    STATUS_CHOICES = (
        ("Active", "Active"),
        ("Inactive", "Inactive"),
    )

    title = models.CharField(max_length=200)
    notice_type = models.CharField(max_length=30, choices=NOTICE_TYPE_CHOICES, default="General")
    target = models.CharField(max_length=30, choices=TARGET_CHOICES, default="All")
    school_class = models.CharField(max_length=100, blank=True, null=True)

    description = models.TextField()
    attachment = models.FileField(upload_to="notices/", null=True, blank=True)

    published_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    publish_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Active")
    is_pinned = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title