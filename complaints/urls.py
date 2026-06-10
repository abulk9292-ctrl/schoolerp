from django.urls import path
from . import views

urlpatterns = [

    # ADMIN COMPLAINT LIST
    path("", views.complaint_list, name="complaint_list"),

    # ADD COMPLAINT
    path("add/<int:student_id>/", views.complaint_add, name="complaint_add"),

    # TEACHER COMPLAINT DASHBOARD
    path(
        "teacher-dashboard/",
        views.teacher_complaint_dashboard,
        name="teacher_complaint_dashboard"
    ),

    # TEACHER SUBMIT SOLUTION
    path(
        "teacher-submit/<int:pk>/",
        views.teacher_submit_complaint,
        name="teacher_submit_complaint"
    ),

    # ADMIN APPROVAL PANEL
    path(
        "admin-approval/",
        views.admin_complaint_approval,
        name="admin_complaint_approval"
    ),

    # ADMIN APPROVE / SOLVE
    path("solve/<int:pk>/", views.complaint_solve, name="complaint_solve"),

    # ADMIN REJECT / SEND BACK
    path("reject/<int:pk>/", views.complaint_reject, name="complaint_reject"),

    # EDIT
    path("edit/<int:pk>/", views.complaint_edit, name="complaint_edit"),

    # DELETE
    path("delete/<int:pk>/", views.complaint_delete, name="complaint_delete"),
]