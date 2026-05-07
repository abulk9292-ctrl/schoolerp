from django.contrib import admin
from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):

    # 🔥 LIST VIEW (table)
    list_display = (
        'employee_id',
        'name',
        'designation',
        'phone',
        'salary',
        'is_active',
        'is_erp_admin',

        # Quick permission view
        'can_access_students',
        'can_access_fees',
        'can_access_attendance',
        'can_access_payroll',
        'can_access_exams',
        'can_access_reports',
    )

    # 🔍 FILTER
    list_filter = (
        'is_active',
        'is_erp_admin',
        'can_access_students',
        'can_access_teachers',
        'can_access_academics',
        'can_access_attendance',
        'can_access_fees',
        'can_access_payroll',
        'can_access_exams',
        'can_access_reports',
        'can_access_admissions',
        'can_access_idcards',
        'can_access_communications',
        'can_access_expenses',
        'can_access_backup',
        'can_access_settings',
    )

    # 🔎 SEARCH
    search_fields = (
        'employee_id',
        'name',
        'designation',
        'phone',
    )

    readonly_fields = ('employee_id',)

    # 🧠 CLEAN UI GROUPING
    fieldsets = (

        # 🔹 BASIC INFO
        ('👤 Basic Info', {
            'fields': (
                'user',
                'employee_id',
                'name',
                'designation',
                'qualification',
                'subject_specialization',
                'phone',
                'aadhaar_number',
                'joining_date',
                'salary',
                'photo',
                'is_active',
            )
        }),

        # 🔹 MAIN PERMISSION
        ('🔐 Core Access', {
            'fields': (
                'is_erp_admin',
                'can_access_students',
                'can_access_teachers',
                'can_access_academics',
                'can_access_attendance',
            )
        }),

        # 🔹 FINANCIAL
        ('💰 Financial Access', {
            'fields': (
                'can_access_fees',
                'can_access_payroll',
                'can_access_expenses',
            )
        }),

        # 🔹 ACADEMIC
        ('📚 Academic Access', {
            'fields': (
                'can_access_exams',
                'can_access_reports',
                'can_access_admissions',
                'can_access_idcards',
            )
        }),

        # 🔹 SYSTEM / COMMUNICATION
        ('📡 System Access', {
            'fields': (
                'can_access_communications',
                'can_access_backup',
                'can_access_settings',
            )
        }),
    )