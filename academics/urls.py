from django.urls import path
from . import views

urlpatterns = [

    # =========================
    # CLASS
    # =========================
    path(
        'classes/',
        views.class_list,
        name='class_list'
    ),

    path(
        'classes/edit/<int:pk>/',
        views.class_edit,
        name='class_edit'
    ),

    path(
        'classes/delete/<int:pk>/',
        views.class_delete,
        name='class_delete'
    ),

    # =========================
    # SUBJECT
    # =========================
    path(
        'subjects/',
        views.subject_list,
        name='subject_list'
    ),

    path(
        'subjects/edit/<int:pk>/',
        views.subject_edit,
        name='subject_edit'
    ),

    path(
        'subjects/delete/<int:pk>/',
        views.subject_delete,
        name='subject_delete'
    ),

    # =========================
    # CLASS SUBJECT ASSIGN
    # =========================
    path(
        'class-subjects/',
        views.class_subject_assign,
        name='class_subject_assign'
    ),

]