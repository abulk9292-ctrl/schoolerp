from django.urls import path
from . import views

urlpatterns = [


# =====================================================
# TEACHER AUTH
# =====================================================

path(
    "login/",
    views.teacher_login,
    name="teacher_login"
),

path(
    "logout/",
    views.teacher_logout,
    name="teacher_logout"
),

path(
    "dashboard/",
    views.teacher_dashboard,
    name="teacher_dashboard"
),

# =====================================================
# PRINT
# =====================================================

path(
    "teacher-password-print/",
    views.teacher_password_print,
    name="teacher_password_print"
),

path(
    "salary-slips/<int:pk>/",
    views.employee_salary_slips_print,
    name="employee_salary_slips_print"
),

# =====================================================
# STATUS
# =====================================================

path(
    "discontinue/<int:pk>/",
    views.employee_discontinue,
    name="employee_discontinue"
),

path(
    "rejoin/<int:pk>/",
    views.employee_rejoin,
    name="employee_rejoin"
),

# =====================================================
# EMPLOYEE MANAGEMENT
# =====================================================

path(
    "add/",
    views.employee_add,
    name="employee_add"
),

path(
    "edit/<int:pk>/",
    views.employee_edit,
    name="employee_edit"
),

path(
    "reset-password/<int:pk>/",
    views.employee_reset_password,
    name="employee_reset_password"
),

path(
    "delete/<int:pk>/",
    views.employee_delete,
    name="employee_delete"
),

# =====================================================
# EMPLOYEE RECYCLE BIN
# =====================================================

path(
    "recycle-bin/",
    views.employee_recycle_bin,
    name="employee_recycle_bin"
),

path(
    "restore/<int:pk>/",
    views.employee_restore,
    name="employee_restore"
),

path(
    "permanent-delete/<int:pk>/",
    views.employee_permanent_delete,
    name="employee_permanent_delete"
),

# =====================================================
# EMPLOYEE DETAIL
# =====================================================

path(
    "<int:pk>/",
    views.employee_detail,
    name="employee_detail"
),

path(
    "",
    views.employee_list,
    name="employee_list"
),


]
