from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import (
    AcademicSession,
    Class,
    Section,
    Subject,
    ClassSubject,
    ClassRoutine,
)

from .forms import (
    AcademicSessionForm,
    ClassForm,
    SectionForm,
    SubjectForm,
    ClassSubjectAssignForm,
    ClassRoutineForm,
)


# =========================
# PERMISSION HELPER
# =========================

def has_academics_permission(request):
    if request.user.is_superuser or request.user.is_staff:
        return True

    emp = getattr(request.user, "employee", None)

    if not emp:
        return False

    if getattr(emp, "is_erp_admin", False):
        return True

    return getattr(emp, "can_access_academics", False)


def permission_denied_redirect(request):
    messages.error(request, "❌ Permission Denied")
    return redirect("teacher_login")


# =========================
# ACADEMIC SESSION LIST + ADD
# =========================

@login_required
def session_list(request):
    if not has_academics_permission(request):
        return permission_denied_redirect(request)

    if request.method == "POST":
        form = AcademicSessionForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "✅ Academic session added successfully.")
            return redirect("session_list")
    else:
        form = AcademicSessionForm()

    sessions = AcademicSession.objects.all().order_by("-start_date")

    return render(request, "academics/session_list.html", {
        "form": form,
        "sessions": sessions,
    })


# =========================
# ACADEMIC SESSION EDIT
# =========================

@login_required
def session_edit(request, pk):
    if not has_academics_permission(request):
        return permission_denied_redirect(request)

    session_obj = get_object_or_404(AcademicSession, pk=pk)

    if request.method == "POST":
        form = AcademicSessionForm(request.POST, instance=session_obj)

        if form.is_valid():
            form.save()
            messages.success(request, "✅ Academic session updated successfully.")
            return redirect("session_list")
    else:
        form = AcademicSessionForm(instance=session_obj)

    sessions = AcademicSession.objects.all().order_by("-start_date")

    return render(request, "academics/session_list.html", {
        "form": form,
        "sessions": sessions,
        "edit_mode": True,
        "session_obj": session_obj,
    })


# =========================
# ACADEMIC SESSION DELETE
# =========================

@login_required
def session_delete(request, pk):
    if not has_academics_permission(request):
        return permission_denied_redirect(request)

    session_obj = get_object_or_404(AcademicSession, pk=pk)

    if request.method == "POST":
        session_obj.delete()
        messages.success(request, "🗑 Academic session deleted successfully.")
        return redirect("session_list")

    return render(request, "academics/session_confirm_delete.html", {
        "session_obj": session_obj,
    })


# =========================
# CLASS LIST + ADD
# =========================

@login_required
def class_list(request):
    if not has_academics_permission(request):
        return permission_denied_redirect(request)

    if request.method == "POST":
        form = ClassForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "✅ Class added successfully.")
            return redirect("class_list")
    else:
        form = ClassForm()

    classes = Class.objects.select_related("class_teacher").all().order_by("class_name")

    return render(request, "academics/class_list.html", {
        "classes": classes,
        "form": form,
    })


# =========================
# CLASS EDIT
# =========================

@login_required
def class_edit(request, pk):
    if not has_academics_permission(request):
        return permission_denied_redirect(request)

    class_obj = get_object_or_404(Class, pk=pk)

    if request.method == "POST":
        form = ClassForm(request.POST, instance=class_obj)

        if form.is_valid():

            old_teacher = class_obj.class_teacher

            class_instance = form.save()

            try:
                from teachers.models import Employee

                # ---------------------------------
                # OLD TEACHER REMOVE
                # ---------------------------------

                if (
                    old_teacher and
                    old_teacher != class_instance.class_teacher
                ):
                    old_teacher.assigned_class = None
                    old_teacher.assigned_section = ""
                    old_teacher.save(
                        update_fields=[
                            "assigned_class",
                            "assigned_section"
                        ]
                    )

                # ---------------------------------
                # NEW TEACHER ASSIGN
                # ---------------------------------

                if class_instance.class_teacher:

                    teacher = class_instance.class_teacher

                    teacher.assigned_class = class_instance

                    if not teacher.assigned_section:
                        teacher.assigned_section = ""

                    teacher.save(
                        update_fields=[
                            "assigned_class",
                            "assigned_section"
                        ]
                    )

            except Exception as e:
                print("Teacher Sync Error:", e)

            messages.success(
                request,
                "✅ Class updated successfully."
            )

            return redirect("class_list")

    else:
        form = ClassForm(instance=class_obj)

    classes = (
        Class.objects
        .select_related("class_teacher")
        .all()
        .order_by("class_name")
    )

    return render(
        request,
        "academics/class_list.html",
        {
            "classes": classes,
            "form": form,
            "edit_mode": True,
            "class_obj": class_obj,
        }
    )


