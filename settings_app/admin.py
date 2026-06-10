from django.contrib import admin

from .models import GeneralSetting


# =========================
# GENERAL SETTINGS ADMIN
# =========================

@admin.register(GeneralSetting)
class GeneralSettingAdmin(admin.ModelAdmin):

    list_display = (
        "school_name",
        "principal_name",
        "weekly_holiday",
        "half_day_enabled",
        "half_day",
        "count_holiday_attendance",
        "updated_at",
    )

    list_filter = (
        "weekly_holiday",
        "half_day_enabled",
        "half_day",
        "count_holiday_attendance",
    )

    search_fields = (
        "school_name",
        "principal_name",
    )

    readonly_fields = (
        "updated_at",
    )

    fieldsets = (

        # =========================
        # SCHOOL INFO
        # =========================
        (
            "🏫 School Information",
            {
                "fields": (
                    "school_name",
                    "principal_name",
                    "school_logo",
                    "school_header",
                    "principal_signature",
                )
            }
        ),

        # =========================
        # HOLIDAY SETTINGS
        # =========================
        (
            "📅 Holiday & Attendance Settings",
            {
                "fields": (
                    "weekly_holiday",
                    "half_day_enabled",
                    "half_day",
                    "count_holiday_attendance",
                )
            }
        ),

        # =========================
        # SYSTEM INFO
        # =========================
        (
            "⚙ System Information",
            {
                "fields": (
                    "updated_at",
                )
            }
        ),

    )