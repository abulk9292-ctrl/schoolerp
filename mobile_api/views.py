from math import radians, sin, cos, sqrt, atan2
from datetime import time

from django.contrib.auth import authenticate
from django.utils import timezone
from django.shortcuts import render

from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from students.models import Student
from teachers.models import Employee
from attendance.models import StudentAttendance, TeacherAttendance

from .serializers import (
    StudentSerializer,
    StudentAttendanceSerializer,
    TeacherAttendanceSerializer,
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


@api_view(['GET'])
@permission_classes([AllowAny])
def api_home(request):
    return Response({
        "status": "success",
        "message": "Mobile API is working"
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    username = request.data.get('username')
    password = request.data.get('password')

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

    token, created = Token.objects.get_or_create(user=user)

    return Response({
        "status": "success",
        "message": "Login successful",
        "token": token.key,
        "user_id": user.id,
        "username": user.username,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_api(request):
    user = request.user
    return Response({
        "status": "success",
        "user": {
            "id": user.id,
            "username": user.username,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_summary_api(request):
    today = timezone.now().date()

    total_students = Student.objects.count()
    total_teachers = Employee.objects.count()

    today_student_attendance = StudentAttendance.objects.filter(date=today)
    today_teacher_attendance = TeacherAttendance.objects.filter(date=today)

    return Response({
        "status": "success",
        "date": str(today),
        "summary": {
            "total_students": total_students,
            "total_teachers": total_teachers,
            "student_attendance": {
                "present": today_student_attendance.filter(status='Present').count(),
                "absent": today_student_attendance.filter(status='Absent').count(),
                "late": today_student_attendance.filter(status='Late').count(),
                "total_marked": today_student_attendance.count(),
            },
            "teacher_attendance": {
                "present": today_teacher_attendance.filter(status='Present').count(),
                "absent": today_teacher_attendance.filter(status='Absent').count(),
                "late": today_teacher_attendance.filter(status='Late').count(),
                "total_marked": today_teacher_attendance.count(),
            }
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_list_api(request):
    students = Student.objects.all().order_by('id')
    serializer = StudentSerializer(students, many=True)

    return Response({
        "status": "success",
        "count": students.count(),
        "results": serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def students_by_class_api(request, class_name):
    students = Student.objects.filter(
        class_assigned__class_name__iexact=class_name,
        is_active=True
    ).order_by('roll_no', 'id')

    data = []
    for student in students:
        data.append({
            "id": student.id,
            "student_id": student.student_id,
            "name": student.student_name,
            "roll_no": student.roll_no,
            "class_name": student.class_assigned.class_name,
        })

    return Response({
        "status": "success",
        "class_name": class_name,
        "count": students.count(),
        "students": data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_attendance_list_api(request):
    date = request.GET.get('date')

    if date:
        records = StudentAttendance.objects.filter(date=date).order_by('-id')
    else:
        records = StudentAttendance.objects.all().order_by('-id')[:100]

    serializer = StudentAttendanceSerializer(records, many=True)

    return Response({
        "status": "success",
        "count": len(serializer.data),
        "results": serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_student_attendance_api(request):
    student_id = request.data.get('student_id')
    status_value = request.data.get('status')
    remarks = request.data.get('remarks', '')
    date = request.data.get('date')

    if not student_id or not status_value:
        return Response({
            "status": "error",
            "message": "student_id and status are required"
        }, status=400)

    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return Response({
            "status": "error",
            "message": "Student not found"
        }, status=404)

    if not date:
        date = timezone.now().date()

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
        "attendance_id": attendance.id
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def student_bulk_attendance_mark_api(request):
    attendance_list = request.data.get('attendance', [])

    if not attendance_list:
        return Response({
            "status": "error",
            "message": "No attendance data provided"
        }, status=400)

    saved_count = 0
    today = timezone.now().date()

    for item in attendance_list:
        student_id = item.get('student_id')
        status_value = item.get('status', 'Present')
        remarks = item.get('remarks', '')

        if not student_id:
            continue

        try:
            student = Student.objects.get(id=student_id)

            StudentAttendance.objects.update_or_create(
                student=student,
                date=today,
                defaults={
                    'status': status_value,
                    'remarks': remarks,
                }
            )
            saved_count += 1

        except Student.DoesNotExist:
            continue

    return Response({
        "status": "success",
        "message": f"{saved_count} students attendance marked successfully",
        "saved_count": saved_count
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_attendance_report_api(request, student_id):
    records = StudentAttendance.objects.filter(
        student_id=student_id
    ).order_by('-date')

    serializer = StudentAttendanceSerializer(records, many=True)

    return Response({
        "status": "success",
        "student_id": student_id,
        "count": records.count(),
        "results": serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_attendance_summary_api(request):
    date = request.GET.get('date')

    if not date:
        date = timezone.now().date()

    records = StudentAttendance.objects.filter(date=date)

    return Response({
        "status": "success",
        "date": str(date),
        "summary": {
            "present": records.filter(status='Present').count(),
            "absent": records.filter(status='Absent').count(),
            "late": records.filter(status='Late').count(),
            "total": records.count(),
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_attendance_list_api(request):
    date = request.GET.get('date')

    if date:
        records = TeacherAttendance.objects.filter(date=date).order_by('-id')
    else:
        records = TeacherAttendance.objects.all().order_by('-id')[:100]

    serializer = TeacherAttendanceSerializer(records, many=True)

    return Response({
        "status": "success",
        "count": len(serializer.data),
        "results": serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_teacher_attendance_api(request):
    teacher_id = request.data.get('teacher_id')
    date = request.data.get('date')
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')
    remarks = request.data.get('remarks')
    selfie = request.FILES.get('selfie')

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
        employee = Employee.objects.get(id=teacher_id)
    except Employee.DoesNotExist:
        return Response({
            "status": "error",
            "message": "Teacher not found"
        }, status=404)

    if not date:
        date = timezone.now().date()

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
    within_range = distance_meters <= ALLOWED_RADIUS_METERS

    if not within_range:
        return Response({
            "status": "error",
            "message": "You are outside school range. Attendance not allowed.",
            "distance_meters": round(distance_meters, 2)
        }, status=403)

    current_local_time = timezone.localtime().time()

    if current_local_time > LATE_AFTER_TIME:
        final_status = 'Late'
        auto_remarks = 'Late attendance from mobile'
    else:
        final_status = 'Present'
        auto_remarks = 'On time attendance from mobile'

    if remarks:
        auto_remarks = f"{auto_remarks} | {remarks}"

    existing = TeacherAttendance.objects.filter(employee=employee, date=date).first()

    if existing:
        existing.status = final_status
        existing.latitude = latitude
        existing.longitude = longitude
        existing.distance_meters = round(distance_meters, 2)
        existing.within_range = within_range
        existing.remarks = auto_remarks
        existing.selfie = selfie
        existing.save()

        return Response({
            "status": "success",
            "message": "Teacher attendance updated successfully",
            "attendance_id": existing.id,
            "final_status": final_status,
            "within_range": within_range,
            "distance_meters": round(distance_meters, 2),
            "marked_time": str(current_local_time),
        })

    attendance = TeacherAttendance.objects.create(
        employee=employee,
        date=date,
        status=final_status,
        latitude=latitude,
        longitude=longitude,
        distance_meters=round(distance_meters, 2),
        within_range=within_range,
        selfie=selfie,
        remarks=auto_remarks
    )

    return Response({
        "status": "success",
        "message": "Teacher attendance marked successfully",
        "attendance_id": attendance.id,
        "final_status": final_status,
        "within_range": within_range,
        "distance_meters": round(distance_meters, 2),
        "marked_time": str(current_local_time),
    })


def teacher_attendance_test_page(request):
    return render(request, 'mobile_api/teacher_attendance_test.html')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_attendance_summary_api(request):
    date = request.GET.get('date')

    if not date:
        date = timezone.now().date()

    records = TeacherAttendance.objects.filter(date=date)

    return Response({
        "status": "success",
        "date": str(date),
        "summary": {
            "present": records.filter(status='Present').count(),
            "absent": records.filter(status='Absent').count(),
            "late": records.filter(status='Late').count(),
            "total": records.count(),
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_attendance_employee_report_api(request, employee_id):
    records = TeacherAttendance.objects.filter(employee_id=employee_id).order_by('-date')

    serializer = TeacherAttendanceSerializer(records, many=True)

    return Response({
        "status": "success",
        "employee_id": employee_id,
        "count": records.count(),
        "results": serializer.data
    })