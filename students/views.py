import base64
import random
from io import BytesIO, StringIO

import pandas as pd
import qrcode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password, make_password
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .forms import StudentForm, StudentImportForm
from .models import Student, StudentOTP, Parent
from academics.models import Class, AcademicSession
from collections import defaultdict
from django.db.models.functions import ExtractMonth


# =========================================================
# GLOBAL SESSION HELPERS
# =========================================================

def get_selected_session(request):
    from datetime import datetime

    selected_session = request.session.get("selected_session")

    if not selected_session:
        today = datetime.now()
        year = today.year

        if today.month >= 4:
            selected_session = f"{year}-{year + 1}"
        else:
            selected_session = f"{year - 1}-{year}"

        request.session["selected_session"] = selected_session

    return selected_session


def get_selected_academic_session(request):
    selected_session = get_selected_session(request)

    field_names = [f.name for f in AcademicSession._meta.fields]

    for field in ["session_name", "name", "academic_session", "session", "title"]:
        if field in field_names:
            obj = AcademicSession.objects.filter(**{field: selected_session}).first()
            if obj:
                return obj

    if "is_active" in field_names:
        return AcademicSession.objects.filter(is_active=True).first()

    return AcademicSession.objects.first()


def apply_session_filter(queryset, selected_session=None, academic_session=None):
    try:
        model_fields = [f.name for f in queryset.model._meta.get_fields()]

        if "current_session" in model_fields and academic_session:
            return queryset.filter(current_session=academic_session)

        if "academic_session" in model_fields and selected_session:
            return queryset.filter(academic_session=selected_session)

        if "session" in model_fields and selected_session:
            return queryset.filter(session=selected_session)

    except Exception:
        return queryset

    return queryset


def clean_excel_value(value, default=''):
    if pd.notna(value):
        return value
    return default


def clean_excel_date(value):
    if pd.isna(value) or value == "":
        return None

    try:
        return pd.to_datetime(value).date()
    except Exception:
        return None


# =========================================================
# STUDENT LIST
# =========================================================

@login_required
def student_list(request):
    selected_session = get_selected_session(request)
    academic_session = get_selected_academic_session(request)

    selected_class = request.GET.get('class_assigned')
    selected_section = request.GET.get('section')
    search_query = request.GET.get('q', '').strip()

    students = Student.objects.select_related(
        'class_assigned',
        'sibling_of',
        'current_session'
    ).filter(
        is_active=True,
        is_deleted=False
    ).order_by('id')

    students = apply_session_filter(
        students,
        selected_session=selected_session,
        academic_session=academic_session
    )

    if selected_class:
        students = students.filter(class_assigned_id=selected_class)

    if selected_section:
        students = students.filter(section=selected_section)

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

    sections_qs = Student.objects.filter(
        is_deleted=False
    ).exclude(
        section=""
    ).exclude(
        section__isnull=True
    )

    sections_qs = apply_session_filter(
        sections_qs,
        selected_session=selected_session,
        academic_session=academic_session
    )

    sections = sections_qs.values_list(
        "section",
        flat=True
    ).distinct().order_by("section")

    return render(request, 'students/student_list.html', {
        'students': students,
        'classes': classes,
        'sections': sections,
        'selected_class': selected_class,
        'selected_section': selected_section,
        'search_query': search_query,
        'selected_session': selected_session,
    })

# =========================================================
# ADD / EDIT / DELETE
# =========================================================

@login_required
def student_add(request):
    selected_session = get_selected_session(request)
    academic_session = get_selected_academic_session(request)

    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)

        if form.is_valid():
            student = form.save(commit=False)

            if academic_session:
                student.current_session = academic_session

            student.save()

            messages.success(request, 'Student added successfully.')
            return redirect('student_list')

    else:
        form = StudentForm()

    return render(request, 'students/student_form.html', {
        'form': form,
        'page_title': 'Add Student',
        'selected_session': selected_session,
    })


