from datetime import datetime, timedelta
import calendar
import json
import math
import re
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count
from django.db.models import Q

from students.models import Student
from teachers.models import Employee
from academics.models import Class, AcademicSession
from core.views import get_selected_session

from .models import StudentAttendance, TeacherAttendance, AttendanceAlert, Holiday
from .forms import HolidayForm
from .utils import send_whatsapp_message, send_sms_message, get_holiday_status


SCHOOL_LATITUDE = 26.018448
SCHOOL_LONGITUDE = 88.009799
SCHOOL_RADIUS_METERS = 150


# =========================================================
# COMMON HELPERS
# =========================================================

def get_active_session(request=None):
    if request:
        selected_session = get_selected_session(request)
        session = AcademicSession.objects.filter(session_name=selected_session).first()
        if session:
            return session

    return AcademicSession.objects.filter(is_active=True).first()


def parse_date_safe(date_value):
    if hasattr(date_value, "weekday"):
        return date_value

    try:
        return datetime.strptime(str(date_value), "%Y-%m-%d").date()
    except Exception:
        return timezone.now().date()


def get_month_start_end(date_value):
    selected_date = parse_date_safe(date_value)
    start_date = selected_date.replace(day=1)
    last_day = calendar.monthrange(selected_date.year, selected_date.month)[1]
    end_date = selected_date.replace(day=last_day)
    return start_date, end_date


def daterange(start_date, end_date):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def get_roll_number_value(student):
    """
    Roll no numeric sorting:
    1, 2, 3 ... 10, 11, 12
    Works even if roll_no is saved as text like "01", "2", "10A".
    """
    raw_roll = getattr(student, "roll_no", None)

    if raw_roll is None or str(raw_roll).strip() == "":
        return 999999

    match = re.search(r"\d+", str(raw_roll))
    if match:
        return int(match.group())

    return 999999


def student_numeric_sort_key(student):
    class_name = ""
    class_obj = getattr(student, "class_assigned", None)
    if class_obj:
        class_name = str(getattr(class_obj, "class_name", class_obj))

    section = str(getattr(student, "section", "") or "")
    name = str(getattr(student, "student_name", "") or "")

    return (
        class_name,
        section,
        get_roll_number_value(student),
        name.lower(),
        getattr(student, "id", 0),
    )


def numeric_sort_students(students):
    return sorted(list(students), key=student_numeric_sort_key)


def calculate_distance_meters(lat1, lon1, lat2, lon2):
    try:
        lat1 = float(lat1)
        lon1 = float(lon1)
        lat2 = float(lat2)
        lon2 = float(lon2)

        earth_radius = 6371000
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2)
            * math.sin(delta_lambda / 2) ** 2
        )

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(earth_radius * c, 2)

    except Exception:
        return None


