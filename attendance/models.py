from django.db import models
from students.models import Student
from teachers.models import Employee


# =========================
# STUDENT ATTENDANCE
# =========================
class StudentAttendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Present')
    remarks = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        unique_together = ('student', 'date')
        ordering = ['-date', 'student']

    def __str__(self):
        return f"{self.student} - {self.date} - {self.status}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.status in ['Absent', 'Late']:
            AttendanceAlert.objects.update_or_create(
                alert_type='Student',
                student=self.student,
                date=self.date,
                defaults={
                    'status': self.status,
                    'message_en': f"{self.student.student_name} is {self.status} today.",
                    'message_bn': f"{self.student.student_name} আজ {self.status} আছে।",
                    'approval_status': 'Pending',
                }
            )


# =========================
# TEACHER ATTENDANCE
# =========================
class TeacherAttendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Present')

    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    distance_meters = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    within_range = models.BooleanField(default=False)

    selfie = models.ImageField(
        upload_to='teacher_attendance_selfies/',
        null=True,
        blank=True
    )

    address = models.TextField(null=True, blank=True)
    device_info = models.CharField(max_length=255, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    remarks = models.CharField(max_length=255, null=True, blank=True)
    marked_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date', '-marked_at']

    def __str__(self):
        return f"{self.employee} - {self.date} - {self.status}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.status in ['Absent', 'Late']:
            AttendanceAlert.objects.update_or_create(
                alert_type='Teacher',
                employee=self.employee,
                date=self.date,
                defaults={
                    'status': self.status,
                    'message_en': f"{self.employee.name} is {self.status} today.",
                    'message_bn': f"{self.employee.name} আজ {self.status} আছেন।",
                    'approval_status': 'Pending',
                }
            )


# =========================
# ATTENDANCE ALERT MODEL
# =========================
class AttendanceAlert(models.Model):

    ALERT_TYPE_CHOICES = [
        ('Student', 'Student'),
        ('Teacher', 'Teacher'),
    ]

    APPROVAL_STATUS = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    alert_type = models.CharField(max_length=10, choices=ALERT_TYPE_CHOICES)

    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True)

    date = models.DateField()
    status = models.CharField(max_length=10)

    message_en = models.TextField()
    message_bn = models.TextField()

    approval_status = models.CharField(
        max_length=10,
        choices=APPROVAL_STATUS,
        default='Pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.alert_type == 'Student':
            return f"{self.student} - {self.status} ({self.approval_status})"
        return f"{self.employee} - {self.status} ({self.approval_status})"


# =========================
# HOLIDAY MODEL
# =========================
class Holiday(models.Model):

    HOLIDAY_TYPE_CHOICES = [
        ('Weekly', 'Weekly Holiday'),
        ('Special', 'Special Holiday'),
        ('Emergency', 'Emergency Holiday'),
        ('Festival', 'Festival Holiday'),
        ('Government', 'Government Holiday'),
    ]

    title = models.CharField(max_length=150)
    date = models.DateField()

    holiday_type = models.CharField(
        max_length=30,
        choices=HOLIDAY_TYPE_CHOICES,
        default='Special'
    )

    is_half_day = models.BooleanField(default=False)

    note = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.title} - {self.date}"