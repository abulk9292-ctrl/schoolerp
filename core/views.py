from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Sum
from datetime import date

from students.models import Student
from teachers.models import Employee
from attendance.models import StudentAttendance
from django.shortcuts import render, redirect


@login_required
def dashboard(request):
    today = timezone.now().date()

    current_year = today.year
    sessions = []
    for y in range(current_year - 2, current_year + 3):
        sessions.append(f"{y}-{y + 1}")

    selected_session = request.GET.get('session')
    if not selected_session:
        if today.month >= 4:
            selected_session = f"{current_year}-{current_year + 1}"
        else:
            selected_session = f"{current_year - 1}-{current_year}"

    start_year = int(selected_session.split('-')[0])
    end_year = int(selected_session.split('-')[1])

    session_start = date(start_year, 4, 1)
    session_end = date(end_year, 3, 31)

    total_students = Student.objects.filter(is_active=True).count()
    total_employees = Employee.objects.filter(is_active=True).count()

    today_attendance = StudentAttendance.objects.filter(date=today)

    present = today_attendance.filter(status='Present').count()
    absent = today_attendance.filter(status='Absent').count()
    late = today_attendance.filter(status='Late').count()

    total_marked = present + absent + late

    attendance_percentage = 0
    if total_marked > 0:
        attendance_percentage = round((present / total_marked) * 100, 2)

    teacher_present = 0
    teacher_absent = 0
    teacher_late = 0

    try:
        from attendance.models import TeacherAttendance
        teacher_today = TeacherAttendance.objects.filter(date=today)
        teacher_present = teacher_today.filter(status='Present').count()
        teacher_absent = teacher_today.filter(status='Absent').count()
        teacher_late = teacher_today.filter(status='Late').count()
    except Exception:
        pass

    most_present = (
        StudentAttendance.objects.filter(status='Present')
        .values('student__student_name', 'student__student_id')
        .annotate(total=Count('id'))
        .order_by('-total')
        .first()
    )

    most_absent = (
        StudentAttendance.objects.filter(status='Absent')
        .values('student__student_name', 'student__student_id')
        .annotate(total=Count('id'))
        .order_by('-total')
        .first()
    )

    low_students = []

    students = Student.objects.filter(is_active=True)

    for s in students:
        total = StudentAttendance.objects.filter(student=s).count()
        present_count = StudentAttendance.objects.filter(student=s, status='Present').count()
        percent = (present_count / total * 100) if total > 0 else 0

        if total > 0 and percent < 50:
            low_students.append({
                'student': s,
                'percent': round(percent, 2)
            })

    recent_students = Student.objects.filter(is_active=True).order_by('-id')[:5]

    pending_complaints = 0
    recent_complaints = []

    try:
        from complaints.models import Complaint
        pending_complaints = Complaint.objects.filter(status='Pending').count()
        recent_complaints = Complaint.objects.select_related('student').order_by('-created_at')[:5]
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

        today_collection = FeeCollection.objects.filter(payment_date=today).aggregate(
            total=Sum('deposit_amount')
        )['total'] or 0

        total_collection = FeeCollection.objects.aggregate(
            total=Sum('deposit_amount')
        )['total'] or 0

        monthly_collection = FeeCollection.objects.filter(
            payment_date__year=today.year,
            payment_date__month=today.month
        ).aggregate(total=Sum('deposit_amount'))['total'] or 0

        yearly_collection = FeeCollection.objects.filter(
            payment_date__gte=session_start,
            payment_date__lte=session_end
        ).aggregate(total=Sum('deposit_amount'))['total'] or 0

        estimated_month_fee = FeeStructure.objects.filter(
            is_active=True
        ).aggregate(total=Sum('monthly_fee'))['total'] or 0

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
        total_salary_expense = Salary.objects.aggregate(
            total=Sum('paid_amount')
        )['total'] or 0
    except Exception:
        pass

    try:
        from expenses.models import Expense
        total_other_expense = Expense.objects.aggregate(
            total=Sum('amount')
        )['total'] or 0
    except Exception:
        pass

    total_expense = total_salary_expense + total_other_expense

    total_profit = total_collection - total_expense
    if total_profit < 0:
        total_loss = abs(total_profit)
        total_profit = 0

    month_labels = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
    monthly_fee_data = []
    monthly_expense_data = []

    month_numbers = [4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3]

    for m in month_numbers:
        year = start_year if m >= 4 else end_year

        fee_amount = 0
        salary_amount = 0
        other_amount = 0

        try:
            from fees.models import FeeCollection
            fee_amount = FeeCollection.objects.filter(
                payment_date__year=year,
                payment_date__month=m
            ).aggregate(total=Sum('deposit_amount'))['total'] or 0
        except Exception:
            fee_amount = 0

        try:
            from payroll.models import Salary
            salary_amount = Salary.objects.filter(
                payment_date__year=year,
                payment_date__month=m
            ).aggregate(total=Sum('paid_amount'))['total'] or 0
        except Exception:
            salary_amount = 0

        try:
            from expenses.models import Expense
            other_amount = Expense.objects.filter(
                date__year=year,
                date__month=m
            ).aggregate(total=Sum('amount'))['total'] or 0
        except Exception:
            other_amount = 0

        monthly_fee_data.append(float(fee_amount))
        monthly_expense_data.append(float(salary_amount + other_amount))

    context = {
        'sessions': sessions,
        'selected_session': selected_session,
        'session_start': session_start,
        'session_end': session_end,

        'total_students': total_students,
        'total_employees': total_employees,

        'attendance_percentage': attendance_percentage,
        'present': present,
        'absent': absent,
        'late': late,

        'teacher_present': teacher_present,
        'teacher_absent': teacher_absent,
        'teacher_late': teacher_late,

        'most_present': most_present,
        'most_absent': most_absent,
        'low_students': low_students,

        'pending_complaints': pending_complaints,
        'recent_complaints': recent_complaints,
        'recent_students': recent_students,

        'today_collection': today_collection,
        'total_collection': total_collection,
        'monthly_collection': monthly_collection,
        'yearly_collection': yearly_collection,
        'estimated_month_fee': estimated_month_fee,
        'remaining_month_fee': remaining_month_fee,

        'total_salary_expense': total_salary_expense,
        'total_other_expense': total_other_expense,
        'total_expense': total_expense,
        'total_profit': total_profit,
        'total_loss': total_loss,

        'month_labels': month_labels,
        'monthly_fee_data': monthly_fee_data,
        'monthly_expense_data': monthly_expense_data,
    }

    return render(request, 'dashboard.html', context)


