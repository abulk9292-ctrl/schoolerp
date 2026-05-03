from django.db import models


class Employee(models.Model):
    employee_id = models.CharField(max_length=20, unique=True, blank=True)

    name = models.CharField(max_length=150)
    designation = models.CharField(max_length=100)
    qualification = models.CharField(max_length=150, blank=True, null=True)
    subject_specialization = models.CharField(max_length=150, blank=True, null=True)

    phone = models.CharField(max_length=20, blank=True, null=True)
    aadhaar_number = models.CharField(max_length=30, blank=True, null=True)

    joining_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    photo = models.ImageField(upload_to='employees/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def get_default_raw_password(self):
        if self.phone:
            return self.phone
        return self.employee_id

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and not self.employee_id:
            self.employee_id = f"EMP{self.id}"
            super().save(update_fields=['employee_id'])

    def __str__(self):
        return f"{self.name} ({self.employee_id})"