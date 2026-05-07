from django.urls import path
from . import views


urlpatterns = [
    path("", views.homework_list, name="homework_list"),
    path("add/", views.homework_add, name="homework_add"),
    path("edit/<int:pk>/", views.homework_edit, name="homework_edit"),
    path("delete/<int:pk>/", views.homework_delete, name="homework_delete"),
]