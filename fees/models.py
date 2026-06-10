from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone

from students.models import Student
from academics.models import Class, AcademicSession


class FeeStructure(models.Model):
    class_assigned = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='fee_structures'
    )

    section = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        default=""
    )

    session = models.ForeignKey(
        AcademicSession,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='fee_structures'
    )

    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    admission_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    art_material = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    books_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    uniform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = (
            'class_assigned',
            'section',
            'session'
        )

    def save(self, *args, **kwargs):
        if not self.session:
            self.session = AcademicSession.objects.filter(is_active=True).first()

        super().save(*args, **kwargs)

    def __str__(self):
        session_name = self.session.session_name if self.session else "No Session"
        sec = self.section if self.section else "No Section"

        return f"{self.class_assigned} - {sec} Fee Structure - {session_name}"


class FeeCollection(models.Model):
    PAYMENT_MODE_CHOICES = [
        ('Cash', 'Cash'),
        ('Online', 'Online'),
        ('Card', 'Card'),
        ('Bank', 'Bank'),
    ]

    STATUS_CHOICES = [
        ('Paid', 'Paid'),
        ('Partial', 'Partial'),
        ('Due', 'Due'),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='fee_collections'
    )

    section = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        default=""
    )

    session = models.ForeignKey(
        AcademicSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fee_collections'
    )

    fees_month = models.CharField(max_length=50)
    payment_date = models.DateField()

    receipt_no = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
        null=True
    )

    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    admission_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    art_material = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    books_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    uniform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fine = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    others = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    previous_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Due'
    )

    payment_mode = models.CharField(
        max_length=20,
        choices=PAYMENT_MODE_CHOICES,
        default='Cash'
    )

    operator_name = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    # =========================
    # RECYCLE BIN
    # =========================
    
    is_deleted = models.BooleanField(default=False)
    
    deleted_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_fee_collections'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (
            'student',
            'session',
            'fees_month'
        )

    def get_auto_previous_balance(self):
        latest_due = FeeCollection.objects.filter(
            student=self.student,
            session=self.session
        ).exclude(
            pk=self.pk
        ).order_by(
            '-payment_date',
            '-id'
        ).first()

        if latest_due:
            return latest_due.due_balance or Decimal('0.00')

        return Decimal('0.00')

    def calculate_totals(self):
        if not self.session:
            self.session = AcademicSession.objects.filter(is_active=True).first()

        self.previous_balance = self.get_auto_previous_balance()

        gross_total = (
            (self.monthly_fee or Decimal('0.00')) +
            (self.admission_fee or Decimal('0.00')) +
            (self.registration_fee or Decimal('0.00')) +
            (self.art_material or Decimal('0.00')) +
            (self.transport_fee or Decimal('0.00')) +
            (self.books_fee or Decimal('0.00')) +
            (self.uniform_fee or Decimal('0.00')) +
            (self.fine or Decimal('0.00')) +
            (self.others or Decimal('0.00')) +
            (self.previous_balance or Decimal('0.00'))
        )

        self.discount_amount = (
            gross_total * (self.discount_percent or Decimal('0.00'))
        ) / Decimal('100')

        self.total_amount = gross_total - self.discount_amount

        self.due_balance = self.total_amount - (
            self.deposit_amount or Decimal('0.00')
        )

        if self.due_balance <= 0:
            self.status = 'Paid'
        elif self.deposit_amount > 0:
            self.status = 'Partial'
        else:
            self.status = 'Due'

    def save(self, *args, **kwargs):
        if self.student and not self.section:
            self.section = self.student.section or ""

        if not self.session:
            self.session = AcademicSession.objects.filter(is_active=True).first()

        self.calculate_totals()

        if not self.receipt_no:
            last = FeeCollection.objects.order_by('-id').first()
            next_id = 1 if not last else last.id + 1
            self.receipt_no = f"ARM-REC-{next_id:06d}"

        super().save(*args, **kwargs)

    def __str__(self):
        session_name = self.session.session_name if self.session else "No Session"
        sec = self.section if self.section else "No Section"

        return f"{self.student.student_name} - {sec} - {session_name} - {self.fees_month}"

# =========================================================
# FEE FOLLOW-UP / PROMISE TO PAY
# =========================================================

class FeeFollowUp(models.Model):
    FOLLOWUP_TYPE_CHOICES = [
        ('CALL', 'Call'),
        ('HOME_VISIT', 'Home Visit'),
        ('SCHOOL_MEET', 'School Meeting'),
        ('WHATSAPP', 'WhatsApp'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CALLED', 'Called'),
        ('VISITED', 'Visited'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='fee_followups'
    )

    session = models.ForeignKey(
        AcademicSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fee_followups'
    )

    parent_name = models.CharField(max_length=150, blank=True, null=True)
    mobile = models.CharField(max_length=30, blank=True, null=True)

    due_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    promise_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    promise_date = models.DateField()
    followup_type = models.CharField(
        max_length=20,
        choices=FOLLOWUP_TYPE_CHOICES,
        default='CALL'
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='NORMAL'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    next_action = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='Example: Call father, Visit home, Send WhatsApp reminder'
    )

    remark = models.TextField(blank=True, null=True)
    result_note = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_fee_followups'
    )

    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['promise_date', '-priority', '-id']
        verbose_name = 'Fee Follow-up / Promise'
        verbose_name_plural = 'Fee Follow-ups / Promises'

    @property
    def is_overdue(self):
        return self.status not in ['PAID', 'CANCELLED'] and self.promise_date < timezone.now().date()

    @property
    def is_today(self):
        return self.promise_date == timezone.now().date()

    def save(self, *args, **kwargs):
        if self.student:
            if not self.parent_name:
                self.parent_name = (
                    getattr(self.student, 'guardian_name', None)
                    or getattr(self.student, 'father_name', None)
                    or ''
                )

            if not self.mobile:
                self.mobile = (
                    getattr(self.student, 'phone', None)
                    or getattr(self.student, 'mobile', None)
                    or ''
                )

            if not self.session:
                self.session = (
                    getattr(self.student, 'current_session', None)
                    or AcademicSession.objects.filter(is_active=True).first()
                )

        if self.status in ['PAID', 'CANCELLED'] and not self.completed_at:
            self.completed_at = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} - Promise {self.promise_amount} on {self.promise_date}"
