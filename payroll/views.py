from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse

from teachers.models import Employee
from .models import Salary
from .forms import SalaryForm
from core.context_processors import get_current_session


MONTH_NUMBER = {
    'January': 1,
    'February': 2,
    'March': 3,
    'April': 4,
    'May': 5,
    'June': 6,
    'July': 7,
    'August': 8,
    'September': 9,
    'October': 10,
    'November': 11,
    'December': 12,
}


def get_selected_session(request):
    selected_session = request.session.get("selected_session")

    if not selected_session:
        selected_session = get_current_session()
        request.session["selected_session"] = selected_session

    return selected_session


def get_teacher_absent_count(employee, month, year, selected_session=None):
    month_number = MONTH_NUMBER.get(month, 1)

    try:
        from attendance.models import TeacherAttendance
        from django.db.models import Q

        records = TeacherAttendance.objects.filter(
            employee=employee,
            date__year=year,
            date__month=month_number,
        ).filter(
            Q(status__iexact="Absent") |
            Q(status__iexact="A") |
            Q(status__icontains="absent")
        )

        return records.count()

    except Exception:
        return 0


@login_required
def get_employee_absent_days(request):
    selected_session = get_selected_session(request)

    employee_id = request.GET.get('employee_id')
    month = request.GET.get('month')
    year = request.GET.get('year')

    if not employee_id or not month or not year:
        return JsonResponse({'absent_days': 0})

    try:
        employee = Employee.objects.get(id=employee_id)

        absent_days = get_teacher_absent_count(
            employee=employee,
            month=month,
            year=int(year),
            selected_session=selected_session
        )

    except Exception:
        absent_days = 0

    return JsonResponse({'absent_days': absent_days})


@login_required
def payroll_dashboard(request):
    selected_session = get_selected_session(request)

    current_month = timezone.now().strftime('%B')
    current_year = timezone.now().year

    total_employees = Employee.objects.filter(is_active=True).count()

    salaries = Salary.objects.select_related('employee').filter(
        academic_session=selected_session
    )

    total_paid = sum(s.paid_amount or Decimal('0.00') for s in salaries)
    total_due = sum(s.due_amount or Decimal('0.00') for s in salaries)
    total_advance = sum(s.advance_amount or Decimal('0.00') for s in salaries)

    this_month_expense = sum(
        s.paid_amount or Decimal('0.00')
        for s in salaries
        if s.month == current_month and s.year == current_year
    )

    return render(request, 'payroll/payroll_dashboard.html', {
        'total_employees': total_employees,
        'total_paid': total_paid,
        'total_unpaid': total_due,
        'total_advance': total_advance,
        'this_month_expense': this_month_expense,
        'selected_session': selected_session,
    })


@login_required
def salary_list(request):
    selected_session = get_selected_session(request)

    records = Salary.objects.select_related(
        'employee'
    ).filter(
        academic_session=selected_session,
        is_deleted=False
    ).order_by(
        '-year',
        '-created_at'
    )

    status = request.GET.get('status')
    month = request.GET.get('month')
    year = request.GET.get('year')

    if status:
        records = records.filter(status=status)

    if month:
        records = records.filter(month=month)

    if year:
        records = records.filter(year=year)

    total_paid = Decimal('0.00')
    total_due = Decimal('0.00')
    total_advance = Decimal('0.00')
    total_payable = Decimal('0.00')

    for r in records:
        total_paid += r.paid_amount or Decimal('0.00')
        total_due += r.due_amount or Decimal('0.00')
        total_advance += r.advance_amount or Decimal('0.00')
        total_payable += r.payable_amount or Decimal('0.00')

    paid_count = records.filter(status='Paid').count()
    partial_count = records.filter(status='Partial').count()
    unpaid_count = records.filter(status='Unpaid').count()
    advance_count = records.filter(status='Advance').count()

    return render(request, 'payroll/salary_list.html', {
        'records': records,
        'selected_status': status,
        'selected_month': month,
        'selected_year': year,
        'months': Salary.MONTH_CHOICES,
        'total_paid': total_paid,
        'total_due': total_due,
        'total_advance': total_advance,
        'total_payable': total_payable,
        'paid_count': paid_count,
        'partial_count': partial_count,
        'unpaid_count': unpaid_count,
        'advance_count': advance_count,
        'selected_session': selected_session,
    })


