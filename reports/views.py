from decimal import Decimal

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from django.core.exceptions import FieldError

from students.models import Student
from attendance.models import StudentAttendance, TeacherAttendance
from fees.models import FeeCollection
from complaints.models import Complaint
from core.context_processors import get_current_session


MONTHS = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']


def get_selected_session(request):
    selected_session = request.session.get("selected_session")

    if not selected_session:
        selected_session = get_current_session()
        request.session["selected_session"] = selected_session

    return selected_session


def apply_session_filter(queryset, selected_session):
    """
    Safe session filter.
    Different modules may use different field names:
    academic_session / session / current_session
    """

    from academics.models import AcademicSession

    model_fields = [field.name for field in queryset.model._meta.get_fields()]

    session_obj = AcademicSession.objects.filter(
        session_name=selected_session
    ).first()

    try:

        if "academic_session" in model_fields and session_obj:
            return queryset.filter(academic_session=session_obj)

        if "session" in model_fields and session_obj:
            return queryset.filter(session=session_obj)

        if "current_session" in model_fields and session_obj:
            return queryset.filter(current_session=session_obj)

    except FieldError:
        return queryset

    return queryset


@login_required
def today_attendance_report(request):
    selected_session = get_selected_session(request)

    today = timezone.now().date()

    records = StudentAttendance.objects.filter(date=today)
    records = apply_session_filter(records, selected_session)

    return render(request, 'reports/today_attendance.html', {
        'records': records,
        'date': today,
        'selected_session': selected_session,
    })


@login_required
def teacher_attendance_report(request):
    selected_session = get_selected_session(request)

    records = TeacherAttendance.objects.all().order_by('-date')
    records = apply_session_filter(records, selected_session)

    return render(request, 'reports/teacher_attendance.html', {
        'records': records,
        'selected_session': selected_session,
    })


@login_required
def fees_report(request):
    selected_session = get_selected_session(request)

    records = FeeCollection.objects.all().order_by('-id')
    records = apply_session_filter(records, selected_session)

    total = records.aggregate(total=Sum('deposit_amount'))['total'] or Decimal('0.00')

    income_data = []
    expense_data = []

    current_year = timezone.now().year

    month_map = {
        'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9,
        'Oct': 10, 'Nov': 11, 'Dec': 12, 'Jan': 1, 'Feb': 2, 'Mar': 3
    }

    for m in MONTHS:
        month_no = month_map[m]
        year = current_year if month_no >= 4 else current_year + 1

        income_qs = FeeCollection.objects.filter(
            payment_date__year=year,
            payment_date__month=month_no
        )
        income_qs = apply_session_filter(income_qs, selected_session)

        income = income_qs.aggregate(total=Sum('deposit_amount'))['total'] or Decimal('0.00')

        salary_expense = Decimal('0.00')
        other_expense = Decimal('0.00')

        try:
            from payroll.models import Salary

            salary_qs = Salary.objects.filter(
                payment_date__year=year,
                payment_date__month=month_no
            )
            salary_qs = apply_session_filter(salary_qs, selected_session)

            salary_expense = salary_qs.aggregate(total=Sum('paid_amount'))['total'] or Decimal('0.00')
        except Exception:
            salary_expense = Decimal('0.00')

        try:
            from expenses.models import Expense

            expense_qs = Expense.objects.filter(
                date__year=year,
                date__month=month_no
            )
            expense_qs = apply_session_filter(expense_qs, selected_session)

            other_expense = expense_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        except Exception:
            other_expense = Decimal('0.00')

        income_data.append(float(income))
        expense_data.append(float(salary_expense + other_expense))

    total_income = sum(income_data)
    total_expense = sum(expense_data)
    profit = total_income - total_expense

    return render(request, 'reports/fees_report.html', {
        'records': records,
        'total': total,
        'months': MONTHS,
        'income_data': income_data,
        'expense_data': expense_data,
        'total_income': total_income,
        'total_expense': total_expense,
        'profit': profit,
        'selected_session': selected_session,
    })


@login_required
def profit_loss_report(request):
    selected_session = get_selected_session(request)

    fee_qs = FeeCollection.objects.all()
    fee_qs = apply_session_filter(fee_qs, selected_session)

    income = fee_qs.aggregate(total=Sum('deposit_amount'))['total'] or Decimal('0.00')

    try:
        from expenses.models import Expense

        expense_qs = Expense.objects.all()
        expense_qs = apply_session_filter(expense_qs, selected_session)

        expense = expense_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    except Exception:
        expense = Decimal('0.00')

    try:
        from payroll.models import Salary

        salary_qs = Salary.objects.all()
        salary_qs = apply_session_filter(salary_qs, selected_session)

        salary_expense = salary_qs.aggregate(total=Sum('paid_amount'))['total'] or Decimal('0.00')
    except Exception:
        salary_expense = Decimal('0.00')

    total_expense = expense + salary_expense
    profit = income - total_expense

    return render(request, 'reports/profit_loss.html', {
        'income': income,
        'expense': total_expense,
        'profit': profit,
        'selected_session': selected_session,
    })


@login_required
def low_performance_report(request):
    selected_session = get_selected_session(request)

    students = Student.objects.all()
    students = apply_session_filter(students, selected_session)

    return render(request, 'reports/low_performance.html', {
        'students': students,
        'selected_session': selected_session,
    })


@login_required
def complaint_report(request):
    selected_session = get_selected_session(request)

    complaints = Complaint.objects.all().order_by('-id')
    complaints = apply_session_filter(complaints, selected_session)

    return render(request, 'reports/complaint_report.html', {
        'complaints': complaints,
        'selected_session': selected_session,
    })


@login_required
def reports_home(request):
    selected_session = get_selected_session(request)

    return render(request, 'reports/reports_home.html', {
        'selected_session': selected_session,
    })