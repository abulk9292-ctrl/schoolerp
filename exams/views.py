from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q
from django.core.exceptions import FieldError

import qrcode
import base64
from io import BytesIO

from students.models import Student
from settings_app.models import GeneralSetting
from core.context_processors import get_current_session
from behaviour.models import BehaviourRecord, SkillEvaluation

from .models import (
    Exam,
    ExamRoutine,
    ExamResult,
    StudentResultSummary,
    ExamSubjectAssign,
    ClassTest,
    ClassTestResult,
    ClassTestSubjectMark,
)

from .forms import (
    ExamForm,
    ExamRoutineForm,
    ExamResultForm,
    ClassTestForm,
    ClassTestResultForm,
)


# ================================
# HELPERS
# ================================

def get_selected_session(request):
    selected_session = request.session.get("selected_session")

    if not selected_session:
        selected_session = get_current_session()
        request.session["selected_session"] = selected_session

    return selected_session


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def get_general_settings():
    return GeneralSetting.objects.first()


def get_setting_image_url(settings_obj, field_name, fallback):
    if settings_obj:
        image = getattr(settings_obj, field_name, None)
        if image:
            try:
                return image.url
            except Exception:
                return fallback
    return fallback


def get_student_name(student):
    return (
        getattr(student, "name", None)
        or getattr(student, "student_name", None)
        or getattr(student, "full_name", None)
        or str(student)
    )


def apply_student_search(queryset, search):
    if not search:
        return queryset

    q_obj = Q()

    searchable_fields = [
        "name",
        "student_name",
        "full_name",
        "student_id",
        "student_code",
        "roll_no",
        "registration_no",
        "father_name",
    ]

    model_fields = [field.name for field in Student._meta.get_fields()]

    for field in searchable_fields:
        if field in model_fields:
            q_obj |= Q(**{f"{field}__icontains": search})

    if q_obj:
        return queryset.filter(q_obj)

    return queryset

# ================================
# GPA SYSTEM
# ================================

def get_gpa_from_percentage(percentage):
    percentage = float(percentage or 0)

    if percentage >= 90:
        return 5.00
    if percentage >= 80:
        return 4.50
    if percentage >= 60:
        return 4.00
    if percentage >= 45:
        return 3.50
    if percentage >= 40:
        return 3.00
    if percentage >= 35:
        return 2.00
    return 0.00


# ================================
# RESULT / GRADE / RANK HELPERS
# ================================

def get_final_grade(percentage):
    percentage = float(percentage or 0)

    if percentage >= 90:
        return "AA"
    if percentage >= 80:
        return "A+"
    if percentage >= 60:
        return "A"
    if percentage >= 45:
        return "B+"
    if percentage >= 40:
        return "B"
    if percentage >= 35:
        return "C+"
    if percentage >= 24:
        return "C"
    return "D"


def get_result_status(percentage):
    percentage = float(percentage or 0)
    return "Pass" if percentage >= 35 else "Fail"


# ================================
# CLASS / SUBJECT / STUDENT HELPERS
# ================================

def get_all_classes():
    classes = []

    try:
        from academics.models import Class

        classes = list(
            Class.objects.filter(is_active=True)
            .order_by("class_name")
            .values_list("class_name", flat=True)
        )

    except Exception:
        pass

    return classes


def filter_students_by_class(queryset, class_name):
    if not class_name:
        return queryset

    class_text = str(class_name).strip()

    try:
        return queryset.filter(
            class_assigned__class_name=class_text
        )
    except Exception:
        return queryset.none()


def get_subject_names_for_class(class_name):
    subjects = []

    if class_name:
        try:
            from academics.models import Class, ClassSubject

            class_obj = Class.objects.filter(
                class_name=str(class_name).strip(),
                is_active=True
            ).first()

            if class_obj:
                class_subjects = (
                    ClassSubject.objects.filter(
                        school_class=class_obj,
                        is_active=True
                    )
                    .select_related("subject")
                    .order_by("subject_rank", "subject__subject_name")
                )

                for cs in class_subjects:
                    subject_name = cs.subject.subject_name

                    if subject_name and subject_name not in subjects:
                        subjects.append(subject_name)

        except Exception as e:
            print("SUBJECT LOAD ERROR:", e)

    return subjects


def get_class_subject_objects(class_name):
    if not class_name:
        return []

    try:
        from academics.models import Class, ClassSubject

        class_obj = Class.objects.filter(
            class_name=str(class_name).strip(),
            is_active=True
        ).first()

        if class_obj:
            return (
                ClassSubject.objects.filter(
                    school_class=class_obj,
                    is_active=True
                )
                .select_related("subject")
                .order_by("subject_rank", "subject__subject_name")
            )

    except Exception as e:
        print("CLASS SUBJECT OBJECT LOAD ERROR:", e)

    return []


# ================================
# SUBJECT RANK / DISPLAY ORDER HELPERS
# ================================

def get_subject_rank_map(class_name):
    """
    ClassSubject.subject_rank অনুযায়ী subject order map তৈরি করে।
    যেসব subject-এর rank 0/blank থাকবে, সেগুলো শেষে subject name অনুযায়ী যাবে।
    """
    rank_map = {}

    if not class_name:
        return rank_map

    try:
        from academics.models import Class, ClassSubject

        class_obj = Class.objects.filter(
            class_name=str(class_name).strip(),
            is_active=True
        ).first()

        if not class_obj:
            return rank_map

        class_subjects = (
            ClassSubject.objects.filter(
                school_class=class_obj,
                is_active=True
            )
            .select_related("subject")
            .order_by("subject_rank", "subject__subject_name")
        )

        for index, cs in enumerate(class_subjects, start=1):
            subject_name = getattr(cs.subject, "subject_name", "") or str(cs.subject)
            subject_rank = getattr(cs, "subject_rank", 0) or 9999

            rank_map[str(subject_name).strip()] = (
                subject_rank,
                index,
                str(subject_name).strip().lower()
            )

    except Exception as e:
        print("SUBJECT RANK MAP ERROR:", e)

    return rank_map


def order_subject_names_by_class_rank(subject_names, class_name):
    """
    Result List / Merit / Subject headings-এ alphabetic order না দিয়ে
    ClassSubject.subject_rank অনুযায়ী subject arrange করে।
    """
    subject_list = list(subject_names or [])
    rank_map = get_subject_rank_map(class_name)

    if not rank_map:
        return sorted(subject_list)

    return sorted(
        subject_list,
        key=lambda subject: rank_map.get(
            str(subject).strip(),
            (9999, 9999, str(subject).strip().lower())
        )
    )


def sort_exam_results_by_subject_rank(results, class_name):
    """
    Report Card / Bulk Report Card-এ subject rows rank অনুযায়ী দেখানোর জন্য।
    """
    result_list = list(results or [])
    rank_map = get_subject_rank_map(class_name)

    if not rank_map:
        return sorted(result_list, key=lambda r: str(getattr(r, "subject", "")).lower())

    return sorted(
        result_list,
        key=lambda r: rank_map.get(
            str(getattr(r, "subject", "")).strip(),
            (9999, 9999, str(getattr(r, "subject", "")).strip().lower())
        )
    )


def get_students_queryset():
    qs = Student.objects.all()

    try:
        qs = qs.select_related(
            "class_assigned",
            "current_session"
        )
    except Exception:
        pass

    return qs.order_by(
        "class_assigned__class_name",
        "section",
        "roll_no",
        "student_name",
        "id"
    )


# ================================
# AUTO SUMMARY / GRADE GENERATOR
# ================================

def update_student_summary(student, exam):
    session = exam.academic_session

    results = ExamResult.objects.filter(
        student=student,
        exam=exam,
        academic_session=session
    )

    total_marks = sum((r.total_marks or 0) for r in results)
    max_total_marks = sum((r.max_marks or 0) for r in results)

    percentage = 0
    if max_total_marks > 0:
        percentage = round((total_marks / max_total_marks) * 100, 2)

    grade = get_final_grade(percentage)
    result_status = get_result_status(percentage)
    gpa = get_gpa_from_percentage(percentage)

    summary_defaults = {
        "total_marks": total_marks,
        "max_total_marks": max_total_marks,
        "percentage": percentage,
        "grade": grade,
        "result_status": result_status,
    }

    # GPA field jodi models.py te thake tahole save hobe.
    # Na thakle views.py crash korbe na.
    summary_field_names = [
        field.name for field in StudentResultSummary._meta.get_fields()
    ]

    if "gpa" in summary_field_names:
        summary_defaults["gpa"] = gpa

    StudentResultSummary.objects.update_or_create(
        student=student,
        exam=exam,
        academic_session=session,
        defaults=summary_defaults
    )


# ================================
# AUTO RANK GENERATOR
# ================================

def generate_rank(exam, class_name=None, section=None):
    session = exam.academic_session

    summaries = StudentResultSummary.objects.filter(
        exam=exam,
        academic_session=session,
        max_total_marks__gt=0
    ).select_related(
        "student",
        "student__class_assigned"
    )

    if class_name:
        summaries = summaries.filter(
            student__class_assigned__class_name=str(class_name).strip()
        )

    if section:
        summaries = summaries.filter(
            student__section=str(section).strip()
        )

    summaries = summaries.order_by(
        "student__class_assigned__class_name",
        "student__section",
        "-percentage",
        "-total_marks",
        "student__roll_no",
        "student__id"
    )

    grouped = {}

    for summary in summaries:
        class_key = summary.student.class_assigned.class_name
        section_key = summary.student.section or ""
        group_key = f"{class_key}__{section_key}"

        grouped.setdefault(group_key, []).append(summary)

    for group_items in grouped.values():
        rank = 0
        previous_percentage = None
        previous_total = None

        for index, summary in enumerate(group_items, start=1):
            if (
                previous_percentage == summary.percentage
                and previous_total == summary.total_marks
            ):
                summary.rank = rank
            else:
                rank = index
                summary.rank = rank

            previous_percentage = summary.percentage
            previous_total = summary.total_marks

            summary.save(update_fields=["rank"])


