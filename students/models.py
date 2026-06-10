from django.db import models
from django.contrib.auth.hashers import make_password

from academics.models import Class, AcademicSession


class Student(models.Model):

    student_id = models.CharField(max_length=20, unique=True, blank=True)
    registration_no = models.CharField(max_length=50, unique=True, blank=True)
    admission_no = models.CharField(max_length=50, blank=True, null=True)

    login_username = models.CharField(max_length=100, unique=True, blank=True, null=True)
    login_password = models.CharField(max_length=150, blank=True, null=True)
    login_enabled = models.BooleanField(default=True)

    current_session = models.ForeignKey(
        AcademicSession,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="students"
    )

    student_name = models.CharField(max_length=150)

    class_assigned = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name="students"
    )

    roll_no = models.PositiveIntegerField(blank=True, null=True)
    section = models.CharField(max_length=20, blank=True, null=True, default='')

    admission_date = models.DateField()
    date_of_birth = models.DateField(blank=True, null=True)

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

    religion = models.CharField(
        max_length=50,
        choices=[
            ('Islam', 'Islam'),
            ('Hindu', 'Hindu'),
            ('Christian', 'Christian'),
            ('Sikh', 'Sikh'),
            ('Buddhist', 'Buddhist'),
            ('Other', 'Other'),
        ],
        blank=True,
        null=True
    )

    village = models.CharField(max_length=150, blank=True, null=True)

    father_name = models.CharField(max_length=150, blank=True, null=True)
    mother_name = models.CharField(max_length=150, blank=True, null=True)
    guardian_name = models.CharField(max_length=150, blank=True, null=True)

    phone = models.CharField(max_length=20, blank=True, null=True)
    aadhaar_number = models.CharField(max_length=30, blank=True, null=True)

    transport_required = models.BooleanField(default=False)
    transport_details = models.CharField(max_length=255, blank=True, null=True)

    previous_school = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    photo = models.ImageField(upload_to='students/', blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_promoted = models.BooleanField(default=False)
    is_graduated = models.BooleanField(default=False)

    sibling_of = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='siblings'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['student_name']
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['registration_no']),
            models.Index(fields=['student_name']),
            models.Index(fields=['phone']),
            models.Index(fields=['current_session']),
        ]

    def get_default_raw_password(self):
        if self.date_of_birth:
            return self.date_of_birth.strftime("%d%m%Y")
        if self.phone:
            return str(self.phone)
        if self.registration_no:
            return str(self.registration_no)
        return "123456"

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if is_new and not self.current_session:
            self.current_session = AcademicSession.objects.filter(is_active=True).first()

        super().save(*args, **kwargs)

        update_fields = []

        if not self.student_id:
            self.student_id = f"ARM{self.id}"
            update_fields.append("student_id")

        if not self.registration_no:
            class_part = self.class_assigned.class_name.upper().replace(" ", "")
            self.registration_no = f"ARM-{class_part}-{self.id}"
            update_fields.append("registration_no")

        if not self.login_username:
            self.login_username = self.student_id
            update_fields.append("login_username")

        if not self.login_password:
            raw_password = self.get_default_raw_password()
            self.login_password = make_password(raw_password)
            update_fields.append("login_password")

        if not self.roll_no:
            same_class_students = Student.objects.filter(
                class_assigned=self.class_assigned,
                current_session=self.current_session
            ).exclude(pk=self.pk)

            max_roll = same_class_students.aggregate(
                models.Max("roll_no")
            )["roll_no__max"] or 0

            self.roll_no = max_roll + 1
            update_fields.append("roll_no")

        if update_fields:
            super().save(update_fields=update_fields)

        Parent.objects.get_or_create(
            student=self,
            defaults={
                "username": self.student_id,
                "father_name": self.father_name,
                "mother_name": self.mother_name,
                "phone": self.phone,
            }
        )

    def __str__(self):
        return f"{self.student_name} ({self.student_id})"


class Parent(models.Model):

    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name="parent_login"
    )

    username = models.CharField(max_length=100, unique=True, blank=True)
    password = models.CharField(max_length=150, blank=True)

    father_name = models.CharField(max_length=150, blank=True, null=True)
    mother_name = models.CharField(max_length=150, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.student.student_id

        if not self.password:
            raw_password = self.student.get_default_raw_password()
            self.password = make_password(raw_password)

        if not self.father_name:
            self.father_name = self.student.father_name

        if not self.mother_name:
            self.mother_name = self.student.mother_name

        if not self.phone:
            self.phone = self.student.phone

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Parent of {self.student.student_name}"


class StudentOTP(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE
    )

    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.student_name} OTP"