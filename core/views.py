from datetime import date, datetime

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.db.models import Count, Sum
from django.core.exceptions import FieldError

from students.models import Student
from teachers.models import Employee
from attendance.models import StudentAttendance


# =========================================================
# GLOBAL ACADEMIC SESSION SYSTEM
# =========================================================

def get_current_session():
    today = datetime.now()
    year = today.year

    if today.month >= 4:
        return f"{year}-{year + 1}"

    return f"{year - 1}-{year}"


def get_session_list():
    today = datetime.now()
    current_year = today.year
    sessions = []

    for y in range(current_year - 3, current_year + 4):
        sessions.append(f"{y}-{y + 1}")

    return sessions


def get_selected_session(request):
    selected_session = request.session.get("selected_session")

    if not selected_session:
        selected_session = get_current_session()
        request.session["selected_session"] = selected_session

    return selected_session


def get_session_dates(selected_session):
    try:
        start_year = int(selected_session.split("-")[0])
        end_year = int(selected_session.split("-")[1])
    except Exception:
        selected_session = get_current_session()
        start_year = int(selected_session.split("-")[0])
        end_year = int(selected_session.split("-")[1])

    return date(start_year, 4, 1), date(end_year, 3, 31)


def apply_session_filter(queryset, selected_session):
    try:
        model_fields = [field.name for field in queryset.model._meta.get_fields()]

        if "academic_session" in model_fields:
            return queryset.filter(academic_session=selected_session)

        if "session" in model_fields:
            return queryset.filter(session=selected_session)

        if "current_session" in model_fields:
            return queryset.filter(current_session=selected_session)

    except FieldError:
        return queryset
    except Exception:
        return queryset

    return queryset


