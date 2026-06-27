from django.contrib import admin, messages
from django.contrib.auth.hashers import make_password

from .models import Student, Parent


# =========================
# Student Actions
# =========================

@admin.action(description="🔐 Reset Student Password (Default)")
def reset_student_password(modeladmin, request, queryset):
    success = 0

    for student in queryset:
        raw_password = student.get_default_raw_password()

        student.login_password = make_password(
            raw_password
        )

        student.save(
            update_fields=['login_password']
        )

        success += 1

    messages.success(
        request,
        f"✅ {success} student password reset done"
    )


@admin.action(description="🎓 Mark Selected Students as Promoted")
def promote_students(modeladmin, request, queryset):
    count = queryset.update(
        is_promoted=True
    )

    messages.success(
        request,
        f"✅ {count} students marked as promoted"
    )


@admin.action(description="↩️ Remove Promotion Status")
def unpromote_students(modeladmin, request, queryset):
    count = queryset.update(
        is_promoted=False
    )

    messages.success(
        request,
        f"✅ Promotion removed from {count} students"
    )


# =========================
# Student Admin
# =========================

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
        'is_promoted',
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
        'gender',
        'is_active',
        'login_enabled',
        'is_promoted',
    )

    list_per_page = 50

    actions = [
        reset_student_password,
        promote_students,
        unpromote_students,
    ]

    def show_default_password(self, obj):
        return obj.get_default_raw_password()

    show_default_password.short_description = (
        "Default Password"
    )


# =========================
# Parent Actions
# =========================

@admin.action(description="🔐 Reset Parent Password")
def reset_parent_password(
    modeladmin,
    request,
    queryset
):
    success = 0

    for parent in queryset:

        raw_password = (
            parent.student
            .get_default_raw_password()
        )

        parent.password = make_password(
            raw_password
        )

        parent.save(
            update_fields=['password']
        )

        success += 1

    messages.success(
        request,
        f"✅ {success} parent password reset done"
    )


# =========================
# Parent Admin
# =========================

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):

    list_display = (
        'student',
        'username',
        'phone',
        'show_default_password',
        'is_active',
    )

    search_fields = (
        'student__student_name',
        'student__student_id',
        'username',
        'phone',
    )

    list_filter = (
        'is_active',
    )

    actions = [
        reset_parent_password,
    ]

    def show_default_password(self, obj):
        return (
            obj.student
            .get_default_raw_password()
        )

    show_default_password.short_description = (
        "Default Password"
    )