def decimal_or_none(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def is_erp_admin_user(request, emp=None):
    if request.user.is_superuser or request.user.is_staff:
        return True
    if emp and getattr(emp, "is_erp_admin", False):
        return True
    return False


def get_class_teacher_permission(request, emp, selected_class=None):
    if is_erp_admin_user(request, emp):
        return True, False, None

    class_obj = None
    if emp:
        class_obj = Class.objects.filter(class_teacher=emp).first()

    if not class_obj:
        return False, False, None

    allowed_class_id = str(class_obj.id)
    if selected_class and str(selected_class) != allowed_class_id:
        return False, True, allowed_class_id

    return True, True, allowed_class_id


# =========================================================
# STUDENT ATTENDANCE
# =========================================================

@login_required
def student_attendance(request):
    active_session = get_active_session(request)
    emp = getattr(request.user, "employee", None)

    selected_date = request.GET.get("date")
    selected_class = request.GET.get("class_id")
    selected_section = request.GET.get("section")

    attendance_date = selected_date if selected_date else timezone.now().date().isoformat()
    attendance_date_obj = parse_date_safe(attendance_date)
    holiday_info = get_holiday_status(attendance_date_obj)

    classes = Class.objects.all().order_by("class_name")

    permission_allowed, is_class_teacher, allowed_class_id = get_class_teacher_permission(
        request,
        emp,
        selected_class,
    )

    if is_class_teacher and not selected_class:
        selected_class = allowed_class_id

    can_mark_attendance = permission_allowed

    if holiday_info["is_holiday"] and not holiday_info["is_half_day"]:
        can_mark_attendance = False

    students = Student.objects.select_related("class_assigned", "current_session").filter(is_active=True)

    if active_session:
        students = students.filter(current_session=active_session)

    if selected_class:
        students = students.filter(class_assigned_id=selected_class)

    if selected_section:
        students = students.filter(section=selected_section)

    students = numeric_sort_students(students)

    existing_records = StudentAttendance.objects.filter(date=attendance_date_obj)

    if active_session:
        existing_records = existing_records.filter(session=active_session)

    if selected_class:
        existing_records = existing_records.filter(student__class_assigned_id=selected_class)

    if selected_section:
        existing_records = existing_records.filter(student__section=selected_section)

    existing_status_map = {
        record.student_id: record.status
        for record in existing_records
    }

    for student in students:
        if student.id in existing_status_map:
            student.current_status = existing_status_map.get(student.id)
        elif holiday_info["is_holiday"]:
            student.current_status = holiday_info["status"]
        else:
            student.current_status = "Not Marked"

    is_update = existing_records.exists()

    if request.method == "POST":
        post_date = request.POST.get("attendance_date")
        post_date_obj = parse_date_safe(post_date)
        post_holiday_info = get_holiday_status(post_date_obj)

        post_class_id = request.POST.get("class_id") or ""
        post_section = request.POST.get("section") or ""

        if post_holiday_info["is_holiday"] and not post_holiday_info["is_half_day"]:
            messages.warning(request, f"⚠️ {post_holiday_info['title']} আছে। Attendance mark করা যাবে না।")
            return redirect(f"/attendance/students/?date={post_date}&class_id={post_class_id}&section={post_section}")

        post_allowed, _, _ = get_class_teacher_permission(request, emp, post_class_id)

        if not post_allowed:
            messages.error(request, "❌ You are not allowed to mark this class attendance.")
            return redirect("/attendance/students/daily-report/")

        if not post_class_id:
            messages.error(request, "❌ Please select a class first.")
            return redirect("/attendance/students/")

        students_to_save = Student.objects.filter(
            is_active=True,
            class_assigned_id=post_class_id,
        )

        if active_session:
            students_to_save = students_to_save.filter(current_session=active_session)

        if post_section:
            students_to_save = students_to_save.filter(section=post_section)

        for student in students_to_save:
            status = request.POST.get(f"status_{student.id}", "Present")

            StudentAttendance.objects.update_or_create(
                student=student,
                session=active_session,
                date=post_date_obj,
                defaults={
                    "status": status,
                    "section": getattr(student, "section", "") or "",
                    "source": "Manual",
                    "marked_by": emp,
                },
            )

        messages.success(request, "✅ Student attendance updated successfully.")
        return redirect(f"/attendance/students/?date={post_date}&class_id={post_class_id}&section={post_section}")

    return render(request, "attendance/student_attendance.html", {
        "students": students,
        "classes": classes,
        "attendance_date": attendance_date,
        "selected_class": selected_class,
        "selected_section": selected_section,
        "is_update": is_update,
        "can_mark_attendance": can_mark_attendance,
        "is_class_teacher": is_class_teacher,
        "allowed_class_id": allowed_class_id,
        "holiday_info": holiday_info,
        "active_session": active_session,
    })


# =========================================================
# TEACHER ATTENDANCE
# =========================================================

@login_required
def teacher_attendance(request):
    active_session = get_active_session(request)
    emp = getattr(request.user, "employee", None)

    if not is_erp_admin_user(request, emp):
        messages.error(request, "❌ You cannot mark teacher attendance.")
        return redirect("/teacher-dashboard/")

    selected_date = request.GET.get("date")
    attendance_date = selected_date if selected_date else timezone.now().date().isoformat()
    attendance_date_obj = parse_date_safe(attendance_date)
    holiday_info = get_holiday_status(attendance_date_obj)

    employees = Employee.objects.filter(is_active=True).order_by("name")

    existing_records = TeacherAttendance.objects.filter(date=attendance_date_obj)

    if active_session:
        existing_records = existing_records.filter(session=active_session)

    existing_status_map = {
        record.employee_id: record.status
        for record in existing_records
    }

    for employee in employees:
        if employee.id in existing_status_map:
            employee.current_status = existing_status_map.get(employee.id)
        elif holiday_info["is_holiday"]:
            employee.current_status = holiday_info["status"]
        else:
            employee.current_status = "Present"

    is_update = existing_records.exists()

    if request.method == "POST":
        post_date = request.POST.get("attendance_date")
        post_date_obj = parse_date_safe(post_date)
        post_holiday_info = get_holiday_status(post_date_obj)

        if post_holiday_info["is_holiday"] and not post_holiday_info["is_half_day"]:
            messages.warning(request, f"⚠️ {post_holiday_info['title']} আছে। Teacher attendance mark করা যাবে না।")
            return redirect(f"/attendance/teachers/?date={post_date}")

        for employee in employees:
            status = request.POST.get(f"status_{employee.id}", "Present")

            TeacherAttendance.objects.update_or_create(
                employee=employee,
                session=active_session,
                date=post_date_obj,
                defaults={
                    "status": status,
                    "source": "Manual",
                    "within_range": True,
                    "remarks": "Marked by admin panel",
                },
            )

        messages.success(request, "✅ Teacher attendance updated successfully.")
        return redirect(f"/attendance/teachers/?date={post_date}")

    return render(request, "attendance/teacher_attendance.html", {
        "employees": employees,
        "attendance_date": attendance_date,
        "is_update": is_update,
        "holiday_info": holiday_info,
        "active_session": active_session,
    })


@login_required
def teacher_mobile_attendance(request):
    active_session = get_active_session(request)
    emp = getattr(request.user, "employee", None)

    if not emp:
        messages.error(request, "❌ Employee profile not found for this user.")
        return redirect("/teacher-dashboard/")

    today = timezone.now().date()
    holiday_info = get_holiday_status(today)

    today_attendance = TeacherAttendance.objects.filter(
        employee=emp,
        session=active_session,
        date=today,
    ).first()

    if request.method == "POST":
        if holiday_info["is_holiday"] and not holiday_info["is_half_day"]:
            messages.warning(request, f"⚠️ Today is {holiday_info['title']}. Attendance not required.")
            return redirect("teacher_mobile_attendance")

        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")
        address = request.POST.get("address", "")
        selfie = request.FILES.get("selfie")

        if today_attendance:
            messages.warning(request, "⚠️ Your attendance is already marked today.")
            return redirect("teacher_mobile_attendance")

        if not latitude or not longitude:
            messages.error(request, "❌ GPS location not found. Please allow location permission.")
            return redirect("teacher_mobile_attendance")

        if not selfie:
            messages.error(request, "❌ Selfie is required for attendance.")
            return redirect("teacher_mobile_attendance")

        distance = calculate_distance_meters(
            latitude,
            longitude,
            SCHOOL_LATITUDE,
            SCHOOL_LONGITUDE,
        )

        latitude_decimal = decimal_or_none(latitude)
        longitude_decimal = decimal_or_none(longitude)
        distance_decimal = decimal_or_none(distance)

        if distance is None or latitude_decimal is None or longitude_decimal is None:
            messages.error(request, "❌ Invalid GPS location.")
            return redirect("teacher_mobile_attendance")

        within_range = distance <= SCHOOL_RADIUS_METERS

        TeacherAttendance.objects.create(
            employee=emp,
            session=active_session,
            date=today,
            status="Present" if within_range else "Absent",
            latitude=latitude_decimal,
            longitude=longitude_decimal,
            distance_meters=distance_decimal,
            within_range=within_range,
            selfie=selfie,
            address=address,
            device_info=request.META.get("HTTP_USER_AGENT", "")[:255],
            ip_address=get_client_ip(request),
            source="GPS",
            remarks=(
                "Marked from mobile with selfie and GPS"
                if within_range
                else f"Outside school radius. Distance: {distance} meters"
            ),
        )

        if not within_range:
            messages.error(request, f"❌ You are outside school range. Distance: {distance} meters.")
            return redirect("teacher_mobile_attendance")

        messages.success(request, f"✅ Attendance marked successfully. Distance: {distance} meters.")
        return redirect("teacher_mobile_attendance")

    return render(request, "attendance/teacher_mobile_attendance.html", {
        "employee": emp,
        "today": today,
        "today_attendance": today_attendance,
        "holiday_info": holiday_info,
        "school_latitude": SCHOOL_LATITUDE,
        "school_longitude": SCHOOL_LONGITUDE,
        "school_radius_meters": SCHOOL_RADIUS_METERS,
        "active_session": active_session,
    })


# =========================================================
# REPORTS
# =========================================================

@login_required
def student_daily_report(request):
    active_session = get_active_session(request)

    selected_date = request.GET.get("date") or timezone.now().date().isoformat()
    selected_date_obj = parse_date_safe(selected_date)

    selected_class = request.GET.get("class_id", "")
    selected_section = request.GET.get("section", "")
    selected_status = request.GET.get("status", "")
    search = request.GET.get("search", "").strip()

    holiday_info = get_holiday_status(selected_date_obj)

    classes = Class.objects.all().order_by("class_name")

    records = StudentAttendance.objects.select_related(
        "student",
        "student__class_assigned",
        "session",
    ).filter(
        date=selected_date_obj
    )

    if active_session:
        records = records.filter(session=active_session)

    if selected_class:
        records = records.filter(
            student__class_assigned_id=selected_class
        )

    if selected_section:
        records = records.filter(
            student__section=selected_section
        )

    if selected_status:
        records = records.filter(
            status=selected_status
        )

    if search:
        records = records.filter(
            Q(student__student_name__icontains=search) |
            Q(student__student_id__icontains=search) |
            Q(student__registration_no__icontains=search)
        )

    present_count = records.filter(
        status="Present"
    ).count()

    absent_count = records.filter(
        status="Absent"
    ).count()

    late_count = records.filter(
        status="Late"
    ).count()

    total_count = records.count()

    records = sorted(
        list(records),
        key=lambda record: student_numeric_sort_key(record.student),
    )

    return render(
        request,
        "attendance/student_daily_report.html",
        {
            "records": records,
            "classes": classes,

            "selected_date": selected_date,
            "selected_class": selected_class,
            "selected_section": selected_section,
            "selected_status": selected_status,
            "search": search,

            "holiday_info": holiday_info,
            "active_session": active_session,

            "present_count": present_count,
            "absent_count": absent_count,
            "late_count": late_count,
            "total_count": total_count,
        }
    )

@login_required
def teacher_daily_report(request):
    active_session = get_active_session(request)

    selected_date = request.GET.get("date") or timezone.now().date().isoformat()
    selected_date_obj = parse_date_safe(selected_date)

    selected_status = request.GET.get("status", "")
    search = request.GET.get("search", "").strip()

    holiday_info = get_holiday_status(selected_date_obj)

    records = TeacherAttendance.objects.select_related(
        "employee",
        "session"
    ).filter(
        date=selected_date_obj
    )

    if active_session:
        records = records.filter(
            session=active_session
        )

    if selected_status:
        records = records.filter(
            status=selected_status
        )

    if search:
        records = records.filter(
            Q(employee__name__icontains=search) |
            Q(employee__employee_id__icontains=search)
        )

    present_count = records.filter(
        status="Present"
    ).count()

    absent_count = records.filter(
        status="Absent"
    ).count()

    late_count = records.filter(
        status="Late"
    ).count()

    total_count = records.count()

    records = records.order_by(
        "employee__name"
    )

    return render(
        request,
        "attendance/teacher_daily_report.html",
        {
            "records": records,
            "selected_date": selected_date,
            "holiday_info": holiday_info,
            "active_session": active_session,

            "selected_status": selected_status,
            "search": search,

            "present_count": present_count,
            "absent_count": absent_count,
            "late_count": late_count,
            "total_count": total_count,
        }
    )


@login_required
def student_percentage_report(request):
    active_session = get_active_session(request)

    selected_class = request.GET.get("class_id")
    selected_section = request.GET.get("section")

    classes = Class.objects.all().order_by("class_name")

    students = Student.objects.select_related("class_assigned", "current_session").filter(is_active=True)

    if active_session:
        students = students.filter(current_session=active_session)

    if selected_class:
        students = students.filter(class_assigned_id=selected_class)

    if selected_section:
        students = students.filter(section=selected_section)

    students = numeric_sort_students(students)

    report_rows = []

    for student in students:
        qs = StudentAttendance.objects.filter(student=student)

        if active_session:
            qs = qs.filter(session=active_session)

        total_days = qs.count()
        present_days = qs.filter(status="Present").count()
        late_days = qs.filter(status="Late").count()
        absent_days = qs.filter(status="Absent").count()

        percentage = round((present_days / total_days) * 100, 2) if total_days > 0 else 0

        report_rows.append({
            "student": student,
            "total_days": total_days,
            "present_days": present_days,
            "late_days": late_days,
            "absent_days": absent_days,
            "percentage": percentage,
        })

    return render(request, "attendance/student_percentage_report.html", {
        "report_rows": report_rows,
        "classes": classes,
        "selected_class": selected_class,
        "selected_section": selected_section,
        "active_session": active_session,
    })


@login_required
def student_monthly_report(request):
    active_session = get_active_session(request)
    classes = Class.objects.all().order_by("class_name")

    selected_class = request.GET.get("class_id")
    selected_section = request.GET.get("section")
    date_str = request.GET.get("date") or timezone.now().date().isoformat()

    start_date, end_date = get_month_start_end(date_str)
    date_headers = list(daterange(start_date, end_date))

    students = Student.objects.select_related("class_assigned", "current_session").filter(is_active=True)

    if active_session:
        students = students.filter(current_session=active_session)

    if selected_class:
        students = students.filter(class_assigned_id=selected_class)

    if selected_section:
        students = students.filter(section=selected_section)

    students = numeric_sort_students(students)

    attendance_records = StudentAttendance.objects.filter(
        date__range=[start_date, end_date],
        student__in=students,
    )

    if active_session:
        attendance_records = attendance_records.filter(session=active_session)

    attendance_map = {
        (record.student_id, record.date): record.status
        for record in attendance_records
    }

    report_rows = []

    for student in students:
        present = 0
        absent = 0
        late = 0
        holiday_days = 0
        working_days = 0
        day_statuses = []

        for day in date_headers:
            holiday_info = get_holiday_status(day)
            status = attendance_map.get((student.id, day))

            if holiday_info["is_holiday"]:
                holiday_days += 1
                short = "HD" if holiday_info["is_half_day"] else "H"

            elif status == "Present":
                present += 1
                working_days += 1
                short = "P"

            elif status == "Absent":
                absent += 1
                working_days += 1
                short = "A"

            elif status == "Late":
                late += 1
                working_days += 1
                short = "L"

            else:
                short = "-"

            day_statuses.append(short)

        percentage = round((present / working_days) * 100, 2) if working_days > 0 else 0

        report_rows.append({
            "student": student,
            "day_statuses": day_statuses,
            "present": present,
            "absent": absent,
            "late": late,
            "holiday_days": holiday_days,
            "working_days": working_days,
            "percentage": percentage,
        })

    return render(request, "attendance/student_monthly_report.html", {
        "classes": classes,
        "selected_class": selected_class,
        "selected_section": selected_section,
        "date": start_date.isoformat(),
        "month_start": start_date,
        "month_end": end_date,
        "date_headers": date_headers,
        "report_rows": report_rows,
        "active_session": active_session,
    })


@login_required
def attendance_graph(request):
    active_session = get_active_session(request)

    selected_class = request.GET.get("class_id")
    selected_section = request.GET.get("section")
    selected_month = request.GET.get("month")

    classes = Class.objects.all().order_by("class_name")

    students = Student.objects.select_related("class_assigned", "current_session").filter(is_active=True)

    if active_session:
        students = students.filter(current_session=active_session)

    if selected_class:
        students = students.filter(class_assigned_id=selected_class)

    if selected_section:
        students = students.filter(section=selected_section)

    attendance_qs = StudentAttendance.objects.filter(student__in=students)

    if active_session:
        attendance_qs = attendance_qs.filter(session=active_session)

    if selected_month:
        attendance_qs = attendance_qs.filter(date__month=selected_month)

    summary = attendance_qs.values("status").annotate(total=Count("id"))

    present = 0
    absent = 0
    late = 0

    for item in summary:
        if item["status"] == "Present":
            present = item["total"]
        elif item["status"] == "Absent":
            absent = item["total"]
        elif item["status"] == "Late":
            late = item["total"]

    student_data = []

    for student in numeric_sort_students(students)[:10]:
        qs = StudentAttendance.objects.filter(student=student)

        if active_session:
            qs = qs.filter(session=active_session)

        total = qs.count()
        present_count = qs.filter(status="Present").count()

        student_data.append({
            "name": student.student_name,
            "roll_no": getattr(student, "roll_no", ""),
            "present": present_count,
            "total": total,
        })

    return render(request, "attendance/attendance_graph.html", {
        "classes": classes,
        "selected_class": selected_class,
        "selected_section": selected_section,
        "selected_month": selected_month,
        "present": present,
        "absent": absent,
        "late": late,
        "student_data": json.dumps(student_data),
        "active_session": active_session,
    })


@login_required
def student_attendance_by_class(request, class_name):
    active_session = get_active_session(request)
    selected_section = request.GET.get("section")

    students = Student.objects.filter(
        class_assigned__class_name__iexact=class_name,
        is_active=True,
    )

    if active_session:
        students = students.filter(current_session=active_session)

    if selected_section:
        students = students.filter(section=selected_section)

    students = numeric_sort_students(students)

    today = timezone.now().date()
    holiday_info = get_holiday_status(today)

    data = []

    for student in students:
        attendance = StudentAttendance.objects.filter(
            student=student,
            session=active_session,
            date=today,
        ).first()

        if holiday_info["is_holiday"]:
            status = "Half Day" if holiday_info["is_half_day"] else "Holiday"
        elif attendance:
            status = attendance.status
        else:
            status = "Not Marked"

        data.append({
            "student": student,
            "status": status,
        })

    return render(request, "attendance/student_attendance_by_class.html", {
        "data": data,
        "class_name": class_name,
        "selected_section": selected_section,
        "holiday_info": holiday_info,
        "active_session": active_session,
    })

# =========================================================
# ATTENDANCE REGISTER
# =========================================================
@login_required
def attendance_register(request):
    active_session = get_active_session(request)
    classes = Class.objects.all().order_by("class_name")

    selected_class = request.GET.get("class_id")
    selected_section = request.GET.get("section")
    date_str = request.GET.get("date") or timezone.now().date().replace(day=1).isoformat()

    date = parse_date_safe(date_str)

    date_headers = [date]
    report_rows = []
    selected_class_obj = None

    # ✅ Class select na korle student load hobena
    if not selected_class:
        return render(request, "attendance/attendance_register.html", {
            "classes": classes,
            "selected_class": selected_class,
            "selected_section": selected_section,
            "selected_class_obj": selected_class_obj,
            "date": date_str,
            "date_headers": date_headers,
            "report_rows": report_rows,
            "active_session": active_session,
            "message": "Please select a class to load attendance register.",
        })

    students = Student.objects.select_related(
        "class_assigned",
        "current_session"
    ).filter(
        is_active=True,
        class_assigned_id=selected_class
    )

    if active_session:
        students = students.filter(current_session=active_session)

    if selected_section:
        students = students.filter(section=selected_section)

    selected_class_obj = Class.objects.filter(id=selected_class).first()

    # ✅ Numeric roll order
    students = sorted(
        students,
        key=lambda s: (
            str(getattr(s, "section", "") or ""),
            int(getattr(s, "roll_no", 0) or 0),
            str(getattr(s, "student_name", "") or "")
        )
    )

    attendance_records = StudentAttendance.objects.filter(
        date=date,
        student__in=students
    )

    if active_session:
        attendance_records = attendance_records.filter(session=active_session)

    attendance_map = {
        record.student_id: record.status
        for record in attendance_records
    }

    holiday_info = get_holiday_status(date)

    for student in students:
        status = attendance_map.get(student.id)

        if holiday_info["is_holiday"]:
            short = "HD" if holiday_info["is_half_day"] else "H"
            holiday_days = 1
            present = absent = late = 0
        elif status == "Present":
            short = "P"
            present, absent, late, holiday_days = 1, 0, 0, 0
        elif status == "Absent":
            short = "A"
            present, absent, late, holiday_days = 0, 1, 0, 0
        elif status == "Late":
            short = "L"
            present, absent, late, holiday_days = 0, 0, 1, 0
        else:
            short = "-"
            present = absent = late = holiday_days = 0

        report_rows.append({
            "student": student,
            "day_statuses": [short],
            "present": present,
            "absent": absent,
            "late": late,
            "holiday_days": holiday_days,
        })

    return render(request, "attendance/attendance_register.html", {
        "classes": classes,
        "selected_class": selected_class,
        "selected_section": selected_section,
        "selected_class_obj": selected_class_obj,
        "date": date_str,
        "date_headers": date_headers,
        "report_rows": report_rows,
        "active_session": active_session,
    })

# =========================================================
# ALERTS
# =========================================================

@login_required
def attendance_alert_list(request):
    active_session = get_active_session(request)
    status = request.GET.get("status", "Pending")

    alerts = AttendanceAlert.objects.select_related(
        "student",
        "employee",
        "session",
    ).all().order_by("-created_at")

    if active_session:
        alerts = alerts.filter(session=active_session)

    if status:
        alerts = alerts.filter(approval_status=status)

    return render(request, "attendance/alert_list.html", {
        "alerts": alerts,
        "selected_status": status,
        "active_session": active_session,
    })


@login_required
def attendance_alert_approve(request, pk):
    alert = get_object_or_404(AttendanceAlert, pk=pk)

    alert.approval_status = "Approved"

    phone = None
    message = alert.message_en

    if alert.alert_type == "Student" and alert.student:
        phone = getattr(alert.student, "phone", None)
        message = alert.message_bn + " / " + alert.message_en

    elif alert.alert_type == "Teacher" and alert.employee:
        phone = getattr(alert.employee, "phone", None)
        message = alert.message_bn + " / " + alert.message_en

    whatsapp_sent = False
    sms_sent = False

    if phone:
        try:
            whatsapp_sent = send_whatsapp_message(phone, message)
            sms_sent = send_sms_message(phone, message)
        except Exception:
            whatsapp_sent = False
            sms_sent = False

    alert.whatsapp_sent = bool(whatsapp_sent)
    alert.sms_sent = bool(sms_sent)
    alert.save(update_fields=["approval_status", "whatsapp_sent", "sms_sent"])

    if phone and (whatsapp_sent or sms_sent):
        messages.success(request, "✅ Alert approved & message sent.")
    elif phone:
        messages.warning(request, "⚠️ Alert approved but message sending failed.")
    else:
        messages.success(request, "✅ Alert approved.")

    return redirect("attendance_alert_list")


@login_required
def attendance_alert_reject(request, pk):
    alert = get_object_or_404(AttendanceAlert, pk=pk)

    alert.approval_status = "Rejected"
    alert.save(update_fields=["approval_status"])

    messages.warning(request, "⚠️ Alert rejected.")
    return redirect("attendance_alert_list")


# =========================================================
# HOLIDAYS
# =========================================================

@login_required
def holiday_list(request):
    holidays = Holiday.objects.all().order_by("-date")

    return render(request, "attendance/holiday_list.html", {
        "holidays": holidays,
    })


@login_required
def holiday_add(request):
    if request.method == "POST":
        form = HolidayForm(request.POST)

        if form.is_valid():
            holiday = form.save()
            messages.success(request, f"✅ Holiday added successfully: {holiday.title}")
            return redirect("holiday_list")
    else:
        form = HolidayForm()

    return render(request, "attendance/holiday_form.html", {
        "form": form,
        "page_title": "Add Holiday",
    })


@login_required
def holiday_edit(request, pk):
    holiday = get_object_or_404(Holiday, pk=pk)

    if request.method == "POST":
        form = HolidayForm(request.POST, instance=holiday)

        if form.is_valid():
            form.save()
            messages.success(request, "✅ Holiday updated successfully.")
            return redirect("holiday_list")
    else:
        form = HolidayForm(instance=holiday)

    return render(request, "attendance/holiday_form.html", {
        "form": form,
        "page_title": "Edit Holiday",
    })


@login_required
def holiday_delete(request, pk):
    holiday = get_object_or_404(Holiday, pk=pk)

    if request.method == "POST":
        holiday.delete()
        messages.success(request, "🗑 Holiday deleted successfully.")
        return redirect("holiday_list")

    return render(request, "attendance/holiday_confirm_delete.html", {
        "holiday": holiday,
    })


# =========================================================
# ATTENDANCE RESET
# =========================================================

@login_required
def attendance_reset(request):
    active_session = get_active_session(request)
    emp = getattr(request.user, "employee", None)

    if not is_erp_admin_user(request, emp):
        messages.error(request, "❌ Only Admin can reset attendance.")
        return redirect("/dashboard/")

    classes = Class.objects.all().order_by("class_name")

    from_date = request.POST.get("from_date") or request.GET.get("from_date")
    to_date = request.POST.get("to_date") or request.GET.get("to_date")
    selected_class = request.POST.get("class_id") or request.GET.get("class_id")
    selected_section = request.POST.get("section") or request.GET.get("section")

    reset_count = 0
    records = StudentAttendance.objects.none()

    if from_date and to_date:
        from_date_obj = parse_date_safe(from_date)
        to_date_obj = parse_date_safe(to_date)

        if from_date_obj > to_date_obj:
            messages.error(request, "❌ From Date cannot be after To Date.")
            return redirect("attendance_reset")

        records = StudentAttendance.objects.select_related(
            "student",
            "student__class_assigned",
            "session",
        ).filter(date__range=[from_date_obj, to_date_obj])

        if active_session:
            records = records.filter(session=active_session)

        if selected_class:
            records = records.filter(student__class_assigned_id=selected_class)

        if selected_section:
            records = records.filter(student__section=selected_section)

        reset_count = records.count()

    if request.method == "POST" and request.POST.get("confirm_reset") == "YES":
        if not from_date or not to_date:
            messages.error(request, "❌ Please select date range.")
            return redirect("attendance_reset")

        deleted_count = records.count()
        records.delete()

        messages.success(request, f"✅ {deleted_count} attendance record(s) reset successfully.")
        return redirect("attendance_reset")

    return render(request, "attendance/attendance_reset.html", {
        "classes": classes,
        "from_date": from_date,
        "to_date": to_date,
        "selected_class": selected_class,
        "selected_section": selected_section,
        "reset_count": reset_count,
        "active_session": active_session,
    })


# =========================================================
# HOLIDAY RESET
# =========================================================

@login_required
def holiday_reset(request):
    emp = getattr(request.user, "employee", None)

    if not is_erp_admin_user(request, emp):
        messages.error(request, "❌ Only Admin can reset holidays.")
        return redirect("/dashboard/")

    from_date = request.POST.get("from_date") or request.GET.get("from_date")
    to_date = request.POST.get("to_date") or request.GET.get("to_date")

    holidays = Holiday.objects.none()
    reset_count = 0

    if from_date and to_date:
        from_date_obj = parse_date_safe(from_date)
        to_date_obj = parse_date_safe(to_date)

        if from_date_obj > to_date_obj:
            messages.error(request, "❌ From Date cannot be after To Date.")
            return redirect("holiday_reset")

        holidays = Holiday.objects.filter(date__range=[from_date_obj, to_date_obj]).order_by("date")
        reset_count = holidays.count()

    if request.method == "POST" and request.POST.get("confirm_reset") == "YES":
        deleted_count = holidays.count()
        holidays.delete()

        messages.success(request, f"✅ {deleted_count} holiday record(s) reset successfully.")
        return redirect("holiday_reset")

    return render(request, "attendance/holiday_reset.html", {
        "from_date": from_date,
        "to_date": to_date,
        "holidays": holidays,
        "reset_count": reset_count,
    })
