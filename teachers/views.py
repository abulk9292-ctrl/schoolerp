from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import Employee
from .forms import EmployeeForm
from django.utils import timezone


# =====================================================
# TEACHER LOGIN - DJANGO AUTH SYSTEM
# =====================================================

def teacher_login(request):

    if request.user.is_authenticated:
        employee = getattr(request.user, "employee", None)

        if employee:
            return redirect("teacher_dashboard")

        if request.user.is_superuser or request.user.is_staff:
            return redirect("dashboard")

        logout(request)

    if request.method == "POST":
        employee_id = request.POST.get("employee_id", "").strip()
        password = request.POST.get("password", "").strip()

        user = authenticate(
            request,
            username=employee_id,
            password=password
        )

        if user is None:
            messages.error(request, "❌ Invalid Employee ID or Password")
            return redirect("teacher_login")

        employee = getattr(user, "employee", None)

        if not employee:
            messages.error(request, "❌ No employee profile linked with this account")
            return redirect("teacher_login")

        if not employee.is_active:
            messages.error(request, "❌ This teacher account is inactive")
            return redirect("teacher_login")

        login(request, user)

        messages.success(request, f"✅ Welcome {employee.name}")
        return redirect("teacher_dashboard")

    return render(request, "teachers/teacher_login.html")


# =====================================================
# TEACHER LOGOUT
# =====================================================

def teacher_logout(request):
    logout(request)
    messages.success(request, "✅ Teacher logged out successfully")
    return redirect("teacher_login")


# =====================================================
# TEACHER DASHBOARD V2 - REPLACE ONLY teacher_dashboard FUNCTION
# =====================================================

