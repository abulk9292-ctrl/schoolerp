from django.urls import path
from . import views

urlpatterns = [
    path('', views.payroll_dashboard, name='payroll_dashboard'),

    path('salary/', views.salary_list, name='salary_list'),
    path('salary/add/', views.salary_add, name='salary_add'),
    path('salary/<int:pk>/', views.salary_detail, name='salary_detail'),
    path('salary/auto-generate/', views.auto_generate_salary, name='auto_generate_salary'),
    path('salary/<int:pk>/edit/', views.salary_edit, name='salary_edit'),
    path('salary/<int:pk>/delete/', views.salary_delete, name='salary_delete'),
    path('salary/<int:pk>/print/', views.salary_print, name='salary_print'),
    path('get-employee-absent-days/', views.get_employee_absent_days, name='get_employee_absent_days'),
]