@login_required
def student_detail(request, pk):
    selected_session = get_selected_session(request)
    academic_session = get_selected_academic_session(request)

    student = get_object_or_404(Student, pk=pk, is_deleted=False)

    siblings = Student.objects.filter(sibling_of=student).order_by('id')
    siblings = apply_session_filter(
        siblings,
        selected_session=selected_session,
        academic_session=academic_session
    )

    classes = Class.objects.all().order_by('id')

    # ================= ATTENDANCE =================
    attendance_total = 0
    attendance_present = 0
    attendance_absent = 0
    attendance_percentage = 0
    attendance_risk = "No Data"

    try:
        from attendance.models import StudentAttendance

        attendance_qs = StudentAttendance.objects.filter(student=student)
        attendance_qs = apply_session_filter(attendance_qs, selected_session, academic_session)

        attendance_total = attendance_qs.count()
        attendance_present = attendance_qs.filter(status='Present').count()
        attendance_absent = attendance_qs.filter(status='Absent').count()

        if attendance_total > 0:
            attendance_percentage = round((attendance_present / attendance_total) * 100, 2)

        if attendance_percentage >= 85:
            attendance_risk = "Safe"
        elif attendance_percentage >= 70:
            attendance_risk = "Warning"
        elif attendance_total > 0:
            attendance_risk = "High Risk"

    except Exception:
        pass

    # ================= FEES =================
    monthly_fee = 0
    total_paid = 0
    total_due = 0
    fee_records = []

    try:
        from fees.models import Fee, FeeStructure

        fee_records = Fee.objects.filter(student=student).order_by('-id')
        fee_records = apply_session_filter(fee_records, selected_session, academic_session)

        total_paid = fee_records.aggregate(total=Sum('amount_paid'))['total'] or 0

        try:
            fee_structure = FeeStructure.objects.get(student=student)
            monthly_fee = fee_structure.monthly_fee
            total_due = max((monthly_fee * 12) - total_paid, 0)
        except Exception:
            pass

    except Exception:
        pass

    # ================= EXAMS =================
    exam_records = []
    try:
        from exams.models import ExamResult
        exam_records = ExamResult.objects.filter(student=student).order_by('-id')
        exam_records = apply_session_filter(exam_records, selected_session, academic_session)
    except Exception:
        pass

    # ================= COMPLAINTS =================
    complaints = []
    pending_complaints = 0
    solved_complaints = 0

    try:
        from complaints.models import Complaint

        complaints = Complaint.objects.filter(student=student).order_by('-created_at')
        complaints = apply_session_filter(complaints, selected_session, academic_session)

        pending_complaints = complaints.filter(status__icontains="Pending").count()
        solved_complaints = complaints.filter(status__icontains="Solved").count()

    except Exception:
        pass

    # ================= UNIT TEST PERFORMANCE =================
    unit_test_marks = []
    unit_test_summary = []
    average_percentage = 0
    weak_subjects = []
    best_subjects = []
    academic_status = "No Data"

    try:
        from exams.models import ClassTestSubjectMark

        unit_test_marks = ClassTestSubjectMark.objects.filter(
            student=student
        ).select_related("class_test").order_by("-class_test__id", "subject")

        grouped = {}

        for mark in unit_test_marks:
            test_id = mark.class_test_id

            if test_id not in grouped:
                grouped[test_id] = {
                    "class_test": mark.class_test,
                    "total_marks": 0,
                    "max_marks": 0,
                    "percentage": 0,
                    "performance": "",
                    "subjects": [],
                    "best_subject": None,
                    "weak_subject": None,
                }

            obtained = mark.marks if mark.marks is not None else 0
            max_mark = mark.total_marks or 100

            grouped[test_id]["total_marks"] += obtained
            grouped[test_id]["max_marks"] += max_mark
            grouped[test_id]["subjects"].append(mark)

        total_percent_sum = 0
        total_tests = 0

        for item in grouped.values():
            if item["max_marks"] > 0:
                item["percentage"] = round((item["total_marks"] / item["max_marks"]) * 100, 2)

            p = item["percentage"]
            total_percent_sum += p
            total_tests += 1

            if p >= 90:
                item["performance"] = "Excellent"
            elif p >= 80:
                item["performance"] = "Best"
            elif p >= 60:
                item["performance"] = "Better"
            elif p >= 40:
                item["performance"] = "Average"
            else:
                item["performance"] = "Low"

            if item["subjects"]:
                sorted_subjects = sorted(
                    item["subjects"],
                    key=lambda x: x.percentage,
                    reverse=True
                )
                item["best_subject"] = sorted_subjects[0]
                item["weak_subject"] = sorted_subjects[-1]

                if item["weak_subject"]:
                    weak_subjects.append(item["weak_subject"])

                if item["best_subject"]:
                    best_subjects.append(item["best_subject"])

            unit_test_summary.append(item)

        if total_tests > 0:
            average_percentage = round(total_percent_sum / total_tests, 2)

        if average_percentage >= 85:
            academic_status = "Excellent"
        elif average_percentage >= 70:
            academic_status = "Good"
        elif average_percentage >= 50:
            academic_status = "Average"
        elif total_tests > 0:
            academic_status = "Fail Risk"

    except Exception:
        pass

    # ================= BEHAVIOUR + SKILLS =================
    behaviour_records = []
    skill_latest = None
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    behaviour_points = 0
    behaviour_score = 100

    try:
        from behaviour.models import BehaviourRecord, SkillEvaluation

        behaviour_records = BehaviourRecord.objects.filter(student=student).order_by("-date", "-id")

        positive_count = behaviour_records.filter(behaviour_type="Positive").count()
        negative_count = behaviour_records.filter(behaviour_type="Negative").count()
        neutral_count = behaviour_records.filter(behaviour_type="Neutral").count()

        behaviour_points = behaviour_records.aggregate(total=Sum("points"))["total"] or 0

        behaviour_score = 100 + behaviour_points
        if behaviour_score > 100:
            behaviour_score = 100
        if behaviour_score < 0:
            behaviour_score = 0

        skill_latest = SkillEvaluation.objects.filter(student=student).order_by("-year", "-id").first()

    except Exception:
        pass

    # ================= CERTIFICATES =================
    certificates = []
    certificate_count = 0

    try:
        from certificates.models import Certificate

        certificates = Certificate.objects.filter(student=student).order_by("-id")
        certificate_count = certificates.count()

    except Exception:
        pass

    # ================= MONTHLY GRAPH DATA =================

    attendance_month_labels = []
    attendance_month_data = []

    fee_month_labels = []
    fee_month_paid_data = []
    fee_month_due_data = []

    try:
        from attendance.models import StudentAttendance

        monthly_attendance = (
            StudentAttendance.objects
            .filter(student=student)
            .annotate(month=ExtractMonth('date'))
        )

        month_map = defaultdict(lambda: {"total": 0, "present": 0})

        for a in monthly_attendance:
            month_map[a.month]["total"] += 1

            if a.status == "Present":
                month_map[a.month]["present"] += 1

        month_names = [
            "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ]

        for m in sorted(month_map.keys()):
            total = month_map[m]["total"]
            present = month_map[m]["present"]

            percent = 0

            if total > 0:
                percent = round((present / total) * 100, 2)

            attendance_month_labels.append(month_names[m])
            attendance_month_data.append(percent)

    except Exception:
        pass

    try:
        from fees.models import FeeCollection

        monthly_fees = (
            FeeCollection.objects
            .filter(student=student)
            .annotate(month=ExtractMonth('payment_date'))
        )

        fee_map_paid = defaultdict(float)
        fee_map_due = defaultdict(float)

        for fee in monthly_fees:
            fee_map_paid[fee.month] += float(fee.deposit_amount or 0)
            fee_map_due[fee.month] += float(fee.due_balance or 0)

        month_names = [
            "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ]

        for m in sorted(fee_map_paid.keys()):
            fee_month_labels.append(month_names[m])
            fee_month_paid_data.append(fee_map_paid[m])
            fee_month_due_data.append(fee_map_due[m])

    except Exception:
        pass


    # ================= SMART AI ENGINE =================

    student_health_index = 100
    ai_risk_level = "Low Risk"
    improvement_status = "Stable"
    smart_parent_alerts = []
    smart_flags = []
    topper_status = False

    # ---------- HEALTH INDEX ----------
    student_health_index = (
        (attendance_percentage * 0.30) +
        (average_percentage * 0.40) +
        (behaviour_score * 0.20)
    )

    if total_due <= 0:
        student_health_index += 10

    if student_health_index > 100:
        student_health_index = 100

    student_health_index = round(student_health_index, 2)

    # ---------- AI RISK LEVEL ----------
    risk_points = 0

    if attendance_percentage < 75:
        risk_points += 30

    if average_percentage < 50:
        risk_points += 35

    if negative_count > positive_count:
        risk_points += 20

    if total_due > 0:
        risk_points += 15

    if risk_points >= 70:
        ai_risk_level = "High Risk"
    elif risk_points >= 40:
        ai_risk_level = "Medium Risk"
    else:
        ai_risk_level = "Low Risk"

    # ---------- IMPROVEMENT TRACK ----------
    if attendance_percentage >= 90 and average_percentage >= 80:
        improvement_status = "Outstanding Growth"

    elif attendance_percentage >= 80 and average_percentage >= 60:
        improvement_status = "Improving"

    elif average_percentage < 40:
        improvement_status = "Needs Immediate Support"

    # ---------- TOPPER DETECTOR ----------
    if average_percentage >= 90:
        topper_status = True
        smart_flags.append("Top Performer")

    if attendance_percentage >= 95:
        smart_flags.append("Attendance Champion")

    if behaviour_score >= 95:
        smart_flags.append("Excellent Discipline")
        # ---------- CLASS RANK ENGINE ----------

    class_rank = None
    section_rank = None
    total_students_in_class = 0
    top_students = []

    try:
        from exams.models import ClassTestSubjectMark

        all_students = Student.objects.filter(
            class_assigned=student.class_assigned,
            is_active=True
        )

        ranking_data = []

        for s in all_students:

            marks_qs = ClassTestSubjectMark.objects.filter(
                student=s
            )

            total_marks = 0
            total_max = 0

            for m in marks_qs:
                total_marks += float(m.marks or 0)
                total_max += float(m.total_marks or 100)

            percentage = 0

            if total_max > 0:
                percentage = round((total_marks / total_max) * 100, 2)

            ranking_data.append({
                "student": s,
                "percentage": percentage,
            })

        ranking_data = sorted(
            ranking_data,
            key=lambda x: x["percentage"],
            reverse=True
        )

        total_students_in_class = len(ranking_data)

        for index, item in enumerate(ranking_data, start=1):

            if item["student"].id == student.id:
                class_rank = index

        top_students = ranking_data[:10]

    except Exception:
        pass


    # ---------- AI PREDICTION ENGINE ----------

    pass_probability = 50
    fail_probability = 50
    future_risk = "Medium"

    pass_probability = (
        (attendance_percentage * 0.25) +
        (average_percentage * 0.50) +
        (behaviour_score * 0.25)
    )

    if pass_probability > 100:
        pass_probability = 100

    fail_probability = 100 - pass_probability

    pass_probability = round(pass_probability, 2)
    fail_probability = round(fail_probability, 2)

    if fail_probability >= 60:
        future_risk = "Critical"

    elif fail_probability >= 35:
        future_risk = "Warning"

    else:
        future_risk = "Safe"


    # ---------- SMART AI RECOMMENDATION ----------

    ai_recommendations = []

    if average_percentage < 50:
        ai_recommendations.append(
            "Needs remedial academic support."
        )

    if attendance_percentage < 75:
        ai_recommendations.append(
            "Attendance counselling recommended."
        )

    if topper_status:
        ai_recommendations.append(
            "Eligible for merit recognition."
        )

    if behaviour_score >= 90:
        ai_recommendations.append(
            "Recommended for leadership activities."
        )

    if total_due > 0:
        ai_recommendations.append(
            "Fee reminder should be sent to guardian."
        )

    if not ai_recommendations:
        ai_recommendations.append(
            "Overall progress is balanced and stable."
        )

    # ---------- SMART PARENT ALERTS ----------
    if attendance_percentage < 75:
        smart_parent_alerts.append(
            "Attendance is below safe limit. Parent meeting recommended."
        )

    if total_due > 0:
        smart_parent_alerts.append(
            "Fee due pending. Kindly clear outstanding balance."
        )

    if negative_count > positive_count:
        smart_parent_alerts.append(
            "Behaviour monitoring recommended."
        )

    if average_percentage < 50:
        smart_parent_alerts.append(
            "Academic performance is weak. Extra guidance needed."
        )

    if not smart_parent_alerts:
        smart_parent_alerts.append(
            "Student performance is currently stable."
        )


    # ================= AI REMARK =================
    ai_remarks = []

    if attendance_risk == "High Risk":
        ai_remarks.append("Attendance is very low. Parent alert recommended.")
    elif attendance_risk == "Warning":
        ai_remarks.append("Attendance needs improvement.")

    if academic_status == "Excellent":
        ai_remarks.append("Excellent academic performance.")
    elif academic_status == "Fail Risk":
        ai_remarks.append("Student is in academic risk zone. Extra support needed.")

    if negative_count > positive_count:
        ai_remarks.append("Behaviour monitoring required.")
    elif positive_count > negative_count:
        ai_remarks.append("Behaviour record is positive.")

    if total_due > 0:
        ai_remarks.append("Fee due exists. Fee reminder recommended.")

    if not ai_remarks:
        ai_remarks.append("Overall performance is stable.")

    return render(request, 'students/student_detail.html', {
        'student': student,
        'siblings': siblings,
        'classes': classes,

        'attendance_total': attendance_total,
        'attendance_present': attendance_present,
        'attendance_absent': attendance_absent,
        'attendance_percentage': attendance_percentage,
        'attendance_risk': attendance_risk,

        'monthly_fee': monthly_fee,
        'total_paid': total_paid,
        'total_due': total_due,
        'fee_records': fee_records,

        'exam_records': exam_records,
        'unit_test_marks': unit_test_marks,
        'unit_test_summary': unit_test_summary,
        'average_percentage': average_percentage,
        'weak_subjects': weak_subjects,
        'best_subjects': best_subjects,
        'academic_status': academic_status,

        'complaints': complaints,
        'pending_complaints': pending_complaints,
        'solved_complaints': solved_complaints,

        'behaviour_records': behaviour_records,
        'skill_latest': skill_latest,
        'positive_count': positive_count,
        'negative_count': negative_count,
        'neutral_count': neutral_count,
        'behaviour_score': behaviour_score,

        'certificates': certificates,
        'certificate_count': certificate_count,

        'ai_remarks': ai_remarks,
        'selected_session': selected_session,
        'attendance_month_labels': attendance_month_labels,
        'attendance_month_data': attendance_month_data,
        'fee_month_labels': fee_month_labels,
        'fee_month_paid_data': fee_month_paid_data,
        'fee_month_due_data': fee_month_due_data,
        'student_health_index': student_health_index,
        'ai_risk_level': ai_risk_level,
        'improvement_status': improvement_status,
        'smart_parent_alerts': smart_parent_alerts,
        'smart_flags': smart_flags,
        'topper_status': topper_status,
        'class_rank': class_rank,
        'section_rank': section_rank,
        'total_students_in_class': total_students_in_class,
        'top_students': top_students,
        'pass_probability': pass_probability,
        'fail_probability': fail_probability,
        'future_risk': future_risk,
        'ai_recommendations': ai_recommendations
    })

@login_required
def student_edit(request, pk):
    selected_session = get_selected_session(request)
    academic_session = get_selected_academic_session(request)

    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)

        if form.is_valid():
            student = form.save(commit=False)

            if academic_session:
                student.current_session = academic_session

            student.save()

            messages.success(request, 'Student updated successfully.')
            return redirect('student_detail', pk=student.pk)

    else:
        form = StudentForm(instance=student)

    return render(request, 'students/student_form.html', {
        'form': form,
        'page_title': 'Edit Student',
        'selected_session': selected_session,
    })


@login_required
def student_delete(request, pk):

    # =====================================
    # DELETE PERMISSION CHECK
    # =====================================

    if not request.user.is_superuser:

        emp = getattr(request.user, "employee", None)

        if not emp or not emp.is_erp_admin:
            messages.error(
                request,
                "❌ Only ERP Admin or Super Admin can delete students."
            )
            return redirect("student_list")

    student = get_object_or_404(
        Student,
        pk=pk,
        is_deleted=False
    )

    if request.method == "POST":

        student.is_deleted = True
        student.is_active = False
        student.deleted_at = timezone.now()

        student.save(
            update_fields=[
                "is_deleted",
                "is_active",
                "deleted_at"
            ]
        )

        messages.success(
            request,
            f"{student.student_name} moved to Recycle Bin."
        )

        return redirect("student_list")

    return render(
        request,
        "students/student_confirm_delete.html",
        {
            "student": student
        }
    )

@login_required
def recycle_bin(request):

    selected_session = get_selected_session(request)
    academic_session = get_selected_academic_session(request)

    search_query = request.GET.get("q", "").strip()
    selected_class = request.GET.get("class", "").strip()

    students = Student.objects.select_related(
        "class_assigned",
        "current_session"
    ).filter(
        is_deleted=True
    ).order_by("-deleted_at")

    students = apply_session_filter(
        students,
        selected_session=selected_session,
        academic_session=academic_session
    )

    if search_query:
        students = students.filter(
            Q(student_name__icontains=search_query) |
            Q(student_id__icontains=search_query) |
            Q(registration_no__icontains=search_query) |
            Q(father_name__icontains=search_query) |
            Q(phone__icontains=search_query)
        )

    if selected_class:
        students = students.filter(
            class_assigned_id=selected_class
        )

    classes = Class.objects.all().order_by("id")

    paginator = Paginator(students, 50)
    page_number = request.GET.get("page")
    students = paginator.get_page(page_number)

    return render(
        request,
        "students/recycle_bin.html",
        {
            "students": students,
            "classes": classes,
            "search_query": search_query,
            "selected_class": selected_class,
            "selected_session": selected_session,
        }
    )


@login_required
def restore_student(request, pk):

    student = get_object_or_404(
        Student,
        pk=pk,
        is_deleted=True
    )

    student.is_deleted = False
    student.is_active = True
    student.deleted_at = None

    student.save(
        update_fields=[
            "is_deleted",
            "is_active",
            "deleted_at"
        ]
    )

    messages.success(
        request,
        f"{student.student_name} restored successfully."
    )

    return redirect("recycle_bin")


@login_required
def permanent_delete_student(request, pk):

    student = get_object_or_404(
        Student,
        pk=pk,
        is_deleted=True
    )

    student.delete()

    messages.success(
        request,
        "Student permanently deleted."
    )

    return redirect("recycle_bin")

    
@login_required
def student_discontinue(request, pk):
    student = get_object_or_404(Student, pk=pk)
    student.is_active = False
    student.save(update_fields=['is_active'])

    messages.warning(request, f'{student.student_name} has been discontinued.')
    return redirect('student_detail', pk=student.pk)

@login_required
def discontinued_students(request):

    students = Student.objects.filter(
        is_active=False,
        is_deleted=False
    ).order_by("student_name")

    return render(
        request,
        "students/discontinued_students.html",
        {
            "students": students
        }
    )


@login_required
def student_readmit(request, pk):
    selected_session = get_selected_session(request)
    academic_session = get_selected_academic_session(request)

    student = get_object_or_404(Student, pk=pk)
    student.is_active = True

    if academic_session:
        student.current_session = academic_session
        student.save(update_fields=['is_active', 'current_session'])
    else:
        student.save(update_fields=['is_active'])

    messages.success(request, f'{student.student_name} has been re-admitted.')
    return redirect('student_detail', pk=student.pk)


# =========================================================
# PROMOTION
# =========================================================

@login_required
def student_promote(request, pk):
    academic_session = get_selected_academic_session(request)

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

    if academic_session:
        student.current_session = academic_session

    if hasattr(student, "is_promoted"):
        student.is_promoted = True
        student.save(update_fields=['class_assigned', 'current_session', 'is_promoted'])
    else:
        student.save(update_fields=['class_assigned', 'current_session'])

    messages.success(request, f'{student.student_name} promoted from {old_class} to {student.class_assigned}.')
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

    messages.success(request, f'{student.student_name} de-promoted from {old_class} to {student.class_assigned}.')
    return redirect('student_detail', pk=student.pk)


@login_required
def add_sibling(request, pk):
    selected_session = get_selected_session(request)
    academic_session = get_selected_academic_session(request)

    main_student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)

        if form.is_valid():
            sibling = form.save(commit=False)
            sibling.sibling_of = main_student

            if academic_session:
                sibling.current_session = academic_session

            sibling.save()

            messages.success(request, 'Sibling added successfully.')
            return redirect('student_detail', pk=main_student.pk)

    else:
        form = StudentForm()

    return render(request, 'students/student_form.html', {
        'form': form,
        'page_title': f'Add Sibling of {main_student.student_name}',
        'selected_session': selected_session,
    })


