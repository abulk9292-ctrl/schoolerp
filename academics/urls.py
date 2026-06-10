from django.urls import path

from . import views


urlpatterns = [

    # =========================
    # ACADEMIC SESSION
    # =========================
    path(
        "sessions/",
        views.session_list,
        name="session_list"
    ),

    path(
        "sessions/edit/<int:pk>/",
        views.session_edit,
        name="session_edit"
    ),

    path(
        "sessions/delete/<int:pk>/",
        views.session_delete,
        name="session_delete"
    ),

    # =========================
    # CLASS
    # =========================
    path(
        "classes/",
        views.class_list,
        name="class_list"
    ),

    path(
        "classes/edit/<int:pk>/",
        views.class_edit,
        name="class_edit"
    ),

    path(
        "classes/delete/<int:pk>/",
        views.class_delete,
        name="class_delete"
    ),

    # =========================
    # SECTION
    # =========================
    path(
        "sections/",
        views.section_list,
        name="section_list"
    ),

    path(
        "sections/edit/<int:pk>/",
        views.section_edit,
        name="section_edit"
    ),

    path(
        "sections/delete/<int:pk>/",
        views.section_delete,
        name="section_delete"
    ),

    # =========================
    # SUBJECT
    # =========================
    path(
        "subjects/",
        views.subject_list,
        name="subject_list"
    ),

    path(
        "subjects/edit/<int:pk>/",
        views.subject_edit,
        name="subject_edit"
    ),

    path(
        "subjects/delete/<int:pk>/",
        views.subject_delete,
        name="subject_delete"
    ),

    # =========================
    # CLASS SUBJECT ASSIGN
    # =========================
    path(
        "class-subjects/",
        views.class_subject_assign,
        name="class_subject_assign"
    ),

    # =========================
    # SUBJECT RANK MANAGE
    # =========================
    path(
        "class-subjects/rank/",
        views.subject_rank_manage,
        name="subject_rank_manage"
    ),
    

    # =========================
    # CLASS ROUTINE
    # =========================
    path(
        "routine/",
        views.class_routine_list,
        name="class_routine_list"
    ),

    path(
        "routine/edit/<int:pk>/",
        views.class_routine_edit,
        name="class_routine_edit"
    ),

    path(
        "routine/delete/<int:pk>/",
        views.class_routine_delete,
        name="class_routine_delete"
    ),

    path(
        "routine/print/",
        views.class_routine_print,
        name="class_routine_print"
    ),

]