# ================================
# UPDATE ALL STUDENTS RESULT SUMMARY
# ================================

def update_all_students_summary(exam):
    session = exam.academic_session

    student_ids = ExamResult.objects.filter(
        exam=exam,
        academic_session=session
    ).values_list("student_id", flat=True).distinct()

    students = Student.objects.filter(
        id__in=student_ids
    ).select_related(
        "class_assigned",
        "current_session"
    )

    for student in students:
        update_student_summary(student, exam)

    generate_rank(exam)
    

# ================================
# DASHBOARD
# ================================

@login_required
def exam_dashboard(request):
    selected_session = get_selected_session(request)

    return render(request, "exams/exam_dashboard.html", {
        "total_exams": Exam.objects.filter(academic_session=selected_session).count(),
        "total_results": ExamResult.objects.filter(academic_session=selected_session).count(),
        "passed": StudentResultSummary.objects.filter(
            academic_session=selected_session,
            result_status="Pass"
        ).count(),
        "failed": StudentResultSummary.objects.filter(
            academic_session=selected_session,
            result_status="Fail"
        ).count(),
        "classes": get_all_classes(),
        "exams": Exam.objects.filter(academic_session=selected_session).order_by("-id"),
        "routines": ExamRoutine.objects.select_related("exam").filter(
            academic_session=selected_session
        ).order_by("-exam__id", "date", "start_time")[:20],
        "settings_obj": get_general_settings(),
        "selected_session": selected_session,
    })


# ================================
# EXAM SETUP
# ================================

@login_required
def exam_add(request):
    selected_session = get_selected_session(request)

    form = ExamForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            exam = form.save(commit=False)
            exam.academic_session = selected_session
            exam.save()

            messages.success(request, "Exam saved successfully.")
            return redirect("exam_dashboard")

        messages.error(request, "Please correct the errors below.")

    return render(request, "exams/exam_form.html", {
        "form": form,
        "page_title": "Add Exam",
        "classes": get_all_classes(),
        "settings_obj": get_general_settings(),
        "selected_session": selected_session,
    })


# ================================
# EXAM EDIT
# ================================

@login_required
def exam_edit(request, pk):
    selected_session = get_selected_session(request)

    exam = get_object_or_404(
        Exam,
        pk=pk,
        academic_session=selected_session
    )

    form = ExamForm(
        request.POST or None,
        instance=exam
    )

    if request.method == "POST":
        if form.is_valid():
            exam_obj = form.save(commit=False)
            exam_obj.academic_session = selected_session
            exam_obj.save()

            messages.success(
                request,
                "Exam updated successfully."
            )

            return redirect("exam_dashboard")

        messages.error(
            request,
            "Please correct the errors."
        )

    return render(request, "exams/exam_form.html", {
        "form": form,
        "page_title": "Edit Exam",
        "classes": get_all_classes(),
        "settings_obj": get_general_settings(),
        "selected_session": selected_session,
    })


# ================================
# EXAM DELETE
# ================================

@login_required
def exam_delete(request, pk):
    selected_session = get_selected_session(request)

    exam = get_object_or_404(
        Exam,
        pk=pk,
        academic_session=selected_session
    )

    exam.delete()

    messages.success(
        request,
        "Exam deleted successfully."
    )

    return redirect("exam_dashboard")


# ================================
# ROUTINE EDIT
# ================================

@login_required
def exam_routine_edit(request, pk):
    selected_session = get_selected_session(request)

    routine = get_object_or_404(
        ExamRoutine,
        pk=pk,
        academic_session=selected_session
    )

    form = ExamRoutineForm(
        request.POST or None,
        instance=routine,
        selected_session=selected_session
    )

    if request.method == "POST":
        if form.is_valid():
            routine_obj = form.save(commit=False)
            routine_obj.academic_session = selected_session
            routine_obj.save()

            messages.success(
                request,
                "Routine updated successfully."
            )

            return redirect("exam_routine")

        messages.error(
            request,
            "Please correct the routine form."
        )

    return render(request, "exams/exam_routine_form.html", {
        "form": form,
        "page_title": "Edit Routine",
        "classes": get_all_classes(),
        "settings_obj": get_general_settings(),
        "selected_session": selected_session,
    })


# ================================
# ROUTINE DELETE
# ================================

@login_required
def exam_routine_delete(request, pk):
    selected_session = get_selected_session(request)

    routine = get_object_or_404(
        ExamRoutine,
        pk=pk,
        academic_session=selected_session
    )

    routine.delete()

    messages.success(
        request,
        "Routine deleted successfully."
    )

    return redirect("exam_routine")


# ================================
# ROUTINE
# ================================

@login_required
def exam_routine(request):
    selected_session = get_selected_session(request)

    selected_class = request.GET.get("class") or request.POST.get("school_class") or request.POST.get("class")
    selected_section = request.GET.get("section") or request.POST.get("section")

    form_data = request.POST.copy() if request.method == "POST" else None

    if request.method == "POST":
        form = ExamRoutineForm(form_data, selected_session=selected_session)

        if form.is_valid():
            routine = form.save(commit=False)
            routine.academic_session = selected_session

            if selected_class:
                routine.school_class = selected_class

            routine.save()

            messages.success(request, "Routine saved successfully.")
            return redirect(f"{reverse('exam_routine')}?class={routine.school_class}")

        messages.error(request, "Please correct the routine form.")

    else:
        initial_data = {}

        if selected_class:
            initial_data["school_class"] = selected_class

        form = ExamRoutineForm(initial=initial_data, selected_session=selected_session)

    routines = ExamRoutine.objects.select_related("exam").filter(
        academic_session=selected_session
    ).order_by(
        "-exam__id", "date", "start_time"
    )

    if selected_class:
        routines = routines.filter(school_class=selected_class)

    if selected_section:
        routines = routines.filter(section=selected_section)

    return render(request, "exams/exam_routine.html", {
        "form": form,
        "routines": routines,
        "page_title": "Exam Routine",
        "classes": get_all_classes(),
        "selected_class": selected_class,
        "selected_section": selected_section,
        "settings_obj": get_general_settings(),
        "selected_session": selected_session,
    })


# ================================
# SINGLE MARK ENTRY
# ================================

@login_required
def result_add(request):
    selected_session = get_selected_session(request)

    selected_class = request.GET.get("class") or request.POST.get("class")
    selected_student_id = request.GET.get("student") or request.POST.get("student")
    selected_exam_id = request.GET.get("exam") or request.POST.get("exam")

    classes = get_all_classes()
    exams = Exam.objects.filter(
        academic_session=selected_session
    ).order_by("-id")

    students = get_students_queryset()
    students = filter_students_by_class(students, selected_class)

    selected_student = None
    selected_exam = None
    subjects = []

    if selected_student_id:
        selected_student = get_object_or_404(Student, id=selected_student_id)

    if selected_exam_id:
        selected_exam = get_object_or_404(
            Exam,
            id=selected_exam_id,
            academic_session=selected_session
        )

    if selected_class:
        subjects = get_class_subject_objects(selected_class)

    if request.method == "POST":
        if not selected_class:
            messages.error(request, "Please select class.")
            return redirect("result_add")

        if not selected_student:
            messages.error(request, "Please select student.")
            return redirect(f"{reverse('result_add')}?class={selected_class}")

        if not selected_exam:
            messages.error(request, "Please select exam.")
            return redirect(f"{reverse('result_add')}?class={selected_class}&student={selected_student_id}")

        saved_count = 0

        for cs in subjects:
            subject_name = cs.subject.subject_name

            written_key = f"written_{cs.subject.id}"
            oral_key = f"oral_{cs.subject.id}"
            max_key = f"max_{cs.subject.id}"
            absent_key = f"absent_{cs.subject.id}"

            is_absent = request.POST.get(absent_key)

            written_marks = 0 if is_absent else safe_int(request.POST.get(written_key), 0)
            oral_marks = 0 if is_absent else safe_int(request.POST.get(oral_key), 0)
            max_marks = safe_int(request.POST.get(max_key), getattr(cs, "full_marks", 100) or 100)

            if written_marks + oral_marks > max_marks:
                messages.error(
                    request,
                    f"{subject_name}: Written + Oral marks cannot be greater than Max Marks."
                )
                return redirect(
                    f"{reverse('result_add')}?class={selected_class}&student={selected_student.id}&exam={selected_exam.id}"
                )

            if is_absent or written_marks > 0 or oral_marks > 0:
                ExamResult.objects.update_or_create(
                    student=selected_student,
                    exam=selected_exam,
                    academic_session=selected_session,
                    subject=subject_name,
                    defaults={
                        "section": getattr(selected_student, "section", "") or "",
                        "written_marks": written_marks,
                        "oral_marks": oral_marks,
                        "max_marks": max_marks,
                        "remarks": "Absent" if is_absent else "",
                    }
                )
                saved_count += 1

        update_student_summary(selected_student, selected_exam)
        generate_rank(selected_exam)

        messages.success(request, f"{saved_count} subject mark(s) saved successfully.")
        return redirect(
            f"{reverse('result_add')}?class={selected_class}&student={selected_student.id}&exam={selected_exam.id}"
        )

    saved_marks = {}

    if selected_student and selected_exam:
        old_results = ExamResult.objects.filter(
            student=selected_student,
            exam=selected_exam,
            academic_session=selected_session
        )

        for r in old_results:
            saved_marks[r.subject] = r

    return render(request, "exams/result_form.html", {
        "classes": classes,
        "students": students,
        "exams": exams,
        "subjects": subjects,
        "selected_class": selected_class,
        "selected_student": selected_student,
        "selected_student_id": selected_student_id,
        "selected_exam": selected_exam,
        "selected_exam_id": selected_exam_id,
        "saved_marks": saved_marks,
        "page_title": "Add Student Marks",
        "settings_obj": get_general_settings(),
        "selected_session": selected_session,
    })

