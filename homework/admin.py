from django.contrib import admin
from .models import Homework


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "school_class",
        "subject",
        "given_by",
        "assigned_date",
        "due_date",
        "status",
    )
    list_filter = ("school_class", "subject", "status", "assigned_date")
    search_fields = ("title", "subject", "description")