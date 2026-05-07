from rest_framework import serializers

from students.models import Student
from attendance.models import StudentAttendance, TeacherAttendance
from homework.models import Homework
from notices.models import Notice
from exams.models import (
    Exam,
    ExamRoutine,
    ExamResult,
    StudentResultSummary,
)


# =========================================================
# STUDENT SERIALIZER
# =========================================================

class StudentSerializer(serializers.ModelSerializer):
    class_name = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = "__all__"

    def get_class_name(self, obj):
        if not getattr(obj, "class_assigned", None):
            return ""

        if hasattr(obj.class_assigned, "name"):
            return obj.class_assigned.name

        if hasattr(obj.class_assigned, "class_name"):
            return obj.class_assigned.class_name

        return str(obj.class_assigned)

    def get_photo_url(self, obj):
        request = self.context.get("request")
        photo = getattr(obj, "photo", None)

        if photo and hasattr(photo, "url"):
            if request:
                return request.build_absolute_uri(photo.url)
            return photo.url

        return ""


# =========================================================
# STUDENT ATTENDANCE SERIALIZER
# =========================================================

class StudentAttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student.student_name",
        read_only=True
    )

    student_id_display = serializers.CharField(
        source="student.student_id",
        read_only=True
    )

    roll_no = serializers.CharField(
        source="student.roll_no",
        read_only=True
    )

    class_name = serializers.SerializerMethodField()

    class Meta:
        model = StudentAttendance
        fields = "__all__"

    def get_class_name(self, obj):
        student = getattr(obj, "student", None)

        if not student or not getattr(student, "class_assigned", None):
            return ""

        if hasattr(student.class_assigned, "name"):
            return student.class_assigned.name

        if hasattr(student.class_assigned, "class_name"):
            return student.class_assigned.class_name

        return str(student.class_assigned)


# =========================================================
# TEACHER ATTENDANCE SERIALIZER
# =========================================================

class TeacherAttendanceSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(
        source="employee.name",
        read_only=True
    )

    employee_id_display = serializers.CharField(
        source="employee.employee_id",
        read_only=True
    )

    designation = serializers.CharField(
        source="employee.designation",
        read_only=True
    )

    selfie_url = serializers.SerializerMethodField()

    class Meta:
        model = TeacherAttendance
        fields = "__all__"

    def get_selfie_url(self, obj):
        request = self.context.get("request")
        selfie = getattr(obj, "selfie", None)

        if selfie and hasattr(selfie, "url"):
            if request:
                return request.build_absolute_uri(selfie.url)
            return selfie.url

        return ""


# =========================================================
# HOMEWORK SERIALIZER
# =========================================================

class HomeworkSerializer(serializers.ModelSerializer):
    given_by_name = serializers.SerializerMethodField()
    employee_id_display = serializers.SerializerMethodField()
    attachment_url = serializers.SerializerMethodField()

    class Meta:
        model = Homework
        fields = "__all__"

    def get_given_by_name(self, obj):
        if obj.given_by:
            return obj.given_by.name
        return ""

    def get_employee_id_display(self, obj):
        if obj.given_by:
            return obj.given_by.employee_id
        return ""

    def get_attachment_url(self, obj):
        request = self.context.get("request")
        attachment = getattr(obj, "attachment", None)

        if attachment and hasattr(attachment, "url"):
            if request:
                return request.build_absolute_uri(attachment.url)
            return attachment.url

        return ""
    
# =========================================================
# EXAM ROUTINE SERIALIZER
# =========================================================

class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = "__all__"


class ExamRoutineSerializer(serializers.ModelSerializer):
    exam_name = serializers.CharField(source="exam.name", read_only=True)
    academic_session = serializers.CharField(source="exam.academic_session", read_only=True)

    class Meta:
        model = ExamRoutine
        fields = "__all__"

# =========================================================
# EXAM RESULT SERIALIZER
# =========================================================

class ExamResultSerializer(serializers.ModelSerializer):

    student_name = serializers.CharField(
        source="student.student_name",
        read_only=True
    )

    student_id_display = serializers.CharField(
        source="student.student_id",
        read_only=True
    )

    exam_name = serializers.CharField(
        source="exam.name",
        read_only=True
    )

    percentage = serializers.ReadOnlyField()
    grade = serializers.ReadOnlyField()
    status = serializers.ReadOnlyField()
    total_marks = serializers.ReadOnlyField()

    class Meta:
        model = ExamResult
        fields = "__all__"


# =========================================================
# RESULT SUMMARY SERIALIZER
# =========================================================

class StudentResultSummarySerializer(serializers.ModelSerializer):

    student_name = serializers.CharField(
        source="student.student_name",
        read_only=True
    )

    student_id_display = serializers.CharField(
        source="student.student_id",
        read_only=True
    )

    exam_name = serializers.CharField(
        source="exam.name",
        read_only=True
    )

    class Meta:
        model = StudentResultSummary
        fields = "__all__"

class NoticeSerializer(serializers.ModelSerializer):
    published_by_name = serializers.SerializerMethodField()
    attachment_url = serializers.SerializerMethodField()

    class Meta:
        model = Notice
        fields = "__all__"

    def get_published_by_name(self, obj):
        if obj.published_by:
            return obj.published_by.name
        return ""

    def get_attachment_url(self, obj):
        request = self.context.get("request")
        attachment = getattr(obj, "attachment", None)

        if attachment and hasattr(attachment, "url"):
            if request:
                return request.build_absolute_uri(attachment.url)
            return attachment.url

        return ""