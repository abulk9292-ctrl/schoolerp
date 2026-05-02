from django.urls import path
from . import views

urlpatterns = [
    path('', views.employee_list, name='employee_list'),
    path('add/', views.employee_add, name='employee_add'),
    path('edit/<int:pk>/', views.employee_edit, name='employee_edit'),
    path('delete/<int:pk>/', views.employee_delete, name='employee_delete'),

    # 🔥 NEW
    path('<int:pk>/', views.employee_detail, name='employee_detail'),
    path('discontinue/<int:pk>/', views.employee_discontinue, name='employee_discontinue'),
    path('rejoin/<int:pk>/', views.employee_rejoin, name='employee_rejoin'),
]