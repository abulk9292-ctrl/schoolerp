from django.urls import path
from . import views

urlpatterns = [
    path('students/', views.student_attendance, name='student_attendance'),
    path('teachers/', views.teacher_attendance, name='teacher_attendance'),

    path('students/daily-report/', views.student_daily_report, name='student_daily_report'),
    path('teachers/daily-report/', views.teacher_daily_report, name='teacher_daily_report'),
    path('students/percentage-report/', views.student_percentage_report, name='student_percentage_report'),
    path('students/monthly-report/', views.student_monthly_report, name='student_monthly_report'),
    path('graph/', views.attendance_graph, name='attendance_graph'),
    path('students/class/<str:class_name>/', views.student_attendance_by_class, name='student_attendance_by_class'),
    path('students/class/<str:class_name>/', views.student_attendance_by_class),
    path('register/', views.attendance_register, name='attendance_register'),
    path('alerts/', views.attendance_alert_list, name='attendance_alert_list'),
    path('alerts/approve/<int:pk>/', views.attendance_alert_approve, name='attendance_alert_approve'),
    path('alerts/reject/<int:pk>/', views.attendance_alert_reject, name='attendance_alert_reject'),
    
    
    
]