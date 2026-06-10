from django.urls import path

from . import views

urlpatterns = [

    # =====================================================
    # HOMEWORK MANAGEMENT
    # =====================================================

    path(
        "",
        views.homework_list,
        name="homework_list"
    ),

    path(
        "add/",
        views.homework_add,
        name="homework_add"
    ),

    path(
        "edit/<int:pk>/",
        views.homework_edit,
        name="homework_edit"
    ),

    path(
        "delete/<int:pk>/",
        views.homework_delete,
        name="homework_delete"
    ),

    # =====================================================
    # STUDENT HOMEWORK
    # =====================================================

    path(
        "student/",
        views.student_homework_list,
        name="student_homework_list"
    ),

    path(
        "student/submit/<int:pk>/",
        views.student_homework_submit,
        name="student_homework_submit"
    ),

    # =====================================================
    # TEACHER REVIEW
    # =====================================================

    path(
        "submissions/",
        views.homework_submission_list,
        name="homework_submission_list"
    ),

    path(
        "submissions/review/<int:pk>/",
        views.homework_submission_review,
        name="homework_submission_review"
    ),

    # =====================================================
    # PARENT HOMEWORK
    # =====================================================

    path(
        "parent/",
        views.parent_homework_list,
        name="parent_homework_list"
    ),

]