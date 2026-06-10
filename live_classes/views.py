from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from students.models import Student
from .forms import LiveClassForm
from .models import LiveClass, LiveClassAttendance


def _student_field_names():
    return {field.name for field in Student._meta.get_fields()}


def _student_from_user(user):
    """
    Safe student finder for AL RAHMAN MISSION ERP.
    Your Student model has login_username/login_password, not user ForeignKey.
    So this function avoids Student.objects.filter(user=user) FieldError.
    """
    if not user or not user.is_authenticated:
        return None

    fields = _student_field_names()
    query = Q()

    if "user" in fields:
        query |= Q(user=user)
    if "login_username" in fields:
        query |= Q(login_username=user.username)
    if "student_id" in fields:
        query |= Q(student_id=user.username)
    if "admission_no" in fields:
        query |= Q(admission_no=user.username)
    if "registration_no" in fields:
        query |= Q(registration_no=user.username)

    if not query:
        return None

    return Student.objects.filter(query).first()


def _students_for_parent_user(user):
    """
    Safe parent-student finder.
    Supports parent_user if exists, otherwise parent_login/login_username style.
    """
    if not user or not user.is_authenticated:
        return Student.objects.none()

    fields = _student_field_names()
    query = Q()

    if "parent_user" in fields:
        query |= Q(parent_user=user)
    if "parent_login" in fields:
        query |= Q(parent_login=user.username)
    if "guardian_username" in fields:
        query |= Q(guardian_username=user.username)
    if "login_username" in fields:
        query |= Q(login_username=user.username)

    if not query:
        return Student.objects.none()

    return Student.objects.filter(query).distinct()


@login_required
def live_class_list(request):
    live_classes = LiveClass.objects.select_related(
        "class_assigned", "teacher", "created_by"
    ).filter(is_active=True)

    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    class_id = request.GET.get("class", "").strip()

    if q:
        live_classes = live_classes.filter(
            Q(title__icontains=q) |
            Q(subject__icontains=q) |
            Q(description__icontains=q)
        )
    if status:
        live_classes = live_classes.filter(status=status)
    if class_id:
        live_classes = live_classes.filter(class_assigned_id=class_id)

    context = {
        "live_classes": live_classes,
        "total_live_classes": live_classes.count(),
        "upcoming_count": live_classes.filter(status="UPCOMING").count(),
        "running_count": live_classes.filter(status="RUNNING").count(),
        "completed_count": live_classes.filter(status="COMPLETED").count(),
    }
    return render(request, "live_classes/live_class_list.html", context)


@login_required
def live_class_add(request):
    if request.method == "POST":
        form = LiveClassForm(request.POST)
        if form.is_valid():
            live_class = form.save(commit=False)
            live_class.created_by = request.user
            live_class.save()
            messages.success(request, "Live class created successfully.")
            return redirect("live_classes:live_class_list")
    else:
        form = LiveClassForm()

    return render(request, "live_classes/live_class_form.html", {
        "form": form,
        "title": "Add Live Class",
    })


@login_required
def live_class_edit(request, pk):
    live_class = get_object_or_404(LiveClass, pk=pk)

    if request.method == "POST":
        form = LiveClassForm(request.POST, instance=live_class)
        if form.is_valid():
            form.save()
            messages.success(request, "Live class updated successfully.")
            return redirect("live_classes:live_class_list")
    else:
        form = LiveClassForm(instance=live_class)

    return render(request, "live_classes/live_class_form.html", {
        "form": form,
        "title": "Edit Live Class",
    })


@login_required
def live_class_delete(request, pk):
    live_class = get_object_or_404(LiveClass, pk=pk)

    if request.method == "POST":
        live_class.delete()
        messages.success(request, "Live class deleted successfully.")
        return redirect("live_classes:live_class_list")

    return render(request, "live_classes/live_class_confirm_delete.html", {
        "live_class": live_class,
    })


@login_required
def live_class_join(request, pk):
    live_class = get_object_or_404(LiveClass, pk=pk, is_active=True)

    student = _student_from_user(request.user)
    if student:
        LiveClassAttendance.objects.get_or_create(
            live_class=live_class,
            student=student,
            defaults={"joined_at": timezone.now()}
        )

    return redirect(live_class.meeting_link)


@login_required
def student_live_class_list(request):
    student = _student_from_user(request.user)
    live_classes = LiveClass.objects.none()

    if student:
        live_classes = LiveClass.objects.filter(
            is_active=True,
            class_assigned=student.class_assigned
        ).order_by("-start_time")

    return render(request, "live_classes/student_live_class_list.html", {
        "student": student,
        "live_classes": live_classes,
    })


@login_required
def parent_live_class_list(request):
    students = _students_for_parent_user(request.user)
    class_ids = students.values_list("class_assigned_id", flat=True)

    live_classes = LiveClass.objects.filter(
        is_active=True,
        class_assigned_id__in=class_ids
    ).order_by("-start_time")

    return render(request, "live_classes/parent_live_class_list.html", {
        "students": students,
        "live_classes": live_classes,
    })