# =========================
# CLASS DELETE
# =========================

@login_required
def class_delete(request, pk):
    if not has_academics_permission(request):
        return permission_denied_redirect(request)

    class_obj = get_object_or_404(Class, pk=pk)

    if request.method == "POST":
        class_obj.delete()
        messages.success(request, "🗑 Class deleted successfully.")
        return redirect("class_list")

    return render(request, "academics/class_confirm_delete.html", {
        "class_obj": class_obj,
    })


# =========================
# SECTION LIST + ADD
# =========================

@login_required
def section_list(request):
    if not has_academics_permission(request):
        return permission_denied_redirect(request)

    if request.method == "POST":
        form = SectionForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "✅ Section added successfully.")
            return redirect("section_list")
    else:
        form = SectionForm()

    sections = Section.objects.select_related("school_class").all().order_by(
        "school_class__class_name",
        "section_name"
    )

    return render(request, "academics/section_list.html", {
        "form": form,
        "sections": sections,
    })


# =========================
# SECTION EDIT
# =========================

@login_required
def section_edit(request, pk):
    if not has_academics_permission(request):
        return permission_denied_redirect(request)

    section_obj = get_object_or_404(Section, pk=pk)

    if request.method == "POST":
        form = SectionForm(request.POST, instance=section_obj)

        if form.is_valid():
            form.save()
            messages.success(request, "✅ Section updated successfully.")
            return redirect("section_list")
    else:
        form = SectionForm(instance=section_obj)

    sections = Section.objects.select_related("school_class").all().order_by(
        "school_class__class_name",
        "section_name"
    )

    return render(request, "academics/section_list.html", {
        "form": form,
        "sections": sections,
        "edit_mode": True,
        "section_obj": section_obj,
    })


# =========================
# SECTION DELETE
# =========================

@login_required
def section_delete(request, pk):
    if not has_academics_permission(request):
        return permission_denied_redirect(request)

    section_obj = get_object_or_404(Section, pk=pk)

    if request.method == "POST":
        section_obj.delete()
        messages.success(request, "🗑 Section deleted successfully.")
        return redirect("section_list")

    return render(request, "academics/section_confirm_delete.html", {
        "section_obj": section_obj,
    })


# =========================
# SUBJECT LIST + ADD
# =========================

@login_required
def subject_list(request):
    if not has_academics_permission(request):
        return permission_denied_redirect(request)

    if request.method == "POST":
        form = SubjectForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "✅ Subject added successfully.")
            return redirect("subject_list")
    else:
        form = SubjectForm()

    subjects = Subject.objects.all().order_by("subject_name")

    return render(request, "academics/subject_list.html", {
        "subjects": subjects,
        "form": form,
    })


# =========================
# SUBJECT EDIT
# =========================

@login_required
def subject_edit(request, pk):
    if not has_academics_permission(request):
        return permission_denied_redirect(request)

    subject = get_object_or_404(Subject, pk=pk)

    if request.method == "POST":
        form = SubjectForm(request.POST, instance=subject)

        if form.is_valid():
            form.save()
            messages.success(request, "✅ Subject updated successfully.")
            return redirect("subject_list")
    else:
        form = SubjectForm(instance=subject)

    subjects = Subject.objects.all().order_by("subject_name")

    return render(request, "academics/subject_list.html", {
        "subjects": subjects,
        "form": form,
        "edit_mode": True,
        "subject_obj": subject,
    })


# =========================
# SUBJECT DELETE
# =========================

@login_required
def subject_delete(request, pk):
    if not has_academics_permission(request):
        return permission_denied_redirect(request)

    subject = get_object_or_404(Subject, pk=pk)

    if request.method == "POST":
        subject.delete()
        messages.success(request, "🗑 Subject deleted successfully.")
        return redirect("subject_list")

    return render(request, "academics/subject_confirm_delete.html", {
        "subject": subject,
    })


