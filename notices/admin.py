from django.contrib import admin
from .models import Notice


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "notice_type",
        "target",
        "school_class",
        "published_by",
        "publish_date",
        "expiry_date",
        "status",
        "is_pinned",
    )
    list_filter = ("notice_type", "target", "status", "is_pinned", "publish_date")
    search_fields = ("title", "description", "school_class")