@login_required(login_url="/teachers/login/")
def teacher_dashboard(request):

    employee = getattr(request.user, "employee", None)

    if not employee:
        messages.error(request, "❌ No employee profile linked")
        return redirect("teacher_login")

    if not employee.is_active:
        logout(request)
        messages.error(request, "❌ Your account is inactive")
        return redirect("teacher_login")

    from django.utils import timezone
    today = timezone.localdate()

    assigned_students_count = 0
    present_today = 0
    absent_today = 0
    late_today = 0

    teacher_attendance_total = 0
    teacher_attendance_present = 0
    teacher_attendance_percentage = 0
    today_teacher_attendance = None

    pending_complaints = 0
    submitted_complaints = 0
    solved_complaints = 0

    active_homework = 0
    total_submissions = 0
    pending_reviews = 0
    reviewed_homework = 0

    salary_paid = 0
    salary_due = 0

    teacher_score = 0
    teacher_grade = "No Data"

    # ================= STUDENTS + TODAY ATTENDANCE =================
    try:
        from students.models import Student
        from attendance.models import StudentAttendance, TeacherAttendance

        students = Student.objects.filter(is_active=True)

        if employee.assigned_class:
            students = students.filter(class_assigned=employee.assigned_class)

        if employee.assigned_section:
            students = students.filter(section=employee.assigned_section)

        assigned_students_count = students.count()

        today_records = StudentAttendance.objects.filter(
            student__in=students,
            date=today
        )

        present_today = today_records.filter(status="Present").count()
        absent_today = today_records.filter(status="Absent").count()
        late_today = today_records.filter(status="Late").count()

        teacher_attendance_qs = TeacherAttendance.objects.filter(employee=employee)
        teacher_attendance_total = teacher_attendance_qs.count()
        teacher_attendance_present = teacher_attendance_qs.filter(status="Present").count()

        if teacher_attendance_total > 0:
            teacher_attendance_percentage = round(
                (teacher_attendance_present / teacher_attendance_total) * 100,
                2
            )

        today_teacher_attendance = teacher_attendance_qs.filter(date=today).first()

    except Exception:
        pass

    # ================= COMPLAINTS =================
    try:
        from complaints.models import Complaint

        complaint_qs = Complaint.objects.select_related("student").all()

        if not employee.is_erp_admin:
            if employee.assigned_class:
                complaint_qs = complaint_qs.filter(student__class_assigned=employee.assigned_class)
            else:
                complaint_qs = complaint_qs.none()

            if employee.assigned_section:
                complaint_qs = complaint_qs.filter(student__section=employee.assigned_section)

        pending_complaints = complaint_qs.filter(status="PENDING_TEACHER").count()
        submitted_complaints = complaint_qs.filter(status="PENDING_ADMIN_APPROVAL").count()
        solved_complaints = complaint_qs.filter(status="SOLVED").count()

    except Exception:
        pass

    # ================= HOMEWORK =================
    try:
        from homework.models import Homework, HomeworkSubmission

        hw_qs = Homework.objects.all()

        if not employee.is_erp_admin:
            hw_qs = hw_qs.filter(given_by=employee)

        active_homework = hw_qs.filter(status="Active").count()

        total_submissions = HomeworkSubmission.objects.filter(
            homework__in=hw_qs
        ).count()

        pending_reviews = HomeworkSubmission.objects.filter(
            homework__in=hw_qs
        ).exclude(status="Reviewed").count()

        reviewed_homework = HomeworkSubmission.objects.filter(
            homework__in=hw_qs,
            status="Reviewed"
        ).count()

    except Exception:
        pass

    # ================= SALARY =================
    try:
        from payroll.models import Salary

        salary_qs = Salary.objects.filter(employee=employee)

        for s in salary_qs:
            salary_paid += s.paid_amount or 0
            salary_due += s.due_amount or 0

    except Exception:
        pass

    # ================= AI TEACHER SCORE =================
    try:
        attendance_score = teacher_attendance_percentage

        complaint_score = 100
        total_complaints = pending_complaints + submitted_complaints + solved_complaints
        if total_complaints > 0:
            complaint_score = round((solved_complaints / total_complaints) * 100, 2)

        homework_score = 100
        if total_submissions > 0:
            homework_score = round((reviewed_homework / total_submissions) * 100, 2)

        class_attendance_score = 0
        total_today = present_today + absent_today + late_today
        if total_today > 0:
            class_attendance_score = round((present_today / total_today) * 100, 2)

        teacher_score = round(
            (attendance_score * 0.35) +
            (complaint_score * 0.20) +
            (homework_score * 0.20) +
            (class_attendance_score * 0.25),
            2
        )

        if teacher_score >= 90:
            teacher_grade = "Platinum Teacher"
        elif teacher_score >= 80:
            teacher_grade = "Gold Teacher"
        elif teacher_score >= 65:
            teacher_grade = "Silver Teacher"
        elif teacher_score > 0:
            teacher_grade = "Needs Improvement"
        else:
            teacher_grade = "No Data"

    except Exception:
        teacher_score = 0
        teacher_grade = "No Data"

    return render(request, "teachers/teacher_dashboard.html", {
        "employee": employee,

        "assigned_students_count": assigned_students_count,
        "present_today": present_today,
        "absent_today": absent_today,
        "late_today": late_today,

        "teacher_attendance_total": teacher_attendance_total,
        "teacher_attendance_present": teacher_attendance_present,
        "teacher_attendance_percentage": teacher_attendance_percentage,
        "today_teacher_attendance": today_teacher_attendance,

        "pending_complaints": pending_complaints,
        "submitted_complaints": submitted_complaints,
        "solved_complaints": solved_complaints,

        "active_homework": active_homework,
        "total_submissions": total_submissions,
        "pending_reviews": pending_reviews,
        "reviewed_homework": reviewed_homework,

        "salary_paid": salary_paid,
        "salary_due": salary_due,

        "teacher_score": teacher_score,
        "teacher_grade": teacher_grade,
    })


# =====================================================
# ADMIN PERMISSION HELPER
# =====================================================

def check_permission(request, permission_field):

    if not request.user.is_authenticated:
        return False

    if request.user.is_superuser or request.user.is_staff:
        return True

    emp = getattr(request.user, "employee", None)

    if not emp:
        return False

    if emp.is_erp_admin:
        return True

    return getattr(emp, permission_field, False)


# =====================================================
# EMPLOYEE LIST
# =====================================================

@login_required
def employee_list(request):

    if not check_permission(request, "can_access_teachers"):
        messages.error(request, "❌ Permission Denied")
        return redirect("dashboard")

    employees = Employee.objects.filter(is_deleted=False).order_by("id")

    return render(request, "teachers/employee_list.html", {
        "employees": employees
    })


# =====================================================
# EMPLOYEE DETAIL
# =====================================================

