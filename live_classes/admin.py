from django.contrib import admin
from .models import LiveClass, LiveClassAttendance


@admin.register(LiveClass)
class LiveClassAdmin(admin.ModelAdmin):
    list_display = ("title", "class_assigned", "section", "subject", "start_time", "status", "is_active")
    list_filter = ("status", "is_active", "class_assigned")
    search_fields = ("title", "subject", "meeting_link")


@admin.register(LiveClassAttendance)
class LiveClassAttendanceAdmin(admin.ModelAdmin):
    list_display = ("live_class", "student", "joined_at")
    search_fields = ("live_class__title", "student__student_name")