# ================================
# OPTIMIZED RESULT LIST
# ================================

@login_required
def result_list(request):
    selected_session = get_selected_session(request)

    exam_id = request.GET.get("exam", "").strip()
    class_name = request.GET.get("class", "").strip()
    selected_section = request.GET.get("section", "").strip()
    search = request.GET.get("search", "").strip()

    exams = Exam.objects.filter(
        academic_session=selected_session
    ).order_by("-id")

    classes = get_all_classes()

    selected_exam = None

    students = get_students_queryset()

    if class_name:
        students = filter_students_by_class(students, class_name)

    if selected_section:
        students = students.filter(section=selected_section)

    students = apply_student_search(students, search)

    summaries = StudentResultSummary.objects.none()
    subjects = []
    result_rows = []

    if exam_id:
        selected_exam = get_object_or_404(
            Exam,
            id=exam_id,
            academic_session=selected_session
        )

        update_all_students_summary(selected_exam)
        generate_rank(
            selected_exam,
            class_name=class_name if class_name else None,
            section=selected_section if selected_section else None
        )

        results = ExamResult.objects.filter(
            exam=selected_exam,
            academic_session=selected_session,
            student_id__in=students.values_list("id", flat=True)
        ).select_related(
            "student",
            "student__class_assigned",
            "exam"
        ).order_by(
            "student__roll_no",
            "student__student_name",
            "subject"
        )

        subjects = list(
            results.values_list("subject", flat=True)
            .distinct()
            .order_by("subject")
        )

        subjects = order_subject_names_by_class_rank(
            subjects,
            class_name
        )

        summaries = StudentResultSummary.objects.filter(
            exam=selected_exam,
            academic_session=selected_session,
            student_id__in=students.values_list("id", flat=True)
        ).select_related(
            "student",
            "student__class_assigned",
            "exam"
        ).order_by(
            "student__class_assigned__class_name",
            "student__section",
            "rank",
            "student__roll_no",
            "student__student_name"
        )

        result_map = {}

        for r in results:
            result_map.setdefault(r.student_id, {})
            result_map[r.student_id][r.subject] = r

        for summary in summaries:
            subject_marks = []

            for subject in subjects:
                mark = result_map.get(summary.student_id, {}).get(subject)

                subject_marks.append({
                    "subject": subject,
                    "mark": mark,
                    "total": mark.total_marks if mark else "-",
                    "max": mark.max_marks if mark else "-",
                    "grade": mark.grade if mark else "-",
                })

            result_rows.append({
                "summary": summary,
                "student": summary.student,
                "subject_marks": subject_marks,
            })

    total_students = summaries.count() if exam_id else 0
    pass_count = summaries.filter(result_status="Pass").count() if exam_id else 0
    fail_count = summaries.filter(result_status="Fail").count() if exam_id else 0

    avg_percentage = 0
    if total_students:
        total_percentage = sum((s.percentage or 0) for s in summaries)
        avg_percentage = round(total_percentage / total_students, 2)

    return render(request, "exams/result_list.html", {
        "result_rows": result_rows,
        "subjects": subjects,
        "exams": exams,
        "classes": classes,
        "selected_exam": selected_exam,
        "selected_exam_id": exam_id,
        "selected_class": class_name,
        "selected_section": selected_section,
        "search": search,
        "total_students": total_students,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "avg_percentage": avg_percentage,
        "settings_obj": get_general_settings(),
        "selected_session": selected_session,
    })

@login_required
def result_sheet_select(request):
    selected_session = get_selected_session(request)

    exams = Exam.objects.filter(
        academic_session=selected_session
    ).order_by("-id")

    classes = get_all_classes()

    return render(request, "exams/result_sheet_select.html", {
        "exams": exams,
        "classes": classes,
        "settings_obj": get_general_settings(),
        "selected_session": selected_session,
    })


# ================================
# BULK MARKS ENTRY
# ================================

@login_required
def bulk_result_entry(request):
    selected_session = get_selected_session(request)

    exams = Exam.objects.filter(
        academic_session=selected_session
    ).order_by("-id")

    classes = get_all_classes()

    selected_exam_id = request.GET.get("exam") or request.POST.get("exam")
    selected_class = request.GET.get("class") or request.POST.get("class")

    students = get_students_queryset()
    students = filter_students_by_class(students, selected_class)

    subjects = get_class_subject_objects(selected_class)

    if request.method == "POST":
        if not selected_exam_id:
            messages.error(request, "Please select exam.")
            return redirect("bulk_result_entry")

        if not selected_class:
            messages.error(request, "Please select class.")
            return redirect("bulk_result_entry")

        exam = get_object_or_404(
            Exam,
            id=selected_exam_id,
            academic_session=selected_session
        )

        for student in students:
            for cs in subjects:
                subject_name = cs.subject.subject_name

                written_key = f"written_{student.id}_{cs.subject.id}"
                oral_key = f"oral_{student.id}_{cs.subject.id}"
                absent_key = f"absent_{student.id}_{cs.subject.id}"

                is_absent = request.POST.get(absent_key)

                written_marks = 0 if is_absent else safe_int(request.POST.get(written_key), 0)
                oral_marks = 0 if is_absent else safe_int(request.POST.get(oral_key), 0)
                max_marks = getattr(cs, 'full_marks', None) or getattr(cs, 'total_marks', None) or 100

                if written_marks + oral_marks > max_marks:
                    messages.error(
                        request,
                        f"{get_student_name(student)} - {subject_name}: marks cannot be greater than max marks."
                    )
                    return redirect(
                        f"{reverse('bulk_result_entry')}?exam={exam.id}&class={selected_class}"
                    )

                if is_absent or written_marks > 0 or oral_marks > 0:
                    ExamResult.objects.update_or_create(
                        student=student,
                        exam=exam,
                        academic_session=selected_session,
                        subject=subject_name,
                        defaults={
                            "section": getattr(student, "section", "") or "",
                            "written_marks": written_marks,
                            "oral_marks": oral_marks,
                            "max_marks": max_marks,
                            "remarks": "Absent" if is_absent else "",
                        }
                    )

        update_all_students_summary(exam)

        messages.success(request, "Bulk marks saved successfully.")
        return redirect(
            f"{reverse('bulk_result_entry')}?exam={exam.id}&class={selected_class}"
        )

    saved_marks = {}

    if selected_exam_id:
        try:
            exam_obj = Exam.objects.get(
                id=selected_exam_id,
                academic_session=selected_session
            )

            old_results = ExamResult.objects.filter(
                exam=exam_obj,
                academic_session=selected_session
            )

            for r in old_results:
                saved_marks[f"{r.student_id}_{r.subject}"] = {
                    "written": r.written_marks,
                    "oral": r.oral_marks,
                    "remarks": r.remarks,
                }

        except Exception:
            pass

    return render(request, "exams/bulk_entry.html", {
        "students": students,
        "subjects": subjects,
        "exams": exams,
        "classes": classes,
        "selected_exam_id": selected_exam_id,
        "selected_class": selected_class,
        "saved_marks": saved_marks,
        "settings_obj": get_general_settings(),
        "selected_session": selected_session,
    })


# ================================
# POPUP ENTRY
# ================================

@login_required
def popup_result_entry(request):
    selected_session = get_selected_session(request)

    exams = Exam.objects.filter(
        academic_session=selected_session
    ).order_by("-id")

    classes = get_all_classes()

    exam_id = request.GET.get("exam") or request.POST.get("exam")
    class_name = request.GET.get("class") or request.POST.get("class")
    selected_section = request.GET.get("section") or request.POST.get("section")
    search = request.GET.get("search", "").strip()

    selected_exam = None

    students = get_students_queryset()
    students = filter_students_by_class(students, class_name)

    if selected_section:
        students = students.filter(section=selected_section)

    students = apply_student_search(students, search)

    subject_names = get_subject_names_for_class(class_name)

    if exam_id:
        selected_exam = get_object_or_404(
            Exam,
            id=exam_id,
            academic_session=selected_session
        )

    if request.method == "POST":
        student_id = request.POST.get("student")
        exam_post_id = request.POST.get("exam")

        if not student_id:
            messages.error(request, "Please select a student.")
            return redirect(
                f"{reverse('popup_result_entry')}?exam={exam_id or ''}&class={class_name or ''}&section={selected_section or ''}&search={search or ''}"
            )

        if not exam_post_id:
            messages.error(request, "Please select an exam.")
            return redirect("popup_result_entry")

        student = get_object_or_404(Student, id=student_id)

        exam = get_object_or_404(
            Exam,
            id=exam_post_id,
            academic_session=selected_session
        )

        subject_list = request.POST.getlist("subject[]")
        written_list = request.POST.getlist("written_marks[]")
        oral_list = request.POST.getlist("oral_marks[]")
        max_list = request.POST.getlist("max_marks[]")

        saved_count = 0

        for i, subject in enumerate(subject_list):
            subject = str(subject).strip()

            if not subject:
                continue

            written_marks = safe_int(written_list[i], 0) if i < len(written_list) else 0
            oral_marks = safe_int(oral_list[i], 0) if i < len(oral_list) else 0
            max_marks = safe_int(max_list[i], 100) if i < len(max_list) else 100

            if written_marks + oral_marks > max_marks:
                messages.error(
                    request,
                    f"{subject}: Written + Oral marks cannot be greater than Max Marks."
                )
                return redirect(
                    f"{reverse('popup_result_entry')}?exam={exam.id}&class={class_name or ''}&section={selected_section or ''}&search={search or ''}"
                )

            ExamResult.objects.update_or_create(
                student=student,
                exam=exam,
                academic_session=selected_session,
                subject=subject,
                defaults={
                    "section": getattr(student, "section", "") or "",
                    "written_marks": written_marks,
                    "oral_marks": oral_marks,
                    "max_marks": max_marks,
                }
            )

            saved_count += 1

        update_student_summary(student, exam)
        update_all_students_summary(exam)
        generate_rank(exam)

        messages.success(request, f"{saved_count} subject mark(s) saved successfully.")

        return redirect(
            f"{reverse('popup_result_entry')}?exam={exam.id}&class={class_name or ''}&section={selected_section or ''}&search={search or ''}"
        )

    summaries = []

    if selected_exam:
        update_all_students_summary(selected_exam)
        generate_rank(selected_exam)

        for student in students:
            summary = StudentResultSummary.objects.filter(
                student=student,
                exam=selected_exam,
                academic_session=selected_session
            ).first()

            subject_marks = []

            for subject_name in subject_names:
                result = ExamResult.objects.filter(
                    student=student,
                    exam=selected_exam,
                    academic_session=selected_session,
                    subject=subject_name
                ).first()

                subject_marks.append({
                    "name": subject_name,
                    "marks": result.total_marks if result else "",
                    "written": result.written_marks if result else "",
                    "oral": result.oral_marks if result else "",
                    "max": result.max_marks if result else 100,
                })

            summaries.append({
                "student": student,
                "summary": summary,
                "subject_marks": subject_marks,
            })

    return render(request, "exams/popup_entry.html", {
        "students": students,
        "summaries": summaries,
        "subjects": subject_names,
        "exams": exams,
        "classes": classes,
        "selected_exam": selected_exam,
        "selected_exam_id": exam_id,
        "selected_class": class_name,
        "selected_section": selected_section,
        "search": search,
        "settings_obj": get_general_settings(),
        "selected_session": selected_session,
    })


