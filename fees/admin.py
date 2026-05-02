from django.contrib import admin
from .models import FeeCollection


@admin.register(FeeCollection)
class FeeCollectionAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'fees_month',
        'payment_date',
        'total_amount',
        'discount_amount',
        'deposit_amount',
        'due_balance',
        'payment_mode',
    )
    list_filter = ('fees_month', 'payment_date', 'payment_mode')
    search_fields = (
        'student__student_name',
        'student__student_id',
        'student__registration_no',
        'operator_name',
    )