@login_required(login_url="/admin-login/")
def set_global_session(request):
    selected_session = request.GET.get("session")

    if selected_session:
        request.session["selected_session"] = selected_session
        messages.success(request, f"Session changed to {selected_session}")

    return redirect(request.META.get("HTTP_REFERER", "/dashboard/"))


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@login_required(login_url="/admin-login/")
def dashboard(request):
    if not (request.user.is_superuser or request.user.is_staff):
        emp = getattr(request.user, "employee", None)

        if emp:
            return redirect("/teachers/dashboard/")

        logout(request)
        return redirect("/admin-login/")

    today = timezone.now().date()

    sessions = get_session_list()
    selected_session = get_selected_session(request)
    session_start, session_end = get_session_dates(selected_session)

    students_qs = Student.objects.filter(is_active=True)
    students_qs = apply_session_filter(students_qs, selected_session)

    total_students = students_qs.count()
    total_employees = Employee.objects.filter(is_active=True).count()

    today_attendance = StudentAttendance.objects.filter(date=today)
    today_attendance = apply_session_filter(today_attendance, selected_session)

    present = today_attendance.filter(status="Present").count()
    absent = today_attendance.filter(status="Absent").count()
    late = today_attendance.filter(status="Late").count()

    total_marked = present + absent + late
    attendance_percentage = round((present / total_marked) * 100, 2) if total_marked > 0 else 0

    teacher_present = 0
    teacher_absent = 0
    teacher_late = 0

    try:
        from attendance.models import TeacherAttendance

        teacher_today = TeacherAttendance.objects.filter(date=today)
        teacher_today = apply_session_filter(teacher_today, selected_session)

        teacher_present = teacher_today.filter(status="Present").count()
        teacher_absent = teacher_today.filter(status="Absent").count()
        teacher_late = teacher_today.filter(status="Late").count()
    except Exception:
        pass

    most_present = (
        apply_session_filter(
            StudentAttendance.objects.filter(
                status="Present",
                date__gte=session_start,
                date__lte=session_end,
            ),
            selected_session
        )
        .values("student__student_name", "student__student_id")
        .annotate(total=Count("id"))
        .order_by("-total")
        .first()
    )

    most_absent = (
        apply_session_filter(
            StudentAttendance.objects.filter(
                status="Absent",
                date__gte=session_start,
                date__lte=session_end,
            ),
            selected_session
        )
        .values("student__student_name", "student__student_id")
        .annotate(total=Count("id"))
        .order_by("-total")
        .first()
    )

    low_students = []

    for s in students_qs:
        attendance_qs = StudentAttendance.objects.filter(
            student=s,
            date__gte=session_start,
            date__lte=session_end,
        )
        attendance_qs = apply_session_filter(attendance_qs, selected_session)

        total = attendance_qs.count()
        present_count = attendance_qs.filter(status="Present").count()
        percent = (present_count / total * 100) if total > 0 else 0

        if total > 0 and percent < 50:
            low_students.append({
                "student": s,
                "percent": round(percent, 2)
            })

    recent_students = students_qs.order_by("-id")[:5]

    pending_complaints = 0
    recent_complaints = []

    try:
        from complaints.models import Complaint

        complaint_qs = Complaint.objects.filter(status="Pending")
        complaint_qs = apply_session_filter(complaint_qs, selected_session)

        pending_complaints = complaint_qs.count()

        recent_complaints = Complaint.objects.select_related("student").order_by("-created_at")
        recent_complaints = apply_session_filter(recent_complaints, selected_session)[:5]
    except Exception:
        pass

    today_collection = 0
    total_collection = 0
    monthly_collection = 0
    yearly_collection = 0
    estimated_month_fee = 0
    remaining_month_fee = 0

    try:
        from fees.models import FeeCollection, FeeStructure

        today_fee_qs = FeeCollection.objects.filter(payment_date=today)
        today_fee_qs = apply_session_filter(today_fee_qs, selected_session)

        today_collection = today_fee_qs.aggregate(total=Sum("deposit_amount"))["total"] or 0

        total_fee_qs = FeeCollection.objects.filter(
            payment_date__gte=session_start,
            payment_date__lte=session_end,
        )
        total_fee_qs = apply_session_filter(total_fee_qs, selected_session)

        total_collection = total_fee_qs.aggregate(total=Sum("deposit_amount"))["total"] or 0

        monthly_fee_qs = FeeCollection.objects.filter(
            payment_date__year=today.year,
            payment_date__month=today.month
        )
        monthly_fee_qs = apply_session_filter(monthly_fee_qs, selected_session)

        monthly_collection = monthly_fee_qs.aggregate(total=Sum("deposit_amount"))["total"] or 0
        yearly_collection = total_collection

        fee_structure_qs = FeeStructure.objects.filter(is_active=True)
        fee_structure_qs = apply_session_filter(fee_structure_qs, selected_session)

        estimated_month_fee = fee_structure_qs.aggregate(total=Sum("monthly_fee"))["total"] or 0
        remaining_month_fee = estimated_month_fee - monthly_collection

        if remaining_month_fee < 0:
            remaining_month_fee = 0
    except Exception:
        pass

    total_salary_expense = 0
    total_other_expense = 0
    total_profit = 0
    total_loss = 0

    try:
        from payroll.models import Salary

        salary_qs = Salary.objects.filter(
            payment_date__gte=session_start,
            payment_date__lte=session_end,
        )
        salary_qs = apply_session_filter(salary_qs, selected_session)

        total_salary_expense = salary_qs.aggregate(total=Sum("paid_amount"))["total"] or 0
    except Exception:
        pass

    try:
        from expenses.models import Expense

        expense_qs = Expense.objects.filter(
            date__gte=session_start,
            date__lte=session_end,
        )
        expense_qs = apply_session_filter(expense_qs, selected_session)

        total_other_expense = expense_qs.aggregate(total=Sum("amount"))["total"] or 0
    except Exception:
        pass

    total_expense = total_salary_expense + total_other_expense
    total_profit = total_collection - total_expense

    if total_profit < 0:
        total_loss = abs(total_profit)
        total_profit = 0

    month_labels = [
        "Apr", "May", "Jun", "Jul", "Aug", "Sep",
        "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"
    ]

    month_numbers = [4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3]

    start_year = int(selected_session.split("-")[0])
    end_year = int(selected_session.split("-")[1])

    monthly_fee_data = []
    monthly_expense_data = []

    for m in month_numbers:
        year = start_year if m >= 4 else end_year

        fee_amount = 0
        salary_amount = 0
        other_amount = 0

        try:
            from fees.models import FeeCollection

            fee_qs = FeeCollection.objects.filter(
                payment_date__year=year,
                payment_date__month=m
            )
            fee_qs = apply_session_filter(fee_qs, selected_session)

            fee_amount = fee_qs.aggregate(total=Sum("deposit_amount"))["total"] or 0
        except Exception:
            fee_amount = 0

        try:
            from payroll.models import Salary

            salary_qs = Salary.objects.filter(
                payment_date__year=year,
                payment_date__month=m
            )
            salary_qs = apply_session_filter(salary_qs, selected_session)

            salary_amount = salary_qs.aggregate(total=Sum("paid_amount"))["total"] or 0
        except Exception:
            salary_amount = 0

        try:
            from expenses.models import Expense

            other_qs = Expense.objects.filter(
                date__year=year,
                date__month=m
            )
            other_qs = apply_session_filter(other_qs, selected_session)

            other_amount = other_qs.aggregate(total=Sum("amount"))["total"] or 0
        except Exception:
            other_amount = 0

        monthly_fee_data.append(float(fee_amount))
        monthly_expense_data.append(float(salary_amount + other_amount))

    context = {
        "sessions": sessions,
        "selected_session": selected_session,
        "session_start": session_start,
        "session_end": session_end,

        "total_students": total_students,
        "total_employees": total_employees,

        "attendance_percentage": attendance_percentage,
        "present": present,
        "absent": absent,
        "late": late,

        "teacher_present": teacher_present,
        "teacher_absent": teacher_absent,
        "teacher_late": teacher_late,

        "most_present": most_present,
        "most_absent": most_absent,
        "low_students": low_students,

        "pending_complaints": pending_complaints,
        "recent_complaints": recent_complaints,
        "recent_students": recent_students,

        "today_collection": today_collection,
        "total_collection": total_collection,
        "monthly_collection": monthly_collection,
        "yearly_collection": yearly_collection,
        "estimated_month_fee": estimated_month_fee,
        "remaining_month_fee": remaining_month_fee,

        "total_salary_expense": total_salary_expense,
        "total_other_expense": total_other_expense,
        "total_expense": total_expense,
        "total_profit": total_profit,
        "total_loss": total_loss,

        "month_labels": month_labels,
        "monthly_fee_data": monthly_fee_data,
        "monthly_expense_data": monthly_expense_data,
    }

    return render(request, "dashboard.html", context)