@login_required
def employee_detail(request, pk):

    if not check_permission(request, "can_access_teachers"):
        messages.error(request, "❌ Permission Denied")
        return redirect("dashboard")

    employee = get_object_or_404(Employee, pk=pk)

    attendance_total = 0
    attendance_present = 0
    attendance_absent = 0
    attendance_late = 0
    attendance_percentage = 0

    try:
        from attendance.models import TeacherAttendance

        attendance_queryset = TeacherAttendance.objects.filter(employee=employee)

        attendance_total = attendance_queryset.count()
        attendance_present = attendance_queryset.filter(status="Present").count()
        attendance_absent = attendance_queryset.filter(status="Absent").count()
        attendance_late = attendance_queryset.filter(status="Late").count()

        if attendance_total > 0:
            attendance_percentage = round(
                (attendance_present / attendance_total) * 100,
                2
            )

    except Exception:
        pass

    salary_records = []
    total_salary_paid = 0
    total_salary_due = 0
    total_salary_advance = 0
    total_salary_payable = 0
    latest_salary = None

    paid_salary_count = 0
    unpaid_salary_count = 0
    partial_salary_count = 0
    advance_salary_count = 0

    try:
        from payroll.models import Salary

        salary_records = Salary.objects.filter(
            employee=employee
        ).order_by("-year", "-created_at")

        latest_salary = salary_records.first()

        for s in salary_records:
            total_salary_paid += s.paid_amount or 0
            total_salary_due += s.due_amount or 0
            total_salary_advance += s.advance_amount or 0
            total_salary_payable += s.payable_amount or 0

        paid_salary_count = salary_records.filter(status="Paid").count()
        unpaid_salary_count = salary_records.filter(status="Unpaid").count()
        partial_salary_count = salary_records.filter(status="Partial").count()
        advance_salary_count = salary_records.filter(status="Advance").count()

    except Exception:
        pass

    return render(request, "teachers/employee_detail.html", {
        "employee": employee,

        "attendance_total": attendance_total,
        "attendance_present": attendance_present,
        "attendance_absent": attendance_absent,
        "attendance_late": attendance_late,
        "attendance_percentage": attendance_percentage,

        "salary_records": salary_records,
        "latest_salary": latest_salary,

        "total_salary_paid": total_salary_paid,
        "total_salary_due": total_salary_due,
        "total_salary_advance": total_salary_advance,
        "total_salary_payable": total_salary_payable,

        "paid_salary_count": paid_salary_count,
        "unpaid_salary_count": unpaid_salary_count,
        "partial_salary_count": partial_salary_count,
        "advance_salary_count": advance_salary_count,
    })


# =====================================================
# EMPLOYEE ADD
# =====================================================

@login_required
def employee_add(request):

    if not check_permission(request, "can_access_teachers"):
        messages.error(request, "❌ Permission Denied")
        return redirect("dashboard")

    if request.method == "POST":
        form = EmployeeForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, "✅ Employee added successfully.")
            return redirect("employee_list")
    else:
        form = EmployeeForm()

    return render(request, "teachers/employee_form.html", {
        "form": form,
        "page_title": "Add Employee"
    })


# =====================================================
# EMPLOYEE EDIT
# =====================================================

@login_required
def employee_edit(request, pk):

    if not check_permission(request, "can_access_teachers"):
        messages.error(request, "❌ Permission Denied")
        return redirect("dashboard")

    employee = get_object_or_404(Employee, pk=pk)

    if request.method == "POST":
        form = EmployeeForm(request.POST, request.FILES, instance=employee)

        if form.is_valid():
            form.save()
            messages.success(request, "✅ Employee updated successfully.")
            return redirect("employee_detail", pk=employee.pk)
    else:
        form = EmployeeForm(instance=employee)

    return render(request, "teachers/employee_form.html", {
        "form": form,
        "page_title": "Edit Employee"
    })


# =====================================================
# EMPLOYEE DELETE
# =====================================================

@login_required
def employee_delete(request, pk):

    
    if not check_permission(request, "can_access_teachers"):
        messages.error(request, "❌ Permission Denied")
        return redirect("dashboard")

    employee = get_object_or_404(
        Employee,
        pk=pk,
        is_deleted=False
    )
    
    if request.method == "POST":
    
        employee.is_deleted = True
        employee.deleted_at = timezone.now()
        employee.deleted_by = request.user
    
        employee.save()
    
        messages.success(
            request,
            "🗑 Employee moved to recycle bin successfully."
        )
    
        return redirect("employee_list")
    
    return render(
        request,
        "teachers/employee_confirm_delete.html",
        {
            "employee": employee
    }
    )




# =====================================================
# EMPLOYEE DISCONTINUE
# =====================================================

