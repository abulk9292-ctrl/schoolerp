from django.urls import path
from . import views

urlpatterns = [

    # =====================================================
    # DASHBOARD
    # =====================================================

    path(
        '',
        views.behaviour_dashboard,
        name='behaviour_dashboard'
    ),

    # =====================================================
    # BEHAVIOUR RECORDS
    # =====================================================

    path(
        'records/',
        views.behaviour_record_list,
        name='behaviour_record_list'
    ),

    path(
        'records/add/',
        views.behaviour_record_add,
        name='behaviour_record_add'
    ),

    path(
        'records/edit/<int:pk>/',
        views.behaviour_record_edit,
        name='behaviour_record_edit'
    ),

    path(
        'records/delete/<int:pk>/',
        views.behaviour_record_delete,
        name='behaviour_record_delete'
    ),

    # =====================================================
    # SKILL EVALUATION
    # =====================================================

    path(
        'skills/',
        views.skill_evaluation_list,
        name='skill_evaluation_list'
    ),

    path(
        'skills/add/',
        views.skill_evaluation_add,
        name='skill_evaluation_add'
    ),

    path(
        'skills/edit/<int:pk>/',
        views.skill_evaluation_edit,
        name='skill_evaluation_edit'
    ),

    path(
        'skills/delete/<int:pk>/',
        views.skill_evaluation_delete,
        name='skill_evaluation_delete'
    ),

    # =====================================================
    # STUDENT PROFILE
    # =====================================================

    path(
        'student/<int:student_id>/',
        views.student_behaviour_profile,
        name='student_behaviour_profile'
    ),

]