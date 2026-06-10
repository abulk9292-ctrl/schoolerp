from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import Complaint
from students.models import Student
from teachers.models import Employee


def get_teacher_employee(request):
    if request.user.is_authenticated:
        emp = getattr(request.user, "employee", None)
        if emp and emp.is_active:
            return emp
    teacher_id = request.session.get("teacher_id")
    if teacher_id:
        return Employee.objects.filter(id=teacher_id, is_active=True).first()
    return None


def teacher_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not get_teacher_employee(request):
            messages.error(request, "Please login as teacher.")
            return redirect("teacher_login")
        return view_func(request, *args, **kwargs)
    return wrapper


def is_admin_user(request):
    if not request.user.is_authenticated:
        return False
    if request.user.is_superuser or request.user.is_staff:
        return True
    emp = getattr(request.user, "employee", None)
    return bool(emp and emp.is_erp_admin)


def filter_teacher_complaints(employee, qs):
    if not employee:
        return qs.none()
    if employee.is_erp_admin:
        return qs
    designation = str(employee.designation or "").lower()
    if "principal" in designation or "head" in designation:
        return qs
    if not employee.assigned_class:
        return qs.none()
    qs = qs.filter(student__class_assigned=employee.assigned_class)
    if employee.assigned_section:
        qs = qs.filter(student__section=employee.assigned_section)
    return qs


@login_required
def complaint_list(request):
    if not is_admin_user(request):
        messages.error(request, "Permission denied.")
        return redirect("teacher_complaint_dashboard")

    complaints = Complaint.objects.select_related("student", "student__class_assigned").all().order_by("-created_at")
    status = request.GET.get("status", "").strip()
    search = request.GET.get("search", "").strip()

    if status:
        complaints = complaints.filter(status=status)
    if search:
        complaints = complaints.filter(title__icontains=search) | complaints.filter(student__student_name__icontains=search)

    return render(request, "complaints/list.html", {
        "complaints": complaints,
        "selected_status": status,
        "search": search,
        "total_count": complaints.count(),
        "pending_teacher_count": Complaint.objects.filter(status="PENDING_TEACHER").count(),
        "pending_admin_count": Complaint.objects.filter(status="PENDING_ADMIN_APPROVAL").count(),
        "solved_count": Complaint.objects.filter(status="SOLVED").count(),
        "rejected_count": Complaint.objects.filter(status="REJECTED").count(),
    })