# =========================================================
# REPORTS
# =========================================================

@login_required(login_url="/admin-login/")
def today_attendance_report(request):
    selected_session = get_selected_session(request)
    today = timezone.now().date()

    records = StudentAttendance.objects.select_related("student").filter(date=today)
    records = apply_session_filter(records, selected_session)

    return render(request, "reports/today_attendance.html", {
        "records": records,
        "title": "Today Attendance Report",
        "selected_session": selected_session,
    })


@login_required(login_url="/admin-login/")
def teacher_attendance_report(request):
    selected_session = get_selected_session(request)
    records = []

    try:
        from attendance.models import TeacherAttendance
        records = TeacherAttendance.objects.all().order_by("-date")
        records = apply_session_filter(records, selected_session)
    except Exception:
        records = []

    return render(request, "reports/teacher_attendance.html", {
        "records": records,
        "title": "Teacher Attendance Report",
        "selected_session": selected_session,
    })


@login_required(login_url="/admin-login/")
def fees_report(request):
    selected_session = get_selected_session(request)
    session_start, session_end = get_session_dates(selected_session)

    records = []

    try:
        from fees.models import FeeCollection

        records = FeeCollection.objects.select_related("student").filter(
            payment_date__gte=session_start,
            payment_date__lte=session_end,
        ).order_by("-payment_date")

        records = apply_session_filter(records, selected_session)
    except Exception:
        records = []

    return render(request, "reports/fees_report.html", {
        "records": records,
        "title": "Fees Report",
        "selected_session": selected_session,
    })


