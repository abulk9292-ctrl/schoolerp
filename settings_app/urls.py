from django.urls import path
from . import views

urlpatterns = [
    path('', views.general_settings, name='general_settings'),
]