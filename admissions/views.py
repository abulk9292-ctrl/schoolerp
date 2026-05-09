from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import OnlineAdmission
from students.models import Student


def set_if_field(obj, field_name, value):
    if hasattr(obj, field_name):
        setattr(obj, field_name, value)


@login_required
def online_admission_list(request):
    admissions = OnlineAdmission.objects.all().order_by("-id")
    return render(request, "admissions/online_admission_list.html", {
        "admissions": admissions
    })


@login_required
def approve_admission(request, pk):
    admission = get_object_or_404(OnlineAdmission, pk=pk)

    if admission.status == "Approved":
        messages.warning(request, "Already approved.")
        return redirect("online_admission_list")

    student = Student()

    set_if_field(student, "name", admission.student_name)
    set_if_field(student, "father_name", admission.father_name)
    set_if_field(student, "mother_name", admission.mother_name)
    set_if_field(student, "date_of_birth", admission.date_of_birth)
    set_if_field(student, "dob", admission.date_of_birth)
    set_if_field(student, "class_assigned", admission.class_applied)
    set_if_field(student, "student_class", admission.class_applied)
    set_if_field(student, "phone", admission.phone)
    set_if_field(student, "address", admission.address)
    set_if_field(student, "aadhaar_number", admission.aadhaar_number)

    if admission.photo:
        set_if_field(student, "photo", admission.photo)

    student.save()

    admission.status = "Approved"
    admission.created_student_id = student.id
    admission.save()

    messages.success(request, "Admission approved and student added successfully.")
    return redirect("online_admission_list")


@login_required
def reject_admission(request, pk):
    admission = get_object_or_404(OnlineAdmission, pk=pk)
    admission.status = "Rejected"
    admission.save()

    messages.success(request, "Admission rejected.")
    return redirect("online_admission_list")

from .forms import OnlineAdmissionForm


def admission_apply(request):

    if request.method == "POST":

        form = OnlineAdmissionForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Admission Form Submitted Successfully."
            )

            return redirect("admission_apply")

    else:

        form = OnlineAdmissionForm()

    return render(
        request,
        "admissions/admission_apply.html",
        {
            "form": form
        }
    )