@login_required(login_url="/admin-login/")
def profit_loss_report(request):
    selected_session = get_selected_session(request)
    session_start, session_end = get_session_dates(selected_session)

    total_fee = 0
    total_salary = 0
    total_other_expense = 0
    profit = 0
    loss = 0

    try:
        from fees.models import FeeCollection

        fee_qs = FeeCollection.objects.filter(
            payment_date__gte=session_start,
            payment_date__lte=session_end,
        )
        fee_qs = apply_session_filter(fee_qs, selected_session)

        total_fee = fee_qs.aggregate(total=Sum("deposit_amount"))["total"] or 0
    except Exception:
        pass

    try:
        from payroll.models import Salary

        salary_qs = Salary.objects.filter(
            payment_date__gte=session_start,
            payment_date__lte=session_end,
        )
        salary_qs = apply_session_filter(salary_qs, selected_session)

        total_salary = salary_qs.aggregate(total=Sum("paid_amount"))["total"] or 0
    except Exception:
        pass

    try:
        from expenses.models import Expense

        expense_qs = Expense.objects.filter(
            date__gte=session_start,
            date__lte=session_end,
        )
        expense_qs = apply_session_filter(expense_qs, selected_session)

        total_other_expense = expense_qs.aggregate(total=Sum("amount"))["total"] or 0
    except Exception:
        pass

    total_expense = total_salary + total_other_expense
    profit = total_fee - total_expense

    if profit < 0:
        loss = abs(profit)
        profit = 0

    return render(request, "reports/profit_loss.html", {
        "total_fee": total_fee,
        "total_salary": total_salary,
        "total_other_expense": total_other_expense,
        "total_expense": total_expense,
        "profit": profit,
        "loss": loss,
        "title": "Profit Loss Report",
        "selected_session": selected_session,
    })


@login_required(login_url="/admin-login/")
def low_performance_report(request):
    selected_session = get_selected_session(request)
    session_start, session_end = get_session_dates(selected_session)

    students = Student.objects.filter(is_active=True)
    students = apply_session_filter(students, selected_session)

    data = []

    for s in students:
        attendance_qs = StudentAttendance.objects.filter(
            student=s,
            date__gte=session_start,
            date__lte=session_end,
        )
        attendance_qs = apply_session_filter(attendance_qs, selected_session)

        total = attendance_qs.count()
        present = attendance_qs.filter(status="Present").count()
        absent = attendance_qs.filter(status="Absent").count()

        percent = (present / total * 100) if total > 0 else 0

        if total > 0 and percent < 50:
            data.append({
                "student": s,
                "percent": round(percent, 2),
                "total": total,
                "present": present,
                "absent": absent,
            })

    return render(request, "reports/low_performance.html", {
        "data": data,
        "title": "Low Performance Students",
        "selected_session": selected_session,
    })


@login_required(login_url="/admin-login/")
def complaint_report(request):
    selected_session = get_selected_session(request)
    records = []

    try:
        from complaints.models import Complaint

        records = Complaint.objects.select_related("student").all().order_by("-created_at")
        records = apply_session_filter(records, selected_session)
    except Exception:
        records = []

    return render(request, "reports/complaint_report.html", {
        "records": records,
        "title": "Complaint Report",
        "selected_session": selected_session,
    })


# =========================================================
# TEACHER DASHBOARD REDIRECT SUPPORT
# =========================================================

@login_required(login_url="/teachers/login/")
def teacher_dashboard(request):
    return redirect("/teachers/dashboard/")


# =========================================================
# CUSTOM ADMIN LOGIN
# =========================================================