# ================================
# REPORT CARD
# ================================

@login_required
def report_card_select(request):
    selected_session = get_selected_session(request)

    settings_obj = get_general_settings()
    classes = get_all_classes()

    selected_class = request.GET.get("class")
    selected_section = request.GET.get("section")

    students = get_students_queryset()
    students = filter_students_by_class(
        students,
        selected_class
    )

    if selected_section:
        students = students.filter(
            section=selected_section
        )

    exams = Exam.objects.filter(
        academic_session=selected_session
    ).order_by("-id")

    student_id = request.GET.get("student_id")
    exam_id = request.GET.get("exam_id")

    if student_id and exam_id:
        student = get_object_or_404(Student, id=student_id)

        exam = get_object_or_404(
            Exam,
            id=exam_id,
            academic_session=selected_session
        )

        update_student_summary(student, exam)
        generate_rank(exam)

        results = ExamResult.objects.filter(
            student=student,
            exam=exam,
            academic_session=selected_session
        ).order_by("id")

        results = sort_exam_results_by_subject_rank(
            results,
            getattr(student.class_assigned, "class_name", "")
        )

        written_total = sum(r.written_marks for r in results)
        oral_total = sum(r.oral_marks for r in results)
        grand_total = sum(r.total_marks for r in results)
        max_total = sum(r.max_marks for r in results)

        percentage = 0
        if max_total > 0:
            percentage = round((grand_total / max_total) * 100, 2)

        final_grade = get_final_grade(percentage)
        result_status = "Pass" if percentage >= 35 else "Fail"
        gpa = get_gpa_from_percentage(percentage)

        summary = StudentResultSummary.objects.filter(
            student=student,
            exam=exam,
            academic_session=selected_session
        ).first()

        class_rank = summary.rank if summary else "-"

        attendance_percentage = 0

        try:
            from attendance.models import StudentAttendance

            attendance_records = StudentAttendance.objects.filter(student=student)

            try:
                attendance_records = attendance_records.filter(
                    session__session_name=selected_session
                )
            except Exception:
                pass

            total_days = attendance_records.count()
            present_days = attendance_records.filter(status__iexact="Present").count()

            if total_days > 0:
                attendance_percentage = round((present_days / total_days) * 100, 2)

        except Exception:
            attendance_percentage = 0

        roll_no = getattr(student, "roll_no", "") or "-"
        registration_no = getattr(student, "registration_no", "") or "-"
        result_no = f"ARM-RESULT-{student.id}-{exam.id}"

                # =====================================
        # AUTO QR CODE GENERATOR
        # =====================================

        qr_text = f"""
        AL RAHMAN MISSION RESULT

        Student: {student.student_name}
        Student ID: {student.student_id}
        Roll: {student.roll_no}

        Class: {student.class_assigned}
        Section: {student.section}

        Exam: {exam.name}
        Session: {selected_session}

        Total: {grand_total}/{max_total}
        Percentage: {percentage}%
        Grade: {final_grade}

        Result: {result_status}
        Rank: {class_rank}
        """

        qr = qrcode.QRCode(
            version=1,
            box_size=5,
            border=2,
        )

        qr.add_data(qr_text)
        qr.make(fit=True)

        qr_img = qr.make_image(
            fill_color="black",
            back_color="white"
        )

        buffer = BytesIO()

        qr_img.save(buffer, format="PNG")

        qr_code = (
            "data:image/png;base64,"
            + base64.b64encode(
                buffer.getvalue()
            ).decode()
        )

        behaviour_records = BehaviourRecord.objects.filter(
            student=student
        ).order_by("-date", "-id")[:5]

        positive_behaviour_count = BehaviourRecord.objects.filter(
            student=student,
            behaviour_type="Positive"
        ).count()

        negative_behaviour_count = BehaviourRecord.objects.filter(
            student=student,
            behaviour_type="Negative"
        ).count()

        latest_skill = SkillEvaluation.objects.filter(
            student=student
        ).order_by("-year", "-id").first()

                # =====================================
        # AI REPORT CARD ENGINE
        # =====================================

        student_health_index = 100
        ai_risk_level = "Low Risk"
        pass_probability = 50
        fail_probability = 50
        ai_remark = ""
        ai_recommendation = ""
        performance_badge = "Average"

        behaviour_score = 100

        behaviour_score = (
            100
            + (positive_behaviour_count * 2)
            - (negative_behaviour_count * 5)
        )

        if behaviour_score > 100:
            behaviour_score = 100

        if behaviour_score < 0:
            behaviour_score = 0

        student_health_index = (
            (attendance_percentage * 0.30)
            + (percentage * 0.50)
            + (behaviour_score * 0.20)
        )

        if student_health_index > 100:
            student_health_index = 100

        student_health_index = round(
            student_health_index,
            2
        )

        pass_probability = round(
            student_health_index,
            2
        )

        fail_probability = round(
            100 - pass_probability,
            2
        )

        risk_points = 0

        if attendance_percentage < 75:
            risk_points += 30

        if percentage < 40:
            risk_points += 40

        if negative_behaviour_count >= 5:
            risk_points += 25

        if risk_points >= 70:
            ai_risk_level = "High Risk"

        elif risk_points >= 40:
            ai_risk_level = "Medium Risk"

        else:
            ai_risk_level = "Low Risk"

        # =====================================
        # AI REMARK
        # =====================================

        if percentage >= 90:
            ai_remark = (
                "Outstanding academic performance detected."
            )

            performance_badge = "Top Performer"

            ai_recommendation = (
                "Recommended for scholarship and leadership activities."
            )

        elif percentage >= 75:
            ai_remark = (
                "Very good and stable academic performance."
            )

            performance_badge = "Excellent"

            ai_recommendation = (
                "Maintain current consistency."
            )

        elif percentage >= 50:
            ai_remark = (
                "Average performance with improvement potential."
            )

            performance_badge = "Improving"

            ai_recommendation = (
                "Needs more subject practice and revision."
            )

        else:
            ai_remark = (
                "Academic performance requires immediate attention."
            )

            performance_badge = "Needs Attention"

            ai_recommendation = (
                "Special academic guidance strongly recommended."
            )

        return render(request, "exams/report_card.html", {
            "student": student,
            "exam": exam,
            "results": results,
            "written_total": written_total,
            "oral_total": oral_total,
            "grand_total": grand_total,
            "max_total": max_total,
            "percentage": percentage,
            "final_grade": final_grade,
            "result_status": result_status,
            "gpa": gpa,
            "class_rank": class_rank,
            "roll_no": roll_no,
            "registration_no": registration_no,
            "result_no": result_no,
            "attendance_percentage": attendance_percentage,
            "academic_session": selected_session,
            "classes": classes,
            "selected_class": selected_class,
            "selected_section": selected_section,
            "settings_obj": settings_obj,
            "header_url": get_setting_image_url(settings_obj, "school_header", "/static/images/header.jpg"),
            "logo_url": get_setting_image_url(settings_obj, "school_logo", "/static/images/logo.png"),
            "principal_sign": get_setting_image_url(settings_obj, "principal_signature", "/static/images/principal_sign.png"),
            "qr_code": qr_code,
            "behaviour_records": behaviour_records,
            "positive_behaviour_count": positive_behaviour_count,
            "negative_behaviour_count": negative_behaviour_count,
            "latest_skill": latest_skill,
            "selected_session": selected_session,
            "ai_remark": ai_remark,
            "ai_recommendation": ai_recommendation,
            "performance_badge": performance_badge,
            "student_health_index": student_health_index,
            "ai_risk_level": ai_risk_level,
            "pass_probability": pass_probability,
            "fail_probability": fail_probability,
            "ai_remark": ai_remark,
            "ai_recommendation": ai_recommendation,
            "performance_badge": performance_badge,
            "behaviour_score": behaviour_score,
        })

    return render(request, "exams/report_card_select.html", {
        "students": students,
        "exams": exams,
        "classes": classes,
        "selected_class": selected_class,
        "selected_section": selected_section,
        "settings_obj": settings_obj,
        "selected_session": selected_session,
    })


# ================================
# BULK REPORT CARD
# ================================

@login_required
def report_card_bulk_select(request):
    selected_session = get_selected_session(request)

    exams = Exam.objects.filter(
        academic_session=selected_session
    ).order_by("-id")

    classes = get_all_classes()

    return render(request, "exams/report_card_bulk_select.html", {
        "exams": exams,
        "classes": classes,
        "settings_obj": get_general_settings(),
        "selected_session": selected_session,
    })


