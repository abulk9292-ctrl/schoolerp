from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import Admission
from .forms import AdmissionForm
from students.models import Student
from academics.models import Class


# =====================================================
# ADMISSION PERMISSION HELPER
# =====================================================

def can_manage_admissions(request):

    if not request.user.is_authenticated:
        return False

    if request.user.is_superuser or request.user.is_staff:
        return True

    employee = getattr(request.user, "employee", None)

    if not employee:
        return False

    if employee.is_erp_admin:
        return True

    return getattr(employee, "can_access_admissions", False)


# =====================================================
# ONLINE ADMISSION LIST
# =====================================================

@login_required
def online_admission_list(request):

    if not can_manage_admissions(request):
        messages.error(request, "❌ Permission Denied")
        return redirect("dashboard")

    selected_class = request.GET.get("class")
    selected_section = request.GET.get("section")
    selected_status = request.GET.get("status")

    admissions = Admission.objects.all().order_by("-id")

    if selected_class:
        admissions = admissions.filter(
            student_class__iexact=selected_class
        )

    if selected_section:
        admissions = admissions.filter(
            section=selected_section
        )

    if selected_status:
        admissions = admissions.filter(
            status=selected_status
        )

    classes = (
        Admission.objects.exclude(student_class="")
        .values_list("student_class", flat=True)
        .distinct()
        .order_by("student_class")
    )

    sections = (
        Admission.objects.exclude(section="")
        .exclude(section__isnull=True)
        .values_list("section", flat=True)
        .distinct()
        .order_by("section")
    )

    return render(
        request,
        "admissions/online_admission_list.html",
        {
            "admissions": admissions,
            "classes": classes,
            "sections": sections,
            "selected_class": selected_class,
            "selected_section": selected_section,
            "selected_status": selected_status,
        }
    )


# =====================================================
# GET OR CREATE CLASS
# =====================================================

def get_or_create_class(class_name):

    class_name = (class_name or "").strip()

    if not class_name:
        return None

    class_obj = Class.objects.filter(
        class_name__iexact=class_name
    ).first()

    if class_obj:
        return class_obj

    return Class.objects.create(
        class_name=class_name
    )


# =====================================================
# APPROVE ADMISSION
# =====================================================

@login_required
def approve_admission(request, pk):

    if not can_manage_admissions(request):
        messages.error(request, "❌ Permission Denied")
        return redirect("dashboard")

    admission = get_object_or_404(
        Admission,
        pk=pk
    )

    # Already approved check
    if (
        admission.status == "Approved"
        and admission.created_student_id
    ):
        if Student.objects.filter(
            id=admission.created_student_id
        ).exists():

            messages.warning(
                request,
                "Already approved and student already added."
            )
            return redirect("online_admission_list")

    class_obj = get_or_create_class(
        admission.student_class
    )

    if not class_obj:
        messages.error(
            request,
            "Class name missing. Please correct admission form."
        )
        return redirect("online_admission_list")

    # Duplicate Student Protection
    existing_student = Student.objects.filter(
        student_name__iexact=admission.student_name,
        phone=admission.mobile
    ).first()

    if existing_student:

        admission.status = "Approved"
        admission.created_student_id = existing_student.id
        admission.approved_by = request.user
        admission.approved_at = timezone.now()
        admission.save()

        messages.warning(
            request,
            f"Student already exists: "
            f"{existing_student.student_name} "
            f"({existing_student.student_id})"
        )

        return redirect("online_admission_list")

    # Create Student
    student = Student.objects.create(
        student_name=admission.student_name,
        father_name=admission.father_name,
        mother_name=admission.mother_name,
        date_of_birth=admission.date_of_birth,
        admission_date=timezone.now().date(),
        class_assigned=class_obj,
        section=admission.section,
        phone=admission.mobile,
        gender=admission.gender,
        aadhaar_number=admission.aadhaar_no,
        previous_school=admission.previous_school,
        address=admission.address,
        transport_required=admission.transport_required,
        photo=admission.student_photo
        if admission.student_photo
        else None,
        is_active=True,
    )

    admission.status = "Approved"
    admission.created_student_id = student.id
    admission.approved_by = request.user
    admission.approved_at = timezone.now()
    admission.is_duplicate_checked = True
    admission.save()

    messages.success(
        request,
        f"Approved successfully. "
        f"Student added: "
        f"{student.student_name} "
        f"({student.student_id})"
    )

    return redirect("online_admission_list")


# =====================================================
# REJECT ADMISSION
# =====================================================

@login_required
def reject_admission(request, pk):

    if not can_manage_admissions(request):
        messages.error(request, "❌ Permission Denied")
        return redirect("dashboard")

    admission = get_object_or_404(
        Admission,
        pk=pk
    )

    admission.status = "Rejected"
    admission.approved_by = request.user
    admission.approved_at = timezone.now()

    admission.save(
        update_fields=[
            "status",
            "approved_by",
            "approved_at"
        ]
    )

    messages.success(
        request,
        "Admission rejected."
    )

    return redirect("online_admission_list")


# =====================================================
# PUBLIC ADMISSION FORM
# =====================================================

def admission_apply(request):

    if request.method == "POST":

        form = AdmissionForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            mobile = (
                form.cleaned_data.get("mobile")
                or ""
            ).strip()

            student_name = (
                form.cleaned_data.get("student_name")
                or ""
            ).strip()

            duplicate = Admission.objects.filter(
                student_name__iexact=student_name,
                mobile=mobile,
                status="Pending"
            ).exists()

            if duplicate:

                messages.warning(
                    request,
                    "A pending admission already exists "
                    "for this student."
                )

                return redirect("admission_apply")

            admission = form.save(commit=False)
            admission.is_duplicate_checked = True
            admission.save()

            messages.success(
                request,
                "Admission Form Submitted Successfully."
            )

            return redirect("admission_apply")

        else:
            messages.error(
                request,
                "Form submit hoyni. Please check required fields."
            )

    else:
        form = AdmissionForm()

    return render(
        request,
        "admissions/admission_apply.html",
        {
            "form": form
        }
    )