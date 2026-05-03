from django.contrib import admin, messages
from django.contrib.auth.hashers import make_password

from .models import Student, Parent


@admin.action(description="🔐 Reset Student Password (Default)")
def reset_student_password(modeladmin, request, queryset):
    success = 0

    for student in queryset:
        raw_password = student.get_default_raw_password()
        student.login_password = make_password(raw_password)
        student.save(update_fields=['login_password'])
        success += 1

    messages.success(request, f"✅ {success} student password reset done")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        'student_id',
        'registration_no',
        'student_name',
        'class_assigned',
        'roll_no',
        'phone',
        'date_of_birth',
        'login_username',
        'show_default_password',
        'login_enabled',
        'is_active',
    )

    search_fields = (
        'student_id',
        'registration_no',
        'student_name',
        'phone',
        'login_username',
    )

    list_filter = (
        'class_assigned',
        'is_active',
        'gender',
        'login_enabled',
    )

    actions = [reset_student_password]

    def show_default_password(self, obj):
        return obj.get_default_raw_password()

    show_default_password.short_description = "Default Password"


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'username',
        'phone',
        'show_default_password',
        'is_active',
    )

    def show_default_password(self, obj):
        return obj.student.get_default_raw_password()

    show_default_password.short_description = "Default Password"