from django.urls import path
from . import views

urlpatterns = [

    # =====================================================
    # STUDENT / PARENT AUTH
    # =====================================================

    path(
        "login/",
        views.student_login,
        name="student_login"
    ),

    path(
        "logout/",
        views.student_logout,
        name="student_logout"
    ),

    path(
        "dashboard/",
        views.student_dashboard,
        name="student_dashboard"
    ),

    path(
        "parent/login/",
        views.parent_login,
        name="parent_login"
    ),

    path(
        "parent/logout/",
        views.parent_logout,
        name="parent_logout"
    ),

    path(
        "parent/dashboard/",
        views.parent_dashboard,
        name="parent_dashboard"
    ),

    # =====================================================
    # PASSWORD RESET / RESULT CHECK
    # =====================================================

    path(
        "forgot/",
        views.student_forgot_password,
        name="student_forgot"
    ),

    path(
        "verify/",
        views.student_verify_otp,
        name="student_verify_otp"
    ),

    path(
        "reset/",
        views.student_reset_password,
        name="student_reset_password"
    ),

    path(
        "student/change-password/",
        views.student_change_password,
        name="student_change_password"
    ),

    path(
        "result-check/",
        views.public_result_check,
        name="public_result_check"
    ),

    # =====================================================
    # STUDENT / PARENT COMPLAINT PORTAL
    # =====================================================

    path(
        "student-complaints/",
        views.student_complaint_list,
        name="student_complaint_list"
    ),

    path(
        "student-complaints/add/",
        views.student_complaint_add,
        name="student_complaint_add"
    ),

    path(
        "parent-complaints/",
        views.parent_complaint_list,
        name="parent_complaint_list"
    ),

    path(
        "parent-complaints/add/",
        views.parent_complaint_add,
        name="parent_complaint_add"
    ),

    # =====================================================
    # IMPORT SYSTEM
    # =====================================================

    path(
        "import/",
        views.student_import,
        name="student_import"
    ),

    path(
        "import-preview/",
        views.student_import_preview,
        name="student_import_preview"
    ),

    path(
        "import-confirm/",
        views.student_import_confirm,
        name="student_import_confirm"
    ),

    path(
        "download-demo/",
        views.download_student_demo,
        name="download_student_demo"
    ),

    # =====================================================
    # EXPORT / PRINT / PASSWORD PRINT
    # =====================================================

    path(
        "export-excel/",
        views.export_students_excel,
        name="export_students_excel"
    ),

    path(
        "class-wise-download/",
        views.student_classwise_download,
        name="student_classwise_download"
    ),

    path(
        "bulk-password-print/",
        views.bulk_student_password_print,
        name="bulk_student_password_print"
    ),

    # =====================================================
    # ID CARD / QR
    # =====================================================

    path(
        "id-card/<int:pk>/",
        views.student_id_card,
        name="student_id_card"
    ),

    path(
        "id-cards-print/",
        views.student_id_cards_print,
        name="student_id_cards_print"
    ),

    path(
        "qr-profile/<int:pk>/",
        views.student_qr_profile,
        name="student_qr_profile"
    ),

    path(
        "qr-attendance/<int:pk>/",
        views.student_qr_attendance,
        name="student_qr_attendance"
    ),

    # =====================================================
    # STUDENT STATUS / CLASS MOVEMENT
    # =====================================================

    path(
        "discontinue/<int:pk>/",
        views.student_discontinue,
        name="student_discontinue"
    ),

    path(
        "readmit/<int:pk>/",
        views.student_readmit,
        name="student_readmit"
    ),

    path(
        "promote/<int:pk>/",
        views.student_promote,
        name="student_promote"
    ),

    path(
        "demote/<int:pk>/",
        views.student_demote,
        name="student_demote"
    ),

    path(
        "bulk-promotion/",
        views.bulk_promotion,
        name="bulk_promotion"
    ),

    path(
        "add-sibling/<int:pk>/",
        views.add_sibling,
        name="add_sibling"
    ),

    # =====================================================
    # BASIC CRUD
    # Keep dynamic routes at bottom
    # =====================================================

    path(
        "add/",
        views.student_add,
        name="student_add"
    ),

    path(
        "edit/<int:pk>/",
        views.student_edit,
        name="student_edit"
    ),

    path(
        "delete/<int:pk>/",
        views.student_delete,
        name="student_delete"
    ),

    path(
        "<int:pk>/",
        views.student_detail,
        name="student_detail"
    ),

    path(
        "",
        views.student_list,
        name="student_list"
    ),

    # =====================================================
    # RECYCLE BIN
    # =====================================================

    path(
        "recycle-bin/",
        views.recycle_bin,
        name="recycle_bin"
    ),
    
    path(
        "restore/<int:pk>/",
        views.restore_student,
        name="restore_student"
    ),
    
    path(
        "permanent-delete/<int:pk>/",
        views.permanent_delete_student,
        name="permanent_delete_student"
    ),
    
    path(
        "discontinued/",
        views.discontinued_students,
        name="discontinued_students"
    ),
]
