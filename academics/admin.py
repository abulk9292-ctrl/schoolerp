from django.contrib import admin

from .models import (
    AcademicSession,
    Class,
    Section,
    Subject,
    ClassSubject,
    ClassRoutine,
)


# =========================
# ACADEMIC SESSION ADMIN
# =========================

@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):

    list_display = (
        "session_name",
        "start_date",
        "end_date",
        "is_active",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "session_name",
    )

    ordering = (
        "-start_date",
    )


# =========================
# CLASS ADMIN
# =========================

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):

    list_display = (
        "class_name",
        "class_teacher",
        "is_active",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "class_name",
        "class_teacher__name",
        "class_teacher__employee_name",
    )

    ordering = (
        "class_name",
    )


# =========================
# SECTION ADMIN
# =========================

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):

    list_display = (
        "school_class",
        "section_name",
        "is_active",
    )

    list_filter = (
        "school_class",
        "is_active",
    )

    search_fields = (
        "school_class__class_name",
        "section_name",
    )

    ordering = (
        "school_class__class_name",
        "section_name",
    )


# =========================
# SUBJECT ADMIN
# =========================

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):

    list_display = (
        "subject_name",
        "subject_code",
        "is_active",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "subject_name",
        "subject_code",
    )

    ordering = (
        "subject_name",
    )


# =========================
# CLASS SUBJECT ADMIN
# =========================

@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):

    list_display = (
        "school_class",
        "subject_rank",
        "subject",
        "full_marks",
        "pass_marks",
        "written_marks",
        "oral_marks",
        "practical_marks",
        "is_active",
    )

    list_editable = (
        "subject_rank",
    )

    list_filter = (
        "school_class",
        "subject",
        "is_active",
    )

    search_fields = (
        "school_class__class_name",
        "subject__subject_name",
        "subject__subject_code",
    )

    ordering = (
        "school_class__class_name",
        "subject_rank",
        "subject__subject_name",
    )

    fieldsets = (

        (
            "Basic Information",
            {
                "fields": (
                    "school_class",
                    "subject",
                    "subject_rank",
                    "is_active",
                )
            }
        ),

        (
            "Marks Setup",
            {
                "fields": (
                    "full_marks",
                    "pass_marks",
                    "written_marks",
                    "oral_marks",
                    "practical_marks",
                )
            }
        ),

    )

# =========================
# CLASS ROUTINE ADMIN
# =========================

@admin.register(ClassRoutine)
class ClassRoutineAdmin(admin.ModelAdmin):

    list_display = (
        "class_name",
        "section",
        "day",
        "period",
        "start_time",
        "end_time",
        "subject",
        "teacher",
        "room",
        "is_active",
    )

    list_filter = (
        "class_name",
        "section",
        "day",
        "is_active",
    )

    search_fields = (
        "class_name",
        "section",
        "subject",
        "teacher",
        "room",
    )

    ordering = (
        "class_name",
        "section",
        "day",
        "start_time",
    )