@login_required
def report_card_bulk_print(request):
    selected_session = get_selected_session(request)

    exam_id = request.GET.get("exam")
    selected_class = request.GET.get("class")
    selected_section = request.GET.get("section")

    exam = Exam.objects.filter(
        id=exam_id,
        academic_session=selected_session
    ).first() if exam_id else None

    cards = []

    students = Student.objects.all().order_by("roll_no", "student_name")

    if selected_class:
        filtered_students = []

        for student in students:
            student_class_obj = getattr(student, "class_assigned", None)

            student_class_id = str(getattr(student_class_obj, "id", ""))
            student_class_text = str(student_class_obj).strip()

            if (
                selected_class == student_class_id
                or selected_class.strip().lower() == student_class_text.lower()
            ):
                filtered_students.append(student)

        students = filtered_students

    if selected_section:
        students = [
            s for s in students
            if getattr(s, "section", "") == selected_section
        ]

    for student in students:
        results = ExamResult.objects.filter(
            student=student,
            exam_id=exam_id,
            academic_session=selected_session
        )

        if not results.exists():
            continue

        results = sort_exam_results_by_subject_rank(
            results,
            getattr(student.class_assigned, "class_name", "")
        )

        written_total = 0
        oral_total = 0
        grand_total = 0
        max_total = 0

        for r in results:
            written = getattr(r, "written_marks", 0) or 0
            oral = getattr(r, "oral_marks", 0) or 0
            total = getattr(r, "total_marks", 0) or 0
            max_marks = getattr(r, "max_marks", 100) or 100

            written_total += written
            oral_total += oral
            grand_total += total
            max_total += max_marks

        percentage = 0
        if max_total > 0:
            percentage = round((grand_total / max_total) * 100, 2)

        final_grade = get_final_grade(percentage)
        result_status = "Pass" if percentage >= 35 else "Fail"
        gpa = get_gpa_from_percentage(percentage)

        summary = StudentResultSummary.objects.filter(
            student=student,
            exam=exam,
            academic_session=selected_session
        ).first()

        # ================= ATTENDANCE =================
        attendance_percentage = 0

        try:
            from attendance.models import StudentAttendance

            attendance_records = StudentAttendance.objects.filter(
                student=student
            )

            try:
                attendance_records = attendance_records.filter(
                    session__session_name=selected_session
                )
            except Exception:
                pass

            total_days = attendance_records.count()
            present_days = attendance_records.filter(
                status__iexact="Present"
            ).count()

            if total_days > 0:
                attendance_percentage = round(
                    (present_days / total_days) * 100,
                    2
                )

        except Exception:
            attendance_percentage = 0

        # ================= QR CODE =================
        qr_text = f"""
AL RAHMAN MISSION RESULT

Student: {student.student_name}
Student ID: {student.student_id}
Roll: {student.roll_no}

Class: {student.class_assigned}
Section: {student.section}

Exam: {exam.name if exam else "-"}
Session: {selected_session}

Total: {grand_total}/{max_total}
Percentage: {percentage}%
Grade: {final_grade}
GPA: {gpa}

Result: {result_status}
Rank: {summary.rank if summary else "-"}
"""

        qr = qrcode.QRCode(
            version=1,
            box_size=4,
            border=2,
        )

        qr.add_data(qr_text)
        qr.make(fit=True)

        qr_img = qr.make_image(
            fill_color="black",
            back_color="white"
        )

        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")

        qr_code = (
            "data:image/png;base64,"
            + base64.b64encode(buffer.getvalue()).decode()
        )

        # ================= BEHAVIOUR =================
        positive_behaviour_count = BehaviourRecord.objects.filter(
            student=student,
            behaviour_type="Positive"
        ).count()

        negative_behaviour_count = BehaviourRecord.objects.filter(
            student=student,
            behaviour_type="Negative"
        ).count()

        latest_skill = SkillEvaluation.objects.filter(
            student=student
        ).order_by("-year", "-id").first()

        # ================= AI ENGINE =================
        behaviour_score = (
            100
            + (positive_behaviour_count * 2)
            - (negative_behaviour_count * 5)
        )

        if behaviour_score > 100:
            behaviour_score = 100

        if behaviour_score < 0:
            behaviour_score = 0

        student_health_index = (
            (attendance_percentage * 0.30)
            + (percentage * 0.50)
            + (behaviour_score * 0.20)
        )

        if student_health_index > 100:
            student_health_index = 100

        student_health_index = round(student_health_index, 2)

        pass_probability = round(student_health_index, 2)
        fail_probability = round(100 - pass_probability, 2)

        risk_points = 0

        if attendance_percentage < 75:
            risk_points += 30

        if percentage < 40:
            risk_points += 40

        if negative_behaviour_count >= 5:
            risk_points += 25

        if risk_points >= 70:
            ai_risk_level = "High Risk"
        elif risk_points >= 40:
            ai_risk_level = "Medium Risk"
        else:
            ai_risk_level = "Low Risk"

        if percentage >= 90:
            ai_remark = "Outstanding academic performance detected."
            performance_badge = "Top Performer"
            ai_recommendation = "Recommended for scholarship and leadership activities."

        elif percentage >= 75:
            ai_remark = "Very good and stable academic performance."
            performance_badge = "Excellent"
            ai_recommendation = "Maintain current consistency."

        elif percentage >= 50:
            ai_remark = "Average performance with improvement potential."
            performance_badge = "Improving"
            ai_recommendation = "Needs more subject practice and revision."

        else:
            ai_remark = "Academic performance requires immediate attention."
            performance_badge = "Needs Attention"
            ai_recommendation = "Special academic guidance strongly recommended."

        cards.append({
            "student": student,
            "exam": exam,
            "results": results,

            "written_total": written_total,
            "oral_total": oral_total,
            "grand_total": grand_total,
            "max_total": max_total,

            "percentage": percentage,
            "final_grade": final_grade,
            "gpa": gpa,
            "result_status": result_status,

            "attendance_percentage": attendance_percentage,
            "class_rank": summary.rank if summary else "-",
            "academic_session": selected_session,

            "qr_code": qr_code,

            "latest_skill": latest_skill,
            "positive_behaviour_count": positive_behaviour_count,
            "negative_behaviour_count": negative_behaviour_count,

            "student_health_index": student_health_index,
            "ai_risk_level": ai_risk_level,
            "pass_probability": pass_probability,
            "fail_probability": fail_probability,
            "performance_badge": performance_badge,
            "ai_remark": ai_remark,
            "ai_recommendation": ai_recommendation,
            "behaviour_score": behaviour_score,
        })

    settings_obj = get_general_settings()

    return render(request, "exams/report_card_bulk_print.html", {
        "cards": cards,
        "exam": exam,
        "selected_class": selected_class,
        "selected_section": selected_section,
        "settings_obj": settings_obj,
        "header_url": get_setting_image_url(
            settings_obj,
            "school_header",
            "/static/images/header.jpg"
        ),
        "logo_url": get_setting_image_url(
            settings_obj,
            "school_logo",
            "/static/images/logo.png"
        ),
        "principal_sign": get_setting_image_url(
            settings_obj,
            "principal_signature",
            "/static/images/principal_sign.png"
        ),
        "selected_session": selected_session,
    })

# =====================================
# SECTION-WISE MERIT LIST / SUBJECT TOPPER
# =====================================

