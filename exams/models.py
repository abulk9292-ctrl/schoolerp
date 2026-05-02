from django.db import models
from students.models import Student


class Exam(models.Model):
    name = models.CharField(max_length=100)
    academic_session = models.CharField(max_length=20, default="2025-26")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name


class ExamRoutine(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    school_class = models.CharField(max_length=50)
    subject = models.CharField(max_length=100)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    total_marks = models.IntegerField(default=100)

    def __str__(self):
        return f"{self.exam} - {self.school_class} - {self.subject}"


class ExamResult(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)

    written_marks = models.IntegerField(default=0)
    oral_marks = models.IntegerField(default=0)
    max_marks = models.IntegerField(default=100)

    class Meta:
        unique_together = ('student', 'exam', 'subject')

    @property
    def total_marks(self):
        return self.written_marks + self.oral_marks

    @property
    def percentage(self):
        if self.max_marks > 0:
            return round((self.total_marks / self.max_marks) * 100, 2)
        return 0

    @property
    def grade(self):
        p = self.percentage
        if p >= 90:
            return "AA"
        elif p >= 80:
            return "A+"
        elif p >= 60:
            return "A"
        elif p >= 45:
            return "B+"
        elif p >= 40:
            return "B"
        elif p >= 35:
            return "C+"
        elif p >= 24:
            return "C"
        return "D"

    def __str__(self):
        return f"{self.student} - {self.exam} - {self.subject}"


class StudentResultSummary(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)

    total_marks = models.IntegerField(default=0)
    max_total_marks = models.IntegerField(default=0)
    percentage = models.FloatField(default=0)
    grade = models.CharField(max_length=10, blank=True)
    result_status = models.CharField(max_length=20, default="Pass")
    rank = models.IntegerField(default=0)

    class Meta:
        unique_together = ('student', 'exam')

    def __str__(self):
        return f"{self.student} - {self.exam} - Rank {self.rank}"