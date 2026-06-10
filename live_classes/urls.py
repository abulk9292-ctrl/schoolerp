from django.urls import path
from . import views

app_name = "live_classes"

urlpatterns = [
    path("", views.live_class_list, name="live_class_list"),
    path("add/", views.live_class_add, name="live_class_add"),
    path("<int:pk>/edit/", views.live_class_edit, name="live_class_edit"),
    path("<int:pk>/delete/", views.live_class_delete, name="live_class_delete"),
    path("<int:pk>/join/", views.live_class_join, name="live_class_join"),

    path("student/", views.student_live_class_list, name="student_live_class_list"),
    path("parent/", views.parent_live_class_list, name="parent_live_class_list"),
]