@login_required
def today_attendance_report(request):
    today = timezone.now().date()
    records = StudentAttendance.objects.select_related('student').filter(date=today)

    return render(request, 'reports/today_attendance.html', {
        'records': records,
        'title': 'Today Attendance Report'
    })


@login_required
def teacher_attendance_report(request):
    records = []

    try:
        from attendance.models import TeacherAttendance
        records = TeacherAttendance.objects.all().order_by('-date')
    except Exception:
        records = []

    return render(request, 'reports/teacher_attendance.html', {
        'records': records,
        'title': 'Teacher Attendance Report'
    })


@login_required
def fees_report(request):
    records = []

    try:
        from fees.models import FeeCollection
        records = FeeCollection.objects.select_related('student').all().order_by('-payment_date')
    except Exception:
        records = []

    return render(request, 'reports/fees_report.html', {
        'records': records,
        'title': 'Fees Report'
    })


@login_required
def profit_loss_report(request):
    total_fee = 0
    total_salary = 0
    profit = 0
    loss = 0

    try:
        from fees.models import FeeCollection
        total_fee = FeeCollection.objects.aggregate(total=Sum('deposit_amount'))['total'] or 0
    except Exception:
        pass

    try:
        from payroll.models import Salary
        total_salary = Salary.objects.aggregate(total=Sum('paid_amount'))['total'] or 0
    except Exception:
        pass

    profit = total_fee - total_salary

    if profit < 0:
        loss = abs(profit)
        profit = 0

    return render(request, 'reports/profit_loss.html', {
        'total_fee': total_fee,
        'total_salary': total_salary,
        'profit': profit,
        'loss': loss,
        'title': 'Profit Loss Report'
    })


