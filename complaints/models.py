from django.db import models
from django.utils import timezone
from students.models import Student


class Complaint(models.Model):

    STATUS_CHOICES = [
        ("PENDING_TEACHER", "Pending Teacher Action"),
        ("PENDING_ADMIN_APPROVAL", "Pending Admin Approval"),
        ("SOLVED", "Solved"),
        ("REJECTED", "Rejected / Send Back"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="complaints"
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    parent_name = models.CharField(max_length=150, blank=True, null=True)

    status = models.CharField(
        max_length=40,
        choices=STATUS_CHOICES,
        default="PENDING_TEACHER"
    )

    teacher_solution = models.TextField(blank=True, null=True)
    handled_by_teacher = models.CharField(max_length=150, blank=True, null=True)
    teacher_submitted_at = models.DateTimeField(blank=True, null=True)

    admin_solution = models.TextField(blank=True, null=True)
    admin_approved_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    solved_at = models.DateTimeField(blank=True, null=True)

    def submit_by_teacher(self, teacher_name, solution_text):
        self.teacher_solution = solution_text
        self.handled_by_teacher = teacher_name
        self.teacher_submitted_at = timezone.now()
        self.status = "PENDING_ADMIN_APPROVAL"
        self.save()

    def approve_by_admin(self, admin_solution=None):
        if admin_solution:
            self.admin_solution = admin_solution

        self.status = "SOLVED"
        self.admin_approved_at = timezone.now()
        self.solved_at = timezone.now()
        self.save()

    def reject_by_admin(self, admin_solution=None):
        if admin_solution:
            self.admin_solution = admin_solution

        self.status = "REJECTED"
        self.save()

    def __str__(self):
        return f"{self.student.student_name} - {self.title}"