from django.contrib import admin
from django.urls import path, include
from core.views import dashboard
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect


# 🔥 ROOT → WEBSITE
def home_redirect(request):
    return redirect('/site/')


urlpatterns = [
    path('admin/', admin.site.urls),

    # 🔥 ROOT = WEBSITE
    path('', home_redirect),

    # 🔥 PUBLIC WEBSITE
    path('site/', include('website.urls')),

    # 🔥 ERP DASHBOARD (NEW URL)
    path('dashboard/', dashboard, name='dashboard'),

    # Main Modules
    path('academics/', include('academics.urls')),
    path('students/', include('students.urls')),
    path('teachers/', include('teachers.urls')),
    path('attendance/', include('attendance.urls')),
    path('fees/', include('fees.urls')),
    path('payroll/', include('payroll.urls')),
    path('expenses/', include('expenses.urls')),

    # Modules
    path('reports/', include('reports.urls')),
    path('admissions/', include('admissions.urls')),
    path('idcards/', include('idcards.urls')),
    path('communications/', include('communications.urls')),
    path('api/', include('api.urls')),

    # Extra
    path('settings/', include('settings_app.urls')),
    path('complaints/', include('complaints.urls')),

    # Mobile API
    path('mobile-api/', include('mobile_api.urls')),

    # Exams + Backup
    path('exams/', include('exams.urls')),
    path('backup/', include('backup.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)