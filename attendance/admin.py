from django.contrib import admin

from .models import (
    StudentAttendance,
    TeacherAttendance,
    AttendanceAlert,
    Holiday,
)


# =========================================================
# STUDENT ATTENDANCE
# =========================================================

@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "student_roll_no",
        "session",
        "date",
        "section",
        "status",
    )

    list_filter = (
        "status",
        "session",
        "section",
        "date",
    )

    search_fields = (
        "student__student_name",
        "student__student_id",
        "student__roll_no",
    )

    ordering = (
        "-date",
        "student__section",
        "student__roll_no",
        "student__student_name",
    )

    date_hierarchy = "date"

    @admin.display(description="Roll No")
    def student_roll_no(self, obj):
        return getattr(obj.student, "roll_no", "")


# =========================================================
# TEACHER ATTENDANCE
# =========================================================

@admin.register(TeacherAttendance)
class TeacherAttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "session",
        "date",
        "status",
        "within_range",
        "distance_meters",
    )

    list_filter = (
        "status",
        "within_range",
        "session",
        "date",
    )

    search_fields = (
        "employee__name",
        "employee__phone",
    )

    ordering = (
        "-date",
        "employee__name",
    )

    date_hierarchy = "date"


# =========================================================
# ATTENDANCE ALERT
# =========================================================

@admin.register(AttendanceAlert)
class AttendanceAlertAdmin(admin.ModelAdmin):
    list_display = (
        "alert_type",
        "student",
        "employee",
        "attendance_status",
        "approval_status",
        "date",
    )

    list_filter = (
        "alert_type",
        "approval_status",
        "attendance_status",
        "date",
    )

    search_fields = (
        "student__student_name",
        "student__student_id",
        "student__roll_no",
        "employee__name",
    )

    ordering = (
        "-created_at",
    )

    date_hierarchy = "date"


# =========================================================
# HOLIDAY
# =========================================================

@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "date",
        "holiday_type",
        "is_half_day",
        "is_active",
    )

    list_filter = (
        "holiday_type",
        "is_half_day",
        "is_active",
        "date",
    )

    search_fields = (
        "title",
        "note",
    )

    ordering = (
        "-date",
    )

    date_hierarchy = "date"