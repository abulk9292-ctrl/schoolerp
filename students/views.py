from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Q
from django.core.paginator import Paginator

from .models import Student
from .forms import StudentForm
from academics.models import Class


@login_required
def student_list(request):
    selected_class = request.GET.get('class_assigned')
    search_query = request.GET.get('q', '').strip()

    students = Student.objects.select_related('class_assigned', 'sibling_of').all().order_by('id')

    if selected_class:
        students = students.filter(class_assigned_id=selected_class)

    if search_query:
        students = students.filter(
            Q(student_name__icontains=search_query) |
            Q(father_name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(student_id__icontains=search_query) |
            Q(registration_no__icontains=search_query)
        )

    paginator = Paginator(students, 20)
    page_number = request.GET.get('page')
    students = paginator.get_page(page_number)

    classes = Class.objects.all().order_by('id')

    return render(request, 'students/student_list.html', {
        'students': students,
        'classes': classes,
        'selected_class': selected_class,
        'search_query': search_query,
    })


@login_required
def student_add(request):
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student added successfully.')
            return redirect('student_list')
    else:
        form = StudentForm()

    return render(request, 'students/student_form.html', {
        'form': form,
        'page_title': 'Add Student'
    })


@login_required
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    siblings = Student.objects.filter(sibling_of=student).order_by('id')
    classes = Class.objects.all().order_by('id')

    attendance_total = 0
    attendance_present = 0
    attendance_absent = 0
    attendance_percentage = 0

    try:
        from attendance.models import StudentAttendance

        attendance_total = StudentAttendance.objects.filter(student=student).count()
        attendance_present = StudentAttendance.objects.filter(student=student, status='Present').count()
        attendance_absent = StudentAttendance.objects.filter(student=student, status='Absent').count()

        if attendance_total > 0:
            attendance_percentage = round((attendance_present / attendance_total) * 100, 2)
    except Exception:
        pass

    monthly_fee = 0
    total_paid = 0
    total_due = 0
    fee_records = []

    try:
        from fees.models import Fee, FeeStructure

        fee_records = Fee.objects.filter(student=student).order_by('-id')
        total_paid = fee_records.aggregate(total=Sum('amount_paid'))['total'] or 0

        try:
            fee_structure = FeeStructure.objects.get(student=student)
            monthly_fee = fee_structure.monthly_fee
            total_due = max((monthly_fee * 12) - total_paid, 0)
        except FeeStructure.DoesNotExist:
            pass
    except Exception:
        pass

    exam_records = []

    try:
        from exams.models import Result
        exam_records = Result.objects.filter(student=student).order_by('-id')
    except Exception:
        try:
            from exams.models import ExamResult
            exam_records = ExamResult.objects.filter(student=student).order_by('-id')
        except Exception:
            pass

    complaints = []

    try:
        from complaints.models import Complaint
        complaints = Complaint.objects.filter(student=student).order_by('-created_at')
    except Exception:
        pass

    return render(request, 'students/student_detail.html', {
        'student': student,
        'siblings': siblings,
        'classes': classes,

        'attendance_total': attendance_total,
        'attendance_present': attendance_present,
        'attendance_absent': attendance_absent,
        'attendance_percentage': attendance_percentage,

        'monthly_fee': monthly_fee,
        'total_paid': total_paid,
        'total_due': total_due,
        'fee_records': fee_records,

        'exam_records': exam_records,
        'complaints': complaints,
    })


@login_required
def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student updated successfully.')
            return redirect('student_detail', pk=student.pk)
    else:
        form = StudentForm(instance=student)

    return render(request, 'students/student_form.html', {
        'form': form,
        'page_title': 'Edit Student'
    })


@login_required
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        student.delete()
        messages.success(request, 'Student deleted successfully.')
        return redirect('student_list')

    return render(request, 'students/student_confirm_delete.html', {
        'student': student
    })


@login_required
def student_discontinue(request, pk):
    student = get_object_or_404(Student, pk=pk)

    student.is_active = False
    student.save(update_fields=['is_active'])

    messages.warning(request, f'{student.student_name} has been discontinued.')
    return redirect('student_detail', pk=student.pk)


@login_required
def student_readmit(request, pk):
    student = get_object_or_404(Student, pk=pk)

    student.is_active = True
    student.save(update_fields=['is_active'])

    messages.success(request, f'{student.student_name} has been re-admitted.')
    return redirect('student_detail', pk=student.pk)


@login_required
def student_promote(request, pk):
    student = get_object_or_404(Student, pk=pk)
    classes = list(Class.objects.all().order_by('id'))

    current_index = None
    for index, cls in enumerate(classes):
        if cls.id == student.class_assigned_id:
            current_index = index
            break

    if current_index is None:
        messages.error(request, 'Current class not found.')
        return redirect('student_detail', pk=student.pk)

    if current_index + 1 >= len(classes):
        messages.warning(request, 'This student is already in the highest class.')
        return redirect('student_detail', pk=student.pk)

    old_class = student.class_assigned
    student.class_assigned = classes[current_index + 1]
    student.save(update_fields=['class_assigned'])

    messages.success(
        request,
        f'{student.student_name} promoted from {old_class} to {student.class_assigned}.'
    )
    return redirect('student_detail', pk=student.pk)


@login_required
def student_demote(request, pk):
    student = get_object_or_404(Student, pk=pk)
    classes = list(Class.objects.all().order_by('id'))

    current_index = None
    for index, cls in enumerate(classes):
        if cls.id == student.class_assigned_id:
            current_index = index
            break

    if current_index is None:
        messages.error(request, 'Current class not found.')
        return redirect('student_detail', pk=student.pk)

    if current_index - 1 < 0:
        messages.warning(request, 'This student is already in the lowest class.')
        return redirect('student_detail', pk=student.pk)

    old_class = student.class_assigned
    student.class_assigned = classes[current_index - 1]
    student.save(update_fields=['class_assigned'])

    messages.success(
        request,
        f'{student.student_name} de-promoted from {old_class} to {student.class_assigned}.'
    )
    return redirect('student_detail', pk=student.pk)


@login_required
def add_sibling(request, pk):
    main_student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            sibling = form.save(commit=False)
            sibling.sibling_of = main_student
            sibling.save()
            messages.success(request, 'Sibling added successfully.')
            return redirect('student_detail', pk=main_student.pk)
    else:
        form = StudentForm()

    return render(request, 'students/student_form.html', {
        'form': form,
        'page_title': f'Add Sibling of {main_student.student_name}'
    })


@login_required
def bulk_promotion(request):
    classes = Class.objects.all().order_by('id')

    if request.method == 'POST':
        from_class_id = request.POST.get('from_class')
        to_class_id = request.POST.get('to_class')

        if not from_class_id or not to_class_id:
            messages.error(request, 'Please select both classes.')
            return redirect('bulk_promotion')

        if from_class_id == to_class_id:
            messages.error(request, 'From and To class cannot be same.')
            return redirect('bulk_promotion')

        from_class = get_object_or_404(Class, id=from_class_id)
        to_class = get_object_or_404(Class, id=to_class_id)

        # 🔥 ONLY ACTIVE STUDENTS
        students = Student.objects.filter(
            class_assigned=from_class,
            is_active=True
        )

        count = students.count()

        students.update(class_assigned=to_class)

        messages.success(
            request,
            f'{count} students promoted from {from_class} to {to_class}.'
        )

        return redirect('student_list')

    return render(request, 'students/bulk_promotion.html', {
        'classes': classes
    })
import pandas as pd
from django.http import HttpResponse


@login_required
def export_students_excel(request):
    students = Student.objects.select_related('class_assigned').all()

    data = []
    for s in students:
        data.append({
            'Student ID': s.student_id,
            'Registration No': s.registration_no,
            'Name': s.student_name,
            'Class': str(s.class_assigned),
            'Roll No': s.roll_no,
            'Father Name': s.father_name,
            'Phone': s.phone,
            'Status': 'Active' if s.is_active else 'Inactive'
        })

    df = pd.DataFrame(data)

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="students.xlsx"'

    df.to_excel(response, index=False)

    return response

from django.urls import reverse
import qrcode
from io import BytesIO
import base64


@login_required
def student_id_card(request, pk):
    student = get_object_or_404(Student, pk=pk)

    # 🔥 QR will open attendance page directly
    qr_data = request.build_absolute_uri(
        reverse('student_qr_profile', args=[student.pk])
    )

    qr = qrcode.make(qr_data)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")

    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render(request, 'students/id_card.html', {
        'student': student,
        'qr_code': qr_base64
    })

import qrcode
from io import BytesIO
import base64


@login_required
def student_id_card(request, pk):
    student = get_object_or_404(Student, pk=pk)

    qr_data = f"{student.student_id} | {student.student_name} | {student.class_assigned}"

    qr = qrcode.make(qr_data)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")

    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render(request, 'students/id_card.html', {
        'student': student,
        'qr_code': qr_base64
    })

@login_required
def student_id_cards_print(request):
    students = Student.objects.select_related('class_assigned').filter(is_active=True).order_by('id')[:10]

    return render(request, 'students/id_cards_print.html', {
        'students': students
    })

from django.utils import timezone


@login_required
def student_qr_profile(request, pk):
    student = get_object_or_404(Student, pk=pk)
    today = timezone.localdate()

    if request.method == 'POST':
        status = request.POST.get('status')

        try:
            from attendance.models import StudentAttendance

            attendance, created = StudentAttendance.objects.update_or_create(
                student=student,
                date=today,
                defaults={
                    'status': status
                }
            )

            messages.success(request, f'{student.student_name} attendance marked as {status}.')
        except Exception as e:
            messages.error(request, f'Attendance error: {e}')

        return redirect('student_qr_profile', pk=student.pk)

    return render(request, 'students/qr_profile.html', {
        'student': student,
        'today': today
    })
# ==============================
# 🔥 STUDENT EXCEL IMPORT SYSTEM
# ==============================

from .forms import StudentImportForm
from academics.models import AcademicSession
import pandas as pd


@login_required
def student_import(request):
    if request.method == 'POST':
        form = StudentImportForm(request.POST, request.FILES)

        if form.is_valid():
            excel_file = request.FILES['excel_file']

            try:
                df = pd.read_excel(excel_file)

                active_session = AcademicSession.objects.filter(is_active=True).first()

                for _, row in df.iterrows():
                    Student.objects.create(
                        student_name=row.get('student_name'),
                        admission_no=row.get('admission_no'),
                        admission_date=row.get('admission_date'),

                        current_session=active_session,

                        class_assigned_id=row.get('class_id'),
                        roll_no=row.get('roll_no'),

                        father_name=row.get('father_name'),
                        mother_name=row.get('mother_name'),
                        guardian_name=row.get('guardian_name'),
                        phone=row.get('phone'),

                        gender=row.get('gender'),
                        date_of_birth=row.get('date_of_birth'),
                        aadhaar_number=row.get('aadhaar_number'),

                        transport_required=row.get('transport_required', False),
                        transport_details=row.get('transport_details'),

                        previous_school=row.get('previous_school'),
                        address=row.get('address'),

                        is_active=True,
                    )

                messages.success(request, "Students imported successfully!")
                return redirect('student_list')

            except Exception as e:
                messages.error(request, f"Import Error: {e}")
    else:
        form = StudentImportForm()

    return render(request, 'students/student_import.html', {
        'form': form
    })


# ==============================
# 🔥 DEMO EXCEL DOWNLOAD
# ==============================

@login_required
def download_student_demo(request):
    data = [{
        'student_name': 'Rahim',
        'admission_no': 'ADM001',
        'admission_date': '2024-01-10',
        'class_id': 1,
        'roll_no': 1,
        'father_name': 'Karim',
        'mother_name': 'Salma',
        'guardian_name': 'Karim',
        'phone': '9999999999',
        'gender': 'Male',
        'date_of_birth': '2010-05-01',
        'aadhaar_number': '123456789012',
        'transport_required': True,
        'transport_details': 'Van',
        'previous_school': 'ABC School',
        'address': 'Village XYZ'
    }]

    df = pd.DataFrame(data)

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="student_import_demo.xlsx"'

    df.to_excel(response, index=False)

    return response