@login_required
def merit_list(request):
    selected_session = get_selected_session(request)

    exams = Exam.objects.filter(
        academic_session=selected_session
    ).order_by("-id")

    classes = get_all_classes()

    exam_id = request.GET.get("exam", "").strip()
    class_name = request.GET.get("class", "").strip()
    selected_section = request.GET.get("section", "").strip()

    selected_exam = None
    merit_students = []
    subject_toppers = []

    pass_count = 0
    fail_count = 0
    total_students = 0
    avg_percentage = 0
    highest_percentage = 0

    class_topper = None
    section_topper = None
    school_topper = None

    if exam_id:
        selected_exam = get_object_or_404(
            Exam,
            id=exam_id,
            academic_session=selected_session
        )

        update_all_students_summary(selected_exam)
        generate_rank(
            selected_exam,
            class_name=class_name if class_name else None,
            section=selected_section if selected_section else None
        )

        summaries = StudentResultSummary.objects.filter(
            exam=selected_exam,
            academic_session=selected_session,
            max_total_marks__gt=0
        ).select_related(
            "student",
            "student__class_assigned"
        )

        if class_name:
            summaries = summaries.filter(
                student__class_assigned__class_name=class_name
            )

        if selected_section:
            summaries = summaries.filter(
                student__section=selected_section
            )

        summaries = summaries.order_by(
            "rank",
            "-percentage",
            "-total_marks",
            "student__roll_no"
        )

        total_students = summaries.count()
        pass_count = summaries.filter(result_status="Pass").count()
        fail_count = summaries.filter(result_status="Fail").count()

        if total_students > 0:
            avg_percentage = round(
                sum((s.percentage or 0) for s in summaries) / total_students,
                2
            )

            highest_percentage = summaries.first().percentage or 0

            first_summary = summaries.first()

            school_topper = first_summary
            class_topper = first_summary

            if selected_section:
                section_topper = first_summary

        for s in summaries:
            merit_students.append({
                "rank": s.rank,
                "student": s.student,
                "percentage": s.percentage,
                "grade": s.grade,
                "status": s.result_status,
                "total": s.total_marks,
                "max_total": s.max_total_marks,
                "section": s.student.section or "-",
                "class_name": s.student.class_assigned.class_name,
            })
        # =====================================
        # MERIT TABLE SORTING
        # =====================================

        sort = request.GET.get("sort", "").strip()

        if sort == "rank":
            merit_students = sorted(
                merit_students,
                key=lambda x: (
                    x["rank"] if x["rank"] else 9999
                )
            )

        elif sort == "roll":
            merit_students = sorted(
                merit_students,
                key=lambda x: (
                    int(x["student"].roll_no)
                    if str(x["student"].roll_no).isdigit()
                    else 9999
                )
            )

        elif sort == "student":
            merit_students = sorted(
                merit_students,
                key=lambda x: (
                    x["student"].student_name.lower()
                )
            )

        elif sort == "sid":
            merit_students = sorted(
                merit_students,
                key=lambda x: (
                    x["student"].student_id or ""
                )
            )

        elif sort == "class":
            merit_students = sorted(
                merit_students,
                key=lambda x: (
                    x["class_name"] or ""
                )
            )

        elif sort == "section":
            merit_students = sorted(
                merit_students,
                key=lambda x: (
                    x["section"] or ""
                )
            )

        elif sort == "total":
            merit_students = sorted(
                merit_students,
                key=lambda x: (
                    x["total"] or 0
                ),
                reverse=True
            )

        elif sort == "percentage":
            merit_students = sorted(
                merit_students,
                key=lambda x: (
                    x["percentage"] or 0
                ),
                reverse=True
            )

        elif sort == "grade":
            merit_students = sorted(
                merit_students,
                key=lambda x: (
                    x["grade"] or ""
                )
            )

        elif sort == "status":
            merit_students = sorted(
                merit_students,
                key=lambda x: (
                    x["status"] or ""
                )
            )


        # ================================
        # SUBJECT TOPPERS
        # ================================

        result_qs = ExamResult.objects.filter(
            exam=selected_exam,
            academic_session=selected_session
        ).select_related(
            "student",
            "student__class_assigned"
        )

        if class_name:
            result_qs = result_qs.filter(
                student__class_assigned__class_name=class_name
            )

        if selected_section:
            result_qs = result_qs.filter(
                student__section=selected_section
            )

        subject_names = list(
            result_qs.values_list(
                "subject",
                flat=True
            ).distinct().order_by("subject")
        )

        subject_names = order_subject_names_by_class_rank(
            subject_names,
            class_name
        )

        for subject in subject_names:
            subject_results = result_qs.filter(
                subject=subject
            )

            top_result = sorted(
                subject_results,
                key=lambda r: (
                    -(r.total_marks or 0),
                    -((r.percentage or 0)),
                    r.student.roll_no or 9999
                )
            )

            if top_result:
                best = top_result[0]

                subject_toppers.append({
                    "subject": subject,
                    "student": best.student,
                    "marks": best.total_marks,
                    "max_marks": best.max_marks,
                    "percentage": best.percentage,
                    "grade": best.grade,
                    "class_name": best.student.class_assigned.class_name,
                    "section": best.student.section or "-",
                })

    return render(request, "exams/merit_list.html", {
        "exams": exams,
        "classes": classes,
        "selected_exam": selected_exam,
        "selected_exam_id": exam_id,
        "selected_class": class_name,
        "selected_section": selected_section,
        "merit_students": merit_students,
        "subject_toppers": subject_toppers,
        "school_topper": school_topper,
        "class_topper": class_topper,
        "section_topper": section_topper,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "avg_percentage": avg_percentage,
        "total_students": total_students,
        "highest_percentage": highest_percentage,
        "settings_obj": get_general_settings(),
        "selected_session": selected_session,
    })


# ================================
# TOPPER RESULT
# ================================

@login_required
def topper_result(request):
    selected_session = get_selected_session(request)

    exam_id = request.GET.get("exam")
    class_name = request.GET.get("class")

    exams = Exam.objects.filter(
        academic_session=selected_session
    ).order_by("-id")

    classes = get_all_classes()

    selected_exam = None
    toppers = []

    if exam_id:
        selected_exam = get_object_or_404(
            Exam,
            id=exam_id,
            academic_session=selected_session
        )

        summaries = StudentResultSummary.objects.filter(
            exam=selected_exam,
            academic_session=selected_session
        ).select_related("student").order_by(
            "-percentage",
            "-total_marks"
        )

        if class_name:
            filtered_toppers = []

            for s in summaries:
                student_class = getattr(s.student, "class_assigned", None)

                if student_class and str(student_class).strip().lower() == str(class_name).strip().lower():
                    filtered_toppers.append(s)

            toppers = filtered_toppers
        else:
            toppers = list(summaries)

    return render(request, "exams/topper_result.html", {
        "toppers": toppers,
        "exams": exams,
        "classes": classes,
        "selected_exam": selected_exam,
        "selected_class": class_name,
        "settings_obj": get_general_settings(),
        "selected_session": selected_session,
    })


# ================================
# ADMIT CARD
# ================================

@login_required
def admit_card_select(request):
    selected_session = get_selected_session(request)

    settings_obj = get_general_settings()

    exams = Exam.objects.filter(
        academic_session=selected_session
    ).order_by("-id")

    classes = get_all_classes()

    exam_id = request.GET.get("exam")
    class_name = request.GET.get("class")
    selected_section = request.GET.get("section")
    student_id = request.GET.get("student")
    search = request.GET.get("search", "").strip()

    selected_exam = None
    selected_student = None

    students = get_students_queryset()
    students = filter_students_by_class(students, class_name)

    if selected_section:
        students = students.filter(section=selected_section)

    students = apply_student_search(students, search)

    if exam_id:
        selected_exam = get_object_or_404(
            Exam,
            id=exam_id,
            academic_session=selected_session
        )

    if student_id:
        selected_student = get_object_or_404(Student, id=student_id)

    routines = ExamRoutine.objects.none()

    if selected_exam:
        routines = ExamRoutine.objects.filter(
            exam=selected_exam,
            academic_session=selected_session
        ).order_by("date", "start_time")

        if class_name:
            routines = routines.filter(school_class=class_name)

        if selected_section:
            routines = routines.filter(section=selected_section)

    header_url = get_setting_image_url(
        settings_obj,
        "school_header",
        "/static/images/header.jpg"
    )

    logo_url = get_setting_image_url(
        settings_obj,
        "school_logo",
        "/static/images/logo.png"
    )

    principal_sign = get_setting_image_url(
        settings_obj,
        "principal_signature",
        "/static/images/principal_sign.png"
    )

    if selected_exam and selected_student:
        return render(request, "exams/admit_card_print.html", {
            "exam": selected_exam,
            "student": selected_student,
            "students": [selected_student],
            "routines": routines,
            "academic_session": selected_session,
            "selected_class": class_name,
            "selected_section": selected_section,
            "classes": classes,
            "search": search,
            "settings_obj": settings_obj,
            "header_url": header_url,
            "logo_url": logo_url,
            "principal_sign": principal_sign,
            "selected_session": selected_session,
        })

    return render(request, "exams/admit_card_select.html", {
        "exams": exams,
        "students": students,
        "classes": classes,
        "selected_exam": selected_exam,
        "selected_exam_id": exam_id,
        "selected_class": class_name,
        "selected_section": selected_section,
        "search": search,
        "settings_obj": settings_obj,
        "selected_session": selected_session,
    })


@login_required
def admit_card_bulk_print(request):
    selected_session = get_selected_session(request)

    settings_obj = get_general_settings()

    exams = Exam.objects.filter(
        academic_session=selected_session
    ).order_by("-id")

    classes = get_all_classes()

    exam_id = request.POST.get("exam") or request.GET.get("exam")

    if exam_id in [None, "", "None"]:
        messages.error(request, "Please select exam first.")
        return redirect("admit_card_select")

    class_name = request.POST.get("class") or request.GET.get("class")
    selected_section = request.POST.get("section") or request.GET.get("section")

    selected_ids = (
        request.POST.getlist("students")
        or request.GET.getlist("students")
    )

    selected_exam = None
    students = Student.objects.none()
    routines = ExamRoutine.objects.none()

    if exam_id:
        selected_exam = get_object_or_404(
            Exam,
            id=exam_id,
            academic_session=selected_session
        )

        students = get_students_queryset()
        students = filter_students_by_class(students, class_name)

        if selected_section:
            students = students.filter(section=selected_section)

        if selected_ids:
            students = students.filter(id__in=selected_ids)

        routines = ExamRoutine.objects.filter(
            exam=selected_exam,
            academic_session=selected_session
        ).order_by("date", "start_time")

        if class_name:
            routines = routines.filter(school_class=class_name)

        if selected_section:
            routines = routines.filter(section=selected_section)

    header_url = get_setting_image_url(
        settings_obj,
        "school_header",
        "/static/images/header.jpg"
    )

    logo_url = get_setting_image_url(
        settings_obj,
        "school_logo",
        "/static/images/logo.png"
    )

    principal_sign = get_setting_image_url(
        settings_obj,
        "principal_signature",
        "/static/images/principal_sign.png"
    )

    return render(request, "exams/admit_card_bulk_print.html", {
        "exams": exams,
        "classes": classes,
        "exam": selected_exam,
        "selected_exam": selected_exam,
        "selected_exam_id": exam_id,
        "selected_class": class_name,
        "selected_section": selected_section,
        "students": students,
        "routines": routines,
        "academic_session": selected_session,
        "settings_obj": settings_obj,
        "header_url": header_url,
        "logo_url": logo_url,
        "principal_sign": principal_sign,
        "selected_session": selected_session,
    })


# ================================
# DESK SLIP
# ================================

@login_required
def desk_slip_select(request):
    selected_session = get_selected_session(request)

    settings_obj = get_general_settings()

    exams = Exam.objects.filter(
        academic_session=selected_session
    ).order_by("-id")

    classes = get_all_classes()

    exam_id = request.GET.get("exam")
    class_name = request.GET.get("class")
    search = request.GET.get("search", "").strip()

    students = get_students_queryset()
    students = filter_students_by_class(students, class_name)
    students = apply_student_search(students, search)

    selected_exam = None

    if exam_id:
        selected_exam = get_object_or_404(
            Exam,
            id=exam_id,
            academic_session=selected_session
        )

    return render(request, "exams/desk_slip_select.html", {
        "exams": exams,
        "classes": classes,
        "students": students,
        "selected_exam": selected_exam,
        "selected_exam_id": exam_id,
        "selected_class": class_name,
        "search": search,
        "settings_obj": settings_obj,
        "selected_session": selected_session,
    })


