from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import Admission
from .forms import AdmissionForm
from students.models import Student


def set_if_field(obj, field_name, value):
    if hasattr(obj, field_name):
        setattr(obj, field_name, value)


@login_required
def online_admission_list(request):
    admissions = Admission.objects.all().order_by("-id")
    return render(request, "admissions/online_admission_list.html", {
        "admissions": admissions
    })


@login_required
def approve_admission(request, pk):
    admission = get_object_or_404(Admission, pk=pk)

    if admission.status == "Approved":
        messages.warning(request, "Already approved.")
        return redirect("online_admission_list")

    student = Student()

    set_if_field(student, "name", admission.student_name)
    set_if_field(student, "father_name", admission.father_name)
    set_if_field(student, "mother_name", admission.mother_name)
    set_if_field(student, "date_of_birth", admission.date_of_birth)
    set_if_field(student, "dob", admission.date_of_birth)

    set_if_field(student, "class_assigned", admission.student_class)
    set_if_field(student, "student_class", admission.student_class)

    set_if_field(student, "phone", admission.mobile)
    set_if_field(student, "mobile", admission.mobile)
    set_if_field(student, "guardian_mobile", admission.guardian_mobile)

    set_if_field(student, "address", admission.address)
    set_if_field(student, "aadhaar_number", admission.aadhaar_no)
    set_if_field(student, "aadhaar_no", admission.aadhaar_no)

    set_if_field(student, "gender", admission.gender)
    set_if_field(student, "previous_school", admission.previous_school)
    set_if_field(student, "transport_required", admission.transport_required)
    set_if_field(student, "hostel_required", admission.hostel_required)

    if admission.student_photo:
        set_if_field(student, "photo", admission.student_photo)
        set_if_field(student, "student_photo", admission.student_photo)

    student.save()

    admission.status = "Approved"

    if hasattr(admission, "student_id"):
        admission.student_id = student.id

    if hasattr(admission, "created_student_id"):
        admission.created_student_id = student.id

    admission.save()

    messages.success(request, "Admission approved and student added successfully.")
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
        form = AdmissionForm()

    return render(request, "admissions/admission_apply.html", {
        "form": form
    })