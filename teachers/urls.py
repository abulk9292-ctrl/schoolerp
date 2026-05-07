from django.urls import path
from . import views

urlpatterns = [

    path('', views.employee_list, name='employee_list'),

    path('add/', views.employee_add, name='employee_add'),

    path('edit/<int:pk>/', views.employee_edit, name='employee_edit'),

    path('delete/<int:pk>/', views.employee_delete, name='employee_delete'),

    # 🔥 EMPLOYEE DETAIL
    path('<int:pk>/', views.employee_detail, name='employee_detail'),

    # 🔥 STATUS
    path(
        'discontinue/<int:pk>/',
        views.employee_discontinue,
        name='employee_discontinue'
    ),

    path(
        'rejoin/<int:pk>/',
        views.employee_rejoin,
        name='employee_rejoin'
    ),

    # 🔥 PASSWORD PRINT
    path(
        'teacher-password-print/',
        views.teacher_password_print,
        name='teacher_password_print'
    ),

    # 🔥 PRINT ALL SALARY SLIPS
    path(
        'salary-slips/<int:pk>/',
        views.employee_salary_slips_print,
        name='employee_salary_slips_print'
    ),

]