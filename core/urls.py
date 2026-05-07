from django.urls import path
from . import views

urlpatterns = [
    # ❌ REMOVE dashboard duplicate (important)
    # path('dashboard/', views.dashboard),

    # ✅ Only teacher dashboard এখানে থাকবে
    path('teacher-dashboard/', views.teacher_dashboard, name='teacher_dashboard'),

    # Reports
    path('today-attendance/', views.today_attendance_report, name='today_attendance'),
    path('teacher-attendance/', views.teacher_attendance_report, name='teacher_attendance'),
    path('fees-report/', views.fees_report, name='fees_report'),
    path('profit-loss/', views.profit_loss_report, name='profit_loss'),
    path('low-performance/', views.low_performance_report, name='low_performance'),
    path('complaints/', views.complaint_report, name='complaint_report'),
]