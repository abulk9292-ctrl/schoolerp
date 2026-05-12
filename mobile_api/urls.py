from django.urls import path
from . import views


urlpatterns = [

    # =========================================================
    # API HOME
    # =========================================================

    path(
        '',
        views.api_home,
        name='api_home'
    ),

    # =========================================================
    # AUTH APIs
    # =========================================================

    path(
        'login/',
        views.login_api,
        name='login_api'
    ),

    path(
        'logout/',
        views.logout_api,
        name='logout_api'
    ),

    path(
        'profile/',
        views.profile_api,
        name='profile_api'
    ),

    # =========================================================
    # DASHBOARD APIs
    # =========================================================

    path(
        'dashboard-summary/',
        views.dashboard_summary_api,
        name='dashboard_summary_api'
    ),

    # =========================================================
    # STUDENT APIs
    # =========================================================

    # -------------------------
    # Student List
    # -------------------------

    path(
        'students/',
        views.student_list_api,
        name='student_list_api'
    ),

    # -------------------------
    # Student Detail
    # -------------------------

    path(
        'students/<int:student_id>/',
        views.student_detail_api,
        name='student_detail_api'
    ),

    # -------------------------
    # Students By Class
    # -------------------------

    path(
        'students-by-class/<str:class_name>/',
        views.students_by_class_api,
        name='students_by_class_api'
    ),

    # =========================================================
    # STUDENT ATTENDANCE APIs
    # =========================================================

    # -------------------------
    # Attendance List
    # -------------------------

    path(
        'student-attendance/',
        views.student_attendance_list_api,
        name='student_attendance_list_api'
    ),

    # -------------------------
    # Mark Attendance
    # -------------------------

    path(
        'student-attendance/mark/',
        views.mark_student_attendance_api,
        name='mark_student_attendance_api'
    ),

    # -------------------------
    # Bulk Attendance
    # -------------------------

    path(
        'student-attendance/bulk-mark/',
        views.student_bulk_attendance_mark_api,
        name='student_bulk_attendance_mark_api'
    ),

    # -------------------------
    # Attendance Summary
    # -------------------------

    path(
        'student-attendance-summary/',
        views.student_attendance_summary_api,
        name='student_attendance_summary_api'
    ),

    # -------------------------
    # Student Attendance Report
    # -------------------------

    path(
        'student-attendance-report/<int:student_id>/',
        views.student_attendance_report_api,
        name='student_attendance_report_api'
    ),

    # -------------------------
    # Student Attendance %
    # -------------------------

    path(
        'student-attendance-percentage/<int:student_id>/',
        views.student_attendance_percentage_api,
        name='student_attendance_percentage_api'
    ),

    # =========================================================
    # TEACHER ATTENDANCE APIs
    # =========================================================

    # -------------------------
    # Attendance List
    # -------------------------

    path(
        'teacher-attendance/',
        views.teacher_attendance_list_api,
        name='teacher_attendance_list_api'
    ),

    # -------------------------
    # Mark Attendance
    # -------------------------

    path(
        'teacher-attendance/mark/',
        views.mark_teacher_attendance_api,
        name='mark_teacher_attendance_api'
    ),

    # -------------------------
    # Attendance Summary
    # -------------------------

    path(
        'teacher-attendance-summary/',
        views.teacher_attendance_summary_api,
        name='teacher_attendance_summary_api'
    ),

    # -------------------------
    # Teacher Attendance Report
    # -------------------------

    path(
        'teacher-attendance-report/<int:employee_id>/',
        views.teacher_attendance_employee_report_api,
        name='teacher_attendance_employee_report_api'
    ),

    # -------------------------
    # My Attendance Report
    # -------------------------

    path(
        'teacher-attendance-my-report/',
        views.teacher_attendance_my_report_api,
        name='teacher_attendance_my_report_api'
    ),

    # =========================================================
    # TEST PAGE
    # =========================================================

    path(
        'test-attendance/',
        views.teacher_attendance_test_page,
        name='test_attendance_page'
    ),
    
    # =====================================================
    # HOMEWORK APIs
    # =====================================================

    path(
        'homeworks/',
        views.homework_list_api,
        name='homework_list_api'
    ),

    path(
        'homeworks/<int:homework_id>/',
        views.homework_detail_api,
        name='homework_detail_api'
    ),

    # =====================================================
    # EXAM ROUTINE APIs
    # =====================================================

    path(
       'exams/',
        views.exam_list_api,
        name='exam_list_api'
    ),

    path(
        'exam-routines/',
        views.exam_routine_api,
        name='exam_routine_api'
    ),

    # =====================================================
    # RESULT APIs
    # =====================================================

    path(
        'student-results/',
        views.student_result_api,
        name='student_result_api'
    ),

    path(
        'result-summary/',
        views.result_summary_api,
        name='result_summary_api'
    ),

    # =====================================================
    # NOTICE APIs
    # =====================================================
    path(
        'notices/',
        views.notice_list_api,
        name='notice_list_api'
    ),

    # =====================================================
    # MARKS ENTRY APIs
    # =====================================================

    path(
        'marks-entry/',
        views.marks_entry_api,
        name='marks_entry_api'
    ),

    path(
        'bulk-marks-entry/',
        views.bulk_marks_entry_api,
        name='bulk_marks_entry_api'
    ),

    path(
        "student-attendance-register/",
        views.student_attendance_register_api,
        name="student_attendance_register_api"
    ),

    path(
        "qr-attendance/mark/",
        views.qr_student_attendance_api,
        name="qr_student_attendance_api"
    ),

    path("qr-attendance/mark/", views.qr_student_attendance_api, name="qr_student_attendance_api"),

]