from django.urls import path
from django.shortcuts import redirect
from . import views


# =====================================================
# OLD TEACHER DASHBOARD REDIRECT
# =====================================================

def old_teacher_dashboard_redirect(request):
    return redirect("/teachers/dashboard/")


urlpatterns = [

    # =====================================================
    # LEGACY URL REDIRECTS
    # =====================================================

    path(
        "teacher-dashboard/",
        old_teacher_dashboard_redirect,
        name="old_teacher_dashboard_redirect"
    ),

    # =====================================================
    # SESSION
    # =====================================================

    path(
        "set-session/",
        views.set_global_session,
        name="set_global_session"
    ),

    # =====================================================
    # REPORTS
    # =====================================================

    path(
        "today-attendance/",
        views.today_attendance_report,
        name="today_attendance"
    ),

    path(
        "teacher-attendance/",
        views.teacher_attendance_report,
        name="teacher_attendance"
    ),

    path(
        "fees-report/",
        views.fees_report,
        name="fees_report"
    ),

    path(
        "profit-loss/",
        views.profit_loss_report,
        name="profit_loss"
    ),

    path(
        "low-performance/",
        views.low_performance_report,
        name="low_performance"
    ),

    path(
        "complaints/",
        views.complaint_report,
        name="complaint_report"
    ),
    
    # =====================================================
    # RECYCLE BIN
    # ===================================================== 
    path(
        "recycle-bin/",
        views.recycle_bin_dashboard,
        name="recycle_bin_dashboard"
    ),
]