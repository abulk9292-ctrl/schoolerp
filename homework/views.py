from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import Homework, HomeworkSubmission
from .forms import HomeworkForm, HomeworkSubmissionForm, HomeworkReviewForm


@login_required
def homework_list(request):
    homeworks = Homework.objects.select_related(
        "given_by"
    ).all().order_by("-id")

    class_name = request.GET.get("class")
    status = request.GET.get("status")
    search = request.GET.get("search")

    if class_name:
        homeworks = homeworks.filter(school_class__icontains=class_name)

    if status:
        homeworks = homeworks.filter(status=status)

    if search:
        homeworks = homeworks.filter(title__icontains=search)

    active_count = Homework.objects.filter(status="Active").count()
    closed_count = Homework.objects.filter(status="Closed").count()
    submission_count = HomeworkSubmission.objects.count()

    return render(request, "homework/homework_list.html", {
        "homeworks": homeworks,
        "selected_class": class_name,
        "selected_status": status,
        "search": search,
        "active_count": active_count,
        "closed_count": closed_count,
        "submission_count": submission_count,
    })

@login_required
def homework_add(request):
    if request.method == "POST":
        form = HomeworkForm(request.POST, request.FILES)

        if form.is_valid():
            homework = form.save(commit=False)

            employee = getattr(request.user, "employee", None)
            if employee:
                homework.given_by = employee

            homework.save()

            messages.success(request, "Homework added successfully.")
            return redirect("homework_list")
    else:
        form = HomeworkForm()

    return render(request, "homework/homework_form.html", {
        "form": form,
        "page_title": "Add Homework",
    })


@login_required
def homework_edit(request, pk):
    homework = get_object_or_404(Homework, pk=pk)

    employee = getattr(request.user, "employee", None)

    if employee and homework.given_by and homework.given_by != employee:
        if not request.user.is_superuser and not request.user.is_staff:
            messages.error(request, "You cannot edit another teacher's homework.")
            return redirect("homework_list")

    if request.method == "POST":
        form = HomeworkForm(request.POST, request.FILES, instance=homework)

        if form.is_valid():
            form.save()
            messages.success(request, "Homework updated successfully.")
            return redirect("homework_list")
    else:
        form = HomeworkForm(instance=homework)

    return render(request, "homework/homework_form.html", {
        "form": form,
        "page_title": "Edit Homework",
    })


@login_required
def homework_delete(request, pk):
    homework = get_object_or_404(Homework, pk=pk)

    employee = getattr(request.user, "employee", None)

    if employee and homework.given_by and homework.given_by != employee:
        if not request.user.is_superuser and not request.user.is_staff:
            messages.error(request, "You cannot delete another teacher's homework.")
            return redirect("homework_list")

    homework.delete()
    messages.success(request, "Homework deleted successfully.")
    return redirect("homework_list")


# =====================================================
# STUDENT HOMEWORK
# =====================================================

def student_homework_list(request):
    student_id = request.session.get("student_id")

    if not student_id:
        return redirect("student_login")

    from students.models import Student

    student = get_object_or_404(Student, id=student_id)

    homeworks = Homework.objects.filter(
        status="Active"
    ).order_by("-id")

    if student.class_assigned:
        homeworks = homeworks.filter(
            school_class__iexact=str(student.class_assigned)
        )

    submissions = HomeworkSubmission.objects.filter(
        student=student
    ).select_related("homework")

    submitted_map = {
        submission.homework_id: submission
        for submission in submissions
    }

    return render(request, "homework/student_homework_list.html", {
        "student": student,
        "homeworks": homeworks,
        "submitted_map": submitted_map,
    })


def student_homework_submit(request, pk):
    student_id = request.session.get("student_id")

    if not student_id:
        return redirect("student_login")

    from students.models import Student

    student = get_object_or_404(Student, id=student_id)
    homework = get_object_or_404(Homework, pk=pk, status="Active")

    existing_submission = HomeworkSubmission.objects.filter(
        homework=homework,
        student=student
    ).first()

    if existing_submission:
        messages.warning(request, "You have already submitted this homework.")
        return redirect("student_homework_list")

    if request.method == "POST":
        form = HomeworkSubmissionForm(request.POST, request.FILES)

        if form.is_valid():
            submission = form.save(commit=False)
            submission.homework = homework
            submission.student = student

            if homework.due_date and timezone.localdate() > homework.due_date:
                submission.status = "Late"
            else:
                submission.status = "Submitted"

            submission.save()

            messages.success(request, "Homework submitted successfully.")
            return redirect("student_homework_list")
    else:
        form = HomeworkSubmissionForm()

    return render(request, "homework/student_homework_submit.html", {
        "student": student,
        "homework": homework,
        "form": form,
    })


# =====================================================
# TEACHER REVIEW
# =====================================================

@login_required
def homework_submission_list(request):
    submissions = HomeworkSubmission.objects.select_related(
        "homework",
        "student",
        "reviewed_by"
    ).order_by("-submitted_at")

    employee = getattr(request.user, "employee", None)

    if employee and not request.user.is_superuser and not request.user.is_staff:
        submissions = submissions.filter(homework__given_by=employee)

    status = request.GET.get("status")
    search = request.GET.get("search")

    if status:
        submissions = submissions.filter(status=status)

    if search:
        submissions = submissions.filter(
            student__student_name__icontains=search
        )

    return render(request, "homework/homework_submission_list.html", {
        "submissions": submissions,
        "selected_status": status,
        "search": search,
    })


@login_required
def homework_submission_review(request, pk):
    submission = get_object_or_404(
        HomeworkSubmission.objects.select_related(
            "homework",
            "student",
            "reviewed_by"
        ),
        pk=pk
    )

    employee = getattr(request.user, "employee", None)

    if employee and submission.homework.given_by and submission.homework.given_by != employee:
        if not request.user.is_superuser and not request.user.is_staff:
            messages.error(request, "You cannot review another teacher's homework.")
            return redirect("homework_submission_list")

    if request.method == "POST":
        form = HomeworkReviewForm(request.POST, instance=submission)

        if form.is_valid():
            reviewed = form.save(commit=False)
            reviewed.reviewed_by = employee
            reviewed.reviewed_at = timezone.now()
            reviewed.status = "Reviewed"
            reviewed.save()

            messages.success(request, "Homework reviewed successfully.")
            return redirect("homework_submission_list")
    else:
        form = HomeworkReviewForm(instance=submission)

    return render(request, "homework/homework_submission_review.html", {
        "submission": submission,
        "form": form,
    })


# =====================================================
# PARENT HOMEWORK VIEW
# =====================================================

def parent_homework_list(request):
    parent_id = request.session.get("parent_id")

    if not parent_id:
        return redirect("parent_login")

    from students.models import Parent

    parent = get_object_or_404(Parent, id=parent_id)
    student = parent.student

    homeworks = Homework.objects.filter(
        status="Active",
        school_class__iexact=str(student.class_assigned)
    ).order_by("-id")

    submissions = HomeworkSubmission.objects.filter(
        student=student
    ).select_related("homework")

    submitted_map = {
        submission.homework_id: submission
        for submission in submissions
    }

    return render(request, "homework/parent_homework_list.html", {
        "parent": parent,
        "student": student,
        "homeworks": homeworks,
        "submitted_map": submitted_map,
    })