def custom_login(request):
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.is_staff:
            return redirect("/dashboard/")

        emp = getattr(request.user, "employee", None)

        if emp:
            return redirect("/teachers/dashboard/")

        logout(request)
        return redirect("/admin-login/")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is None:
            messages.error(request, "❌ Invalid username or password.")
            return redirect("/admin-login/")

        if not (user.is_superuser or user.is_staff):
            emp = getattr(user, "employee", None)

            if emp:
                messages.error(request, "❌ Teachers must login from Teacher Login page.")
                return redirect("/teachers/login/")

            messages.error(request, "❌ Permission denied.")
            return redirect("/admin-login/")

        login(request, user)
        messages.success(request, "✅ Welcome Admin.")
        return redirect("/dashboard/")

    return render(request, "login.html")

# =========================================================
# RECYCLE BIN DASHBOARD
# =========================================================

from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from teachers.models import Employee
from fees.models import FeeCollection
from payroll.models import Salary
from expenses.models import Expense


@login_required(login_url="/admin-login/")
def recycle_bin_dashboard(request):

    deleted_employees = 0
    deleted_fees = 0
    deleted_salary = 0
    deleted_expenses = 0

    employee_warning = 0
    fee_warning = 0
    salary_warning = 0
    expense_warning = 0

    employee_cleanup = 0
    fee_cleanup = 0
    salary_cleanup = 0
    expense_cleanup = 0

    warning_date = timezone.now() - timedelta(days=30)
    cleanup_date = timezone.now() - timedelta(days=60)

    # EMPLOYEE
    try:
        deleted_employees = Employee.objects.filter(
            is_deleted=True
        ).count()

        employee_warning = Employee.objects.filter(
            is_deleted=True,
            deleted_at__lte=warning_date
        ).count()

        employee_cleanup = Employee.objects.filter(
            is_deleted=True,
            deleted_at__lte=cleanup_date
        ).count()

    except Exception:
        pass

    # FEES
    try:
        deleted_fees = FeeCollection.objects.filter(
            is_deleted=True
        ).count()

        fee_warning = FeeCollection.objects.filter(
            is_deleted=True,
            deleted_at__lte=warning_date
        ).count()

        fee_cleanup = FeeCollection.objects.filter(
            is_deleted=True,
            deleted_at__lte=cleanup_date
        ).count()

    except Exception:
        pass

    # SALARY
    try:
        deleted_salary = Salary.objects.filter(
            is_deleted=True
        ).count()

        salary_warning = Salary.objects.filter(
            is_deleted=True,
            deleted_at__lte=warning_date
        ).count()

        salary_cleanup = Salary.objects.filter(
            is_deleted=True,
            deleted_at__lte=cleanup_date
        ).count()

    except Exception:
        pass

    # EXPENSES
    try:
        deleted_expenses = Expense.objects.filter(
            is_deleted=True
        ).count()

        expense_warning = Expense.objects.filter(
            is_deleted=True,
            deleted_at__lte=warning_date
        ).count()

        expense_cleanup = Expense.objects.filter(
            is_deleted=True,
            deleted_at__lte=cleanup_date
        ).count()

    except Exception:
        pass

    total_deleted = (
        deleted_employees +
        deleted_fees +
        deleted_salary +
        deleted_expenses
    )

    return render(
        request,
        "dashboard/recycle_bin_dashboard.html",
        {
            "deleted_employees": deleted_employees,
            "deleted_fees": deleted_fees,
            "deleted_salary": deleted_salary,
            "deleted_expenses": deleted_expenses,

            "employee_warning": employee_warning,
            "fee_warning": fee_warning,
            "salary_warning": salary_warning,
            "expense_warning": expense_warning,

            "employee_cleanup": employee_cleanup,
            "fee_cleanup": fee_cleanup,
            "salary_cleanup": salary_cleanup,
            "expense_cleanup": expense_cleanup,

            "total_deleted": total_deleted,
        }
    )