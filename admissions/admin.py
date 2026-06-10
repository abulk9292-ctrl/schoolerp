from django.contrib import admin
from .models import Admission


@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):

    list_display = (
        "admission_no",
        "student_name",
        "student_class",
        "section",
        "mobile",
        "status",
        "created_student_id",
        "approved_at",
        "created_at",
    )

    list_filter = (
        "status",
        "student_class",
        "section",
        "gender",
        "transport_required",
        "hostel_required",
        "created_at",
    )

    search_fields = (
        "admission_no",
        "student_name",
        "father_name",
        "mother_name",
        "mobile",
        "guardian_mobile",
        "aadhaar_no",
    )

    readonly_fields = (
        "admission_no",
        "created_student_id",
        "approved_at",
        "approved_by",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )

    list_per_page = 50

    fieldsets = (

        (
            "Admission Information",
            {
                "fields": (
                    "admission_no",
                    "status",
                    "remarks",
                )
            }
        ),

        (
            "Student Information",
            {
                "fields": (
                    "student_name",
                    "father_name",
                    "mother_name",
                    "date_of_birth",
                    "gender",
                    "student_class",
                    "section",
                )
            }
        ),

        (
            "Contact Information",
            {
                "fields": (
                    "mobile",
                    "guardian_mobile",
                    "aadhaar_no",
                    "address",
                )
            }
        ),

        (
            "Additional Information",
            {
                "fields": (
                    "previous_school",
                    "transport_required",
                    "hostel_required",
                    "student_photo",
                )
            }
        ),

        (
            "Approval Details",
            {
                "fields": (
                    "created_student_id",
                    "approved_at",
                    "approved_by",
                    "is_duplicate_checked",
                )
            }
        ),

        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            }
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "approved_by"
        )