@login_required
def bulk_promotion(request):
    selected_session = get_selected_session(request)
    academic_session = get_selected_academic_session(request)

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

        students = Student.objects.filter(
            class_assigned=from_class,
            is_active=True
        )

        students = apply_session_filter(
            students,
            selected_session=selected_session,
            academic_session=academic_session
        )

        count = 0

        for student in students:
            student.class_assigned = to_class

            if academic_session:
                student.current_session = academic_session

            update_fields = ['class_assigned', 'current_session']

            if hasattr(student, "is_promoted"):
                student.is_promoted = True
                update_fields.append('is_promoted')

            student.save(update_fields=update_fields)
            count += 1

        messages.success(request, f'{count} students promoted from {from_class} to {to_class}.')
        return redirect('student_list')

    return render(request, 'students/bulk_promotion.html', {
        'classes': classes,
        'selected_session': selected_session,
    })


# =========================================================
# EXPORT
# =========================================================

@login_required
def export_students_excel(request):
    selected_session = get_selected_session(request)
    academic_session = get_selected_academic_session(request)

    students = Student.objects.select_related(
        'class_assigned',
        'current_session'
    ).filter(is_active=True)

    students = apply_session_filter(
        students,
        selected_session=selected_session,
        academic_session=academic_session
    )

    data = []

    for s in students:
        data.append({
            'Student ID': s.student_id,
            'Registration No': s.registration_no,
            'Name': s.student_name,
            'Session': str(s.current_session) if s.current_session else '',
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


# =========================================================
# ID CARD
# =========================================================

@login_required
def student_id_card(request, pk):
    selected_session = get_selected_session(request)

    student = get_object_or_404(Student, pk=pk)

    qr_url = student.student_id

    qr_img = qrcode.make(qr_url)
    buffer = BytesIO()
    qr_img.save(buffer, format="PNG")
    qr_code = base64.b64encode(buffer.getvalue()).decode()

    student_name = student.student_name or "STUDENT NAME"

    return render(request, 'students/id_card.html', {
        'student': student,
        'student_name': student_name,
        'qr_code': qr_code,
        'qr_url': qr_url,
        'selected_session': selected_session,
    })


@login_required
def student_id_cards_print(request):
    selected_session = get_selected_session(request)
    academic_session = get_selected_academic_session(request)

    selected_class = request.GET.get("class")
    selected_ids = request.GET.getlist("students")

    all_students = Student.objects.select_related(
        "class_assigned",
        "current_session"
    ).filter(is_active=True).order_by(
        "class_assigned",
        "roll_no",
        "student_name"
    )

    all_students = apply_session_filter(
        all_students,
        selected_session=selected_session,
        academic_session=academic_session
    )

    if selected_class and selected_class != "all":
        all_students = all_students.filter(class_assigned_id=selected_class)

    class_list = Class.objects.all().order_by("id")

    card_students = []

    if selected_ids:
        students = Student.objects.select_related(
            "class_assigned",
            "current_session"
        ).filter(
            id__in=selected_ids,
            is_active=True
        ).order_by(
            "class_assigned",
            "roll_no",
            "student_name"
        )

        students = apply_session_filter(
            students,
            selected_session=selected_session,
            academic_session=academic_session
        )

        for student in students:
            qr_url = student.student_id

            qr_img = qrcode.make(qr_url)
            buffer = BytesIO()
            qr_img.save(buffer, format="PNG")
            qr_code = base64.b64encode(buffer.getvalue()).decode()

            card_students.append({
                "student": student,
                "student_name": student.student_name or "NO NAME",
                "qr_code": qr_code,
                "qr_url": qr_url,
            })

    return render(request, "students/id_cards_print.html", {
        "all_students": all_students,
        "class_list": class_list,
        "selected_class": selected_class,
        "selected_ids": selected_ids,
        "card_students": card_students,
        "selected_session": selected_session,
    })


# =========================================================
# QR PROFILE + ATTENDANCE
# =========================================================

@login_required
def student_qr_profile(request, pk):
    selected_session = get_selected_session(request)
    academic_session = get_selected_academic_session(request)

    student = get_object_or_404(Student, pk=pk)
    today = timezone.localdate()

    if request.method == 'POST':
        status = request.POST.get('status') or 'Present'

        try:
            from attendance.models import StudentAttendance

            defaults = {'status': status}

            attendance_fields = [f.name for f in StudentAttendance._meta.get_fields()]

            if "academic_session" in attendance_fields:
                defaults["academic_session"] = selected_session

            if "session" in attendance_fields:
                defaults["session"] = selected_session

            StudentAttendance.objects.update_or_create(
                student=student,
                date=today,
                defaults=defaults
            )

            messages.success(request, f'{student.student_name} attendance marked as {status}.')

        except Exception as e:
            messages.error(request, f'Attendance error: {e}')

        return redirect('student_qr_profile', pk=student.pk)

    return render(request, 'students/qr_profile.html', {
        'student': student,
        'today': today,
        'selected_session': selected_session,
    })


def student_qr_attendance(request, pk):
    selected_session = get_selected_session(request)

    student = get_object_or_404(Student, pk=pk)
    today = timezone.localdate()

    try:
        from attendance.models import StudentAttendance

        defaults = {'status': 'Present'}
        attendance_fields = [f.name for f in StudentAttendance._meta.get_fields()]

        if "academic_session" in attendance_fields:
            defaults["academic_session"] = selected_session

        if "session" in attendance_fields:
            defaults["session"] = selected_session

        attendance, created = StudentAttendance.objects.get_or_create(
            student=student,
            date=today,
            defaults=defaults
        )

        if not created:
            attendance.status = "Present"

            update_fields = ["status"]

            if "academic_session" in attendance_fields:
                attendance.academic_session = selected_session
                update_fields.append("academic_session")

            if "session" in attendance_fields:
                attendance.session = selected_session
                update_fields.append("session")

            attendance.save(update_fields=update_fields)

        messages.success(request, f"{student.student_name} attendance marked.")

    except Exception as e:
        messages.error(request, f"Attendance error: {e}")

    return render(request, 'students/student_attendance.html', {
        'student': student,
        'date': today,
        'selected_session': selected_session,
    })


# =========================================================
# STUDENT EXCEL IMPORT
# =========================================================

@login_required
def student_import(request):
    selected_session = get_selected_session(request)
    academic_session = get_selected_academic_session(request)

    errors = []
    success_count = 0
    failed_count = 0

    if request.method == 'POST':
        form = StudentImportForm(request.POST, request.FILES)

        if form.is_valid():
            excel_file = request.FILES.get('excel_file')

            try:
                df = pd.read_excel(excel_file)

                for index, row in df.iterrows():
                    row_no = index + 2

                    student_name = str(row.get('student_name', '')).strip()
                    admission_no = ''

                    if not student_name:
                        failed_count += 1
                        errors.append(f"Row {row_no}: Student name is required.")
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
                        student_name=student_name,
                        admission_no=admission_no,
                        admission_date=clean_excel_date(row.get('admission_date')) or timezone.localdate(),
                        current_session=academic_session,
                        class_assigned=class_obj,
                        roll_no=clean_excel_value(row.get('roll_no'), None),
                        father_name=clean_excel_value(row.get('father_name'), ''),
                        mother_name=clean_excel_value(row.get('mother_name'), ''),
                        guardian_name=clean_excel_value(row.get('guardian_name'), ''),
                        phone=str(clean_excel_value(row.get('phone'), '')).strip(),
                        gender=clean_excel_value(row.get('gender'), ''),
                        date_of_birth=clean_excel_date(row.get('date_of_birth')),
                        aadhaar_number=str(clean_excel_value(row.get('aadhaar_number'), '')).strip(),
                        transport_required=str(row.get('transport_required', '')).lower() in ['true', 'yes', '1'],
                        transport_details=clean_excel_value(row.get('transport_details'), ''),
                        previous_school=clean_excel_value(row.get('previous_school'), ''),
                        address=clean_excel_value(row.get('address'), ''),
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
        'selected_session': selected_session,
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
    selected_session = get_selected_session(request)
    academic_session = get_selected_academic_session(request)

    data_json = request.session.get('import_data')

    if not data_json:
        messages.error(request, "No import data found.")
        return redirect('student_import')

    df = pd.read_json(StringIO(data_json))

    success_count = 0
    failed_count = 0
    errors = []

    for index, row in df.iterrows():
        row_no = index + 2

        try:
            student_name = str(row.get('student_name', '')).strip()
            admission_no = ''

            if not student_name:
                failed_count += 1
                errors.append(f"Row {row_no}: Student name is required.")
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
                student_name=student_name,
                admission_no=admission_no,
                admission_date=clean_excel_date(row.get('admission_date')) or timezone.localdate(),
                current_session=academic_session,
                class_assigned=class_obj,
                roll_no=clean_excel_value(row.get('roll_no'), None),
                father_name=clean_excel_value(row.get('father_name'), ''),
                mother_name=clean_excel_value(row.get('mother_name'), ''),
                guardian_name=clean_excel_value(row.get('guardian_name'), ''),
                phone=str(clean_excel_value(row.get('phone'), '')).strip(),
                gender=clean_excel_value(row.get('gender'), ''),
                date_of_birth=clean_excel_date(row.get('date_of_birth')),
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
        'form': StudentImportForm(),
        'selected_session': selected_session,
    })