@login_required
def desk_slip_bulk_print(request):
    selected_session = get_selected_session(request)

    settings_obj = get_general_settings()

    exams = Exam.objects.filter(
        academic_session=selected_session
    ).order_by("-id")

    classes = get_all_classes()

    exam_id = request.POST.get("exam") or request.GET.get("exam")
    class_name = request.POST.get("class") or request.GET.get("class")

    selected_ids = (
        request.POST.getlist("students")
        or request.GET.getlist("students")
    )

    selected_exam = None
    students = Student.objects.none()

    if exam_id:
        selected_exam = get_object_or_404(
            Exam,
            id=exam_id,
            academic_session=selected_session
        )

        students = get_students_queryset()

        students = filter_students_by_class(
            students,
            class_name
        )

        if selected_ids:
            students = students.filter(
                id__in=selected_ids
            )

    header_url = get_setting_image_url(
        settings_obj,
        "school_header",
        "/static/images/header.jpg"
    )

    logo_url = get_setting_image_url(
        settings_obj,
        "school_logo",
        "/static/images/logo.png"
    )

    return render(
        request,
        "exams/desk_slip_bulk_print.html",
        {
            "exam": selected_exam,
            "students": students,
            "selected_class": class_name,
            "header_url": header_url,
            "logo_url": logo_url,
            "settings_obj": settings_obj,
            "selected_session": selected_session,
            "academic_session": selected_session,
            "exams": exams,
            "classes": classes,
        }
    )


# ================================
# BLANK MARKS SHEET
# ================================

@login_required
def blank_marks_sheet_select(request):
    selected_session = get_selected_session(request)

    settings_obj = get_general_settings()

    exams = Exam.objects.filter(
        academic_session=selected_session
    ).order_by("-id")

    classes = get_all_classes()

    return render(request, "exams/blank_marks_sheet_select.html", {
        "exams": exams,
        "classes": classes,
        "settings_obj": settings_obj,
        "selected_session": selected_session,
    })


@login_required
def blank_marks_sheet_print(request):
    selected_session = get_selected_session(request)

    settings_obj = get_general_settings()

    exam_id = request.GET.get("exam")
    class_name = request.GET.get("class")

    if exam_id in [None, "", "None"]:
        messages.error(request, "Please select exam first.")
        return redirect("blank_marks_sheet_select")

    selected_exam = get_object_or_404(
        Exam,
        id=exam_id,
        academic_session=selected_session
    )

    students = get_students_queryset()
    students = filter_students_by_class(students, class_name)

    subjects = get_class_subject_objects(class_name)

    header_url = get_setting_image_url(
        settings_obj,
        "school_header",
        "/static/images/header.jpg"
    )

    logo_url = get_setting_image_url(
        settings_obj,
        "school_logo",
        "/static/images/logo.png"
    )

    return render(request, "exams/blank_marks_sheet_print.html", {
        "exam": selected_exam,
        "students": students,
        "subjects": subjects,
        "selected_class": class_name,
        "header_url": header_url,
        "logo_url": logo_url,
        "settings_obj": settings_obj,
        "selected_session": selected_session,
        "academic_session": selected_session,
    })


# =====================================
# PREMIUM ONLINE RESULT PORTAL
# =====================================

def online_result_portal(request):
    selected_session = get_current_session()

    result_data = None
    error = None

    if request.method == "POST":
        student_id = request.POST.get("student_id")
        exam_id = request.POST.get("exam")
        dob = request.POST.get("dob")
        student_class = request.POST.get("student_class")

        try:
            try:
                student = Student.objects.get(
                    student_id=student_id,
                    date_of_birth=dob,
                    class_assigned__class_name=student_class
                )
            except Exception:
                student = Student.objects.get(
                    student_id=student_id,
                    date_of_birth=dob,
                    class_assigned=student_class
                )

            exam = Exam.objects.get(
                id=exam_id,
                academic_session=selected_session
            )

            summary = StudentResultSummary.objects.filter(
                student=student,
                exam=exam,
                academic_session=selected_session
            ).first()

            results = ExamResult.objects.filter(
                student=student,
                exam=exam,
                academic_session=selected_session
            )

            class_rank = "-"

            try:
                class_students = StudentResultSummary.objects.filter(
                    exam=exam,
                    academic_session=selected_session,
                    student__class_assigned__class_name=student_class
                ).order_by("-percentage", "-total_marks")
            except Exception:
                class_students = StudentResultSummary.objects.filter(
                    exam=exam,
                    academic_session=selected_session,
                    student__class_assigned=student_class
                ).order_by("-percentage", "-total_marks")

            for i, s in enumerate(class_students, start=1):
                if s.student.id == student.id:
                    class_rank = i
                    break

            if summary:
                total_subjects = results.count()
                total_obtained = 0
                total_max = 0

                for r in results:
                    total_obtained += (
                        (r.written_marks or 0)
                        + (r.oral_marks or 0)
                    )
                    total_max += (r.max_marks or 0)

                result_data = {
                    "student": student,
                    "exam": exam,
                    "summary": summary,
                    "results": results,
                    "total_subjects": total_subjects,
                    "total_obtained": total_obtained,
                    "total_max": total_max,
                    "student_class": student_class,
                    "class_rank": class_rank,
                }

            else:
                error = "Result not published yet."

        except Student.DoesNotExist:
            error = "Invalid Student ID, Date of Birth or Class."

        except Exam.DoesNotExist:
            error = "Invalid Exam."

        except Exception as e:
            print("ONLINE RESULT ERROR:", e)
            error = "Something went wrong."

    return render(request, "exams/online_result_portal.html", {
        "exams": Exam.objects.filter(
            academic_session=selected_session
        ).order_by("-id"),
        "classes": get_all_classes(),
        "result_data": result_data,
        "error": error,
        "settings_obj": get_general_settings(),
        "selected_session": selected_session,
    })


@login_required
def exam_routine_select_print(request):
    selected_session = get_selected_session(request)

    exam_id = request.GET.get("exam")
    class_name = request.GET.get("class")
    selected_section = request.GET.get("section")

    exams = Exam.objects.filter(
        academic_session=selected_session
    ).order_by("-id")

    routines = ExamRoutine.objects.filter(
        academic_session=selected_session
    ).order_by(
        "date",
        "start_time"
    )

    if exam_id:
        routines = routines.filter(exam_id=exam_id)

    if class_name:
        routines = routines.filter(school_class=class_name)

    if selected_section:
        routines = routines.filter(section=selected_section)

    classes = ExamRoutine.objects.filter(
        academic_session=selected_session
    ).values_list(
        "school_class",
        flat=True
    ).distinct().order_by("school_class")

    selected_exam = None

    if exam_id:
        selected_exam = Exam.objects.filter(
            id=exam_id,
            academic_session=selected_session
        ).first()

    return render(request, "exams/exam_routine_select_print.html", {
        "exams": exams,
        "classes": classes,
        "routines": routines,
        "selected_exam": selected_exam,
        "selected_exam_id": exam_id,
        "selected_class": class_name,
        "selected_section": selected_section,
        "selected_session": selected_session,
        "academic_session": selected_session,
    })

# =====================================
# CLASS TESTS - MULTI SUBJECT UNIT TEST
# =====================================

def get_unit_test_performance(percentage):
    if percentage >= 90:
        return "Excellent"
    elif percentage >= 80:
        return "Best"
    elif percentage >= 60:
        return "Better"
    elif percentage >= 40:
        return "Average"
    return "Low"


def get_class_test_subjects(class_test):
    if not class_test:
        return []

    try:
        from academics.models import Class, ClassSubject

        class_obj = Class.objects.filter(
            class_name=str(class_test.class_name).strip()
        ).first()

        if class_obj:
            return (
                ClassSubject.objects.filter(
                    school_class=class_obj,
                    is_active=True
                )
                .select_related("subject")
                .order_by("subject_rank", "subject__subject_name")
            )
    except Exception:
        pass

    return []


def get_class_test_students(class_test):
    students = Student.objects.none()

    if not class_test:
        return students

    try:
        students = Student.objects.filter(
            class_assigned__class_name=str(class_test.class_name).strip()
        )

        if class_test.section:
            students = students.filter(section=str(class_test.section).strip())

        return students.order_by("roll_no", "student_name", "id")
    except Exception:
        return Student.objects.none()


def refresh_class_test_total(class_test_result):
    if not class_test_result:
        return

    total = 0

    for mark in class_test_result.subject_marks.all():
        total += mark.total_marks or 0

    class_test_result.marks_obtained = total

    total_possible = (
        class_test_result.subject_marks.count()
        * (class_test_result.class_test.total_marks or 0)
    )

    percentage = 0

    if total_possible:
        percentage = round((total / total_possible) * 100, 2)

    class_test_result.remarks = get_unit_test_performance(percentage)
    class_test_result.save(update_fields=["marks_obtained", "remarks"])


