from django.contrib import admin
from .models import StudentQuestion


@admin.register(StudentQuestion)
class StudentQuestionAdmin(admin.ModelAdmin):
    list_display = ("student", "class_assigned", "subject", "title", "status", "asked_at", "answered_by")
    list_filter = ("status", "class_assigned", "subject", "is_visible_to_parent")
    search_fields = ("student__student_name", "title", "question_text", "answer_text")
