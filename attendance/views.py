from datetime import datetime, timedelta
import json

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count

from students.models import Student
from teachers.models import Employee
from academics.models import Class
from .models import StudentAttendance, TeacherAttendance


@login_required
def student_attendance(request):
    selected_date = request.GET.get('date')
    selected_class = request.GET.get('class_id')

    if selected_date:
        attendance_date = selected_date
    else:
        attendance_date = timezone.now().date().isoformat()

    classes = Class.objects.all().order_by('class_name')
    students = Student.objects.select_related('class_assigned').filter(is_active=True).order_by('roll_no', 'student_name')

    if selected_class:
        students = students.filter(class_assigned_id=selected_class)

    existing_records = StudentAttendance.objects.filter(date=attendance_date)
    existing_status_map = {record.student_id: record.status for record in existing_records}

    for student in students:
        student.current_status = existing_status_map.get(student.id, 'Present')

    is_update = existing_records.exists()

    if request.method == 'POST':
        post_date = request.POST.get('attendance_date')
        post_class_id = request.POST.get('class_id') or ''

        students_to_save = Student.objects.filter(is_active=True)

        if post_class_id:
            students_to_save = students_to_save.filter(class_assigned_id=post_class_id)

        for student in students_to_save:
            status = request.POST.get(f'status_{student.id}', 'Present')

            StudentAttendance.objects.update_or_create(
                student=student,
                date=post_date,
                defaults={'status': status}
            )

        messages.success(request, 'Student attendance updated successfully.')
        redirect_url = f'/attendance/students/?date={post_date}'
        if post_class_id:
            redirect_url += f'&class_id={post_class_id}'
        return redirect(redirect_url)

    context = {
        'students': students,
        'classes': classes,
        'attendance_date': attendance_date,
        'selected_class': selected_class,
        'is_update': is_update,
    }
    return render(request, 'attendance/student_attendance.html', context)


@login_required
def teacher_attendance(request):
    selected_date = request.GET.get('date')

    if selected_date:
        attendance_date = selected_date
    else:
        attendance_date = timezone.now().date().isoformat()

    employees = Employee.objects.filter(is_active=True).order_by('name')

    existing_records = TeacherAttendance.objects.filter(date=attendance_date)
    existing_status_map = {record.employee_id: record.status for record in existing_records}

    for employee in employees:
        employee.current_status = existing_status_map.get(employee.id, 'Present')

    is_update = existing_records.exists()

    if request.method == 'POST':
        post_date = request.POST.get('attendance_date')

        for employee in employees:
            status = request.POST.get(f'status_{employee.id}', 'Present')

            TeacherAttendance.objects.update_or_create(
                employee=employee,
                date=post_date,
                defaults={'status': status}
            )

        messages.success(request, 'Teacher attendance updated successfully.')
        return redirect(f'/attendance/teachers/?date={post_date}')

    context = {
        'employees': employees,
        'attendance_date': attendance_date,
        'is_update': is_update,
    }
    return render(request, 'attendance/teacher_attendance.html', context)


@login_required
def student_daily_report(request):
    selected_date = request.GET.get('date') or timezone.now().date().isoformat()
    selected_class = request.GET.get('class_id')

    classes = Class.objects.all().order_by('class_name')

    records = StudentAttendance.objects.select_related(
        'student', 'student__class_assigned'
    ).filter(date=selected_date).order_by(
        'student__class_assigned__class_name', 'student__roll_no', 'student__student_name'
    )

    if selected_class:
        records = records.filter(student__class_assigned_id=selected_class)

    return render(request, 'attendance/student_daily_report.html', {
        'records': records,
        'classes': classes,
        'selected_date': selected_date,
        'selected_class': selected_class,
    })


@login_required
def teacher_daily_report(request):
    selected_date = request.GET.get('date') or timezone.now().date().isoformat()

    records = TeacherAttendance.objects.select_related('employee').filter(
        date=selected_date
    ).order_by('employee__name')

    return render(request, 'attendance/teacher_daily_report.html', {
        'records': records,
        'selected_date': selected_date,
    })


