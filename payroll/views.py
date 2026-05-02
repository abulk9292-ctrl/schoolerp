from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse

from teachers.models import Employee
from .models import Salary
from .forms import SalaryForm


def get_teacher_absent_count(employee, month, year):
    month_number = {
        'January': 1, 'February': 2, 'March': 3,
        'April': 4, 'May': 5, 'June': 6,
        'July': 7, 'August': 8, 'September': 9,
        'October': 10, 'November': 11, 'December': 12,
    }.get(month, 1)

    try:
        from attendance.models import TeacherAttendance

        return TeacherAttendance.objects.filter(
            employee=employee,
            date__year=year,
            date__month=month_number,
            status='Absent'
        ).count()
    except Exception:
        return 0


@login_required
def get_employee_absent_days(request):
    employee_id = request.GET.get('employee_id')
    month = request.GET.get('month')
    year = request.GET.get('year')

    if not employee_id or not month or not year:
        return JsonResponse({'absent_days': 0})

    try:
        employee = Employee.objects.get(id=employee_id)
        absent_days = get_teacher_absent_count(employee, month, int(year))
    except Exception:
        absent_days = 0

    return JsonResponse({'absent_days': absent_days})


@login_required
def payroll_dashboard(request):
    current_month = timezone.now().strftime('%B')
    current_year = timezone.now().year

    total_employees = Employee.objects.filter(is_active=True).count()
    salaries = Salary.objects.all()

    total_paid = sum(s.paid_amount for s in salaries)
    total_due = sum(s.due_amount for s in salaries)
    total_advance = sum(s.advance_amount for s in salaries)

    this_month_expense = sum(
        s.paid_amount for s in salaries
        if s.month == current_month and s.year == current_year
    )

    return render(request, 'payroll/payroll_dashboard.html', {
        'total_employees': total_employees,
        'total_paid': total_paid,
        'total_unpaid': total_due,
        'total_advance': total_advance,
        'this_month_expense': this_month_expense,
    })


@login_required
def salary_list(request):
    records = Salary.objects.select_related('employee').all().order_by('-year', '-created_at')

    status = request.GET.get('status')
    if status:
        records = records.filter(status=status)

    return render(request, 'payroll/salary_list.html', {
        'records': records
    })


@login_required
def salary_add(request):
    employees = Employee.objects.filter(is_active=True)
    salary_records = Salary.objects.all()

    if request.method == 'POST':
        form = SalaryForm(request.POST)

        if form.is_valid():
            employee = form.cleaned_data['employee']
            month = form.cleaned_data['month']
            year = form.cleaned_data['year']
            new_paid = form.cleaned_data.get('paid_amount') or Decimal('0.00')

            existing = Salary.objects.filter(
                employee=employee,
                month=month,
                year=year
            ).first()

            # 🔥 SECOND PAYMENT LOGIC
            if existing:
                old_paid = existing.paid_amount or Decimal('0.00')

                existing.paid_amount = old_paid + new_paid
                existing.payment_date = form.cleaned_data.get('payment_date')
                existing.payment_only_update = True

                existing.save()

                messages.warning(
                    request,
                    f'⚠️ Already exists! Previous Paid: ₹{old_paid} | New: ₹{new_paid} | Total Paid: ₹{existing.paid_amount} | Due: ₹{existing.due_amount}'
                )
                return redirect('salary_print', pk=existing.pk)

            # 🔥 FIRST TIME CREATE → FULL CALCULATION
            salary = form.save(commit=False)

            # ✅ Auto absent detect from TeacherAttendance
            salary.absent_days = get_teacher_absent_count(employee, month, year)

            # ✅ But if user manually typed absent_days, keep manual value
            manual_absent = request.POST.get('absent_days')
            if manual_absent not in [None, '']:
                try:
                    salary.absent_days = int(manual_absent)
                except Exception:
                    pass

            salary.save()

            messages.success(
                request,
                f'✅ Salary created. Paid: ₹{salary.paid_amount} | Due: ₹{salary.due_amount}'
            )
            return redirect('salary_print', pk=salary.pk)

    else:
        form = SalaryForm()

    return render(request, 'payroll/salary_form.html', {
        'form': form,
        'title': 'Add Salary',
        'employees': employees,
        'salary_records': salary_records,
    })


@login_required
def salary_detail(request, pk):
    salary = get_object_or_404(Salary.objects.select_related('employee'), pk=pk)

    return render(request, 'payroll/salary_detail.html', {
        'salary': salary
    })


@login_required
def salary_edit(request, pk):
    salary = get_object_or_404(Salary, pk=pk)

    if request.method == 'POST':
        form = SalaryForm(request.POST, instance=salary)
        if form.is_valid():
            salary = form.save(commit=False)

            manual_absent = request.POST.get('absent_days')
            if manual_absent not in [None, '']:
                try:
                    salary.absent_days = int(manual_absent)
                except Exception:
                    pass

            salary.save()

            messages.success(
                request,
                f'Updated. Paid: ₹{salary.paid_amount} | Due: ₹{salary.due_amount}'
            )
            return redirect('salary_list')
    else:
        form = SalaryForm(instance=salary)

    return render(request, 'payroll/salary_form.html', {
        'form': form,
        'title': 'Edit Salary',
        'employees': Employee.objects.filter(is_active=True),
        'salary_records': Salary.objects.all(),
    })


@login_required
def salary_delete(request, pk):
    salary = get_object_or_404(Salary.objects.select_related('employee'), pk=pk)

    if request.method == 'POST':
        salary.delete()
        messages.success(request, 'Salary deleted successfully.')
        return redirect('salary_list')

    return render(request, 'payroll/salary_confirm_delete.html', {
        'salary': salary
    })


@login_required
def auto_generate_salary(request):
    if request.method == 'POST':
        month = request.POST.get('month')
        year = int(request.POST.get('year'))
        payment_date = request.POST.get('payment_date')

        employees = Employee.objects.filter(is_active=True)
        created = 0
        skipped = 0

        for employee in employees:
            absent_days = get_teacher_absent_count(employee, month, year)

            salary, is_created = Salary.objects.get_or_create(
                employee=employee,
                month=month,
                year=year,
                defaults={
                    'basic_salary': employee.salary or 0,
                    'bonus': 0,
                    'absent_days': absent_days,
                    'extra_deduction': 0,
                    'paid_amount': 0,
                    'payment_date': payment_date,
                }
            )

            if is_created:
                salary.save()
                created += 1
            else:
                skipped += 1

        messages.success(
            request,
            f'Auto payroll completed. Created: {created}, Skipped existing: {skipped}.'
        )
        return redirect('salary_list')

    current_year = timezone.now().year

    return render(request, 'payroll/auto_generate_salary.html', {
        'current_year': current_year
    })


@login_required
def salary_print(request, pk):
    salary = get_object_or_404(Salary.objects.select_related('employee'), pk=pk)

    return render(request, 'payroll/salary_print.html', {
        'salary': salary
    })