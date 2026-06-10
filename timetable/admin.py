from django.contrib import admin
from .models import Period, ClassTimetable, TimetableHoliday


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ("name", "start_time", "end_time", "order", "is_break")
    list_editable = ("order", "is_break")


@admin.register(TimetableHoliday)
class TimetableHolidayAdmin(admin.ModelAdmin):
    list_display = ("day", "title", "is_holiday")
    list_editable = ("is_holiday",)


@admin.register(ClassTimetable)
class ClassTimetableAdmin(admin.ModelAdmin):
    list_display = ("class_assigned", "section", "day", "period", "subject", "teacher", "room_no", "is_active")
    list_filter = ("day", "class_assigned", "is_active")
    search_fields = ("section", "room_no", "subject__subject_name", "teacher__name")
