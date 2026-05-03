from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from django.contrib.auth.hashers import check_password, make_password

from .models import Student, StudentOTP
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
# 🔥 UPGRADED STUDENT EXCEL IMPORT SYSTEM
# ==============================

from .forms import StudentImportForm
from academics.models import AcademicSession
import pandas as pd


@login_required
def student_import(request):
    errors = []
    success_count = 0
    failed_count = 0

    if request.method == 'POST':
        form = StudentImportForm(request.POST, request.FILES)

        if form.is_valid():
            excel_file = request.FILES['excel_file']

            try:
                df = pd.read_excel(excel_file)
                active_session = AcademicSession.objects.filter(is_active=True).first()

                for index, row in df.iterrows():
                    row_no = index + 2

                    student_name = str(row.get('student_name', '')).strip()
                    phone = str(row.get('phone', '')).strip()
                    admission_no = str(row.get('admission_no', '')).strip()

                    if not student_name:
                        continue

                    if admission_no and Student.objects.filter(admission_no=admission_no).exists():
                        failed_count += 1
                        errors.append(f"Row {row_no}: Admission No already exists.")
                        continue

                    class_obj = None
                    class_id = row.get('class_id')
                    class_name = row.get('class_name')

                    if pd.notna(class_id):
                        class_obj = Class.objects.filter(id=class_id).first()

                    if not class_obj and pd.notna(class_name):
                        class_obj = Class.objects.filter(class_name__iexact=str(class_name).strip()).first()

                    if not class_obj:
                        failed_count += 1
                        errors.append(f"Row {row_no}: Class not found.")
                        continue

                    Student.objects.create(
                        student_name=student_name,
                        admission_no=admission_no,
                        admission_date=row.get('admission_date') if pd.notna(row.get('admission_date')) else None,
                        current_session=active_session,
                        class_assigned=class_obj,
                        roll_no=row.get('roll_no') if pd.notna(row.get('roll_no')) else None,
                        father_name=row.get('father_name') if pd.notna(row.get('father_name')) else '',
                        mother_name=row.get('mother_name') if pd.notna(row.get('mother_name')) else '',
                        guardian_name=row.get('guardian_name') if pd.notna(row.get('guardian_name')) else '',
                        phone=phone,
                        gender=row.get('gender') if pd.notna(row.get('gender')) else '',
                        date_of_birth=row.get('date_of_birth') if pd.notna(row.get('date_of_birth')) else None,
                        aadhaar_number=row.get('aadhaar_number') if pd.notna(row.get('aadhaar_number')) else '',
                        transport_required=True if str(row.get('transport_required')).lower() in ['true', 'yes', '1'] else False,
                        transport_details=row.get('transport_details') if pd.notna(row.get('transport_details')) else '',
                        previous_school=row.get('previous_school') if pd.notna(row.get('previous_school')) else '',
                        address=row.get('address') if pd.notna(row.get('address')) else '',
                        is_active=True,
                    )

                    success_count += 1

                messages.success(request, f"{success_count} students imported successfully. {failed_count} failed.")

            except Exception as e:
                messages.error(request, f"Import Error: {e}")

    else:
        form = StudentImportForm()

    return render(request, 'students/student_import.html', {
        'form': form,
        'errors': errors,
        'success_count': success_count,
        'failed_count': failed_count,
    })


@login_required
def download_student_demo(request):
    data = [{
        'student_name': 'Rahim',
        'admission_no': 'ADM001',
        'admission_date': '2024-01-10',
        'class_id': 1,
        'class_name': 'Class I',
        'roll_no': 1,
        'father_name': 'Karim',
        'mother_name': 'Salma',
        'guardian_name': 'Karim',
        'phone': '9999999999',
        'gender': 'Male',
        'date_of_birth': '2010-05-01',
        'aadhaar_number': '123456789012',
        'transport_required': 'Yes',
        'transport_details': 'Van',
        'previous_school': 'ABC School',
        'address': 'Village XYZ'
    }]

    df = pd.DataFrame(data)

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="student_import_demo.xlsx"'

    df.to_excel(response, index=False)

    return response

# ==============================
# 🔥 UPGRADED STUDENT EXCEL IMPORT SYSTEM
# ==============================

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponse

import pandas as pd

from .models import Student
from .forms import StudentImportForm
from academics.models import Class, AcademicSession


def clean_excel_value(value, default=''):
    if pd.notna(value):
        return value
    return default


