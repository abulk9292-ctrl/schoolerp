from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth import logout

from core.views import (
    dashboard,
    teacher_dashboard,
    custom_login,
)


# =========================================================
# ROOT REDIRECT
# =========================================================

def home_redirect(request):
    return redirect('/site/')


# =========================================================
# CLEAN LOGOUT
# =========================================================

def logout_view(request):
    logout(request)
    return redirect('login')


# =========================================================
# URL PATTERNS
# =========================================================

urlpatterns = [

    # =====================================================
    # ADMIN PANEL
    # =====================================================

    path(
        'admin/',
        admin.site.urls
    ),

    # =====================================================
    # ROOT WEBSITE
    # =====================================================

    path(
        '',
        home_redirect
    ),
    
    path("admissions/", include("admissions.urls")),

    # =====================================================
    # PUBLIC WEBSITE
    # =====================================================

    path(
        'site/',
        include('website.urls')
    ),

    # =====================================================
    # AUTHENTICATION
    # =====================================================

    path(
        'login/',
        custom_login,
        name='login'
    ),

    path(
        'logout/',
        logout_view,
        name='logout'
    ),

    # =====================================================
    # DASHBOARDS
    # =====================================================

    path(
        'dashboard/',
        dashboard,
        name='dashboard'
    ),

    path(
        'teacher-dashboard/',
        teacher_dashboard,
        name='teacher_dashboard'
    ),

    # =====================================================
    # MAIN ERP MODULES
    # =====================================================

    path(
        'academics/',
        include('academics.urls')
    ),

    path(
        'students/',
        include('students.urls')
    ),

    path(
        'teachers/',
        include('teachers.urls')
    ),

    path(
        'attendance/',
        include('attendance.urls')
    ),

    path(
        'fees/',
        include('fees.urls')
    ),

    path(
        'payroll/',
        include('payroll.urls')
    ),

    path(
        'expenses/',
        include('expenses.urls')
    ),

    # =====================================================
    # EXTRA MODULES
    # =====================================================

    path(
        'reports/',
        include('reports.urls')
    ),

    path(
        'admissions/',
        include('admissions.urls')
    ),

    path(
        'idcards/',
        include('idcards.urls')
    ),

    path(
        'communications/',
        include('communications.urls')
    ),

    path(
        'complaints/',
        include('complaints.urls')
    ),

    path(
        'settings/',
        include('settings_app.urls')
    ),

    # =====================================================
    # EXAMS + BACKUP
    # =====================================================

    path(
        'exams/',
        include('exams.urls')
    ),

    path(
        'backup/',
        include('backup.urls')
    ),

    # =====================================================
    # APIs
    # =====================================================

    # Main API
    path(
        'api/',
        include('api.urls')
    ),

    # Mobile API
    path(
        'mobile-api/',
        include('mobile_api.urls')
    ),

    # =====================================================
    # CORE EXTRA URLS
    # =====================================================

    path(
        '',
        include('core.urls')
    ),

    # =====================================================
    # HOMEWORK URLS
    # =====================================================

    path('homework/', include('homework.urls')),

    path('notices/', include('notices.urls')),
    
]


# =========================================================
# MEDIA + STATIC FILES
# =========================================================

if settings.DEBUG:

    # MEDIA FILES
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

    # STATIC FILES
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )

    

    