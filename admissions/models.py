from django.db import models


class Admission(models.Model):

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]

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
        max_length=200,
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

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.student_name