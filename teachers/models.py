from django.db import models
from django.contrib.auth.models import User


class Employee(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employee'
    )

    employee_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    name = models.CharField(max_length=150)
    designation = models.CharField(max_length=100)

    qualification = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    subject_specialization = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    # ==========================================
    # CLASS TEACHER ASSIGNMENT
    # ==========================================

    assigned_class = models.ForeignKey(
        'academics.Class',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_teachers'
    )

    assigned_section = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    # ==========================================
    # BASIC INFO
    # ==========================================

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    aadhaar_number = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    joining_date = models.DateField()

    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    photo = models.ImageField(
        upload_to='employees/',
        blank=True,
        null=True
    )

    is_active = models.BooleanField(default=True)

    # ==========================================
    # ERP ACCESS CONTROL
    # ==========================================

    is_erp_admin = models.BooleanField(default=False)

    can_access_students = models.BooleanField(default=False)
    can_access_teachers = models.BooleanField(default=False)
    can_access_academics = models.BooleanField(default=False)
    can_access_attendance = models.BooleanField(default=True)
    can_access_fees = models.BooleanField(default=False)
    can_access_payroll = models.BooleanField(default=False)
    can_access_exams = models.BooleanField(default=False)
    can_access_reports = models.BooleanField(default=False)
    can_access_admissions = models.BooleanField(default=False)
    can_access_idcards = models.BooleanField(default=False)
    can_access_communications = models.BooleanField(default=False)
    can_access_expenses = models.BooleanField(default=False)
    can_access_backup = models.BooleanField(default=False)
    can_access_settings = models.BooleanField(default=False)

    # ==========================================
    # RECYCLE BIN
    # ==========================================

    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(
        null=True,
        blank=True
    )

    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_employees'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    # ==========================================
    # PASSWORD GENERATOR
    # ==========================================

    def get_default_raw_password(self):
        if self.phone:
            return str(self.phone)

        if self.employee_id:
            return str(self.employee_id)

        return "12345678"

    # ==========================================
    # AUTO USER CREATION + LOGIN SYNC
    # ==========================================

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        if not self.employee_id:
            self.employee_id = f"EMP{self.id}"
            super().save(update_fields=["employee_id"])

        password = self.get_default_raw_password()

        existing_user = User.objects.filter(
            username=self.employee_id
        ).first()

        # --------------------------------------
        # EXISTING USER FOUND
        # --------------------------------------

        if existing_user and self.user != existing_user:

            self.user = existing_user

            self.user.first_name = self.name
            self.user.is_active = self.is_active
            self.user.save()

            super().save(update_fields=["user"])

        # --------------------------------------
        # CREATE NEW USER
        # --------------------------------------

        elif not self.user:

            user = User.objects.create_user(
                username=self.employee_id,
                password=password,
                first_name=self.name,
            )

            user.is_staff = False
            user.is_superuser = False
            user.is_active = self.is_active
            user.save()

            self.user = user

            super().save(update_fields=["user"])

        # --------------------------------------
        # UPDATE LINKED USER
        # --------------------------------------

        else:

            self.user.username = self.employee_id
            self.user.first_name = self.name
            self.user.is_active = self.is_active

            self.user.save()

    def __str__(self):
        return f"{self.name} ({self.employee_id})"