# =========================================================
# STUDENT LOGIN PANEL
# =========================================================

def student_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            student = Student.objects.get(
                login_username=username,
                login_enabled=True
            )

            if check_password(password, student.login_password):
                if not student.login_password.startswith('pbkdf2_'):
                    student.login_password = make_password(password)
                    student.save(update_fields=['login_password'])

                request.session['student_id'] = student.id
                messages.success(request, f"Welcome {student.student_name}")
                return redirect('student_dashboard')

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

    selected_session = (
        str(student.current_session)
        if student.current_session
        else ""
    )

    # =====================================
    # ATTENDANCE
    # =====================================

    attendance_total = 0
    attendance_present = 0
    attendance_absent = 0
    attendance_percentage = 0
    recent_attendance = []

    try:
        from attendance.models import StudentAttendance

        attendance_qs = StudentAttendance.objects.filter(
            student=student
        ).order_by('-date')

        attendance_qs = apply_session_filter(
            attendance_qs,
            selected_session=selected_session,
            academic_session=student.current_session
        )

        attendance_total = attendance_qs.count()

        attendance_present = attendance_qs.filter(
            status='Present'
        ).count()

        attendance_absent = attendance_qs.filter(
            status='Absent'
        ).count()

        recent_attendance = attendance_qs[:10]

        if attendance_total > 0:
            attendance_percentage = round(
                (attendance_present / attendance_total) * 100,
                2
            )

    except Exception:
        pass

    # =====================================
    # FEES
    # =====================================

    total_paid = 0
    total_due = 0
    fee_records = []

    try:
        from fees.models import Fee

        fee_records = Fee.objects.filter(
            student=student
        ).order_by('-id')

        fee_records = apply_session_filter(
            fee_records,
            selected_session=selected_session,
            academic_session=student.current_session
        )[:10]

        fee_total_qs = Fee.objects.filter(
            student=student
        )

        fee_total_qs = apply_session_filter(
            fee_total_qs,
            selected_session=selected_session,
            academic_session=student.current_session
        )

        total_paid = (
            fee_total_qs.aggregate(
                total=Sum('amount_paid')
            )['total']
            or 0
        )

    except Exception:
        pass

    # =====================================
    # EXAM RESULT
    # =====================================

    exam_records = []

    try:
        from exams.models import Result

        exam_records = Result.objects.filter(
            student=student
        ).order_by('-id')

        exam_records = apply_session_filter(
            exam_records,
            selected_session=selected_session,
            academic_session=student.current_session
        )[:10]

    except Exception:

        try:
            from exams.models import ExamResult

            exam_records = ExamResult.objects.filter(
                student=student
            ).order_by('-id')

            exam_records = apply_session_filter(
                exam_records,
                selected_session=selected_session,
                academic_session=student.current_session
            )[:10]

        except Exception:
            pass

    # =====================================
    # CLASS TEST
    # =====================================

    class_test_marks = []

    try:
        from exams.models import ClassTestSubjectMark

        class_test_marks = (
            ClassTestSubjectMark.objects
            .filter(student=student)
            .select_related("class_test")
            .order_by("-class_test__id", "subject")[:20]
        )

    except Exception:
        pass

    # =====================================
    # COMPLAINTS
    # =====================================

    complaints = []
    total_complaints = 0
    pending_complaints = 0
    solved_complaints = 0
    rejected_complaints = 0

    try:
        from complaints.models import Complaint

        complaints = Complaint.objects.filter(
            student=student
        ).order_by("-created_at")

        total_complaints = complaints.count()

        pending_complaints = complaints.filter(
            status__in=[
                "PENDING_TEACHER",
                "PENDING_ADMIN_APPROVAL"
            ]
        ).count()

        solved_complaints = complaints.filter(
            status="SOLVED"
        ).count()

        rejected_complaints = complaints.filter(
            status="REJECTED"
        ).count()

    except Exception:
        pass

    return render(
        request,
        'students/student_dashboard.html',
        {
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
            'class_test_marks': class_test_marks,

            'selected_session': selected_session,

            # Complaint
            'complaints': complaints,
            'total_complaints': total_complaints,
            'pending_complaints': pending_complaints,
            'solved_complaints': solved_complaints,
            'rejected_complaints': rejected_complaints,
        }
    )
    