@login_required
def student_percentage_report(request):
    selected_class = request.GET.get('class_id')

    classes = Class.objects.all().order_by('class_name')
    students = Student.objects.select_related('class_assigned').filter(is_active=True).order_by(
        'class_assigned__class_name', 'roll_no', 'student_name'
    )

    if selected_class:
        students = students.filter(class_assigned_id=selected_class)

    report_rows = []

    for student in students:
        total_days = StudentAttendance.objects.filter(student=student).count()
        present_days = StudentAttendance.objects.filter(student=student, status='Present').count()
        late_days = StudentAttendance.objects.filter(student=student, status='Late').count()
        absent_days = StudentAttendance.objects.filter(student=student, status='Absent').count()

        percentage = 0
        if total_days > 0:
            percentage = round((present_days / total_days) * 100, 2)

        report_rows.append({
            'student': student,
            'total_days': total_days,
            'present_days': present_days,
            'late_days': late_days,
            'absent_days': absent_days,
            'percentage': percentage,
        })

    return render(request, 'attendance/student_percentage_report.html', {
        'report_rows': report_rows,
        'classes': classes,
        'selected_class': selected_class,
    })


@login_required
def student_monthly_report(request):
    classes = Class.objects.all().order_by('class_name')

    selected_class = request.GET.get('class_id')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    today = timezone.now().date()
    first_day = today.replace(day=1)

    if not start_date_str:
        start_date_str = first_day.isoformat()
    if not end_date_str:
        end_date_str = today.isoformat()

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    date_headers = []
    current = start_date
    while current <= end_date:
        date_headers.append(current)
        current += timedelta(days=1)

    students = Student.objects.select_related('class_assigned').filter(is_active=True)

    if selected_class:
        students = students.filter(class_assigned_id=selected_class)

    attendance_records = StudentAttendance.objects.filter(
        date__range=[start_date, end_date],
        student__in=students
    )

    attendance_map = {}
    for record in attendance_records:
        attendance_map[(record.student_id, record.date)] = record.status

    report_rows = []

    for student in students:
        present = 0
        absent = 0
        late = 0
        day_statuses = []

        for day in date_headers:
            status = attendance_map.get((student.id, day), '-')

            if status == 'Present':
                present += 1
                short = 'P'
            elif status == 'Absent':
                absent += 1
                short = 'A'
            elif status == 'Late':
                late += 1
                short = 'L'
            else:
                short = '-'

            day_statuses.append(short)

        total_days = len(date_headers)
        percentage = round((present / total_days) * 100, 2) if total_days > 0 else 0

        report_rows.append({
            'student': student,
            'day_statuses': day_statuses,
            'present': present,
            'absent': absent,
            'late': late,
            'percentage': percentage,
        })

    context = {
        'classes': classes,
        'selected_class': selected_class,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'date_headers': date_headers,
        'report_rows': report_rows,
    }

    return render(request, 'attendance/student_monthly_report.html', context)


@login_required
def attendance_graph(request):
    selected_class = request.GET.get('class_id')
    selected_month = request.GET.get('month')

    classes = Class.objects.all().order_by('class_name')

    students = Student.objects.filter(is_active=True)

    if selected_class:
        students = students.filter(class_assigned_id=selected_class)

    attendance_qs = StudentAttendance.objects.filter(student__in=students)

    if selected_month:
        attendance_qs = attendance_qs.filter(date__month=selected_month)

    summary = attendance_qs.values('status').annotate(total=Count('id'))

    present = 0
    absent = 0
    late = 0

    for item in summary:
        if item['status'] == 'Present':
            present = item['total']
        elif item['status'] == 'Absent':
            absent = item['total']
        elif item['status'] == 'Late':
            late = item['total']

    student_data = []

    for student in students[:10]:
        total = StudentAttendance.objects.filter(student=student).count()
        present_count = StudentAttendance.objects.filter(student=student, status='Present').count()

        student_data.append({
            'name': student.student_name,
            'present': present_count,
            'total': total
        })

    context = {
        'classes': classes,
        'selected_class': selected_class,
        'present': present,
        'absent': absent,
        'late': late,
        'student_data': json.dumps(student_data),
    }

    return render(request, 'attendance/attendance_graph.html', context)


@login_required
def student_attendance_by_class(request, class_name):
    students = Student.objects.filter(
        class_assigned__class_name__iexact=class_name
    ).order_by('roll_no')

    today = timezone.now().date()

    data = []
    for student in students:
        attendance = StudentAttendance.objects.filter(
            student=student,
            date=today
        ).first()

        data.append({
            'student': student,
            'status': attendance.status if attendance else 'Not Marked'
        })

    return render(request, 'attendance/student_attendance_by_class.html', {
        'data': data,
        'class_name': class_name
    })