@login_required
def class_test_dashboard(request):
    selected_session = get_selected_session(request)
    selected_test_id = request.GET.get("test")

    all_tests = ClassTest.objects.filter(
        academic_session=selected_session
    ).order_by("-id")

    total_tests = all_tests.count()
    total_results = ClassTestSubjectMark.objects.filter(
        class_test_result__academic_session=selected_session
    ).count()

    class_test = None
    result_rows = []

    best_performer = None
    average_performer = None
    low_performer = None

    avg_marks = 0
    highest_marks = 0
    lowest_marks = 0

    if selected_test_id:
        class_test = ClassTest.objects.filter(
            id=selected_test_id,
            academic_session=selected_session
        ).first()

        if not class_test:
            messages.error(request, "Selected Unit Test not found.")
            return redirect("add_class_test_result")

        results = (
            ClassTestResult.objects.filter(
                class_test=class_test,
                academic_session=selected_session
            )
            .select_related("student", "class_test")
            .prefetch_related("subject_marks")
            .order_by("student__roll_no", "student__student_name")
        )

        for result in results:
            max_marks = result.subject_marks.count() * (class_test.total_marks or 0)
            percentage = round((result.marks_obtained / max_marks) * 100, 2) if max_marks else 0

            result_rows.append({
                "student": result.student,
                "class_test_result": result,
                "total_marks": result.marks_obtained,
                "max_marks": max_marks,
                "percentage": percentage,
                "performance": get_unit_test_performance(percentage),
                "subjects": result.subject_marks.all(),
            })

        result_rows = sorted(
            result_rows,
            key=lambda x: (-x["percentage"], -x["total_marks"])
        )

        current_rank = 0
        previous_percentage = None
        previous_total = None

        for index, item in enumerate(result_rows, start=1):
            if previous_percentage == item["percentage"] and previous_total == item["total_marks"]:
                item["rank"] = current_rank
            else:
                current_rank = index
                item["rank"] = current_rank

            previous_percentage = item["percentage"]
            previous_total = item["total_marks"]

        if result_rows:
            best_performer = result_rows[0]
            low_performer = result_rows[-1]
            average_list = [x for x in result_rows if x["performance"] == "Average"]
            average_performer = average_list[0] if average_list else result_rows[len(result_rows) // 2]
            total_all = sum(x["total_marks"] for x in result_rows)
            avg_marks = round(total_all / len(result_rows), 2)
            highest_marks = result_rows[0]["total_marks"]
            lowest_marks = result_rows[-1]["total_marks"]

    return render(request, "exams/class_test_dashboard.html", {
        "all_tests": all_tests,
        "total_tests": total_tests,
        "total_results": total_results,
        "selected_test_id": selected_test_id,
        "class_test": class_test,
        "result_rows": result_rows,
        "best_performer": best_performer,
        "average_performer": average_performer,
        "low_performer": low_performer,
        "avg_marks": avg_marks,
        "highest_marks": highest_marks,
        "lowest_marks": lowest_marks,
        "selected_session": selected_session,
    })


@login_required
def class_test_list(request):
    selected_session = get_selected_session(request)

    tests = ClassTest.objects.filter(
        academic_session=selected_session
    ).order_by("-id")

    return render(request, "exams/class_test_list.html", {
        "tests": tests,
        "selected_session": selected_session,
    })


@login_required
def add_class_test(request):
    selected_session = get_selected_session(request)

    form = ClassTestForm(
        request.POST or None,
        selected_session=selected_session
    )

    if request.method == "POST" and form.is_valid():
        class_test = form.save(commit=False)
        class_test.academic_session = selected_session
        class_test.save()

        messages.success(request, "Unit Test Added Successfully")
        return redirect("class_test_list")

    return render(request, "exams/add_class_test.html", {
        "form": form,
        "selected_session": selected_session,
    })


@login_required
def class_test_result_list(request):
    selected_session = get_selected_session(request)

    marks = (
        ClassTestSubjectMark.objects.filter(
            class_test_result__academic_session=selected_session
        )
        .select_related(
            "class_test_result",
            "class_test_result__class_test",
            "class_test_result__student",
        )
        .order_by(
            "-class_test_result__class_test__exam_date",
            "class_test_result__student__roll_no",
            "subject",
        )
    )

    results = []

    for mark in marks:
        result = mark.class_test_result
        class_test = result.class_test if result else None
        student = result.student if result else None
        obtained = mark.total_marks
        max_marks = mark.max_marks or (class_test.total_marks if class_test else 0)
        percentage = round((obtained / max_marks) * 100, 2) if max_marks else 0

        results.append({
            "id": mark.id,
            "mark": mark,
            "class_test": class_test,
            "student": student,
            "subject": mark.subject,
            "marks": obtained,
            "total_marks": max_marks,
            "percentage": percentage,
            "performance": get_unit_test_performance(percentage),
            "remarks": result.remarks if result else "",
        })

    return render(request, "exams/class_test_result_list.html", {
        "results": results,
        "selected_session": selected_session,
    })


@login_required
def add_class_test_result(request):
    selected_session = get_selected_session(request)

    selected_test_id = request.GET.get("class_test") or request.POST.get("class_test")
    selected_student_id = request.GET.get("student") or request.POST.get("student")

    form = ClassTestResultForm(
        request.POST or None,
        selected_test_id=selected_test_id
    )

    class_test = None
    selected_student = None
    subjects = []
    saved_marks = {}

    if selected_test_id:
        class_test = ClassTest.objects.filter(
            id=selected_test_id,
            academic_session=selected_session
        ).first()

        if not class_test:
            messages.error(request, "Selected Unit Test not found.")
            return redirect("add_class_test_result")

        subjects = get_class_test_subjects(class_test)

    if selected_student_id:
        selected_student = get_object_or_404(Student, id=selected_student_id)

        result_obj = ClassTestResult.objects.filter(
            class_test=class_test,
            student=selected_student,
            academic_session=selected_session
        ).first()

        if result_obj:
            old_marks = ClassTestSubjectMark.objects.filter(
                class_test_result=result_obj
            )

            for m in old_marks:
                saved_marks[m.subject] = m

    if request.method == "POST" and selected_test_id and selected_student_id:
        class_test = ClassTest.objects.filter(
            id=selected_test_id,
            academic_session=selected_session
        ).first()

        if not class_test:
            messages.error(request, "Selected Unit Test not found.")
            return redirect("add_class_test_result")

        selected_student = get_object_or_404(Student, id=selected_student_id)

        subject_list = request.POST.getlist("subject[]")
        marks_list = request.POST.getlist("marks[]")

        result_obj, created = ClassTestResult.objects.get_or_create(
            class_test=class_test,
            student=selected_student,
            academic_session=selected_session,
            defaults={
                "marks_obtained": 0,
                "remarks": "",
            }
        )

        for index, subject_name in enumerate(subject_list):
            subject_name = str(subject_name).strip()

            if not subject_name:
                continue

            marks_value = marks_list[index] if index < len(marks_list) else ""

            if marks_value == "":
                continue

            try:
                marks_float = float(marks_value)
            except Exception:
                marks_float = 0

            if marks_float > class_test.total_marks:
                messages.error(
                    request,
                    f"{subject_name}: Marks cannot be greater than {class_test.total_marks}"
                )
                return redirect(
                    f"{reverse('add_class_test_result')}?class_test={class_test.id}&student={selected_student.id}"
                )

            ClassTestSubjectMark.objects.update_or_create(
                class_test_result=result_obj,
                subject=subject_name,
                defaults={
                    "written_marks": marks_float,
                    "oral_marks": 0,
                    "max_marks": class_test.total_marks,
                }
            )

        refresh_class_test_total(result_obj)

        messages.success(request, "Unit Test Result Saved Successfully")

        return redirect(
            f"{reverse('add_class_test_result')}?class_test={class_test.id}&student={selected_student.id}"
        )

    return render(request, "exams/add_class_test_result.html", {
        "form": form,
        "class_test": class_test,
        "selected_test_id": selected_test_id,
        "selected_student": selected_student,
        "selected_student_id": selected_student_id,
        "subjects": subjects,
        "saved_marks": saved_marks,
        "selected_session": selected_session,
    })


@login_required
def edit_class_test_result(request, pk):
    mark = get_object_or_404(
        ClassTestSubjectMark.objects.select_related(
            "class_test_result",
            "class_test_result__class_test",
            "class_test_result__student",
        ),
        pk=pk
    )

    if request.method == "POST":
        marks_value = request.POST.get("marks")

        try:
            marks_float = float(marks_value or 0)
        except Exception:
            marks_float = 0

        class_test = mark.class_test_result.class_test

        if marks_float > class_test.total_marks:
            messages.error(
                request,
                f"Marks cannot be greater than {class_test.total_marks}"
            )
            return redirect("edit_class_test_result", pk=mark.pk)

        mark.written_marks = marks_float
        mark.oral_marks = 0
        mark.max_marks = class_test.total_marks
        mark.save()

        refresh_class_test_total(mark.class_test_result)

        messages.success(request, "Result Updated Successfully")
        return redirect("class_test_result_list")

    return render(request, "exams/edit_class_test_result.html", {
        "mark": mark
    })


@login_required
def delete_class_test_result(request, pk):
    mark = get_object_or_404(
        ClassTestSubjectMark.objects.select_related(
            "class_test_result",
            "class_test_result__class_test",
            "class_test_result__student",
        ),
        pk=pk
    )

    if request.method == "POST":
        result_obj = mark.class_test_result
        mark.delete()

        if result_obj.subject_marks.exists():
            refresh_class_test_total(result_obj)
        else:
            result_obj.delete()

        messages.success(request, "Result Deleted Successfully")
        return redirect("class_test_result_list")

    return render(request, "exams/delete_class_test_result.html", {
        "mark": mark
    })


@login_required
def edit_class_test(request, pk):
    selected_session = get_selected_session(request)

    class_test = get_object_or_404(
        ClassTest,
        pk=pk,
        academic_session=selected_session
    )

    form = ClassTestForm(
        request.POST or None,
        instance=class_test,
        selected_session=selected_session
    )

    if request.method == "POST" and form.is_valid():
        class_test_obj = form.save(commit=False)
        class_test_obj.academic_session = selected_session
        class_test_obj.save()

        messages.success(request, "Class Test Updated Successfully")
        return redirect("class_test_list")

    return render(request, "exams/add_class_test.html", {
        "form": form,
        "selected_session": selected_session,
    })


@login_required
def delete_class_test(request, pk):
    selected_session = get_selected_session(request)

    class_test = get_object_or_404(
        ClassTest,
        pk=pk,
        academic_session=selected_session
    )

    if request.method == "POST":
        class_test.delete()
        messages.success(request, "Class Test Deleted Successfully")
        return redirect("class_test_list")

    return render(request, "exams/delete_class_test.html", {
        "class_test": class_test,
        "selected_session": selected_session,
    })
