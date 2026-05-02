from django.db import models
from academics.models import Class, AcademicSession


class Student(models.Model):
    student_id = models.CharField(max_length=20, unique=True, blank=True)
    registration_no = models.CharField(max_length=50, unique=True, blank=True)

    student_name = models.CharField(max_length=150)
    admission_no = models.CharField(max_length=50, blank=True, null=True)
    admission_date = models.DateField()

    current_session = models.ForeignKey(
        AcademicSession,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    class_assigned = models.ForeignKey(Class, on_delete=models.CASCADE)
    roll_no = models.PositiveIntegerField(blank=True, null=True)

    father_name = models.CharField(max_length=150, blank=True, null=True)
    mother_name = models.CharField(max_length=150, blank=True, null=True)
    guardian_name = models.CharField(max_length=150, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    gender = models.CharField(
        max_length=20,
        choices=[
            ('Male', 'Male'),
            ('Female', 'Female'),
            ('Other', 'Other'),
        ],
        blank=True,
        null=True
    )

    date_of_birth = models.DateField(blank=True, null=True)
    aadhaar_number = models.CharField(max_length=30, blank=True, null=True)

    transport_required = models.BooleanField(default=False)
    transport_details = models.CharField(max_length=255, blank=True, null=True)

    previous_school = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    photo = models.ImageField(upload_to='students/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    sibling_of = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='siblings'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if is_new and not self.current_session:
            self.current_session = AcademicSession.objects.filter(is_active=True).first()

        super().save(*args, **kwargs)

        if is_new and not self.student_id:
            self.student_id = f"ARM{self.id}"

        if is_new and not self.registration_no:
            class_part = self.class_assigned.class_name.upper().replace(" ", "")
            self.registration_no = f"ARM-{class_part}-{self.id}"

        if is_new:
            super().save(update_fields=['student_id', 'registration_no'])

    def __str__(self):
        return f"{self.student_name} ({self.student_id})"