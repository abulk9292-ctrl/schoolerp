from django.db import models
from django.utils import timezone

from students.models import Student


# =========================================================
# EXAM SETUP
# =========================================================

class Exam(models.Model):
    name = models.CharField(max_length=150)
    academic_session = models.CharField(max_length=20, blank=True, null=True)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        session = self.academic_session or ""
        return f"{self.name} {session}".strip()


# =========================================================
# EXAM ROUTINE
# =========================================================

class ExamRoutine(models.Model):
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="routines"
    )

    academic_session = models.CharField(max_length=20, blank=True, null=True)

    school_class = models.CharField(max_length=100)
    section = models.CharField(max_length=20, blank=True, null=True)

    subject = models.CharField(max_length=150)

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    total_marks = models.PositiveIntegerField(default=100)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "start_time"]
        unique_together = (
            "exam",
            "academic_session",
            "school_class",
            "section",
            "subject",
            "date",
        )

    def __str__(self):
        return f"{self.exam} - {self.school_class} - {self.subject}"


# =========================================================
# EXAM SUBJECT ASSIGN
# =========================================================

class ExamSubjectAssign(models.Model):
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="subject_assigns"
    )

    academic_session = models.CharField(max_length=20, blank=True, null=True)

    school_class = models.CharField(max_length=100)
    section = models.CharField(max_length=20, blank=True, null=True)
    subject = models.CharField(max_length=150)

    full_marks = models.PositiveIntegerField(default=100)
    pass_marks = models.PositiveIntegerField(default=34)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["school_class", "section", "subject"]
        unique_together = (
            "exam",
            "academic_session",
            "school_class",
            "section",
            "subject",
        )

    def __str__(self):
        return f"{self.exam} - {self.school_class} - {self.subject}"


# =========================================================
# EXAM RESULT
# =========================================================

class ExamResult(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="exam_results"
    )

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="results"
    )

    academic_session = models.CharField(max_length=20, blank=True, null=True)

    section = models.CharField(max_length=20, blank=True, null=True)
    subject = models.CharField(max_length=150)

    written_marks = models.PositiveIntegerField(default=0)
    oral_marks = models.PositiveIntegerField(default=0)
    max_marks = models.PositiveIntegerField(default=100)

    remarks = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["student__roll_no", "student__student_name", "subject"]
        unique_together = (
            "student",
            "exam",
            "academic_session",
            "subject",
        )

    @property
    def total_marks(self):
        return (self.written_marks or 0) + (self.oral_marks or 0)

    @property
    def percentage(self):
        if self.max_marks:
            return round((self.total_marks / self.max_marks) * 100, 2)
        return 0

    @property
    def grade(self):
        percentage = self.percentage

        if percentage >= 90:
            return "AA"
        if percentage >= 80:
            return "A+"
        if percentage >= 60:
            return "A"
        if percentage >= 45:
            return "B+"
        if percentage >= 40:
            return "B"
        if percentage >= 35:
            return "C+"
        if percentage >= 24:
            return "C"
        return "D"

    def __str__(self):
        return f"{self.student} - {self.exam} - {self.subject}"


# =========================================================
# STUDENT RESULT SUMMARY
# =========================================================

class StudentResultSummary(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="result_summaries"
    )

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="student_summaries"
    )

    academic_session = models.CharField(max_length=20, blank=True, null=True)

    total_marks = models.PositiveIntegerField(default=0)
    max_total_marks = models.PositiveIntegerField(default=0)

    percentage = models.FloatField(default=0)
    grade = models.CharField(max_length=10, blank=True, null=True)
    result_status = models.CharField(max_length=20, default="Fail")

    rank = models.PositiveIntegerField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["rank", "-percentage", "-total_marks"]
        unique_together = (
            "student",
            "exam",
            "academic_session",
        )

    def __str__(self):
        return f"{self.student} - {self.exam} - {self.percentage}%"


# =========================================================
# CLASS TEST
# =========================================================

class ClassTest(models.Model):
    class_name = models.CharField(max_length=100)
    section = models.CharField(max_length=20, blank=True, null=True)

    test_name = models.CharField(max_length=150)
    subject = models.CharField(max_length=150, blank=True, null=True)

    exam_date = models.DateField(default=timezone.now)
    total_marks = models.PositiveIntegerField(default=20)

    academic_session = models.CharField(max_length=20, blank=True, null=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-exam_date", "-id"]

    def __str__(self):
        return f"{self.test_name} - {self.class_name} - {self.subject or ''}".strip()


# =========================================================
# CLASS TEST RESULT
# =========================================================

class ClassTestResult(models.Model):
    class_test = models.ForeignKey(
        ClassTest,
        on_delete=models.CASCADE,
        related_name="results"
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="class_test_results"
    )

    academic_session = models.CharField(max_length=20, blank=True, null=True)

    marks_obtained = models.FloatField(default=0)
    remarks = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["student__roll_no", "student__student_name"]
        unique_together = (
            "class_test",
            "student",
            "academic_session",
        )

    @property
    def percentage(self):
        total = self.class_test.total_marks if self.class_test else 0
        if total:
            return round((self.marks_obtained / total) * 100, 2)
        return 0

    def __str__(self):
        return f"{self.student} - {self.class_test} - {self.marks_obtained}"


# =========================================================
# CLASS TEST SUBJECT MARK
# =========================================================

class ClassTestSubjectMark(models.Model):
    class_test_result = models.ForeignKey(
        ClassTestResult,
        on_delete=models.CASCADE,
        related_name="subject_marks",
        blank=True,
        null=True
    )

    subject = models.CharField(max_length=150)
    written_marks = models.FloatField(default=0)
    oral_marks = models.FloatField(default=0)
    max_marks = models.FloatField(default=100)

    class Meta:
        ordering = ["subject"]
        unique_together = (
            "class_test_result",
            "subject",
        )

    @property
    def total_marks(self):
        return (self.written_marks or 0) + (self.oral_marks or 0)

    def __str__(self):
        return f"{self.class_test_result} - {self.subject}"
