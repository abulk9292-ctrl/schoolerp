from django.db import models
from students.models import Student
from teachers.models import Employee
from academics.models import AcademicSession


def get_active_session():
    return AcademicSession.objects.filter(is_active=True).first()


# =========================
# STUDENT ATTENDANCE
# =========================

class StudentAttendance(models.Model):

    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
    ]

    SOURCE_CHOICES = [
        ('Manual', 'Manual'),
        ('Mobile', 'Mobile'),
        ('Biometric', 'Biometric'),
        ('Import', 'Import'),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE
    )

    session = models.ForeignKey(
        AcademicSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    date = models.DateField()

    section = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Present'
    )

    remarks = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    # ==========================================
    # AUDIT TRACKING
    # ==========================================

    marked_by = models.ForeignKey(
        "teachers.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="marked_student_attendance"
    )

    source = models.CharField(
        max_length=30,
        choices=SOURCE_CHOICES,
        default="Manual"
    )

    class Meta:
        unique_together = ('student', 'session', 'date')
        ordering = ['-date', 'student']

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.session} - "
            f"{self.date} - "
            f"{self.status}"
        )

    def save(self, *args, **kwargs):

        if not self.session:
            self.session = get_active_session()

        if self.student and not self.section:
            self.section = self.student.section or ""

        super().save(*args, **kwargs)

        if self.status in ['Absent', 'Late']:

            AttendanceAlert.objects.update_or_create(
                alert_type='Student',
                student=self.student,
                session=self.session,
                date=self.date,
                defaults={
                    'section': self.section,
                    'attendance_status': self.status,
                    'message_en': (
                        f"{self.student.student_name} "
                        f"is {self.status} today."
                    ),
                    'message_bn': (
                        f"{self.student.student_name} "
                        f"আজ {self.status} আছে।"
                    ),
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

    SOURCE_CHOICES = [
        ('Manual', 'Manual'),
        ('GPS', 'GPS'),
        ('Biometric', 'Biometric'),
        ('Import', 'Import'),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE
    )

    session = models.ForeignKey(
        AcademicSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    date = models.DateField()

    section = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Present'
    )

    # ==================================
    # ATTENDANCE SOURCE
    # ==================================

    source = models.CharField(
        max_length=30,
        choices=SOURCE_CHOICES,
        default='Manual'
    )

    # ==================================
    # GPS DETAILS
    # ==================================

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )

    distance_meters = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    within_range = models.BooleanField(
        default=False
    )

    # ==================================
    # SELFIE
    # ==================================

    selfie = models.ImageField(
        upload_to='teacher_attendance_selfies/',
        null=True,
        blank=True
    )

    # ==================================
    # DEVICE INFO
    # ==================================

    address = models.TextField(
        null=True,
        blank=True
    )

    device_info = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    # ==================================
    # REMARKS
    # ==================================

    remarks = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    marked_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )

    class Meta:
        unique_together = (
            'employee',
            'session',
            'date'
        )

        ordering = [
            '-date',
            '-marked_at'
        ]

    def __str__(self):
        return (
            f"{self.employee} - "
            f"{self.session} - "
            f"{self.date} - "
            f"{self.status}"
        )

    def save(self, *args, **kwargs):

        if not self.session:
            self.session = get_active_session()

        super().save(*args, **kwargs)

        if self.status in ['Absent', 'Late']:

            AttendanceAlert.objects.update_or_create(
                alert_type='Teacher',
                employee=self.employee,
                session=self.session,
                date=self.date,
                defaults={
                    'section': self.section,
                    'attendance_status': self.status,
                    'message_en': (
                        f"{self.employee.name} "
                        f"is {self.status} today."
                    ),
                    'message_bn': (
                        f"{self.employee.name} "
                        f"আজ {self.status} আছেন।"
                    ),
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

    session = models.ForeignKey(AcademicSession, on_delete=models.SET_NULL, null=True, blank=True)

    date = models.DateField()
    section = models.CharField(max_length=20, blank=True, null=True)

    attendance_status = models.CharField(max_length=10)

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
            return f"{self.student} - {self.attendance_status} ({self.approval_status})"

        return f"{self.employee} - {self.attendance_status} ({self.approval_status})"


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

    # Active / Inactive Holiday
    is_active = models.BooleanField(default=True)

    note = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.title} - {self.date}"