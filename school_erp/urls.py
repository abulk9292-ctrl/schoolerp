from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth import logout


from core.views import (
    dashboard,
    custom_login,
)


# =========================================================
# ROOT REDIRECT
# =========================================================

def home_redirect(request):
    return redirect("/site/")


# =========================================================
# LOGOUT VIEW
# =========================================================

def logout_view(request):
    logout(request)
    return redirect("/admin-login/")


# =========================================================
# URL PATTERNS
# =========================================================

urlpatterns = [

    # DJANGO ADMIN PANEL
    path("admin/", admin.site.urls),

    # PUBLIC WEBSITE
    path("", home_redirect, name="home"),
    path("site/", include("website.urls")),

    # ADMIN / STAFF LOGIN
    path("admin-login/", custom_login, name="login"),
    path("logout/", logout_view, name="logout"),

    # ADMIN DASHBOARD
    path("dashboard/", dashboard, name="dashboard"),

    # MAIN ERP MODULES
    path("academics/", include("academics.urls")),
    path("students/", include("students.urls")),
    path("teachers/", include("teachers.urls")),
    path("attendance/", include("attendance.urls")),
    path("fees/", include("fees.urls")),
    path("payroll/", include("payroll.urls")),
    path("expenses/", include("expenses.urls")),
    path("reports/", include("reports.urls")),
    path("admissions/", include("admissions.urls")),
    path("idcards/", include("idcards.urls")),
    path("communications/", include("communications.urls")),
    path("complaints/", include("complaints.urls")),
    path("settings/", include("settings_app.urls")),
    path("exams/", include("exams.urls")),
    path("backup/", include("backup.urls")),
    path("certificates/", include("certificates.urls")),
    path("behaviour/", include("behaviour.urls")),
    path("homework/", include("homework.urls")),
    path("notices/", include("notices.urls")),
    path("live-classes/", include("live_classes.urls")),
    path("question-answers/", include("question_answers.urls")),

    # API URLS
    path("api/", include("api.urls")),
    path("mobile-api/", include("mobile_api.urls")),

    # CORE EXTRA URLS
    path("", include("core.urls")),

    # ONLINE STORE URLS
    path("online-store/", include("online_store.urls")),

    # TIMETABLE URLS
    path("timetable/", include("timetable.urls")),

    # SCHOOL ASSETS URLS
    path("assets/", include("school_assets.urls")),




]


# =========================================================
# MEDIA + STATIC FILES
# =========================================================

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    if settings.STATIC_ROOT:
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)