from math import radians, sin, cos, sqrt, atan2
from datetime import time, timedelta

from django.contrib.auth import authenticate
from django.core.exceptions import FieldError
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_date

from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from students.models import Student
from teachers.models import Employee
from attendance.models import StudentAttendance, TeacherAttendance
from homework.models import Homework
from notices.models import Notice

from exams.models import (
    Exam,
    ExamRoutine,
    ExamResult,
    StudentResultSummary,
)

from .serializers import (
    StudentSerializer,
    StudentAttendanceSerializer,
    TeacherAttendanceSerializer,
    HomeworkSerializer,
    ExamSerializer,
    ExamRoutineSerializer,
    ExamResultSerializer,
    StudentResultSummarySerializer,
    NoticeSerializer,
)


SCHOOL_LATITUDE = 26.018405
SCHOOL_LONGITUDE = 88.009819
ALLOWED_RADIUS_METERS = 150

SCHOOL_START_TIME = time(8, 0)
LATE_AFTER_TIME = time(8, 15)


def calculate_distance_meters(lat1, lon1, lat2, lon2):
    earth_radius = 6371000
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return earth_radius * c


def get_request_date(request, source="query"):
    if source == "data":
        date_value = request.data.get("date")
    else:
        date_value = request.GET.get("date")

    if not date_value:
        return timezone.now().date()

    parsed = parse_date(str(date_value))
    if parsed:
        return parsed

    return timezone.now().date()


def student_class_filter_queryset(class_name):
    try:
        return Student.objects.filter(
            class_assigned__name__iexact=class_name,
            is_active=True
        ).order_by("roll_no", "id")
    except FieldError:
        return Student.objects.filter(
            class_assigned__class_name__iexact=class_name,
            is_active=True
        ).order_by("roll_no", "id")


def get_student_class_name(student):
    if not student.class_assigned:
        return ""

    if hasattr(student.class_assigned, "name"):
        return student.class_assigned.name

    if hasattr(student.class_assigned, "class_name"):
        return student.class_assigned.class_name

    return str(student.class_assigned)


# =========================================================
# API HOME
# =========================================================

@api_view(["GET"])
@permission_classes([AllowAny])
def api_home(request):
    return Response({
        "status": "success",
        "message": "AL RAHMAN MISSION Mobile API is working",
        "version": "1.0"
    })


# =========================================================
# AUTH API
# =========================================================