@login_required
def low_performance_report(request):
    students = Student.objects.filter(is_active=True)
    data = []

    for s in students:
        total = StudentAttendance.objects.filter(student=s).count()
        present = StudentAttendance.objects.filter(student=s, status='Present').count()
        absent = StudentAttendance.objects.filter(student=s, status='Absent').count()

        percent = (present / total * 100) if total > 0 else 0

        if total > 0 and percent < 50:
            data.append({
                'student': s,
                'percent': round(percent, 2),
                'total': total,
                'present': present,
                'absent': absent,
            })

    return render(request, 'reports/low_performance.html', {
        'data': data,
        'title': 'Low Performance Students'
    })


@login_required
def complaint_report(request):
    records = []

    try:
        from complaints.models import Complaint
        records = Complaint.objects.select_related('student').all().order_by('-created_at')
    except Exception:
        records = []

    return render(request, 'reports/complaint_report.html', {
        'records': records,
        'title': 'Complaint Report'
    })

from django.contrib import messages


@login_required
def teacher_dashboard(request):

    # 🔐 Employee get
    employee = getattr(request.user, 'employee', None)

    if not employee:
        messages.error(request, "❌ No employee linked")
        return redirect('/login/')

    # 🔐 যদি inactive হয়
    if not employee.is_active:
        messages.error(request, "❌ You are inactive employee")
        return redirect('/login/')

    # 📊 Basic data
    today = timezone.now().date()

    total_students = 0
    total_present = 0
    total_absent = 0

    try:
        from students.models import Student
        from attendance.models import StudentAttendance

        total_students = Student.objects.filter(is_active=True).count()

        today_attendance = StudentAttendance.objects.filter(date=today)

        total_present = today_attendance.filter(status='Present').count()
        total_absent = today_attendance.filter(status='Absent').count()

    except:
        pass

    # 👨‍🏫 Teacher Attendance
    teacher_status = "Not Marked"

    try:
        from attendance.models import TeacherAttendance

        record = TeacherAttendance.objects.filter(
            employee=employee,
            date=today
        ).first()

        if record:
            teacher_status = record.status

    except:
        pass

    # 💰 Salary Summary
    total_paid = 0
    total_due = 0

    try:
        from payroll.models import Salary

        records = Salary.objects.filter(employee=employee)

        total_paid = sum(s.paid_amount for s in records)
        total_due = sum(getattr(s, 'due_amount', 0) for s in records)

    except:
        pass

    return render(request, 'core/teacher_dashboard.html', {
        'employee': employee,

        'total_students': total_students,
        'total_present': total_present,
        'total_absent': total_absent,

        'teacher_status': teacher_status,

        'total_paid': total_paid,
        'total_due': total_due,
    })

from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect


def custom_login(request):
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.is_staff:
            return redirect('/dashboard/')

        emp = getattr(request.user, 'employee', None)
        if emp:
            return redirect('/teacher-dashboard/')

        return redirect('/login/')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "❌ Invalid username or password.")
            return redirect('/login/')

        if user.is_superuser or user.is_staff:
            login(request, user)
            messages.success(request, "✅ Welcome Admin.")
            return redirect('/dashboard/')

        emp = getattr(user, 'employee', None)

        if not emp:
            messages.error(request, "❌ No employee profile linked.")
            return redirect('/login/')

        if not emp.is_active:
            messages.error(request, "❌ Your account is inactive.")
            return redirect('/login/')

        login(request, user)
        messages.success(request, f"✅ Welcome {emp.name}.")
        return redirect('/teacher-dashboard/')

    return render(request, 'login.html')