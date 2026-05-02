from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import Employee
from .forms import EmployeeForm


@login_required
def employee_list(request):
    employees = Employee.objects.all().order_by('id')
    return render(request, 'teachers/employee_list.html', {'employees': employees})


@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    attendance_total = 0
    attendance_present = 0
    attendance_absent = 0
    attendance_late = 0
    attendance_percentage = 0

    try:
        from attendance.models import TeacherAttendance

        attendance_total = TeacherAttendance.objects.filter(employee=employee).count()
        attendance_present = TeacherAttendance.objects.filter(employee=employee, status='Present').count()
        attendance_absent = TeacherAttendance.objects.filter(employee=employee, status='Absent').count()
        attendance_late = TeacherAttendance.objects.filter(employee=employee, status='Late').count()

        if attendance_total > 0:
            attendance_percentage = round((attendance_present / attendance_total) * 100, 2)
    except Exception:
        pass

    salary_records = []
    total_salary_paid = 0
    total_salary_due = 0

    try:
        from payroll.models import Salary

        salary_records = Salary.objects.filter(employee=employee).order_by('-year', '-created_at')
        total_salary_paid = sum(s.paid_amount for s in salary_records)
        total_salary_due = sum(s.due_amount for s in salary_records)
    except Exception:
        pass

    return render(request, 'teachers/employee_detail.html', {
        'employee': employee,
        'attendance_total': attendance_total,
        'attendance_present': attendance_present,
        'attendance_absent': attendance_absent,
        'attendance_late': attendance_late,
        'attendance_percentage': attendance_percentage,
        'salary_records': salary_records,
        'total_salary_paid': total_salary_paid,
        'total_salary_due': total_salary_due,
    })


@login_required
def employee_add(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee added successfully.')
            return redirect('employee_list')
    else:
        form = EmployeeForm()

    return render(request, 'teachers/employee_form.html', {
        'form': form,
        'page_title': 'Add Employee'
    })


@login_required
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee updated successfully.')
            return redirect('employee_detail', pk=employee.pk)
    else:
        form = EmployeeForm(instance=employee)

    return render(request, 'teachers/employee_form.html', {
        'form': form,
        'page_title': 'Edit Employee'
    })


@login_required
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == 'POST':
        employee.delete()
        messages.success(request, 'Employee deleted successfully.')
        return redirect('employee_list')

    return render(request, 'teachers/employee_confirm_delete.html', {
        'employee': employee
    })


@login_required
def employee_discontinue(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    employee.is_active = False
    employee.save(update_fields=['is_active'])

    messages.warning(request, f'{employee.name} has been discontinued.')
    return redirect('employee_detail', pk=employee.pk)


@login_required
def employee_rejoin(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    employee.is_active = True
    employee.save(update_fields=['is_active'])

    messages.success(request, f'{employee.name} has re-joined.')
    return redirect('employee_detail', pk=employee.pk)