@api_view(["POST"])
@permission_classes([AllowAny])
def login_api(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({
            "status": "error",
            "message": "Username and password are required"
        }, status=400)

    user = authenticate(username=username, password=password)

    if user is None:
        return Response({
            "status": "error",
            "message": "Invalid username or password"
        }, status=401)

    if not user.is_active:
        return Response({
            "status": "error",
            "message": "User account is inactive"
        }, status=403)

    token, created = Token.objects.get_or_create(user=user)

    return Response({
        "status": "success",
        "message": "Login successful",
        "token": token.key,
        "username": user.username,
        "user": {
            "id": user.id,
            "username": user.username,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
        }
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_api(request):
    try:
        request.user.auth_token.delete()
    except Exception:
        pass

    return Response({
        "status": "success",
        "message": "Logout successful"
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profile_api(request):
    user = request.user

    return Response({
        "status": "success",
        "user": {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
        }
    })


# =========================================================
# DASHBOARD API
# =========================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_summary_api(request):
    today = timezone.now().date()

    total_students = Student.objects.filter(is_active=True).count()
    total_teachers = Employee.objects.filter(is_active=True).count()

    today_student_attendance = StudentAttendance.objects.filter(date=today)
    today_teacher_attendance = TeacherAttendance.objects.filter(date=today)

    return Response({
        "status": "success",
        "date": str(today),
        "summary": {
            "total_students": total_students,
            "total_teachers": total_teachers,
            "student_attendance": {
                "present": today_student_attendance.filter(status="Present").count(),
                "absent": today_student_attendance.filter(status="Absent").count(),
                "late": today_student_attendance.filter(status="Late").count(),
                "total_marked": today_student_attendance.count(),
            },
            "teacher_attendance": {
                "present": today_teacher_attendance.filter(status="Present").count(),
                "absent": today_teacher_attendance.filter(status="Absent").count(),
                "late": today_teacher_attendance.filter(status="Late").count(),
                "total_marked": today_teacher_attendance.count(),
            }
        }
    })


# =========================================================
# STUDENT API
# =========================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_list_api(request):
    search = request.GET.get("search", "")
    class_name = request.GET.get("class", "")

    students = Student.objects.filter(is_active=True).order_by("id")

    if search:
        students = students.filter(student_name__icontains=search)

    if class_name:
        students = student_class_filter_queryset(class_name)
        if search:
            students = students.filter(student_name__icontains=search)

    serializer = StudentSerializer(
        students,
        many=True,
        context={"request": request}
    )

    return Response({
        "status": "success",
        "count": students.count(),
        "results": serializer.data
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_detail_api(request, student_id):
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return Response({
            "status": "error",
            "message": "Student not found"
        }, status=404)

    serializer = StudentSerializer(
        student,
        context={"request": request}
    )

    return Response({
        "status": "success",
        "student": serializer.data
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def students_by_class_api(request, class_name):
    date = get_request_date(request, source="query")
    students = student_class_filter_queryset(class_name)

    data = []

    for student in students:
        attendance = StudentAttendance.objects.filter(
            student=student,
            date=date
        ).first()

        data.append({
            "id": student.id,
            "student_id": student.student_id,
            "name": student.student_name,
            "roll_no": student.roll_no,
            "class_name": get_student_class_name(student),
            "status": attendance.status if attendance else "Present",
            "remarks": attendance.remarks if attendance else "",
            "already_marked": True if attendance else False,
        })

    return Response({
        "status": "success",
        "class_name": class_name,
        "date": str(date),
        "count": students.count(),
        "students": data
    })


# =========================================================
# STUDENT ATTENDANCE API
# =========================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_attendance_list_api(request):
    date = request.GET.get("date")
    class_name = request.GET.get("class")

    records = StudentAttendance.objects.select_related("student").all().order_by("-id")

    if date:
        parsed_date = parse_date(str(date))
        if parsed_date:
            records = records.filter(date=parsed_date)

    if class_name:
        try:
            records = records.filter(student__class_assigned__name__iexact=class_name)
        except FieldError:
            records = records.filter(student__class_assigned__class_name__iexact=class_name)

    records = records[:200]

    serializer = StudentAttendanceSerializer(
        records,
        many=True,
        context={"request": request}
    )

    return Response({
        "status": "success",
        "count": len(serializer.data),
        "results": serializer.data
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_student_attendance_api(request):
    student_id = request.data.get("student_id")
    status_value = request.data.get("status")
    remarks = request.data.get("remarks", "")
    date = get_request_date(request, source="data")

    if not student_id or not status_value:
        return Response({
            "status": "error",
            "message": "student_id and status are required"
        }, status=400)

    if status_value not in ["Present", "Absent", "Late"]:
        return Response({
            "status": "error",
            "message": "Invalid status. Use Present, Absent or Late"
        }, status=400)

    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return Response({
            "status": "error",
            "message": "Student not found"
        }, status=404)

    attendance, created = StudentAttendance.objects.update_or_create(
        student=student,
        date=date,
        defaults={
            "status": status_value,
            "remarks": remarks,
        }
    )

    return Response({
        "status": "success",
        "message": "Student attendance saved successfully",
        "created": created,
        "attendance_id": attendance.id,
        "date": str(date),
        "status_value": status_value,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def student_bulk_attendance_mark_api(request):
    attendance_list = request.data.get("attendance", [])
    date = get_request_date(request, source="data")

    if not attendance_list:
        return Response({
            "status": "error",
            "message": "No attendance data provided"
        }, status=400)

    saved_count = 0
    skipped_count = 0

    for item in attendance_list:
        student_id = item.get("student_id")
        status_value = item.get("status", "Present")
        remarks = item.get("remarks", "")

        if not student_id:
            skipped_count += 1
            continue

        if status_value not in ["Present", "Absent", "Late"]:
            skipped_count += 1
            continue

        try:
            student = Student.objects.get(id=student_id)

            StudentAttendance.objects.update_or_create(
                student=student,
                date=date,
                defaults={
                    "status": status_value,
                    "remarks": remarks,
                }
            )

            saved_count += 1

        except Student.DoesNotExist:
            skipped_count += 1
            continue

    return Response({
        "status": "success",
        "message": f"{saved_count} students attendance marked successfully",
        "date": str(date),
        "saved_count": saved_count,
        "skipped_count": skipped_count,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_attendance_report_api(request, student_id):
    records = StudentAttendance.objects.filter(
        student_id=student_id
    ).select_related("student").order_by("-date")

    serializer = StudentAttendanceSerializer(
        records,
        many=True,
        context={"request": request}
    )

    return Response({
        "status": "success",
        "student_id": student_id,
        "count": records.count(),
        "results": serializer.data
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_attendance_summary_api(request):
    date = get_request_date(request, source="query")
    records = StudentAttendance.objects.filter(date=date)

    return Response({
        "status": "success",
        "date": str(date),
        "summary": {
            "present": records.filter(status="Present").count(),
            "absent": records.filter(status="Absent").count(),
            "late": records.filter(status="Late").count(),
            "total": records.count(),
        }
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_attendance_percentage_api(request, student_id):
    records = StudentAttendance.objects.filter(student_id=student_id)

    total = records.count()
    present = records.filter(status="Present").count()
    late = records.filter(status="Late").count()
    absent = records.filter(status="Absent").count()

    percentage = 0

    if total > 0:
        percentage = round(((present + late) / total) * 100, 2)

    return Response({
        "status": "success",
        "student_id": student_id,
        "summary": {
            "total": total,
            "present": present,
            "late": late,
            "absent": absent,
            "percentage": percentage,
        }
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_attendance_register_api(request):
    class_name = request.GET.get("class", "")
    start_date = parse_date(request.GET.get("start_date", ""))
    end_date = parse_date(request.GET.get("end_date", ""))

    if not start_date or not end_date:
        today = timezone.now().date()
        start_date = today
        end_date = today

    if class_name:
        students = student_class_filter_queryset(class_name)
    else:
        students = Student.objects.filter(is_active=True).order_by("class_assigned", "roll_no", "id")

    records = StudentAttendance.objects.filter(
        date__range=[start_date, end_date],
        student__in=students
    ).select_related("student")

    record_map = {}
    for r in records:
        record_map[(r.student_id, r.date)] = r.status

    dates = []
    current = start_date

    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)

    rows = []

    for student in students:
        present = 0
        absent = 0
        late = 0
        day_status = []

        for d in dates:
            status = record_map.get((student.id, d), "-")

            if status == "Present":
                short = "P"
                present += 1
            elif status == "Absent":
                short = "A"
                absent += 1
            elif status == "Late":
                short = "L"
                late += 1
            else:
                short = "-"

            day_status.append({
                "date": str(d),
                "day": d.strftime("%d"),
                "status": short,
            })

        rows.append({
            "id": student.id,
            "student_id": student.student_id,
            "name": student.student_name,
            "roll_no": student.roll_no,
            "class_name": get_student_class_name(student),
            "days": day_status,
            "present": present,
            "absent": absent,
            "late": late,
        })

    return Response({
        "status": "success",
        "class_name": class_name or "All",
        "start_date": str(start_date),
        "end_date": str(end_date),
        "dates": [{"date": str(d), "day": d.strftime("%d")} for d in dates],
        "rows": rows,
    })


# =========================================================
# TEACHER ATTENDANCE API
# =========================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def teacher_attendance_list_api(request):
    date = request.GET.get("date")

    records = TeacherAttendance.objects.select_related("employee").all().order_by("-id")

    if date:
        parsed_date = parse_date(str(date))
        if parsed_date:
            records = records.filter(date=parsed_date)

    records = records[:200]

    serializer = TeacherAttendanceSerializer(
        records,
        many=True,
        context={"request": request}
    )

    return Response({
        "status": "success",
        "count": len(serializer.data),
        "results": serializer.data
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_teacher_attendance_api(request):
    teacher_id = request.data.get("teacher_id")
    date = get_request_date(request, source="data")
    latitude = request.data.get("latitude")
    longitude = request.data.get("longitude")
    remarks = request.data.get("remarks", "")
    selfie = request.FILES.get("selfie")

    if not teacher_id:
        return Response({
            "status": "error",
            "message": "teacher_id is required"
        }, status=400)

    if not latitude or not longitude:
        return Response({
            "status": "error",
            "message": "latitude and longitude are required"
        }, status=400)

    if not selfie:
        return Response({
            "status": "error",
            "message": "Selfie is required for attendance"
        }, status=400)

    try:
        employee = Employee.objects.get(id=teacher_id, is_active=True)
    except Employee.DoesNotExist:
        return Response({
            "status": "error",
            "message": "Teacher not found or inactive"
        }, status=404)

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except ValueError:
        return Response({
            "status": "error",
            "message": "Invalid latitude or longitude"
        }, status=400)

    distance_meters = calculate_distance_meters(
        SCHOOL_LATITUDE,
        SCHOOL_LONGITUDE,
        latitude,
        longitude
    )

    distance_meters = round(distance_meters, 2)
    within_range = distance_meters <= ALLOWED_RADIUS_METERS

    if not within_range:
        return Response({
            "status": "error",
            "message": "You are outside school range. Attendance not allowed.",
            "within_range": False,
            "distance_meters": distance_meters,
            "allowed_radius_meters": ALLOWED_RADIUS_METERS,
        }, status=403)

    current_local_time = timezone.localtime().time()

    if current_local_time > LATE_AFTER_TIME:
        final_status = "Late"
        auto_remarks = "Late attendance from mobile"
    else:
        final_status = "Present"
        auto_remarks = "On time attendance from mobile"

    if remarks:
        auto_remarks = f"{auto_remarks} | {remarks}"

    existing = TeacherAttendance.objects.filter(
        employee=employee,
        date=date
    ).first()

    if existing:
        existing.status = final_status
        existing.latitude = latitude
        existing.longitude = longitude
        existing.distance_meters = distance_meters
        existing.within_range = within_range
        existing.remarks = auto_remarks
        existing.selfie = selfie
        existing.save()

        return Response({
            "status": "success",
            "message": "Teacher attendance updated successfully",
            "already_marked": True,
            "attendance_id": existing.id,
            "employee_id": employee.id,
            "employee_name": employee.name,
            "final_status": final_status,
            "within_range": within_range,
            "distance_meters": distance_meters,
            "marked_time": str(current_local_time),
            "date": str(date),
        })

    attendance = TeacherAttendance.objects.create(
        employee=employee,
        date=date,
        status=final_status,
        latitude=latitude,
        longitude=longitude,
        distance_meters=distance_meters,
        within_range=within_range,
        selfie=selfie,
        remarks=auto_remarks
    )

    return Response({
        "status": "success",
        "message": "Teacher attendance marked successfully",
        "already_marked": False,
        "attendance_id": attendance.id,
        "employee_id": employee.id,
        "employee_name": employee.name,
        "final_status": final_status,
        "within_range": within_range,
        "distance_meters": distance_meters,
        "marked_time": str(current_local_time),
        "date": str(date),
    })


def teacher_attendance_test_page(request):
    return render(request, "mobile_api/teacher_attendance_test.html")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def teacher_attendance_summary_api(request):
    date = get_request_date(request, source="query")
    records = TeacherAttendance.objects.filter(date=date)

    return Response({
        "status": "success",
        "date": str(date),
        "summary": {
            "present": records.filter(status="Present").count(),
            "absent": records.filter(status="Absent").count(),
            "late": records.filter(status="Late").count(),
            "total": records.count(),
        }
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def teacher_attendance_employee_report_api(request, employee_id):
    records = TeacherAttendance.objects.filter(
        employee_id=employee_id
    ).select_related("employee").order_by("-date")

    serializer = TeacherAttendanceSerializer(
        records,
        many=True,
        context={"request": request}
    )

    return Response({
        "status": "success",
        "employee_id": employee_id,
        "count": records.count(),
        "results": serializer.data
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def teacher_attendance_my_report_api(request):
    employee_id = request.GET.get("employee_id")

    if not employee_id:
        return Response({
            "status": "error",
            "message": "employee_id is required"
        }, status=400)

    records = TeacherAttendance.objects.filter(
        employee_id=employee_id
    ).select_related("employee").order_by("-date")

    serializer = TeacherAttendanceSerializer(
        records,
        many=True,
        context={"request": request}
    )

    return Response({
        "status": "success",
        "employee_id": employee_id,
        "count": records.count(),
        "results": serializer.data
    })


# =========================================================
# HOMEWORK API
# =========================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def homework_list_api(request):
    class_name = request.GET.get("class")
    subject = request.GET.get("subject")
    status = request.GET.get("status", "Active")

    homeworks = Homework.objects.select_related(
        "given_by"
    ).all().order_by("-id")

    if class_name:
        homeworks = homeworks.filter(school_class__iexact=class_name)

    if subject:
        homeworks = homeworks.filter(subject__icontains=subject)

    if status:
        homeworks = homeworks.filter(status=status)

    serializer = HomeworkSerializer(
        homeworks,
        many=True,
        context={"request": request}
    )

    return Response({
        "status": "success",
        "count": homeworks.count(),
        "results": serializer.data
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def homework_detail_api(request, homework_id):
    try:
        homework = Homework.objects.select_related(
            "given_by"
        ).get(id=homework_id)
    except Homework.DoesNotExist:
        return Response({
            "status": "error",
            "message": "Homework not found"
        }, status=404)

    serializer = HomeworkSerializer(
        homework,
        context={"request": request}
    )

    return Response({
        "status": "success",
        "homework": serializer.data
    })


# =========================================================
# EXAM API
# =========================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def exam_list_api(request):
    try:
        exams = Exam.objects.filter(is_active=True).order_by("-id")
    except FieldError:
        exams = Exam.objects.all().order_by("-id")

    serializer = ExamSerializer(
        exams,
        many=True,
        context={"request": request}
    )

    return Response({
        "status": "success",
        "count": exams.count(),
        "results": serializer.data
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def exam_routine_api(request):
    exam_id = request.GET.get("exam")
    class_name = request.GET.get("class")
    subject = request.GET.get("subject")

    routines = ExamRoutine.objects.select_related("exam").all().order_by(
        "-exam__id",
        "date",
        "start_time"
    )

    if exam_id:
        routines = routines.filter(exam_id=exam_id)

    if class_name:
        routines = routines.filter(school_class__iexact=class_name)

    if subject:
        routines = routines.filter(subject__icontains=subject)

    serializer = ExamRoutineSerializer(
        routines,
        many=True,
        context={"request": request}
    )

    return Response({
        "status": "success",
        "count": routines.count(),
        "results": serializer.data
    })


# =========================================================
# EXAM RESULT API
# =========================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_result_api(request):
    student_id = request.GET.get("student_id")
    exam_id = request.GET.get("exam")

    results = ExamResult.objects.select_related(
        "student",
        "exam"
    ).all().order_by("subject")

    if student_id:
        results = results.filter(student_id=student_id)

    if exam_id:
        results = results.filter(exam_id=exam_id)

    serializer = ExamResultSerializer(
        results,
        many=True,
        context={"request": request}
    )

    return Response({
        "status": "success",
        "count": results.count(),
        "results": serializer.data
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def result_summary_api(request):
    student_id = request.GET.get("student_id")
    exam_id = request.GET.get("exam")

    summaries = StudentResultSummary.objects.select_related(
        "student",
        "exam"
    ).all().order_by("rank")

    if student_id:
        summaries = summaries.filter(student_id=student_id)

    if exam_id:
        summaries = summaries.filter(exam_id=exam_id)

    serializer = StudentResultSummarySerializer(
        summaries,
        many=True,
        context={"request": request}
    )

    return Response({
        "status": "success",
        "count": summaries.count(),
        "results": serializer.data
    })


# =========================================================
# NOTICE API
# =========================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notice_list_api(request):
    notice_type = request.GET.get("type")
    target = request.GET.get("target")
    class_name = request.GET.get("class")
    pinned = request.GET.get("pinned")

    notices = Notice.objects.select_related("published_by").filter(
        status="Active"
    ).order_by("-is_pinned", "-id")

    if notice_type:
        notices = notices.filter(notice_type__iexact=notice_type)

    if target:
        notices = notices.filter(target__iexact=target)

    if class_name:
        notices = notices.filter(school_class__iexact=class_name)

    if pinned == "1":
        notices = notices.filter(is_pinned=True)

    serializer = NoticeSerializer(
        notices,
        many=True,
        context={"request": request}
    )

    return Response({
        "status": "success",
        "count": notices.count(),
        "results": serializer.data
    })


# =========================================================
# MARKS ENTRY API
# =========================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def marks_entry_api(request):
    student_id = request.data.get("student_id")
    exam_id = request.data.get("exam_id")
    subject = request.data.get("subject")

    written_marks = request.data.get("written_marks", 0)
    oral_marks = request.data.get("oral_marks", 0)
    max_marks = request.data.get("max_marks", 100)

    remarks = request.data.get("remarks", "")

    if not student_id or not exam_id or not subject:
        return Response({
            "status": "error",
            "message": "student_id, exam_id and subject are required"
        }, status=400)

    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return Response({
            "status": "error",
            "message": "Student not found"
        }, status=404)

    try:
        exam = Exam.objects.get(id=exam_id)
    except Exam.DoesNotExist:
        return Response({
            "status": "error",
            "message": "Exam not found"
        }, status=404)

    try:
        written_marks = int(written_marks)
        oral_marks = int(oral_marks)
        max_marks = int(max_marks)
    except ValueError:
        return Response({
            "status": "error",
            "message": "Marks must be numeric"
        }, status=400)

    result, created = ExamResult.objects.update_or_create(
        student=student,
        exam=exam,
        subject=subject,
        defaults={
            "written_marks": written_marks,
            "oral_marks": oral_marks,
            "max_marks": max_marks,
            "remarks": remarks,
        }
    )

    return Response({
        "status": "success",
        "created": created,
        "message": "Marks saved successfully",
        "result": {
            "student": student.student_name,
            "exam": exam.name,
            "subject": result.subject,
            "written_marks": result.written_marks,
            "oral_marks": result.oral_marks,
            "total_marks": result.total_marks,
            "percentage": result.percentage,
            "grade": result.grade,
            "result_status": result.status,
        }
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def bulk_marks_entry_api(request):
    marks_data = request.data.get("marks", [])

    if not marks_data:
        return Response({
            "status": "error",
            "message": "No marks data provided"
        }, status=400)

    saved_count = 0
    skipped_count = 0

    for item in marks_data:
        try:
            student_id = item.get("student_id")
            exam_id = item.get("exam_id")
            subject = item.get("subject")

            written_marks = int(item.get("written_marks", 0))
            oral_marks = int(item.get("oral_marks", 0))
            max_marks = int(item.get("max_marks", 100))
            remarks = item.get("remarks", "")

            student = Student.objects.get(id=student_id)
            exam = Exam.objects.get(id=exam_id)

            ExamResult.objects.update_or_create(
                student=student,
                exam=exam,
                subject=subject,
                defaults={
                    "written_marks": written_marks,
                    "oral_marks": oral_marks,
                    "max_marks": max_marks,
                    "remarks": remarks,
                }
            )

            saved_count += 1

        except Exception:
            skipped_count += 1
            continue

    return Response({
        "status": "success",
        "message": "Bulk marks saved successfully",
        "saved_count": saved_count,
        "skipped_count": skipped_count,
    })