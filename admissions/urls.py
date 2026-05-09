from django.urls import path
from . import views

urlpatterns = [
    path("", views.online_admission_list, name="online_admission_list"),
    path("approve/<int:pk>/", views.approve_admission, name="approve_admission"),
    path("reject/<int:pk>/", views.reject_admission, name="reject_admission"),
]