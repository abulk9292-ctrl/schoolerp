from django.urls import path
from . import views

urlpatterns = [
    path('', views.api_home, name='api_home'),
    path('login/', views.login_api, name='login_api'),
    path('profile/', views.profile_api, name='profile_api'),
    path('dashboard-summary/', views.dashboard_summary_api, name='dashboard_summary_api'),

    # =========================
    # STUDENT APIs
    # =========================
    path('students/', views.student_list_api, name='student_list_api'),

    path('students-by-class/<str:class_name>/', views.students_by_class_api, name='students_by_class_api'),

    path('student-attendance/', views.student_attendance_list_api, name='student_attendance_list_api'),
    path('student-attendance/mark/', views.mark_student_attendance_api, name='mark_student_attendance_api'),

    path('student-attendance/bulk-mark/', views.student_bulk_attendance_mark_api, name='student_bulk_attendance_mark_api'),

    path('student-attendance-summary/', views.student_attendance_summary_api, name='student_attendance_summary_api'),

    path('student-attendance-report/<int:student_id>/', views.student_attendance_report_api, name='student_attendance_report_api'),

    # =========================
    # TEACHER APIs
    # =========================
    path('teacher-attendance/', views.teacher_attendance_list_api, name='teacher_attendance_list_api'),
    path('teacher-attendance/mark/', views.mark_teacher_attendance_api, name='mark_teacher_attendance_api'),

    path('teacher-attendance-summary/', views.teacher_attendance_summary_api, name='teacher_attendance_summary_api'),

    path('teacher-attendance-report/<int:employee_id>/', views.teacher_attendance_employee_report_api, name='teacher_attendance_employee_report_api'),

    # =========================
    # TEST PAGE
    # =========================
    path('test-attendance/', views.teacher_attendance_test_page, name='test_attendance_page'),
]