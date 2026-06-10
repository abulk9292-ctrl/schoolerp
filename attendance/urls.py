from django.urls import path
from . import views


urlpatterns = [
    # =========================
    # STUDENT ATTENDANCE
    # =========================
    path("students/", views.student_attendance, name="student_attendance"),

    # =========================
    # TEACHER ATTENDANCE
    # =========================
    path("teachers/", views.teacher_attendance, name="teacher_attendance"),

    # =========================
    # TEACHER MOBILE GPS + SELFIE
    # =========================
    path("teachers/mobile/", views.teacher_mobile_attendance, name="teacher_mobile_attendance"),

    # =========================
    # DAILY REPORTS
    # =========================
    path("students/daily-report/", views.student_daily_report, name="student_daily_report"),
    path("teachers/daily-report/", views.teacher_daily_report, name="teacher_daily_report"),

    # =========================
    # STUDENT REPORTS
    # =========================
    path("students/percentage-report/", views.student_percentage_report, name="student_percentage_report"),
    path("students/monthly-report/", views.student_monthly_report, name="student_monthly_report"),

    # =========================
    # GRAPH
    # =========================
    path("graph/", views.attendance_graph, name="attendance_graph"),

    # =========================
    # CLASS-WISE ATTENDANCE
    # =========================
    path("students/class/<str:class_name>/", views.student_attendance_by_class, name="student_attendance_by_class"),

    # =========================
    # ATTENDANCE REGISTER
    # =========================
    path("register/", views.attendance_register, name="attendance_register"),

    # =========================
    # ALERTS
    # =========================
    path("alerts/", views.attendance_alert_list, name="attendance_alert_list"),
    path("alerts/approve/<int:pk>/", views.attendance_alert_approve, name="attendance_alert_approve"),
    path("alerts/reject/<int:pk>/", views.attendance_alert_reject, name="attendance_alert_reject"),

    # =========================
    # HOLIDAYS
    # =========================
    path("holidays/", views.holiday_list, name="holiday_list"),
    path("holidays/add/", views.holiday_add, name="holiday_add"),
    path("holidays/edit/<int:pk>/", views.holiday_edit, name="holiday_edit"),
    path("holidays/delete/<int:pk>/", views.holiday_delete, name="holiday_delete"),

    # =========================
    # RESET
    # =========================
    path("reset/", views.attendance_reset, name="attendance_reset"),
    path("holiday-reset/", views.holiday_reset, name="holiday_reset"),
    path("holidays/reset/", views.holiday_reset, name="holiday_reset_old"),
]