# =========================
# CLASS WISE SUBJECT ASSIGN
# =========================

@login_required
def class_subject_assign(request):
    if not has_academics_permission(request):
        return permission_denied_redirect(request)

    selected_class_id = request.GET.get("class") or request.POST.get("school_class")
    selected_class = None
    assigned_subject_ids = []
    subject_rank_map = {}

    if selected_class_id:
        selected_class = get_object_or_404(Class, id=selected_class_id)

        class_subject_qs = ClassSubject.objects.filter(
            school_class=selected_class,
            is_active=True
        ).select_related("subject").order_by(
            "subject_rank",
            "subject__subject_name"
        )

        assigned_subject_ids = list(
            class_subject_qs.values_list("subject_id", flat=True)
        )

        subject_rank_map = {
            cs.subject_id: cs.subject_rank for cs in class_subject_qs
        }

    if request.method == "POST":
        form = ClassSubjectAssignForm(request.POST)

        if form.is_valid():
            school_class = form.cleaned_data["school_class"]
            selected_subjects = form.cleaned_data["subjects"]

            full_marks = form.cleaned_data["full_marks"]
            pass_marks = form.cleaned_data["pass_marks"]
            written_marks = form.cleaned_data["written_marks"]
            oral_marks = form.cleaned_data["oral_marks"]
            practical_marks = form.cleaned_data["practical_marks"]

            ClassSubject.objects.filter(
                school_class=school_class
            ).update(is_active=False)

            default_rank = 1

            for subject in selected_subjects:
                rank_value = request.POST.get(f"subject_rank_{subject.id}")

                try:
                    subject_rank = int(rank_value or default_rank)
                except (TypeError, ValueError):
                    subject_rank = default_rank

                ClassSubject.objects.update_or_create(
                    school_class=school_class,
                    subject=subject,
                    defaults={
                        "subject_rank": subject_rank,
                        "full_marks": full_marks,
                        "pass_marks": pass_marks,
                        "written_marks": written_marks,
                        "oral_marks": oral_marks,
                        "practical_marks": practical_marks,
                        "is_active": True,
                    }
                )

                default_rank += 1

            messages.success(request, "✅ Class-wise subjects assigned with rank successfully.")
            return redirect(f"{request.path}?class={school_class.id}")

    else:
        initial_data = {}

        if selected_class:
            initial_data["school_class"] = selected_class
            initial_data["subjects"] = assigned_subject_ids

            first_assigned = ClassSubject.objects.filter(
                school_class=selected_class,
                is_active=True
            ).order_by(
                "subject_rank",
                "subject__subject_name"
            ).first()

            if first_assigned:
                initial_data["full_marks"] = first_assigned.full_marks
                initial_data["pass_marks"] = first_assigned.pass_marks
                initial_data["written_marks"] = first_assigned.written_marks
                initial_data["oral_marks"] = first_assigned.oral_marks
                initial_data["practical_marks"] = first_assigned.practical_marks

        form = ClassSubjectAssignForm(initial=initial_data)

    subjects = Subject.objects.filter(is_active=True).order_by("subject_name")

    subject_rows = []
    for index, subject in enumerate(subjects, start=1):
        subject_rows.append({
            "subject": subject,
            "is_assigned": subject.id in assigned_subject_ids,
            "rank": subject_rank_map.get(subject.id, index),
        })

    class_subjects = ClassSubject.objects.select_related(
        "school_class",
        "subject"
    ).filter(is_active=True).order_by(
        "school_class__class_name",
        "subject_rank",
        "subject__subject_name"
    )

    if selected_class:
        class_subjects = class_subjects.filter(school_class=selected_class)

    return render(request, "academics/class_subject_assign.html", {
        "form": form,
        "classes": Class.objects.filter(is_active=True).order_by("class_name"),
        "subjects": subjects,
        "subject_rows": subject_rows,
        "class_subjects": class_subjects,
        "selected_class": selected_class,
        "assigned_subject_ids": assigned_subject_ids,
    })


# =========================
# SUBJECT RANK MANAGEMENT
# =========================

