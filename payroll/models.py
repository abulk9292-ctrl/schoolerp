from decimal import Decimal, ROUND_HALF_UP
import calendar

from django.db import models
from teachers.models import Employee


class Salary(models.Model):

    MONTH_CHOICES = [
        ('January', 'January'),
        ('February', 'February'),
        ('March', 'March'),
        ('April', 'April'),
        ('May', 'May'),
        ('June', 'June'),
        ('July', 'July'),
        ('August', 'August'),
        ('September', 'September'),
        ('October', 'October'),
        ('November', 'November'),
        ('December', 'December'),
    ]

    STATUS_CHOICES = [
        ('Paid', 'Paid'),
        ('Unpaid', 'Unpaid'),
        ('Partial', 'Partial'),
        ('Advance', 'Advance'),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='salary_records'
    )

    month = models.CharField(max_length=20, choices=MONTH_CHOICES)
    year = models.IntegerField()

    basic_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    bonus = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    absent_days = models.PositiveIntegerField(default=0)

    payable_absent_days = models.PositiveIntegerField(default=0)

    month_days = models.PositiveIntegerField(default=30)

    per_day_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    attendance_deduction = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    extra_deduction = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    net_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    previous_due = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    payable_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    due_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    advance_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    payment_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Unpaid'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('employee', 'month', 'year')
        ordering = ['-year', '-id']

    def __str__(self):
        return f"{self.employee.name} - {self.month} {self.year}"

    # ==========================
    # MONTH NUMBER
    # ==========================
    def get_month_number(self):

        months = {
            'January': 1,
            'February': 2,
            'March': 3,
            'April': 4,
            'May': 5,
            'June': 6,
            'July': 7,
            'August': 8,
            'September': 9,
            'October': 10,
            'November': 11,
            'December': 12,
        }

        return months.get(self.month, 1)

    # ==========================
    # PREVIOUS DUE
    # ==========================
    def get_previous_due_amount(self):

        current_month_no = self.get_month_number()

        previous_records = Salary.objects.filter(
            employee=self.employee
        ).exclude(pk=self.pk)

        latest_record = None
        latest_key = None

        for record in previous_records:

            record_month_no = record.get_month_number()

            if (
                record.year < self.year
                or (
                    record.year == self.year
                    and record_month_no < current_month_no
                )
            ):

                key = (record.year, record_month_no)

                if latest_key is None or key > latest_key:
                    latest_key = key
                    latest_record = record

        if latest_record:
            return latest_record.due_amount or Decimal('0.00')

        return Decimal('0.00')

    # ==========================
    # PAYMENT STATUS
    # ==========================
    def calculate_payment_status(self):

        if not self.paid_amount:
            self.paid_amount = Decimal('0.00')

        if not self.payable_amount:
            self.payable_amount = Decimal('0.00')

        if self.paid_amount >= self.payable_amount:

            self.due_amount = Decimal('0.00')

            self.advance_amount = (
                self.paid_amount - self.payable_amount
            )

            if self.advance_amount > 0:
                self.status = 'Advance'
            else:
                self.status = 'Paid'

        elif self.paid_amount > 0:

            self.due_amount = (
                self.payable_amount - self.paid_amount
            )

            self.advance_amount = Decimal('0.00')

            self.status = 'Partial'

        else:

            self.due_amount = self.payable_amount
            self.advance_amount = Decimal('0.00')
            self.status = 'Unpaid'

        # Safety
        if self.due_amount < 0:
            self.due_amount = Decimal('0.00')

    # ==========================
    # MAIN SALARY CALCULATION
    # ==========================
    def calculate_salary(self):

        # Auto basic salary
        if not self.basic_salary:
            self.basic_salary = (
                self.employee.salary or Decimal('0.00')
            )

        month_number = self.get_month_number()

        # Month days
        self.month_days = calendar.monthrange(
            self.year,
            month_number
        )[1]

        # Per day salary
        if self.basic_salary:

            self.per_day_salary = (
                self.basic_salary / Decimal(self.month_days)
            ).quantize(
                Decimal('0.01'),
                rounding=ROUND_HALF_UP
            )

        else:
            self.per_day_salary = Decimal('0.00')

        # ==========================
        # ATTENDANCE CHECK
        # ==========================
        try:

            from attendance.models import TeacherAttendance

            self.absent_days = TeacherAttendance.objects.filter(
                employee=self.employee,
                date__year=self.year,
                date__month=month_number,
                status='Absent'
            ).count()

        except Exception:
            self.absent_days = 0

        # ==========================
        # RULES
        # absent 0  = 1 day bonus
        # absent 1  = no deduction
        # absent >1 = absent-1 deduction
        # ==========================

        auto_bonus = Decimal('0.00')

        if self.absent_days == 0:

            self.payable_absent_days = 0

            auto_bonus = self.per_day_salary

        elif self.absent_days == 1:

            self.payable_absent_days = 0

        else:

            self.payable_absent_days = (
                self.absent_days - 1
            )

        # Only auto bonus if no manual bonus
        if self.bonus <= 0:
            self.bonus = auto_bonus

        # Deduction
        self.attendance_deduction = (
            self.per_day_salary
            * Decimal(self.payable_absent_days)
        ).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )

        # Net Salary
        self.net_salary = (

            self.basic_salary
            + self.bonus
            - self.attendance_deduction
            - self.extra_deduction

        ).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )

        # Safety
        if self.net_salary < 0:
            self.net_salary = Decimal('0.00')

        # Previous Due
        self.previous_due = self.get_previous_due_amount()

        # Final Payable
        self.payable_amount = (
            self.net_salary + self.previous_due
        ).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )

        self.calculate_payment_status()

    # ==========================
    # SAVE
    # ==========================
    def save(self, *args, **kwargs):

        if getattr(self, 'payment_only_update', False):

            self.calculate_payment_status()

        else:

            self.calculate_salary()

        super().save(*args, **kwargs)