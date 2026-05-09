from django.db import models


class OnlineAdmission(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]

    student_name = models.CharField(max_length=150)
    father_name = models.CharField(max_length=150, blank=True, null=True)
    mother_name = models.CharField(max_length=150, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    class_applied = models.CharField(max_length=50)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    aadhaar_number = models.CharField(max_length=30, blank=True, null=True)
    photo = models.ImageField(upload_to="admissions/", blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    created_student_id = models.IntegerField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.student_name