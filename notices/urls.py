from django.urls import path
from . import views


urlpatterns = [
    path("", views.notice_list, name="notice_list"),
    path("add/", views.notice_add, name="notice_add"),
    path("edit/<int:pk>/", views.notice_edit, name="notice_edit"),
    path("delete/<int:pk>/", views.notice_delete, name="notice_delete"),
]