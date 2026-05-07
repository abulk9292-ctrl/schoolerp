from django.urls import path
from . import views

urlpatterns = [
    path('', views.complaint_list, name='complaint_list'),

    path('add/<int:student_id>/', views.complaint_add, name='complaint_add'),

    path('solve/<int:pk>/', views.complaint_solve, name='complaint_solve'),

    # 🔥 NEW
    path('edit/<int:pk>/', views.complaint_edit, name='complaint_edit'),
    path('delete/<int:pk>/', views.complaint_delete, name='complaint_delete'),
]