# =========================================================
# PARENT LOGIN SYSTEM
# =========================================================

def parent_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            parent = Parent.objects.get(username=username, is_active=True)

            if check_password(password, parent.password):
                if not parent.password.startswith('pbkdf2_'):
                    parent.password = make_password(password)
                    parent.save(update_fields=['password'])

                request.session['parent_id'] = parent.id
                return redirect('parent_dashboard')

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
    selected_session = str(student.current_session) if student.current_session else ""

    # ================= ATTENDANCE =================
    attendance_total = 0
    attendance_present = 0
    attendance_absent = 0
    attendance_percentage = 0
    recent_attendance = []

    try:
        from attendance.models import StudentAttendance

        attendance_qs = StudentAttendance.objects.filter(student=student).order_by('-date')
        attendance_qs = apply_session_filter(
            attendance_qs,
            selected_session=selected_session,
            academic_session=student.current_session
        )

        attendance_total = attendance_qs.count()
        attendance_present = attendance_qs.filter(status='Present').count()
        attendance_absent = attendance_qs.filter(status='Absent').count()
        recent_attendance = attendance_qs[:10]

        if attendance_total > 0:
            attendance_percentage = round((attendance_present / attendance_total) * 100, 2)

    except Exception:
        pass

    # ================= FEES =================
    total_paid = 0
    total_due = 0
    monthly_fee = 0
    fee_records = []

    try:
        from fees.models import Fee, FeeStructure

        fee_records_qs = Fee.objects.filter(student=student).order_by('-id')
        fee_records_qs = apply_session_filter(
            fee_records_qs,
            selected_session=selected_session,
            academic_session=student.current_session
        )

        fee_records = fee_records_qs[:10]
        total_paid = fee_records_qs.aggregate(total=Sum('amount_paid'))['total'] or 0

        try:
            fee_structure = FeeStructure.objects.filter(student=student).first()

            if not fee_structure and student.class_assigned:
                fee_structure = FeeStructure.objects.filter(
                    class_assigned=student.class_assigned
                ).first()

            if fee_structure and hasattr(fee_structure, 'monthly_fee'):
                monthly_fee = fee_structure.monthly_fee or 0
                total_due = max((monthly_fee * 12) - total_paid, 0)
        except Exception:
            pass

    except Exception:
        try:
            from fees.models import FeeCollection

            fee_records_qs = FeeCollection.objects.filter(student=student).order_by('-id')
            fee_records_qs = apply_session_filter(
                fee_records_qs,
                selected_session=selected_session,
                academic_session=student.current_session
            )

            fee_records = fee_records_qs[:10]
            total_paid = fee_records_qs.aggregate(total=Sum('deposit_amount'))['total'] or 0

            last_collection = fee_records_qs.first()
            if last_collection and hasattr(last_collection, 'due_balance'):
                total_due = last_collection.due_balance or 0

        except Exception:
            pass

    # ================= ACADEMIC / CLASS TEST =================
    exam_records = []
    class_test_marks = []
    average_percentage = 0

    try:
        from exams.models import Result

        exam_records = Result.objects.filter(student=student).order_by('-id')
        exam_records = apply_session_filter(
            exam_records,
            selected_session=selected_session,
            academic_session=student.current_session
        )[:10]

    except Exception:
        try:
            from exams.models import ExamResult

            exam_records = ExamResult.objects.filter(student=student).order_by('-id')
            exam_records = apply_session_filter(
                exam_records,
                selected_session=selected_session,
                academic_session=student.current_session
            )[:10]

        except Exception:
            pass

    try:
        from exams.models import ClassTestSubjectMark

        class_test_marks_qs = ClassTestSubjectMark.objects.filter(
            student=student
        ).select_related(
            "class_test"
        ).order_by("-class_test__id", "subject")

        class_test_marks = class_test_marks_qs[:20]

        total_marks = 0
        total_max = 0

        for mark in class_test_marks_qs:
            total_marks += float(mark.marks or 0)
            total_max += float(mark.total_marks or 100)

        if total_max > 0:
            average_percentage = round((total_marks / total_max) * 100, 2)

    except Exception:
        pass

    # ================= COMPLAINTS =================
    complaints = []
    pending_complaints = 0
    solved_complaints = 0

    try:
        from complaints.models import Complaint

        complaints_qs = Complaint.objects.filter(student=student).order_by('-id')
        complaints = complaints_qs[:10]
        pending_complaints = complaints_qs.filter(status__icontains="Pending").count()
        solved_complaints = complaints_qs.filter(status__icontains="Solved").count()

    except Exception:
        pass

    # ================= BEHAVIOUR =================
    behaviour_score = 100
    positive_count = 0
    negative_count = 0

    try:
        from behaviour.models import BehaviourRecord

        behaviour_records = BehaviourRecord.objects.filter(student=student)
        positive_count = behaviour_records.filter(behaviour_type="Positive").count()
        negative_count = behaviour_records.filter(behaviour_type="Negative").count()

        behaviour_points = behaviour_records.aggregate(total=Sum("points"))["total"] or 0
        behaviour_score = 100 + behaviour_points

        if behaviour_score > 100:
            behaviour_score = 100
        if behaviour_score < 0:
            behaviour_score = 0

    except Exception:
        pass

    # ================= PARENT AI ENGINE =================
    student_health_index = 100
    ai_risk_level = "Low Risk"
    pass_probability = 50
    fail_probability = 50
    future_risk = "Safe"
    smart_parent_alerts = []
    ai_recommendations = []

    student_health_index = (
        (attendance_percentage * 0.30) +
        (average_percentage * 0.50) +
        (behaviour_score * 0.20)
    )

    if total_due <= 0:
        student_health_index += 10

    if student_health_index > 100:
        student_health_index = 100

    student_health_index = round(student_health_index, 2)

    pass_probability = student_health_index

    if pass_probability > 100:
        pass_probability = 100

    fail_probability = round(100 - pass_probability, 2)
    pass_probability = round(pass_probability, 2)

    risk_points = 0

    if attendance_percentage < 75:
        risk_points += 30

    if average_percentage < 50:
        risk_points += 40

    if negative_count > positive_count:
        risk_points += 15

    if total_due > 0:
        risk_points += 15

    if risk_points >= 70:
        ai_risk_level = "High Risk"
        future_risk = "Critical"
    elif risk_points >= 40:
        ai_risk_level = "Medium Risk"
        future_risk = "Warning"
    else:
        ai_risk_level = "Low Risk"
        future_risk = "Safe"

    if attendance_percentage < 75:
        smart_parent_alerts.append("Attendance is below safe limit. Please contact class teacher.")

    if total_due > 0:
        smart_parent_alerts.append("Fee due is pending. Please clear the outstanding balance.")

    if average_percentage < 50:
        smart_parent_alerts.append("Academic performance needs extra guidance.")

    if negative_count > positive_count:
        smart_parent_alerts.append("Behaviour monitoring is recommended.")

    if not smart_parent_alerts:
        smart_parent_alerts.append("Student performance is currently stable.")

    if average_percentage < 50:
        ai_recommendations.append("Extra academic support is recommended.")

    if attendance_percentage < 75:
        ai_recommendations.append("Attendance counselling is recommended.")

    if behaviour_score >= 90:
        ai_recommendations.append("Excellent discipline maintained.")

    if pass_probability >= 85:
        ai_recommendations.append("Student is performing strongly. Keep regular practice continuing.")

    if total_due > 0:
        ai_recommendations.append("Fee reminder should be followed up with school accounts.")

    if not ai_recommendations:
        ai_recommendations.append("Overall progress is balanced.")

    return render(request, 'students/parent_dashboard.html', {
        'parent': parent,
        'student': student,
        'attendance_total': attendance_total,
        'attendance_present': attendance_present,
        'attendance_absent': attendance_absent,
        'attendance_percentage': attendance_percentage,
        'recent_attendance': recent_attendance,
        'monthly_fee': monthly_fee,
        'total_paid': total_paid,
        'total_due': total_due,
        'fee_records': fee_records,
        'exam_records': exam_records,
        'class_test_marks': class_test_marks,
        'complaints': complaints,
        'pending_complaints': pending_complaints,
        'solved_complaints': solved_complaints,
        'average_percentage': average_percentage,
        'behaviour_score': behaviour_score,
        'student_health_index': student_health_index,
        'ai_risk_level': ai_risk_level,
        'pass_probability': pass_probability,
        'fail_probability': fail_probability,
        'future_risk': future_risk,
        'smart_parent_alerts': smart_parent_alerts,
        'ai_recommendations': ai_recommendations,
        'selected_session': selected_session,
    })

