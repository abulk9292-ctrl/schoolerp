from decimal import Decimal

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone

from students.models import Student
from attendance.models import StudentAttendance, TeacherAttendance
from fees.models import FeeCollection
from complaints.models import Complaint


MONTHS = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']


@login_required
def today_attendance_report(request):
    today = timezone.now().date()
    records = StudentAttendance.objects.filter(date=today)

    return render(request, 'reports/today_attendance.html', {
        'records': records,
        'date': today
    })


@login_required
def teacher_attendance_report(request):
    records = TeacherAttendance.objects.all().order_by('-date')

    return render(request, 'reports/teacher_attendance.html', {
        'records': records
    })


@login_required
def fees_report(request):
    records = FeeCollection.objects.all().order_by('-id')
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

        income = FeeCollection.objects.filter(
            payment_date__year=year,
            payment_date__month=month_no
        ).aggregate(total=Sum('deposit_amount'))['total'] or Decimal('0.00')

        salary_expense = Decimal('0.00')
        other_expense = Decimal('0.00')

        try:
            from payroll.models import Salary
            salary_expense = Salary.objects.filter(
                payment_date__year=year,
                payment_date__month=month_no
            ).aggregate(total=Sum('paid_amount'))['total'] or Decimal('0.00')
        except Exception:
            salary_expense = Decimal('0.00')

        try:
            from expenses.models import Expense
            other_expense = Expense.objects.filter(
                date__year=year,
                date__month=month_no
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
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
    })


@login_required
def profit_loss_report(request):
    income = FeeCollection.objects.aggregate(total=Sum('deposit_amount'))['total'] or 0

    try:
        from expenses.models import Expense
        expense = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
    except Exception:
        expense = 0

    try:
        from payroll.models import Salary
        salary_expense = Salary.objects.aggregate(total=Sum('paid_amount'))['total'] or 0
    except Exception:
        salary_expense = 0

    total_expense = expense + salary_expense
    profit = income - total_expense

    return render(request, 'reports/profit_loss.html', {
        'income': income,
        'expense': total_expense,
        'profit': profit
    })


@login_required
def low_performance_report(request):
    students = Student.objects.all()

    return render(request, 'reports/low_performance.html', {
        'students': students
    })


@login_required
def complaint_report(request):
    complaints = Complaint.objects.all().order_by('-id')

    return render(request, 'reports/complaint_report.html', {
        'complaints': complaints
    })


@login_required
def reports_home(request):
    return render(request, 'reports/reports_home.html')