@login_required
def salary_add(request):
    selected_session = get_selected_session(request)

    employees = Employee.objects.filter(is_active=True).order_by('name')

    salary_records = Salary.objects.select_related('employee').filter(
        academic_session=selected_session
    ).order_by('-year', '-created_at')

    if request.method == 'POST':
        form = SalaryForm(request.POST)

        if form.is_valid():
            employee = form.cleaned_data['employee']
            month = form.cleaned_data['month']
            year = form.cleaned_data['year']
            new_paid = form.cleaned_data.get('paid_amount') or Decimal('0.00')
            payment_date = form.cleaned_data.get('payment_date') or timezone.now().date()

            existing = Salary.objects.filter(
                employee=employee,
                month=month,
                year=year,
                academic_session=selected_session
            ).first()

            if existing:
                old_paid = existing.paid_amount or Decimal('0.00')

                existing.paid_amount = old_paid + new_paid
                existing.payment_date = payment_date
                existing.academic_session = selected_session

                existing.payment_only_update = True
                existing.save()

                messages.warning(
                    request,
                    f'⚠️ Salary already exists. Previous Paid: ₹{old_paid} | '
                    f'New Paid: ₹{new_paid} | Total Paid: ₹{existing.paid_amount} | '
                    f'Due: ₹{existing.due_amount}'
                )

                return redirect('salary_print', pk=existing.pk)

            salary = form.save(commit=False)
            salary.academic_session = selected_session
            salary.payment_date = payment_date
            salary.save()

            messages.success(
                request,
                f'✅ Salary created successfully. '
                f'Absent: {salary.absent_days} days | '
                f'Paid: ₹{salary.paid_amount} | Due: ₹{salary.due_amount}'
            )

            return redirect('salary_print', pk=salary.pk)

    else:
        form = SalaryForm()

    return render(request, 'payroll/salary_form.html', {
        'form': form,
        'title': 'Add Salary',
        'employees': employees,
        'salary_records': salary_records,
        'selected_session': selected_session,
    })


@login_required
def salary_detail(request, pk):

    selected_session = get_selected_session(request)

    salary = Salary.objects.select_related(
        'employee'
    ).filter(
        pk=pk,
        academic_session=selected_session,
        is_deleted=False
    ).first()

    if not salary:

        messages.warning(
            request,
            "Salary record not found in the selected academic session."
        )

        return redirect("salary_list")

    return render(
        request,
        'payroll/salary_detail.html',
        {
            'salary': salary,
            'selected_session': selected_session,
        }
    )

@login_required
def salary_edit(request, pk):
    selected_session = get_selected_session(request)

    salary = get_object_or_404(
        Salary.objects.select_related('employee'),
        pk=pk,
        academic_session=selected_session
    )

    if request.method == 'POST':
        form = SalaryForm(request.POST, instance=salary)

        if form.is_valid():
            salary = form.save(commit=False)
            salary.academic_session = selected_session
            salary.save()

            messages.success(
                request,
                f'✅ Salary updated. Paid: ₹{salary.paid_amount} | Due: ₹{salary.due_amount}'
            )

            return redirect('salary_list')

    else:
        form = SalaryForm(instance=salary)

    return render(request, 'payroll/salary_form.html', {
        'form': form,
        'title': 'Edit Salary',
        'employees': Employee.objects.filter(is_active=True).order_by('name'),
        'salary_records': Salary.objects.select_related('employee').filter(
            academic_session=selected_session
        ).order_by('-year', '-created_at'),
        'selected_session': selected_session,
    })


