from django.urls import path
from . import views

urlpatterns = [

    path('', views.reports_home, name='reports_home'),

    path('today-attendance/', views.today_attendance_report, name='today_attendance_report'),
    path('teacher-attendance/', views.teacher_attendance_report, name='teacher_attendance_report'),
    path('fees/', views.fees_report, name='fees_report'),
    path('profit-loss/', views.profit_loss_report, name='profit_loss_report'),
    path('low-performance/', views.low_performance_report, name='low_performance_report'),
    path('complaints/', views.complaint_report, name='complaint_report'),

]