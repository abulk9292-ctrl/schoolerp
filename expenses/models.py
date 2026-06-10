from django.db import models
from django.contrib.auth.models import User

class Expense(models.Model):

    CATEGORY_CHOICES = [
        ('Electricity', 'Electricity'),
        ('Maintenance', 'Maintenance'),
        ('Stationary', 'Stationary'),
        ('Salary Extra', 'Salary Extra'),
        ('Transport', 'Transport'),
        ('Other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True, null=True)

    # =========================
    # RECYCLE BIN
    # =========================

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
        related_name='deleted_expenses'
    )

    def __str__(self):
        return f"{self.title} - {self.amount}"