@login_required
def student_import(request):
    errors = []
    success_count = 0
    failed_count = 0

    if request.method == 'POST':
        form = StudentImportForm(request.POST, request.FILES)

        if form.is_valid():
            excel_file = request.FILES.get('excel_file')

            try:
                df = pd.read_excel(excel_file)
                active_session = AcademicSession.objects.filter(is_active=True).first()

                for index, row in df.iterrows():
                    row_no = index + 2

                    student_name = str(row.get('student_name', '')).strip()
                    admission_no = str(row.get('admission_no', '')).strip()

                    if not student_name:
                        failed_count += 1
                        errors.append(f"Row {row_no}: Student name is required.")
                        continue

                    if admission_no and Student.objects.filter(admission_no=admission_no).exists():
                        failed_count += 1
                        errors.append(f"Row {row_no}: Admission No already exists.")
                        continue

                    class_obj = None

                    class_id = row.get('class_id')
                    class_name = row.get('class_name')

                    if pd.notna(class_id):
                        try:
                            class_obj = Class.objects.filter(id=int(class_id)).first()
                        except Exception:
                            class_obj = None

                    if not class_obj and pd.notna(class_name):
                        class_obj = Class.objects.filter(
                            class_name__iexact=str(class_name).strip()
                        ).first()

                    if not class_obj:
                        failed_count += 1
                        errors.append(f"Row {row_no}: Class not found.")
                        continue

                    Student.objects.create(
                        # ✅ student_id / registration_no দিচ্ছি না
                        # ✅ তাই model.save() auto-generate করবে

                        student_name=student_name,
                        admission_no=admission_no,
                        admission_date=clean_excel_value(row.get('admission_date'), None),
                        current_session=active_session,
                        class_assigned=class_obj,
                        roll_no=clean_excel_value(row.get('roll_no'), None),

                        father_name=clean_excel_value(row.get('father_name'), ''),
                        mother_name=clean_excel_value(row.get('mother_name'), ''),
                        guardian_name=clean_excel_value(row.get('guardian_name'), ''),
                        phone=str(clean_excel_value(row.get('phone'), '')).strip(),

                        gender=clean_excel_value(row.get('gender'), ''),
                        date_of_birth=clean_excel_value(row.get('date_of_birth'), None),
                        aadhaar_number=str(clean_excel_value(row.get('aadhaar_number'), '')).strip(),

                        transport_required=str(row.get('transport_required', '')).lower() in ['true', 'yes', '1'],
                        transport_details=clean_excel_value(row.get('transport_details'), ''),
                        previous_school=clean_excel_value(row.get('previous_school'), ''),
                        address=clean_excel_value(row.get('address'), ''),

                        is_active=True,
                    )

                    success_count += 1

                messages.success(
                    request,
                    f"{success_count} students imported successfully. {failed_count} failed."
                )

            except Exception as e:
                messages.error(request, f"Import Error: {e}")

    else:
        form = StudentImportForm()

    return render(request, 'students/student_import.html', {
        'form': form,
        'errors': errors,
        'success_count': success_count,
        'failed_count': failed_count,
    })


@login_required
def download_student_demo(request):
    data = [{
        'student_name': 'Rahim',
        'admission_no': 'ADM001',
        'admission_date': '2024-01-10',
        'class_id': 1,
        'class_name': 'Class I',
        'roll_no': 1,
        'father_name': 'Karim',
        'mother_name': 'Salma',
        'guardian_name': 'Karim',
        'phone': '9999999999',
        'gender': 'Male',
        'date_of_birth': '2010-05-01',
        'aadhaar_number': '123456789012',
        'transport_required': 'Yes',
        'transport_details': 'Van',
        'previous_school': 'ABC School',
        'address': 'Village XYZ'
    }]

    df = pd.DataFrame(data)

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="student_import_demo.xlsx"'

    df.to_excel(response, index=False)

    return response


@login_required
def student_import_preview(request):
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')

        if not excel_file:
            messages.error(request, "Please upload a file.")
            return redirect('student_import')

        try:
            df = pd.read_excel(excel_file)
            request.session['import_data'] = df.to_json()

            preview_data = df.head(20).to_dict(orient='records')

            return render(request, 'students/student_import_preview.html', {
                'preview_data': preview_data,
                'total_rows': len(df)
            })

        except Exception as e:
            messages.error(request, f"Preview Error: {e}")
            return redirect('student_import')

    return redirect('student_import')