@login_required
def subject_rank_manage(request):
    if not has_academics_permission(request):
        return permission_denied_redirect(request)

    selected_class_id = request.GET.get("class") or request.POST.get("class")
    selected_class = None
    class_subjects = ClassSubject.objects.none()

    if selected_class_id:
        selected_class = get_object_or_404(Class, id=selected_class_id)
        class_subjects = ClassSubject.objects.select_related(
            "school_class",
            "subject"
        ).filter(
            school_class=selected_class,
            is_active=True
        ).order_by(
            "subject_rank",
            "subject__subject_name"
        )

    if request.method == "POST" and selected_class:
        for cs in class_subjects:
            rank_value = request.POST.get(f"rank_{cs.id}")

            try:
                cs.subject_rank = int(rank_value or 0)
            except (TypeError, ValueError):
                cs.subject_rank = 0

            cs.save(update_fields=["subject_rank"])

        messages.success(request, "✅ Subject rank/order updated successfully.")
        return redirect(f"{request.path}?class={selected_class.id}")

    return render(request, "academics/subject_rank_manage.html", {
        "classes": Class.objects.filter(is_active=True).order_by("class_name"),
        "selected_class": selected_class,
        "class_subjects": class_subjects,
    })


# =========================
# CLASS ROUTINE LIST + ADD
# =========================

@login_required
def class_routine_list(request):
    if not has_academics_permission(request):
        return permission_denied_redirect(request)

    if request.method == "POST":
        form = ClassRoutineForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "✅ Class routine added successfully.")
            return redirect("class_routine_list")
    else:
        form = ClassRoutineForm()

    routines = ClassRoutine.objects.all().order_by(
        "class_name",
        "section",
        "day",
        "start_time"
    )

    return render(request, "academics/class_routine_list.html", {
        "form": form,
        "routines": routines,
    })


# =========================
# CLASS ROUTINE EDIT
# =========================

@login_required
def class_routine_edit(request, pk):
    if not has_academics_permission(request):
        return permission_denied_redirect(request)

    routine_obj = get_object_or_404(ClassRoutine, pk=pk)

    if request.method == "POST":
        form = ClassRoutineForm(request.POST, instance=routine_obj)

        if form.is_valid():
            form.save()
            messages.success(request, "✅ Class routine updated successfully.")
            return redirect("class_routine_list")
    else:
        form = ClassRoutineForm(instance=routine_obj)

    routines = ClassRoutine.objects.all().order_by(
        "class_name",
        "section",
        "day",
        "start_time"
    )

    return render(request, "academics/class_routine_list.html", {
        "form": form,
        "routines": routines,
        "edit_mode": True,
        "routine_obj": routine_obj,
    })


# =========================
# CLASS ROUTINE DELETE
# =========================

@login_required
def class_routine_delete(request, pk):
    if not has_academics_permission(request):
        return permission_denied_redirect(request)

    routine_obj = get_object_or_404(ClassRoutine, pk=pk)

    if request.method == "POST":
        routine_obj.delete()
        messages.success(request, "🗑 Class routine deleted successfully.")
        return redirect("class_routine_list")

    return render(request, "academics/class_routine_confirm_delete.html", {
        "routine_obj": routine_obj,
    })


# =========================
# CLASS ROUTINE PRINT
# =========================

@login_required
def class_routine_print(request):
    if not has_academics_permission(request):
        return permission_denied_redirect(request)

    selected_class = request.GET.get("class_name", "").strip()
    selected_section = request.GET.get("section", "").strip()

    routines = ClassRoutine.objects.filter(is_active=True).order_by(
        "class_name",
        "section",
        "day",
        "start_time"
    )

    if selected_class:
        routines = routines.filter(class_name=selected_class)

    if selected_section:
        routines = routines.filter(section=selected_section)

    classes = ClassRoutine.objects.filter(is_active=True).values_list(
        "class_name",
        flat=True
    ).distinct().order_by("class_name")

    sections = ClassRoutine.objects.filter(is_active=True)

    if selected_class:
        sections = sections.filter(class_name=selected_class)

    sections = sections.values_list(
        "section",
        flat=True
    ).exclude(
        section__isnull=True
    ).exclude(
        section=""
    ).distinct().order_by("section")

    return render(request, "academics/class_routine_print.html", {
        "routines": routines,
        "classes": classes,
        "sections": sections,
        "selected_class": selected_class,
        "selected_section": selected_section,
    })