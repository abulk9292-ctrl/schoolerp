from django.urls import path
from . import views

app_name = "question_answers"

urlpatterns = [
    path("", views.question_list, name="question_list"),
    path("ask/", views.question_ask, name="question_ask"),
    path("<int:pk>/answer/", views.question_answer, name="question_answer"),
    path("<int:pk>/detail/", views.question_detail, name="question_detail"),
    path("<int:pk>/delete/", views.question_delete, name="question_delete"),

    path("student/", views.student_question_list, name="student_question_list"),
    path("parent/", views.parent_question_list, name="parent_question_list"),
]