@login_required
def student_import_confirm(request):
    data_json = request.session.get('import_data')

    if not data_json:
        messages.error(request, "No import data found.")
        return redirect('student_import')

    df = pd.read_json(data_json)

    success_count = 0
    failed_count = 0
    errors = []

    active_session = AcademicSession.objects.filter(is_active=True).first()

    for index, row in df.iterrows():
        row_no = index + 2

        try:
            student_name = str(row.get('student_name', '')).strip()
            admission_no = str(row.get('admission_no', '')).strip()

            if not student_name:
                failed_count += 1
                errors.append(f"Row {row_no}: Student name is required.")
                continue

            if admission_no and Student.objects.filter(admission_no=admission_no).exists():
                failed_count += 1
                errors.append(f"Row {row_no}: Admission No already exists.")
                continue

            class_obj = None

            if pd.notna(row.get('class_id')):
                try:
                    class_obj = Class.objects.filter(id=int(row.get('class_id'))).first()
                except Exception:
                    class_obj = None

            if not class_obj and pd.notna(row.get('class_name')):
                class_obj = Class.objects.filter(
                    class_name__iexact=str(row.get('class_name')).strip()
                ).first()

            if not class_obj:
                failed_count += 1
                errors.append(f"Row {row_no}: Class not found.")
                continue

            Student.objects.create(
                # ✅ student_id / registration_no ফাঁকা থাকলে auto-generate হবে

                student_name=student_name,
                admission_no=admission_no,
                admission_date=clean_excel_value(row.get('admission_date'), None),
                current_session=active_session,
                class_assigned=class_obj,
                roll_no=clean_excel_value(row.get('roll_no'), None),

                father_name=clean_excel_value(row.get('father_name'), ''),
                mother_name=clean_excel_value(row.get('mother_name'), ''),
                guardian_name=clean_excel_value(row.get('guardian_name'), ''),
                phone=str(clean_excel_value(row.get('phone'), '')).strip(),

                gender=clean_excel_value(row.get('gender'), ''),
                date_of_birth=clean_excel_value(row.get('date_of_birth'), None),
                aadhaar_number=str(clean_excel_value(row.get('aadhaar_number'), '')).strip(),

                transport_required=str(row.get('transport_required', '')).lower() in ['true', 'yes', '1'],
                transport_details=clean_excel_value(row.get('transport_details'), ''),
                previous_school=clean_excel_value(row.get('previous_school'), ''),
                address=clean_excel_value(row.get('address'), ''),

                is_active=True,
            )

            success_count += 1

        except Exception as e:
            failed_count += 1
            errors.append(f"Row {row_no}: {e}")

    request.session.pop('import_data', None)

    messages.success(request, f"{success_count} imported, {failed_count} failed.")

    return render(request, 'students/student_import.html', {
        'errors': errors,
        'success_count': success_count,
        'failed_count': failed_count,
        'form': StudentImportForm()
    })

# ==============================
# 🔥 STUDENT LOGIN PANEL (NEW)
# ==============================

from django.contrib.auth import logout


def student_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            student = Student.objects.get(
                login_username=username,
                login_enabled=True
            )

            # ✅ SECURE PASSWORD CHECK
            if check_password(password, student.login_password):

                # 🔥 OLD PASSWORD AUTO-CONVERT TO HASH
                if not student.login_password.startswith('pbkdf2_'):
                    student.login_password = make_password(password)
                    student.save(update_fields=['login_password'])

                request.session['student_id'] = student.id

                messages.success(request, f"Welcome {student.student_name}")
                return redirect('student_dashboard')
            else:
                messages.error(request, "Invalid login credentials")

        except Student.DoesNotExist:
            messages.error(request, "Invalid login credentials")

    return render(request, 'students/student_login.html')


def student_logout(request):
    request.session.flush()
    return redirect('student_login')


def student_dashboard(request):
    student_id = request.session.get('student_id')

    if not student_id:
        return redirect('student_login')

    student = get_object_or_404(Student, pk=student_id)

    attendance_total = 0
    attendance_present = 0
    attendance_absent = 0
    attendance_percentage = 0
    recent_attendance = []

    try:
        from attendance.models import StudentAttendance

        attendance_qs = StudentAttendance.objects.filter(student=student).order_by('-date')
        attendance_total = attendance_qs.count()
        attendance_present = attendance_qs.filter(status='Present').count()
        attendance_absent = attendance_qs.filter(status='Absent').count()
        recent_attendance = attendance_qs[:10]

        if attendance_total > 0:
            attendance_percentage = round((attendance_present / attendance_total) * 100, 2)
    except Exception:
        pass

    total_paid = 0
    total_due = 0
    fee_records = []

    try:
        from fees.models import Fee
        fee_records = Fee.objects.filter(student=student).order_by('-id')[:10]
        total_paid = Fee.objects.filter(student=student).aggregate(total=Sum('amount_paid'))['total'] or 0
    except Exception:
        pass

    exam_records = []

    try:
        from exams.models import Result
        exam_records = Result.objects.filter(student=student).order_by('-id')[:10]
    except Exception:
        try:
            from exams.models import ExamResult
            exam_records = ExamResult.objects.filter(student=student).order_by('-id')[:10]
        except Exception:
            pass

    return render(request, 'students/student_dashboard.html', {
        'student': student,

        'attendance_total': attendance_total,
        'attendance_present': attendance_present,
        'attendance_absent': attendance_absent,
        'attendance_percentage': attendance_percentage,
        'recent_attendance': recent_attendance,

        'total_paid': total_paid,
        'total_due': total_due,
        'fee_records': fee_records,

        'exam_records': exam_records,
    })

