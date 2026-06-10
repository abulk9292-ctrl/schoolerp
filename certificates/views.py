from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Certificate
from students.models import Student
from core.views import get_selected_session


@login_required
def certificate_dashboard(request):
    selected_session = get_selected_session(request)

    total_certificates = Certificate.objects.filter(
        session=selected_session
    ).count()

    recent_certificates = Certificate.objects.select_related(
        "student"
    ).filter(
        session=selected_session
    ).order_by("-id")[:10]

    return render(request, "certificates/certificate_dashboard.html", {
        "total_certificates": total_certificates,
        "recent_certificates": recent_certificates,
        "selected_session": selected_session,
    })


@login_required
def certificate_list(request):
    selected_session = get_selected_session(request)

    certificates = Certificate.objects.select_related(
        "student"
    ).filter(
        session=selected_session
    ).order_by("-id")

    return render(request, "certificates/certificate_list.html", {
        "certificates": certificates,
        "selected_session": selected_session,
    })


@login_required
def certificate_create(request):
    selected_session = get_selected_session(request)

    students = Student.objects.filter(
        is_active=True
    ).order_by("student_name")

    if request.method == "POST":
        student_id = request.POST.get("student")
        certificate_type = request.POST.get("certificate_type")
        session = request.POST.get("session") or selected_session
        reason = request.POST.get("reason") or ""
        conduct = request.POST.get("conduct") or "Good"
        remarks = request.POST.get("remarks") or ""
        custom_body = request.POST.get("custom_body") or ""

        student = get_object_or_404(Student, id=student_id)

        certificate = Certificate.objects.create(
            student=student,
            certificate_type=certificate_type,
            session=session,
            reason=reason,
            conduct=conduct,
            remarks=remarks,
            custom_body=custom_body,
        )

        messages.success(request, "Certificate Created Successfully")
        return redirect("certificate_detail", pk=certificate.pk)

    return render(request, "certificates/certificate_create.html", {
        "students": students,
        "current_session": selected_session,
        "selected_session": selected_session,
    })


@login_required
def certificate_detail(request, pk):
    selected_session = get_selected_session(request)

    certificate = get_object_or_404(
        Certificate,
        pk=pk,
        session=selected_session
    )

    return render(request, "certificates/certificate_detail.html", {
        "certificate": certificate,
        "selected_session": selected_session,
    })


@login_required
def certificate_delete(request, pk):
    selected_session = get_selected_session(request)

    certificate = get_object_or_404(
        Certificate,
        pk=pk,
        session=selected_session
    )

    certificate.delete()

    messages.success(request, "Certificate Deleted Successfully")
    return redirect("certificate_list")