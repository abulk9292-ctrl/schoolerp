from django.contrib import admin

from .models import (
    Exam,
    ExamRoutine,
    ExamSubjectAssign,
    ExamResult,
    StudentResultSummary,
    ClassTest,
    ClassTestResult,
    ClassTestSubjectMark,
)


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("name", "academic_session", "start_date", "end_date", "is_active")
    list_filter = ("academic_session", "is_active")
    search_fields = ("name", "academic_session")
    ordering = ("-id",)


@admin.register(ExamRoutine)
class ExamRoutineAdmin(admin.ModelAdmin):
    list_display = ("exam", "academic_session", "school_class", "section", "subject", "date", "start_time", "end_time", "total_marks")
    list_filter = ("academic_session", "school_class", "section", "date")
    search_fields = ("exam__name", "school_class", "section", "subject")
    ordering = ("date", "start_time")


@admin.register(ExamSubjectAssign)
class ExamSubjectAssignAdmin(admin.ModelAdmin):
    list_display = ("exam", "academic_session", "school_class", "section", "subject", "full_marks", "pass_marks", "is_active")
    list_filter = ("academic_session", "school_class", "section", "is_active")
    search_fields = ("exam__name", "school_class", "section", "subject")


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ("student", "exam", "academic_session", "section", "subject", "written_marks", "oral_marks", "max_marks")
    list_filter = ("academic_session", "exam", "section", "subject")
    search_fields = ("student__student_name", "student__student_id", "subject")
    ordering = ("student__roll_no", "student__student_name")


@admin.register(StudentResultSummary)
class StudentResultSummaryAdmin(admin.ModelAdmin):
    list_display = ("student", "exam", "academic_session", "total_marks", "max_total_marks", "percentage", "grade", "result_status", "rank")
    list_filter = ("academic_session", "exam", "result_status", "grade")
    search_fields = ("student__student_name", "student__student_id")


@admin.register(ClassTest)
class ClassTestAdmin(admin.ModelAdmin):
    list_display = ("test_name", "class_name", "section", "subject", "exam_date", "total_marks", "academic_session", "is_active")
    list_filter = ("academic_session", "class_name", "section", "subject", "is_active")
    search_fields = ("test_name", "class_name", "section", "subject")


@admin.register(ClassTestResult)
class ClassTestResultAdmin(admin.ModelAdmin):
    list_display = ("class_test", "student", "academic_session", "marks_obtained", "percentage")
    list_filter = ("academic_session", "class_test")
    search_fields = ("student__student_name", "student__student_id")


@admin.register(ClassTestSubjectMark)
class ClassTestSubjectMarkAdmin(admin.ModelAdmin):
    list_display = ("class_test_result", "subject", "written_marks", "oral_marks", "max_marks", "total_marks")
    search_fields = ("subject",)