# =========================
# 🔥 PARENT LOGIN SYSTEM
# =========================

from .models import Parent

def parent_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            parent = Parent.objects.get(
                username=username,
                is_active=True
            )

            if check_password(password, parent.password):

                # 🔥 AUTO HASH UPGRADE
                if not parent.password.startswith('pbkdf2_'):
                    parent.password = make_password(password)
                    parent.save(update_fields=['password'])

                request.session['parent_id'] = parent.id
                return redirect('parent_dashboard')
            else:
                messages.error(request, "Invalid login")

        except Parent.DoesNotExist:
            messages.error(request, "Invalid login")

    return render(request, 'students/parent_login.html')


def parent_dashboard(request):
    parent_id = request.session.get('parent_id')

    if not parent_id:
        return redirect('parent_login')

    parent = get_object_or_404(Parent, id=parent_id)
    student = parent.student

    attendance_total = 0
    attendance_present = 0
    attendance_absent = 0
    attendance_percentage = 0
    recent_attendance = []

    try:
        from attendance.models import StudentAttendance

        attendance_qs = StudentAttendance.objects.filter(student=student).order_by('-date')
        attendance_total = attendance_qs.count()
        attendance_present = attendance_qs.filter(status='Present').count()
        attendance_absent = attendance_qs.filter(status='Absent').count()
        recent_attendance = attendance_qs[:10]

        if attendance_total > 0:
            attendance_percentage = round((attendance_present / attendance_total) * 100, 2)
    except Exception:
        pass

    total_paid = 0
    total_due = 0
    fee_records = []

    try:
        from fees.models import Fee

        fee_records = Fee.objects.filter(student=student).order_by('-id')[:10]
        total_paid = Fee.objects.filter(student=student).aggregate(total=Sum('amount_paid'))['total'] or 0
    except Exception:
        pass

    exam_records = []

    try:
        from exams.models import Result
        exam_records = Result.objects.filter(student=student).order_by('-id')[:10]
    except Exception:
        try:
            from exams.models import ExamResult
            exam_records = ExamResult.objects.filter(student=student).order_by('-id')[:10]
        except Exception:
            pass

    return render(request, 'students/parent_dashboard.html', {
        'parent': parent,
        'student': student,

        'attendance_total': attendance_total,
        'attendance_present': attendance_present,
        'attendance_absent': attendance_absent,
        'attendance_percentage': attendance_percentage,
        'recent_attendance': recent_attendance,

        'total_paid': total_paid,
        'total_due': total_due,
        'fee_records': fee_records,

        'exam_records': exam_records,
    })

def parent_logout(request):
    request.session.flush()
    return redirect('parent_login')

import random
from django.utils import timezone
from datetime import timedelta
from .models import StudentOTP


