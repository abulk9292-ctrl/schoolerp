from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from .models import Complaint
from students.models import Student


@login_required
def complaint_list(request):
    complaints = Complaint.objects.all().order_by('-created_at')
    return render(request, 'complaints/list.html', {'complaints': complaints})


@login_required
def complaint_add(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        parent_name = request.POST.get('parent_name')

        Complaint.objects.create(
            student=student,
            title=title,
            description=description,
            parent_name=parent_name
        )
        return redirect('student_detail', pk=student.id)

    return render(request, 'complaints/add.html', {'student': student})


@login_required
def complaint_solve(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)

    if request.method == 'POST':
        solution = request.POST.get('solution')

        complaint.solution = solution
        complaint.status = 'Solved'
        complaint.solved_at = timezone.now()
        complaint.save()

        return redirect('complaint_list')

    return render(request, 'complaints/solve.html', {'complaint': complaint})