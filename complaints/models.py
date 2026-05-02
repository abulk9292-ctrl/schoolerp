from django.db import models
from students.models import Student

class Complaint(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Solved', 'Solved'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()

    parent_name = models.CharField(max_length=150, blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    solution = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    solved_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.student.student_name} - {self.title}"