@login_required
def complaint_add(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.method == "POST":
        parent_name = request.POST.get("parent_name", "").strip()
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()

        if not parent_name or not title or not description:
            messages.error(request, "All fields are required.")
            return render(request, "complaints/add.html", {"student": student})

        Complaint.objects.create(
            student=student,
            parent_name=parent_name,
            title=title,
            description=description,
            status="PENDING_TEACHER",
        )
        messages.success(request, "Complaint submitted successfully.")
        return redirect("student_detail", pk=student.id)

    return render(request, "complaints/add.html", {"student": student})


@teacher_required
def teacher_complaint_dashboard(request):
    employee = get_teacher_employee(request)
    base = Complaint.objects.select_related("student", "student__class_assigned").all().order_by("-created_at")
    qs = filter_teacher_complaints(employee, base)

    return render(request, "complaints/teacher_complaint_dashboard.html", {
        "employee": employee,
        "complaints": qs.filter(status="PENDING_TEACHER"),
        "pending_complaints": qs.filter(status="PENDING_TEACHER"),
        "submitted_complaints": qs.filter(status="PENDING_ADMIN_APPROVAL"),
        "solved_complaints": qs.filter(status="SOLVED"),
        "rejected_complaints": qs.filter(status="REJECTED"),
        "total_pending": qs.filter(status="PENDING_TEACHER").count(),
        "total_submitted": qs.filter(status="PENDING_ADMIN_APPROVAL").count(),
        "total_solved": qs.filter(status="SOLVED").count(),
        "total_rejected": qs.filter(status="REJECTED").count(),
    })


@teacher_required
def teacher_submit_complaint(request, pk):
    employee = get_teacher_employee(request)
    complaint = get_object_or_404(Complaint.objects.select_related("student", "student__class_assigned"), pk=pk)

    if not filter_teacher_complaints(employee, Complaint.objects.filter(pk=pk)).exists():
        messages.error(request, "You are not allowed to submit this complaint.")
        return redirect("teacher_complaint_dashboard")

    if request.method == "POST":
        teacher_status = request.POST.get("teacher_status", "").strip()
        teacher_solution = request.POST.get("teacher_solution", "").strip()

        if not teacher_status or not teacher_solution:
            messages.error(request, "Teacher status and remark are required.")
            return render(request, "complaints/teacher_submit.html", {"complaint": complaint, "employee": employee})

        complaint.submit_by_teacher(
            teacher_name=employee.name,
            solution_text=f"Teacher Status: {teacher_status}\n\nTeacher Remark:\n{teacher_solution}"
        )
        messages.success(request, "Teacher remark submitted to admin approval.")
        return redirect("teacher_complaint_dashboard")

    return render(request, "complaints/teacher_submit.html", {"complaint": complaint, "employee": employee})


@login_required
def admin_complaint_approval(request):
    if not is_admin_user(request):
        messages.error(request, "Permission denied.")
        return redirect("teacher_complaint_dashboard")

    complaints = Complaint.objects.select_related("student", "student__class_assigned").filter(status="PENDING_ADMIN_APPROVAL").order_by("-teacher_submitted_at", "-created_at")
    return render(request, "complaints/admin_complaint_approval.html", {"complaints": complaints})


@login_required
def complaint_solve(request, pk):
    if not is_admin_user(request):
        messages.error(request, "Permission denied.")
        return redirect("teacher_complaint_dashboard")

    complaint = get_object_or_404(Complaint.objects.select_related("student", "student__class_assigned"), pk=pk)

    if request.method == "POST":
        admin_status = request.POST.get("admin_status", "").strip()
        admin_solution = request.POST.get("admin_solution", "").strip() or request.POST.get("solution", "").strip()

        if not admin_solution:
            messages.error(request, "Admin remark is required.")
            return render(request, "complaints/solve.html", {"complaint": complaint})

        final_note = admin_solution
        if admin_status:
            final_note = f"Admin Status: {admin_status}\n\nAdmin Remark:\n{admin_solution}"

        complaint.approve_by_admin(admin_solution=final_note)
        messages.success(request, "Admin approved and solved the complaint.")
        return redirect("complaint_list")

    return render(request, "complaints/solve.html", {"complaint": complaint})


@login_required
def complaint_reject(request, pk):
    if not is_admin_user(request):
        messages.error(request, "Permission denied.")
        return redirect("teacher_complaint_dashboard")

    complaint = get_object_or_404(Complaint, pk=pk)
    note = request.POST.get("admin_solution", "").strip() or "Admin rejected / sent back for correction."
    complaint.reject_by_admin(admin_solution=note)
    messages.warning(request, "Complaint rejected / sent back.")
    return redirect("admin_complaint_approval")


@login_required
def complaint_edit(request, pk):
    if not is_admin_user(request):
        messages.error(request, "Permission denied.")
        return redirect("teacher_complaint_dashboard")

    complaint = get_object_or_404(Complaint, pk=pk)
    if request.method == "POST":
        complaint.title = request.POST.get("title", "").strip()
        complaint.parent_name = request.POST.get("parent_name", "").strip()
        complaint.description = request.POST.get("description", "").strip()
        status = request.POST.get("status", "").strip()
        if status in ["PENDING_TEACHER", "PENDING_ADMIN_APPROVAL", "SOLVED", "REJECTED"]:
            complaint.status = status
        complaint.save()
        messages.success(request, "Complaint updated successfully.")
        return redirect("complaint_list")

    return render(request, "complaints/edit.html", {"complaint": complaint})


@login_required
def complaint_delete(request, pk):
    if not is_admin_user(request):
        messages.error(request, "Permission denied.")
        return redirect("teacher_complaint_dashboard")

    get_object_or_404(Complaint, pk=pk).delete()
    messages.success(request, "Complaint deleted successfully.")
    return redirect("complaint_list")