def parent_logout(request):
    request.session.flush()
    return redirect('parent_login')


# =========================================================
# PASSWORD RESET
# =========================================================

def student_forgot_password(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')

        try:
            student = Student.objects.get(student_id=student_id)
            otp = str(random.randint(100000, 999999))

            StudentOTP.objects.create(student=student, otp=otp)

            print("OTP:", otp)
            request.session['reset_student'] = student.id

            messages.success(request, "OTP sent. Check terminal demo OTP.")
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
        otp_obj = StudentOTP.objects.filter(student_id=student_id).last()

        if otp_obj and otp_obj.otp == otp_input:
            return redirect('student_reset_password')

        messages.error(request, "Invalid OTP")

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

        student.login_password = make_password(new_password)
        student.save(update_fields=['login_password'])

        request.session.pop('reset_student', None)

        messages.success(request, "Password updated successfully. Please login.")
        return redirect('student_login')

    return render(request, 'students/reset_password.html')


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


# =========================================================
# PUBLIC RESULT CHECK
# =========================================================

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

            selected_session = str(student.current_session) if student.current_session else ""

            try:
                from exams.models import Result

                exam_records = Result.objects.filter(student=student).order_by('-id')
                exam_records = apply_session_filter(
                    exam_records,
                    selected_session=selected_session,
                    academic_session=student.current_session
                )

            except Exception:
                try:
                    from exams.models import ExamResult

                    exam_records = ExamResult.objects.filter(student=student).order_by('-id')
                    exam_records = apply_session_filter(
                        exam_records,
                        selected_session=selected_session,
                        academic_session=student.current_session
                    )

                except Exception:
                    exam_records = []

        except Student.DoesNotExist:
            messages.error(request, "Invalid Student ID or Date of Birth.")

    return render(request, 'students/public_result_check.html', {
        'student': student,
        'exam_records': exam_records,
        'searched': searched,
    })


# =========================================================
# BULK PASSWORD PRINT
# =========================================================

@login_required
def bulk_student_password_print(request):
    selected_session = get_selected_session(request)
    academic_session = get_selected_academic_session(request)

    selected_class = request.GET.get('class_id')

    students = Student.objects.filter(is_active=True).order_by(
        'class_assigned',
        'roll_no',
        'id'
    )

    students = apply_session_filter(
        students,
        selected_session=selected_session,
        academic_session=academic_session
    )

    if selected_class:
        students = students.filter(class_assigned_id=selected_class)

    if request.method == "POST":
        reset_count = 0

        for student in students:
            raw_password = student.get_default_raw_password()
            student.login_username = student.student_id
            student.login_password = make_password(raw_password)
            student.login_enabled = True
            student.save(update_fields=['login_username', 'login_password', 'login_enabled'])
            reset_count += 1

        messages.success(request, f"✅ {reset_count} students password reset done.")

        return redirect(
            f"{request.path}?class_id={selected_class}" if selected_class else request.path
        )

    classes = Class.objects.all().order_by('id')

    return render(request, 'students/bulk_password_print.html', {
        'students': students,
        'classes': classes,
        'selected_class': selected_class,
        'selected_session': selected_session,
    })
# =========================================================
# STUDENT / PARENT COMPLAINT PORTAL
# =========================================================

from complaints.models import Complaint


def student_complaint_list(request):

    student_id = request.session.get('student_id')

    if not student_id:
        return redirect('student_login')

    student = get_object_or_404(Student, id=student_id)

    complaints = Complaint.objects.filter(
        student=student
    ).order_by('-id')

    return render(
        request,
        'students/portal_complaint_list.html',
        {
            'student': student,
            'complaints': complaints,
            'portal_type': 'student',
        }
    )


def student_complaint_add(request):

    student_id = request.session.get('student_id')

    if not student_id:
        return redirect('student_login')

    student = get_object_or_404(Student, id=student_id)

    if request.method == 'POST':

        title = request.POST.get('title')
        complaint_text = request.POST.get('complaint_text')

        Complaint.objects.create(
            student=student,
            title=title,
            description=complaint_text,
            parent_name="Student",
            status='Pending'
        )

        messages.success(
            request,
            'Complaint submitted successfully.'
        )

        return redirect('student_complaint_list')

    return render(
        request,
        'students/portal_complaint_form.html',
        {
            'student': student,
            'portal_type': 'student',
        }
    )


def parent_complaint_list(request):

    parent_id = request.session.get('parent_id')

    if not parent_id:
        return redirect('parent_login')

    parent = get_object_or_404(Parent, id=parent_id)

    student = parent.student

    complaints = Complaint.objects.filter(
        student=student
    ).order_by('-id')

    return render(
        request,
        'students/portal_complaint_list.html',
        {
            'parent': parent,
            'student': student,
            'complaints': complaints,
            'portal_type': 'parent',
        }
    )


def parent_complaint_add(request):

    parent_id = request.session.get('parent_id')

    if not parent_id:
        return redirect('parent_login')

    parent = get_object_or_404(Parent, id=parent_id)

    student = parent.student

    if request.method == 'POST':

        title = request.POST.get('title')
        complaint_text = request.POST.get('complaint_text')

        Complaint.objects.create(
            student=student,
            title=title,
            description=complaint_text,
            parent_name="Parent",
            status='Pending'
        )

        messages.success(
            request,
            'Complaint submitted successfully.'
        )

        return redirect('parent_complaint_list')

    return render(
        request,
        'students/portal_complaint_form.html',
        {
            'parent': parent,
            'student': student,
            'portal_type': 'parent',
        }
    )

@login_required
def student_classwise_download(request):
    selected_session = get_selected_session(request)
    academic_session = get_selected_academic_session(request)

    selected_class = request.GET.get("class_id")
    selected_section = request.GET.get("section")
    selected_gender = request.GET.get("gender")
    selected_religion = request.GET.get("religion")
    selected_village = request.GET.get("village")

    selected_columns = request.GET.getlist("columns")

    if not selected_columns:
        selected_columns = [
            "student_id",
            "student_name",
            "father_name",
            "class",
            "section",
            "roll",
            "gender",
            "religion",
            "village",
            "phone",
        ]

    students = Student.objects.select_related(
        "class_assigned",
        "current_session"
    ).filter(is_active=True).order_by(
        "class_assigned",
        "section",
        "roll_no",
        "student_name"
    )

    students = apply_session_filter(
        students,
        selected_session=selected_session,
        academic_session=academic_session
    )

    if selected_class:
        students = students.filter(class_assigned_id=selected_class)

    if selected_section:
        students = students.filter(section=selected_section)

    if selected_gender:
        students = students.filter(gender=selected_gender)

    if selected_religion:
        students = students.filter(religion=selected_religion)

    if selected_village:
        students = students.filter(village__icontains=selected_village)

    classes = Class.objects.all().order_by("id")

    sections = Student.objects.exclude(
        section=""
    ).exclude(
        section__isnull=True
    ).values_list(
        "section", flat=True
    ).distinct().order_by("section")

    villages = Student.objects.exclude(
        village=""
    ).exclude(
        village__isnull=True
    ).values_list(
        "village", flat=True
    ).distinct().order_by("village")

    return render(request, "students/student_classwise_download.html", {
        "students": students,
        "classes": classes,
        "sections": sections,
        "villages": villages,
        "selected_class": selected_class,
        "selected_section": selected_section,
        "selected_gender": selected_gender,
        "selected_religion": selected_religion,
        "selected_village": selected_village,
        "selected_columns": selected_columns,
        "selected_session": selected_session,
    })