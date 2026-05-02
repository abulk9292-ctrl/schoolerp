from django.urls import path
from . import views

urlpatterns = [
    path('classes/', views.class_list, name='class_list'),
    path('subjects/', views.subject_list, name='subject_list'),
]