from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import Employee
from .forms import EmployeeForm


# 🔐 Permission Helper
def check_permission(request, permission_field):
    if request.user.is_superuser or request.user.is_staff:
        return True

    emp = getattr(request.user, 'employee', None)

    if not emp:
        return False

    if emp.is_erp_admin:
        return True

    return getattr(emp, permission_field, False)


# ✅ Employee List
@login_required
def employee_list(request):

    if not check_permission(request, 'can_access_teachers'):
        messages.error(request, "❌ Permission Denied")
        return redirect('/teacher-dashboard/')

    employees = Employee.objects.all().order_by('id')

    return render(request, 'teachers/employee_list.html', {
        'employees': employees
    })


# ✅ Employee Detail
@login_required
def employee_detail(request, pk):

    if not check_permission(request, 'can_access_teachers'):
        messages.error(request, "❌ Permission Denied")
        return redirect('/teacher-dashboard/')

    employee = get_object_or_404(Employee, pk=pk)

    # =====================================
    # ATTENDANCE SUMMARY
    # =====================================
    attendance_total = 0
    attendance_present = 0
    attendance_absent = 0
    attendance_late = 0
    attendance_percentage = 0

    try:
        from attendance.models import TeacherAttendance

        attendance_queryset = TeacherAttendance.objects.filter(
            employee=employee
        )

        attendance_total = attendance_queryset.count()

        attendance_present = attendance_queryset.filter(
            status='Present'
        ).count()

        attendance_absent = attendance_queryset.filter(
            status='Absent'
        ).count()

        attendance_late = attendance_queryset.filter(
            status='Late'
        ).count()

        if attendance_total > 0:
            attendance_percentage = round(
                (attendance_present / attendance_total) * 100,
                2
            )

    except Exception:
        pass

    # =====================================
    # PAYROLL SUMMARY
    # =====================================
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
        ).order_by(
            '-year',
            '-created_at'
        )

        latest_salary = salary_records.first()

        for s in salary_records:

            total_salary_paid += (
                s.paid_amount or 0
            )

            total_salary_due += (
                s.due_amount or 0
            )

            total_salary_advance += (
                s.advance_amount or 0
            )

            total_salary_payable += (
                s.payable_amount or 0
            )

        # STATUS COUNT
        paid_salary_count = salary_records.filter(
            status='Paid'
        ).count()

        unpaid_salary_count = salary_records.filter(
            status='Unpaid'
        ).count()

        partial_salary_count = salary_records.filter(
            status='Partial'
        ).count()

        advance_salary_count = salary_records.filter(
            status='Advance'
        ).count()

    except Exception:
        pass

    # =====================================
    # CONTEXT
    # =====================================
    return render(request, 'teachers/employee_detail.html', {

        # EMPLOYEE
        'employee': employee,

        # ATTENDANCE
        'attendance_total': attendance_total,
        'attendance_present': attendance_present,
        'attendance_absent': attendance_absent,
        'attendance_late': attendance_late,
        'attendance_percentage': attendance_percentage,

        # SALARY HISTORY
        'salary_records': salary_records,
        'latest_salary': latest_salary,

        # TOTALS
        'total_salary_paid': total_salary_paid,
        'total_salary_due': total_salary_due,
        'total_salary_advance': total_salary_advance,
        'total_salary_payable': total_salary_payable,

        # COUNTS
        'paid_salary_count': paid_salary_count,
        'unpaid_salary_count': unpaid_salary_count,
        'partial_salary_count': partial_salary_count,
        'advance_salary_count': advance_salary_count,

    })



# ✅ Employee Add
@login_required
def employee_add(request):

    if not check_permission(request, 'can_access_teachers'):
        messages.error(request, "❌ Permission Denied")
        return redirect('/teacher-dashboard/')

    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Employee added successfully.')
            return redirect('employee_list')
    else:
        form = EmployeeForm()

    return render(request, 'teachers/employee_form.html', {
        'form': form,
        'page_title': 'Add Employee'
    })


# ✅ Employee Edit
@login_required
def employee_edit(request, pk):

    if not check_permission(request, 'can_access_teachers'):
        messages.error(request, "❌ Permission Denied")
        return redirect('/teacher-dashboard/')

    employee = get_object_or_404(Employee, pk=pk)

    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Employee updated successfully.')
            return redirect('employee_detail', pk=employee.pk)
    else:
        form = EmployeeForm(instance=employee)

    return render(request, 'teachers/employee_form.html', {
        'form': form,
        'page_title': 'Edit Employee'
    })


# ✅ Employee Delete
@login_required
def employee_delete(request, pk):

    if not check_permission(request, 'can_access_teachers'):
        messages.error(request, "❌ Permission Denied")
        return redirect('/teacher-dashboard/')

    employee = get_object_or_404(Employee, pk=pk)

    if request.method == 'POST':
        employee.delete()
        messages.success(request, '🗑 Employee deleted successfully.')
        return redirect('employee_list')

    return render(request, 'teachers/employee_confirm_delete.html', {
        'employee': employee
    })


# ✅ Discontinue
@login_required
def employee_discontinue(request, pk):

    if not check_permission(request, 'can_access_teachers'):
        return redirect('/teacher-dashboard/')

    employee = get_object_or_404(Employee, pk=pk)
    employee.is_active = False
    employee.save(update_fields=['is_active'])

    messages.warning(request, f'{employee.name} discontinued.')
    return redirect('employee_detail', pk=employee.pk)


# ✅ Rejoin
@login_required
def employee_rejoin(request, pk):

    if not check_permission(request, 'can_access_teachers'):
        return redirect('/teacher-dashboard/')

    employee = get_object_or_404(Employee, pk=pk)
    employee.is_active = True
    employee.save(update_fields=['is_active'])

    messages.success(request, f'{employee.name} rejoined.')
    return redirect('employee_detail', pk=employee.pk)


# ✅ Teacher Password Print
@login_required
def teacher_password_print(request):

    if not check_permission(request, 'can_access_teachers'):
        return redirect('/teacher-dashboard/')

    selected_designation = request.GET.get('designation')

    employees = Employee.objects.filter(is_active=True).order_by('designation', 'id')

    if selected_designation:
        employees = employees.filter(designation=selected_designation)

    designations = Employee.objects.filter(
        is_active=True
    ).values_list('designation', flat=True).distinct().order_by('designation')

    return render(request, 'teachers/teacher_password_print.html', {
        'employees': employees,
        'designations': designations,
        'selected_designation': selected_designation,
    })

# ✅ PRINT ALL SALARY SLIPS
@login_required
def employee_salary_slips_print(request, pk):

    if not check_permission(request, 'can_access_teachers'):
        messages.error(request, "❌ Permission Denied")
        return redirect('/teacher-dashboard/')

    employee = get_object_or_404(
        Employee,
        pk=pk
    )

    salary_records = []

    total_paid = 0
    total_due = 0
    total_advance = 0
    total_payable = 0

    try:
        from payroll.models import Salary

        salary_records = Salary.objects.filter(
            employee=employee
        ).order_by(
            '-year',
            '-created_at'
        )

        for s in salary_records:

            total_paid += (
                s.paid_amount or 0
            )

            total_due += (
                s.due_amount or 0
            )

            total_advance += (
                s.advance_amount or 0
            )

            total_payable += (
                s.payable_amount or 0
            )

    except Exception:
        pass

    return render(
        request,
        'teachers/employee_salary_slips_print.html',
        {

            'employee': employee,

            'salary_records': salary_records,

            'total_paid': total_paid,
            'total_due': total_due,
            'total_advance': total_advance,
            'total_payable': total_payable,

        }
    )