def student_forgot_password(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')

        try:
            student = Student.objects.get(student_id=student_id)

            otp = str(random.randint(100000, 999999))

            StudentOTP.objects.create(
                student=student,
                otp=otp
            )

            # 🔥 Demo OTP (console)
            print("OTP:", otp)

            request.session['reset_student'] = student.id

            messages.success(request, f"OTP sent (demo: check terminal)")
            return redirect('student_verify_otp')

        except Student.DoesNotExist:
            messages.error(request, "Student not found")

    return render(request, 'students/forgot_password.html')


def student_verify_otp(request):
    student_id = request.session.get('reset_student')

    if not student_id:
        return redirect('student_login')

    if request.method == 'POST':
        otp_input = request.POST.get('otp')

        try:
            otp_obj = StudentOTP.objects.filter(student_id=student_id).last()

            if otp_obj and otp_obj.otp == otp_input:
                return redirect('student_reset_password')
            else:
                messages.error(request, "Invalid OTP")

        except:
            messages.error(request, "Error")

    return render(request, 'students/verify_otp.html')

def student_reset_password(request):
    student_id = request.session.get('reset_student')

    if not student_id:
        return redirect('student_login')

    student = get_object_or_404(Student, id=student_id)

    if request.method == 'POST':
        new_password = request.POST.get('password')

        if not new_password:
            messages.error(request, "Please enter new password.")
            return redirect('student_reset_password')

        # ✅ HASH PASSWORD
        student.login_password = make_password(new_password)
        student.save(update_fields=['login_password'])

        request.session.pop('reset_student', None)

        messages.success(request, "Password updated successfully. Please login.")
        return redirect('student_login')

    return render(request, 'students/reset_password.html')

from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import check_password, make_password
from .models import Parent


def combined_login(request):
    if request.method == 'POST':
        login_type = request.POST.get('login_type')
        username = request.POST.get('username')
        password = request.POST.get('password')

        # 🎓 STUDENT LOGIN
        if login_type == 'student':
            try:
                student = Student.objects.get(login_username=username, login_enabled=True)

                if check_password(password, student.login_password):

                    if not student.login_password.startswith('pbkdf2_'):
                        student.login_password = make_password(password)
                        student.save(update_fields=['login_password'])

                    request.session['student_id'] = student.id
                    messages.success(request, f"Welcome {student.student_name}")
                    return redirect('student_dashboard')

                messages.error(request, "Invalid student login")
            except Student.DoesNotExist:
                messages.error(request, "Invalid student login")

        # 👨‍👩‍👦 PARENT LOGIN
        elif login_type == 'parent':
            try:
                parent = Parent.objects.get(username=username, is_active=True)

                if check_password(password, parent.password) or password == parent.password:
                    if not parent.password.startswith('pbkdf2_'):
                        parent.password = make_password(password)
                        parent.save(update_fields=['password'])

                    request.session['parent_id'] = parent.id
                    messages.success(request, "Welcome Parent")
                    return redirect('parent_dashboard')

                messages.error(request, "Invalid parent login")
            except Parent.DoesNotExist:
                messages.error(request, "Invalid parent login")

        # 👨‍🏫 STAFF LOGIN
        elif login_type == 'staff':
            user = authenticate(request, username=username, password=password)

            if user is not None and user.is_staff and not user.is_superuser:
                login(request, user)
                messages.success(request, "Welcome Staff")
                return redirect('dashboard')

            messages.error(request, "Invalid staff login")

        # 🔐 ADMIN LOGIN
        elif login_type == 'admin':
            user = authenticate(request, username=username, password=password)

            if user is not None and user.is_superuser:
                login(request, user)
                messages.success(request, "Welcome Admin")
                return redirect('/admin/')

            messages.error(request, "Invalid admin login")

        else:
            messages.error(request, "Please select login type")

    return render(request, 'students/combined_login.html')

# ==============================
# 🔥 PUBLIC RESULT CHECK
# ==============================

def public_result_check(request):
    student = None
    exam_records = []
    searched = False

    if request.method == 'POST':
        searched = True
        student_id = request.POST.get('student_id')
        dob = request.POST.get('date_of_birth')

        try:
            student = Student.objects.get(
                student_id=student_id,
                date_of_birth=dob,
                is_active=True
            )

            try:
                from exams.models import Result
                exam_records = Result.objects.filter(student=student).order_by('-id')
            except Exception:
                try:
                    from exams.models import ExamResult
                    exam_records = ExamResult.objects.filter(student=student).order_by('-id')
                except Exception:
                    exam_records = []

        except Student.DoesNotExist:
            messages.error(request, "Invalid Student ID or Date of Birth.")

    return render(request, 'students/public_result_check.html', {
        'student': student,
        'exam_records': exam_records,
        'searched': searched,
    })

def student_change_password(request):
    student_id = request.session.get('student_id')

    if not student_id:
        return redirect('student_login')

    student = get_object_or_404(Student, id=student_id)

    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not check_password(old_password, student.login_password):
            messages.error(request, "Old password is incorrect.")
            return redirect('student_change_password')

        if new_password != confirm_password:
            messages.error(request, "New password and confirm password do not match.")
            return redirect('student_change_password')

        if len(new_password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
            return redirect('student_change_password')

        student.login_password = make_password(new_password)
        student.save(update_fields=['login_password'])

        messages.success(request, "Password changed successfully.")
        return redirect('student_dashboard')

    return render(request, 'students/student_change_password.html', {
        'student': student
    })