@login_required
def salary_delete(request, pk):

    selected_session = get_selected_session(request)

    salary = get_object_or_404(
        Salary.objects.select_related('employee'),
        pk=pk,
        academic_session=selected_session,
        is_deleted=False
    )

    if request.method == 'POST':

        salary.is_deleted = True
        salary.deleted_at = timezone.now()
        salary.deleted_by = request.user
        salary.save()

        messages.success(
            request,
            '🗑 Salary moved to recycle bin.'
        )

        return redirect('salary_list')

    return render(
        request,
        'payroll/salary_confirm_delete.html',
        {
            'salary': salary,
            'selected_session': selected_session,
        }
    )

@login_required
def auto_generate_salary(request):
    selected_session = get_selected_session(request)

    if request.method == 'POST':
        month = request.POST.get('month')
        year = request.POST.get('year')
        payment_date = request.POST.get('payment_date') or timezone.now().date()

        if not month or not year:
            messages.error(request, 'Please select month and year.')
            return redirect('auto_generate_salary')

        try:
            year = int(year)
        except Exception:
            messages.error(request, 'Invalid year.')
            return redirect('auto_generate_salary')

        employees = Employee.objects.filter(is_active=True).order_by('name')

        created = 0
        skipped = 0

        for employee in employees:
            salary, is_created = Salary.objects.get_or_create(
                employee=employee,
                month=month,
                year=year,
                academic_session=selected_session,
                defaults={
                    'basic_salary': employee.salary or Decimal('0.00'),
                    'bonus': Decimal('0.00'),
                    'extra_deduction': Decimal('0.00'),
                    'paid_amount': Decimal('0.00'),
                    'payment_date': payment_date,
                }
            )

            if is_created:
                salary.academic_session = selected_session
                salary.save()
                created += 1
            else:
                skipped += 1

        messages.success(
            request,
            f'✅ Auto payroll completed. Created: {created}, Skipped existing: {skipped}.'
        )

        return redirect('salary_list')

    current_year = timezone.now().year
    current_month = timezone.now().strftime('%B')

    return render(request, 'payroll/auto_generate_salary.html', {
        'current_year': current_year,
        'current_month': current_month,
        'months': Salary.MONTH_CHOICES,
        'selected_session': selected_session,
    })


@login_required
def salary_print(request, pk):

    selected_session = get_selected_session(request)

    salary = Salary.objects.select_related(
        'employee'
    ).filter(
        pk=pk,
        academic_session=selected_session,
        is_deleted=False
    ).first()

    if not salary:

        messages.warning(
            request,
            "Salary record not found in the selected academic session."
        )

        return redirect("salary_list")

    return render(
        request,
        'payroll/salary_print.html',
        {
            'salary': salary,
            'selected_session': selected_session,
        }
    )

@login_required
def salary_recycle_bin(request):

    records = Salary.objects.select_related(
        'employee'
    ).filter(
        is_deleted=True
    ).order_by(
        '-deleted_at'
    )

    return render(
        request,
        'payroll/salary_recycle_bin.html',
        {
            'records': records
        }
    )


@login_required
def salary_restore(request, pk):

    if not request.user.is_superuser:
        messages.error(
            request,
            "Only Super Admin can restore salary records."
        )
        return redirect('salary_recycle_bin')

    salary = get_object_or_404(
        Salary,
        pk=pk,
        is_deleted=True
    )

    salary.is_deleted = False
    salary.deleted_at = None
    salary.deleted_by = None
    salary.save()

    messages.success(
        request,
        "Salary restored successfully."
    )

    return redirect('salary_recycle_bin')


@login_required
def salary_permanent_delete(request, pk):

    if not request.user.is_superuser:
        messages.error(
            request,
            "Only Super Admin can permanently delete salary records."
        )
        return redirect('salary_recycle_bin')

    salary = get_object_or_404(
        Salary,
        pk=pk,
        is_deleted=True
    )

    if request.method != "POST":
        messages.error(
            request,
            "Invalid request."
        )
        return redirect('salary_recycle_bin')

    salary.delete()

    messages.success(
        request,
        "Salary permanently deleted."
    )

    return redirect('salary_recycle_bin')