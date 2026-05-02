from django.contrib import admin
from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        'student_id',
        'registration_no',
        'student_name',
        'class_assigned',
        'roll_no',
        'phone',
        'is_active',
    )
    search_fields = ('student_id', 'registration_no', 'student_name', 'phone')
    list_filter = ('class_assigned', 'is_active', 'gender')