# ✅ NEW: Attendance Register like manual register
@login_required
def attendance_register(request):
    classes = Class.objects.all().order_by('class_name')

    selected_class = request.GET.get('class_id')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    today = timezone.now().date()
    first_day = today.replace(day=1)

    if not start_date_str:
        start_date_str = first_day.isoformat()
    if not end_date_str:
        end_date_str = today.isoformat()

    date_headers = []
    report_rows = []

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        start_date = first_day
        end_date = today
        start_date_str = first_day.isoformat()
        end_date_str = today.isoformat()

    current = start_date
    while current <= end_date:
        date_headers.append(current)
        current += timedelta(days=1)

    students = Student.objects.select_related('class_assigned').filter(is_active=True).order_by(
        'roll_no', 'student_name'
    )

    selected_class_obj = None

    if selected_class:
        students = students.filter(class_assigned_id=selected_class)
        selected_class_obj = Class.objects.filter(id=selected_class).first()

    attendance_records = StudentAttendance.objects.filter(
        date__range=[start_date, end_date],
        student__in=students
    )

    attendance_map = {}
    for record in attendance_records:
        attendance_map[(record.student_id, record.date)] = record.status

    for student in students:
        day_statuses = []
        present = 0
        absent = 0
        late = 0

        for day in date_headers:
            status = attendance_map.get((student.id, day), '-')

            if status == 'Present':
                short = 'P'
                present += 1
            elif status == 'Absent':
                short = 'A'
                absent += 1
            elif status == 'Late':
                short = 'L'
                late += 1
            else:
                short = '-'

            day_statuses.append(short)

        report_rows.append({
            'student': student,
            'day_statuses': day_statuses,
            'present': present,
            'absent': absent,
            'late': late,
        })

    context = {
        'classes': classes,
        'selected_class': selected_class,
        'selected_class_obj': selected_class_obj,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'date_headers': date_headers,
        'report_rows': report_rows,
    }

    return render(request, 'attendance/attendance_register.html', context)

# =========================
# 🔥 ADMIN ALERT PANEL
# =========================
from .models import AttendanceAlert


@login_required
def attendance_alert_list(request):
    status = request.GET.get('status', 'Pending')

    alerts = AttendanceAlert.objects.all().order_by('-created_at')

    if status:
        alerts = alerts.filter(approval_status=status)

    return render(request, 'attendance/alert_list.html', {
        'alerts': alerts,
        'selected_status': status,
    })


from .utils import send_whatsapp_message, send_sms_message

@login_required
def attendance_alert_approve(request, pk):
    alert = get_object_or_404(AttendanceAlert, pk=pk)

    alert.approval_status = 'Approved'
    alert.save(update_fields=['approval_status'])

    # =========================
    # 🔥 SEND MESSAGE
    # =========================

    phone = None
    message = alert.message_en

    if alert.alert_type == 'Student' and alert.student:
        phone = alert.student.phone
        message = alert.message_bn + " / " + alert.message_en

    elif alert.alert_type == 'Teacher' and alert.employee:
        phone = alert.employee.phone
        message = alert.message_bn + " / " + alert.message_en

    if phone:
        send_whatsapp_message(phone, message)
        send_sms_message(phone, message)

    messages.success(request, 'Alert approved & message sent.')

    return redirect('attendance_alert_list')

from django.shortcuts import get_object_or_404
from .models import AttendanceAlert
from django.contrib import messages


@login_required
def attendance_alert_list(request):
    status = request.GET.get('status', 'Pending')

    alerts = AttendanceAlert.objects.all().order_by('-created_at')

    if status:
        alerts = alerts.filter(approval_status=status)

    return render(request, 'attendance/alert_list.html', {
        'alerts': alerts,
        'selected_status': status,
    })


@login_required
def attendance_alert_approve(request, pk):
    alert = get_object_or_404(AttendanceAlert, pk=pk)

    alert.approval_status = 'Approved'
    alert.save(update_fields=['approval_status'])

    messages.success(request, 'Alert approved.')

    return redirect('attendance_alert_list')


@login_required
def attendance_alert_reject(request, pk):
    alert = get_object_or_404(AttendanceAlert, pk=pk)

    alert.approval_status = 'Rejected'
    alert.save(update_fields=['approval_status'])

    messages.warning(request, 'Alert rejected.')

    return redirect('attendance_alert_list')