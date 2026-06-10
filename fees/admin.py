from django.contrib import admin
from .models import FeeCollection, FeeStructure, FeeFollowUp


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


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = (
        'class_assigned',
        'section',
        'session',
        'monthly_fee',
        'transport_fee',
        'is_active',
    )
    list_filter = ('class_assigned', 'section', 'session', 'is_active')
    search_fields = ('class_assigned__class_name',)


@admin.register(FeeFollowUp)
class FeeFollowUpAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'parent_name',
        'mobile',
        'due_amount',
        'promise_amount',
        'promise_date',
        'followup_type',
        'priority',
        'status',
        'created_by',
    )
    list_filter = (
        'promise_date',
        'followup_type',
        'priority',
        'status',
        'session',
    )
    search_fields = (
        'student__student_name',
        'student__student_id',
        'student__registration_no',
        'parent_name',
        'mobile',
        'remark',
    )
    date_hierarchy = 'promise_date'
