from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Admission(models.Model):

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]

    admission_no = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
        null=True
    )

    student_name = models.CharField(max_length=150)

    father_name = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    mother_name = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    date_of_birth = models.DateField(
        blank=True,
        null=True
    )

    gender = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    student_class = models.CharField(
        max_length=50
    )

    section = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        default=""
    )

    aadhaar_no = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    mobile = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    guardian_mobile = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    previous_school = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    transport_required = models.BooleanField(
        default=False
    )

    hostel_required = models.BooleanField(
        default=False
    )

    student_photo = models.ImageField(
        upload_to="admissions/",
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    created_student_id = models.IntegerField(
        blank=True,
        null=True
    )

    approved_at = models.DateTimeField(
        blank=True,
        null=True
    )

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="approved_admissions"
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    is_duplicate_checked = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["student_name"]),
            models.Index(fields=["mobile"]),
            models.Index(fields=["student_class"]),
            models.Index(fields=["created_at"]),
        ]

    def generate_admission_no(self):
        return f"ADM{self.id:06d}"

    def save(self, *args, **kwargs):

        is_new = self.pk is None

        super().save(*args, **kwargs)

        update_fields = []

        if not self.admission_no:
            self.admission_no = self.generate_admission_no()
            update_fields.append("admission_no")

        if update_fields:
            super().save(update_fields=update_fields)

    @property
    def is_approved(self):
        return self.status == "Approved"

    @property
    def is_rejected(self):
        return self.status == "Rejected"

    @property
    def is_pending(self):
        return self.status == "Pending"

    def __str__(self):
        return f"{self.admission_no} - {self.student_name}"