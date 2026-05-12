from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import Admission
from .forms import AdmissionForm
from students.models import Student
from academics.models import Class


@login_required
def online_admission_list(request):
    admissions = Admission.objects.all().order_by("-id")
    return render(request, "admissions/online_admission_list.html", {
        "admissions": admissions
    })


def get_or_create_class(class_name):
    class_name = (class_name or "").strip()

    if not class_name:
        return None

    class_obj = Class.objects.filter(class_name__iexact=class_name).first()

    if class_obj:
        return class_obj

    return Class.objects.create(class_name=class_name)


@login_required
def approve_admission(request, pk):
    admission = get_object_or_404(Admission, pk=pk)

    # Approved but student already created
    if admission.status == "Approved" and admission.created_student_id:
        if Student.objects.filter(id=admission.created_student_id).exists():
            messages.warning(request, "Already approved and student already added.")
            return redirect("online_admission_list")

    class_obj = get_or_create_class(admission.student_class)

    if not class_obj:
        messages.error(request, "Class name missing. Please correct admission form.")
        return redirect("online_admission_list")

    student = Student.objects.create(
        student_name=admission.student_name,
        father_name=admission.father_name,
        mother_name=admission.mother_name,
        date_of_birth=admission.date_of_birth,
        admission_date=timezone.now().date(),
        class_assigned=class_obj,
        phone=admission.mobile,
        gender=admission.gender,
        aadhaar_number=admission.aadhaar_no,
        previous_school=admission.previous_school,
        address=admission.address,
        transport_required=admission.transport_required,
        photo=admission.student_photo if admission.student_photo else None,
        is_active=True,
    )

    admission.status = "Approved"
    admission.created_student_id = student.id
    admission.save()

    messages.success(
        request,
        f"Approved successfully. Student added: {student.student_name} ({student.student_id})"
    )
    return redirect("online_admission_list")


@login_required
def reject_admission(request, pk):
    admission = get_object_or_404(Admission, pk=pk)
    admission.status = "Rejected"
    admission.save()

    messages.success(request, "Admission rejected.")
    return redirect("online_admission_list")


def admission_apply(request):
    if request.method == "POST":
        form = AdmissionForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, "Admission Form Submitted Successfully.")
            return redirect("admission_apply")
        else:
            messages.error(request, "Form submit hoyni. Please check required fields.")
            print(form.errors)

    else:
        form = AdmissionForm()

    return render(request, "admissions/admission_apply.html", {
        "form": form
    })