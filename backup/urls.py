from django.urls import path
from . import views

urlpatterns = [
    path('', views.manual_backup, name='backup_home'),
    # ✅ Existing (same রাখা হয়েছে)
    path('manual/', views.manual_backup, name='manual_backup'),

    # 🔥 NEW (Backup History Page)
    path('history/', views.backup_history, name='backup_history'),

    # 🔥 NEW (Download specific backup)
    path('download/<str:file_name>/', views.download_backup, name='download_backup'),
]