@login_required
def employee_discontinue(request, pk):

    if not check_permission(request, "can_access_teachers"):
        messages.error(request, "❌ Permission Denied")
        return redirect("dashboard")

    employee = get_object_or_404(Employee, pk=pk)
    employee.is_active = False
    employee.save(update_fields=["is_active"])

    if employee.user:
        employee.user.is_active = False
        employee.user.save(update_fields=["is_active"])

    messages.warning(request, f"{employee.name} discontinued.")
    return redirect("employee_detail", pk=employee.pk)


# =====================================================
# EMPLOYEE REJOIN
# =====================================================

@login_required
def employee_rejoin(request, pk):

    if not check_permission(request, "can_access_teachers"):
        messages.error(request, "❌ Permission Denied")
        return redirect("dashboard")

    employee = get_object_or_404(Employee, pk=pk)
    employee.is_active = True
    employee.save(update_fields=["is_active"])

    if employee.user:
        employee.user.is_active = True
        employee.user.save(update_fields=["is_active"])

    messages.success(request, f"{employee.name} rejoined.")
    return redirect("employee_detail", pk=employee.pk)


# =====================================================
# TEACHER PASSWORD PRINT
# =====================================================

@login_required
def teacher_password_print(request):

    if not check_permission(request, "can_access_teachers"):
        messages.error(request, "❌ Permission Denied")
        return redirect("dashboard")

    selected_designation = request.GET.get("designation")

    employees = Employee.objects.filter(
        is_active=True
    ).order_by("designation", "id")

    if selected_designation:
        employees = employees.filter(designation=selected_designation)

    designations = Employee.objects.filter(
        is_active=True
    ).values_list(
        "designation",
        flat=True
    ).distinct().order_by("designation")

    return render(request, "teachers/teacher_password_print.html", {
        "employees": employees,
        "designations": designations,
        "selected_designation": selected_designation,
    })


# =====================================================
# PRINT ALL SALARY SLIPS
# =====================================================

@login_required
def employee_salary_slips_print(request, pk):

    if not check_permission(request, "can_access_teachers"):
        messages.error(request, "❌ Permission Denied")
        return redirect("dashboard")

    employee = get_object_or_404(Employee, pk=pk)

    salary_records = []
    total_paid = 0
    total_due = 0
    total_advance = 0
    total_payable = 0

    try:
        from payroll.models import Salary

        salary_records = Salary.objects.filter(
            employee=employee
        ).order_by("-year", "-created_at")

        for s in salary_records:
            total_paid += s.paid_amount or 0
            total_due += s.due_amount or 0
            total_advance += s.advance_amount or 0
            total_payable += s.payable_amount or 0

    except Exception:
        pass

    return render(request, "teachers/employee_salary_slips_print.html", {
        "employee": employee,
        "salary_records": salary_records,
        "total_paid": total_paid,
        "total_due": total_due,
        "total_advance": total_advance,
        "total_payable": total_payable,
    })

# =====================================================
# EMPLOYEE RECYCLE BIN
# =====================================================

@login_required
def employee_recycle_bin(request):

    employees = Employee.objects.filter(
        is_deleted=True
    ).order_by("-deleted_at")

    return render(
        request,
        "teachers/employee_recycle_bin.html",
        {
            "employees": employees
        }
    )


@login_required
def employee_restore(request, pk):

    if not request.user.is_superuser:
        messages.error(
            request,
            "Only Super Admin can restore employees."
        )
        return redirect("employee_recycle_bin")

    employee = get_object_or_404(
        Employee,
        pk=pk,
        is_deleted=True
    )

    employee.is_deleted = False
    employee.deleted_at = None
    employee.deleted_by = None
    employee.save()

    messages.success(
        request,
        f"{employee.name} restored successfully."
    )

    return redirect("employee_recycle_bin")


@login_required
def employee_permanent_delete(request, pk):

    if not request.user.is_superuser:
        messages.error(
            request,
            "Only Super Admin can permanently delete employees."
        )
        return redirect("employee_recycle_bin")

    employee = get_object_or_404(
        Employee,
        pk=pk,
        is_deleted=True
    )

    if request.method != "POST":
        messages.error(
            request,
            "Invalid request."
        )
        return redirect("employee_recycle_bin")

    employee.delete()

    messages.success(
        request,
        "Employee permanently deleted."
    )

    return redirect("employee_recycle_bin")