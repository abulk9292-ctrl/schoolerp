from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q
from django.core.exceptions import FieldError

from students.models import Student
from .models import Exam, ExamRoutine, ExamResult, StudentResultSummary
from .forms import ExamForm, ExamRoutineForm, ExamResultForm
from settings_app.models import GeneralSetting


# ================================
# HELPERS
# ================================

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


def get_final_grade(percentage):
    if percentage >= 90:
        return "AA"
    elif percentage >= 80:
        return "A+"
    elif percentage >= 60:
        return "A"
    elif percentage >= 45:
        return "B+"
    elif percentage >= 40:
        return "B"
    elif percentage >= 35:
        return "C+"
    elif percentage >= 24:
        return "C"
    return "D"


def get_all_classes():
    classes = []

    try:
        from academics.models import Class

        classes = list(
            Class.objects.all()
            .order_by("class_name")
            .values_list("class_name", flat=True)
        )

    except Exception:
        pass

    if not classes:
        try:
            classes = list(
                Student.objects.exclude(school_class__isnull=True)
                .exclude(school_class="")
                .order_by("school_class")
                .values_list("school_class", flat=True)
                .distinct()
            )
        except Exception:
            pass

    return classes


def filter_students_by_class(queryset, class_name):
    if not class_name:
        return queryset

    try:
        return queryset.filter(class_assigned__class_name=class_name)
    except FieldError:
        pass

    try:
        return queryset.filter(school_class=class_name)
    except FieldError:
        pass

    return queryset.none()


def get_students_queryset():
    qs = Student.objects.all()

    try:
        qs = qs.select_related("class_assigned", "current_session")
    except Exception:
        pass

    return qs.order_by("id")


def update_student_summary(student, exam):
    results = ExamResult.objects.filter(student=student, exam=exam)

    total_marks = sum(r.total_marks for r in results)
    max_total_marks = sum(r.max_marks for r in results)

    percentage = 0
    if max_total_marks > 0:
        percentage = round((total_marks / max_total_marks) * 100, 2)

    grade = get_final_grade(percentage)
    result_status = "Pass" if percentage >= 35 else "Fail"

    StudentResultSummary.objects.update_or_create(
        student=student,
        exam=exam,
        defaults={
            "total_marks": total_marks,
            "max_total_marks": max_total_marks,
            "percentage": percentage,
            "grade": grade,
            "result_status": result_status,
        }
    )


def generate_rank(exam):

    summaries = StudentResultSummary.objects.filter(
        exam=exam,
        max_total_marks__gt=0
    ).select_related("student").order_by(
        "student__class_assigned",
        "-percentage",
        "-total_marks",
        "student__id"
    )

    grouped = {}

    for summary in summaries:

        class_key = str(summary.student.class_assigned)

        if class_key not in grouped:
            grouped[class_key] = []

        grouped[class_key].append(summary)

    for class_name, class_summaries in grouped.items():

        rank = 0
        previous_percentage = None
        previous_total = None

        for index, summary in enumerate(class_summaries, start=1):

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

def update_all_students_summary(exam):
    student_ids = ExamResult.objects.filter(
        exam=exam
    ).values_list("student_id", flat=True).distinct()

    students = Student.objects.filter(id__in=student_ids)

    for student in students:
        update_student_summary(student, exam)

    generate_rank(exam)


# ================================
# DASHBOARD
# ================================

@login_required
def exam_dashboard(request):
    return render(request, "exams/exam_dashboard.html", {
        "total_exams": Exam.objects.count(),
        "total_results": ExamResult.objects.count(),
        "passed": StudentResultSummary.objects.filter(result_status="Pass").count(),
        "failed": StudentResultSummary.objects.filter(result_status="Fail").count(),
        "classes": get_all_classes(),
        "settings_obj": get_general_settings(),
    })


# ================================
# EXAM SETUP
# ================================

@login_required
def exam_add(request):
    form = ExamForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Exam saved successfully.")
            return redirect("exam_dashboard")
        messages.error(request, "Please correct the errors below.")

    return render(request, "exams/exam_form.html", {
        "form": form,
        "page_title": "Add Exam",
        "classes": get_all_classes(),
        "settings_obj": get_general_settings(),
    })


# ================================
# ROUTINE
# ================================

@login_required
def exam_routine(request):
    selected_class = request.GET.get("class") or request.POST.get("school_class") or request.POST.get("class")

    form_data = request.POST.copy() if request.method == "POST" else None

    if request.method == "POST":
        form = ExamRoutineForm(form_data)

        if form.is_valid():
            routine = form.save(commit=False)

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

        form = ExamRoutineForm(initial=initial_data)

    routines = ExamRoutine.objects.select_related("exam").all().order_by(
        "-exam__id", "date", "start_time"
    )

    if selected_class:
        routines = routines.filter(school_class=selected_class)

    return render(request, "exams/exam_routine.html", {
        "form": form,
        "routines": routines,
        "page_title": "Exam Routine",
        "classes": get_all_classes(),
        "selected_class": selected_class,
        "settings_obj": get_general_settings(),
    })


# ================================
# SINGLE MARK ENTRY
# ================================

@login_required
def result_add(request):
    selected_class = request.GET.get("class") or request.POST.get("class")

    form = ExamResultForm(
        request.POST or None,
        class_name=selected_class
    )

    if request.method == "POST":
        if form.is_valid():
            result = form.save(commit=False)

            if result.written_marks + result.oral_marks > result.max_marks:
                messages.error(request, "Written + Oral marks cannot be greater than Max Marks.")
                return render(request, "exams/result_form.html", {
                    "form": form,
                    "classes": get_all_classes(),
                    "selected_class": selected_class,
                    "page_title": "Add Marks",
                    "settings_obj": get_general_settings(),
                })

            result.save()
            update_student_summary(result.student, result.exam)
            generate_rank(result.exam)

            messages.success(request, "Marks saved successfully.")
            return redirect("result_list")

        messages.error(request, "Please correct the marks form.")

    return render(request, "exams/result_form.html", {
        "form": form,
        "page_title": "Add Marks",
        "classes": get_all_classes(),
        "selected_class": selected_class,
        "settings_obj": get_general_settings(),
    })


# ================================
# RESULT LIST
# ================================

@login_required
def result_list(request):
    exam_id = request.GET.get("exam")
    class_name = request.GET.get("class")

    results = ExamResult.objects.select_related("student", "exam").all().order_by(
        "-exam__id",
        "student__roll_no",
        "student__id",
        "subject"
    )

    if exam_id:
        results = results.filter(exam_id=exam_id)

    if class_name:
        students = filter_students_by_class(get_students_queryset(), class_name)
        results = results.filter(student_id__in=students.values_list("id", flat=True))

    subjects = []
    grouped_dict = {}

    for r in results:
        subject_name = str(r.subject).strip()

        if subject_name not in subjects:
            subjects.append(subject_name)

        student_key = r.student.id

        if student_key not in grouped_dict:
            grouped_dict[student_key] = {
                "student": r.student,
                "exam": r.exam,
                "marks": {},
                "subject_marks": [],
                "grand_total": 0,
                "max_total": 0,
                "percentage": 0,
                "grade": "-",
                "status": "Fail",
                "rank": "-",
            }

        total_marks = r.total_marks or 0
        max_marks = r.max_marks or 100

        grouped_dict[student_key]["marks"][subject_name] = {
            "written": r.written_marks or 0,
            "oral": r.oral_marks or 0,
            "total": total_marks,
            "max": max_marks,
            "grade": r.grade or "-",
        }

        grouped_dict[student_key]["grand_total"] += total_marks
        grouped_dict[student_key]["max_total"] += max_marks

    grouped_results = []

    for item in grouped_dict.values():

        item["subject_marks"] = []

        for sub in subjects:
            mark_data = item["marks"].get(sub)

            if mark_data:
                item["subject_marks"].append(mark_data["total"])
            else:
                item["subject_marks"].append("-")

        if item["max_total"] > 0:
            item["percentage"] = round(
                (item["grand_total"] / item["max_total"]) * 100,
                2
            )

        percentage = item["percentage"]

        if percentage >= 90:
            item["grade"] = "AA"
        elif percentage >= 80:
            item["grade"] = "A+"
        elif percentage >= 60:
            item["grade"] = "A"
        elif percentage >= 45:
            item["grade"] = "B+"
        elif percentage >= 40:
            item["grade"] = "B"
        elif percentage >= 35:
            item["grade"] = "C+"
        elif percentage >= 24:
            item["grade"] = "C"
        else:
            item["grade"] = "D"

        item["status"] = "Pass" if percentage >= 34 else "Fail"

        grouped_results.append(item)

    # ======================================
    # ✅ CLASS WISE / SELECTED LIST RANK
    # ======================================

    grouped_results = sorted(
        grouped_results,
        key=lambda x: (
            -x["percentage"],
            -x["grand_total"]
        )
    )

    current_rank = 0
    previous_percentage = None
    previous_total = None

    for index, item in enumerate(grouped_results, start=1):

        if (
            previous_percentage == item["percentage"]
            and previous_total == item["grand_total"]
        ):
            item["rank"] = current_rank
        else:
            current_rank = index
            item["rank"] = current_rank

        previous_percentage = item["percentage"]
        previous_total = item["grand_total"]

    exams = Exam.objects.all().order_by("-id")

    return render(request, "exams/result_list.html", {
        "grouped_results": grouped_results,
        "subjects": subjects,
        "exams": exams,
        "classes": get_all_classes(),
        "selected_exam": exam_id,
        "selected_class": class_name,
        "settings_obj": get_general_settings(),
    })


@login_required
def result_sheet_select(request):
    exams = Exam.objects.all().order_by("-id")
    classes = get_all_classes()

    return render(request, "exams/result_sheet_select.html", {
        "exams": exams,
        "classes": classes,
        "settings_obj": get_general_settings(),
    })

# ================================
# BULK MARKS ENTRY
# ================================

@login_required
def bulk_result_entry(request):
    exams = Exam.objects.all().order_by("-id")
    classes = get_all_classes()

    selected_exam_id = request.GET.get("exam") or request.POST.get("exam")
    selected_class = request.GET.get("class") or request.POST.get("class")

    students = get_students_queryset()
    students = filter_students_by_class(students, selected_class)

    subjects = []

    if selected_class:
        try:
            from academics.models import Class, ClassSubject

            class_obj = Class.objects.filter(class_name=selected_class).first()

            if class_obj:
                subjects = ClassSubject.objects.filter(
                    school_class=class_obj
                ).select_related("subject").order_by("subject__subject_name")
                
        except Exception:
            subjects = []

    if request.method == "POST":
        if not selected_exam_id:
            messages.error(request, "Please select exam.")
            return redirect("bulk_result_entry")

        if not selected_class:
            messages.error(request, "Please select class.")
            return redirect("bulk_result_entry")

        exam = get_object_or_404(Exam, id=selected_exam_id)

        for student in students:
            for cs in subjects:
                subject_name = cs.subject.subject_name

                written_key = f"written_{student.id}_{cs.subject.id}"
                oral_key = f"oral_{student.id}_{cs.subject.id}"
                absent_key = f"absent_{student.id}_{cs.subject.id}"

                is_absent = request.POST.get(absent_key)

                written_marks = 0 if is_absent else safe_int(request.POST.get(written_key), 0)
                oral_marks = 0 if is_absent else safe_int(request.POST.get(oral_key), 0)
                max_marks = cs.full_marks

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
                        subject=subject_name,
                        defaults={
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
            exam_obj = Exam.objects.get(id=selected_exam_id)

            old_results = ExamResult.objects.filter(
                exam=exam_obj
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
    })

# ================================
# POPUP ENTRY
# ================================

@login_required
def popup_result_entry(request):

    exams = Exam.objects.all().order_by("-id")
    classes = get_all_classes()

    exam_id = request.GET.get("exam") or request.POST.get("exam")
    class_name = request.GET.get("class") or request.POST.get("class")
    search = request.GET.get("search", "").strip()

    selected_exam = None
    subjects = []

    students = get_students_queryset()
    students = filter_students_by_class(students, class_name)
    students = apply_student_search(students, search)

    if exam_id:
        selected_exam = get_object_or_404(Exam, id=exam_id)

    # ✅ Selected class wise subject load - SAFE METHOD
    try:
        from academics.models import ClassSubject

        if class_name:
            all_class_subjects = ClassSubject.objects.all()

            for cs in all_class_subjects:
                cs_class = getattr(cs, "school_class", None)

                class_values = [
                    str(cs_class),
                    str(getattr(cs_class, "name", "")),
                    str(getattr(cs_class, "class_name", "")),
                    str(getattr(cs_class, "title", "")),
                    str(getattr(cs_class, "standard", "")),
                ]

                if str(class_name).strip().lower() in [
                    v.strip().lower() for v in class_values if v
                ]:
                    subjects.append(cs)

    except Exception as e:
        print("CLASS SUBJECT LOAD ERROR:", e)
        subjects = []

    # ✅ Fallback subjects
    if not subjects:
        subjects = [
            "Bengali",
            "English",
            "Mathematics",
            "Science",
            "History",
            "Geography",
        ]

    # ✅ Clean subject names
    subject_names = []
    for sub in subjects:
        if hasattr(sub, "subject"):
            subject_obj = getattr(sub, "subject", None)

            subject_name = (
                getattr(subject_obj, "subject_name", None)
                or getattr(subject_obj, "name", None)
                or getattr(subject_obj, "title", None)
                or str(subject_obj)
            )

            subject_names.append(str(subject_name))
        else:
            subject_names.append(str(sub))

    # ✅ Duplicate remove but serial keep
    clean_subject_names = []
    for s in subject_names:
        if s and s not in clean_subject_names:
            clean_subject_names.append(s)

    subject_names = clean_subject_names

    summaries = []

    if selected_exam:
        update_all_students_summary(selected_exam)
        generate_rank(selected_exam)

        for student in students:

            summary = StudentResultSummary.objects.filter(
                student=student,
                exam=selected_exam
            ).first()

            subject_marks = []

            for subject_name in subject_names:

                result = ExamResult.objects.filter(
                    student=student,
                    exam=selected_exam,
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

    if request.method == "POST":

        student = get_object_or_404(Student, id=request.POST.get("student"))
        exam = get_object_or_404(Exam, id=request.POST.get("exam"))

        subject_list = request.POST.getlist("subject[]")
        written_list = request.POST.getlist("written_marks[]")
        oral_list = request.POST.getlist("oral_marks[]")
        max_list = request.POST.getlist("max_marks[]")

        for i, subject in enumerate(subject_list):

            written_marks = safe_int(written_list[i], 0) if i < len(written_list) else 0
            oral_marks = safe_int(oral_list[i], 0) if i < len(oral_list) else 0
            max_marks = safe_int(max_list[i], 100) if i < len(max_list) else 100

            if not subject:
                continue

            if written_marks == 0 and oral_marks == 0:
                old_result = ExamResult.objects.filter(
                    student=student,
                    exam=exam,
                    subject=subject
                ).first()

                if old_result:
                    continue

            if written_marks + oral_marks > max_marks:
                messages.error(
                    request,
                    f"{subject}: Written + Oral marks cannot be greater than Max Marks."
                )
                return redirect(
                    f"/exams/results/popup-entry/?exam={exam.id}&class={class_name}&search={search}"
                )

            ExamResult.objects.update_or_create(
                student=student,
                exam=exam,
                subject=subject,
                defaults={
                    "written_marks": written_marks,
                    "oral_marks": oral_marks,
                    "max_marks": max_marks,
                }
            )

        update_student_summary(student, exam)
        update_all_students_summary(exam)
        generate_rank(exam)

        messages.success(request, "All subject marks saved successfully.")

        return redirect(
            f"/exams/results/popup-entry/?exam={exam.id}&class={class_name}&search={search}"
        )

    return render(request, "exams/popup_entry.html", {
        "students": students,
        "summaries": summaries,
        "subjects": subject_names,
        "exams": exams,
        "classes": classes,
        "selected_exam": selected_exam,
        "selected_exam_id": exam_id,
        "selected_class": class_name,
        "search": search,
        "settings_obj": get_general_settings(),
    })


# ================================
# REPORT CARD
# ================================

@login_required
def report_card_select(request):
    settings_obj = get_general_settings()

    classes = get_all_classes()
    selected_class = request.GET.get("class")

    students = get_students_queryset()
    students = filter_students_by_class(students, selected_class)

    exams = Exam.objects.all().order_by("-id")

    student_id = request.GET.get("student_id")
    exam_id = request.GET.get("exam_id")

    if student_id and exam_id:
        student = get_object_or_404(Student, id=student_id)
        exam = get_object_or_404(Exam, id=exam_id)

        update_student_summary(student, exam)
        generate_rank(exam)

        results = ExamResult.objects.filter(
            student=student,
            exam=exam
        ).order_by("id")

        written_total = sum(r.written_marks for r in results)
        oral_total = sum(r.oral_marks for r in results)
        grand_total = sum(r.total_marks for r in results)
        max_total = sum(r.max_marks for r in results)

        percentage = 0
        if max_total > 0:
            percentage = round((grand_total / max_total) * 100, 2)

        final_grade = get_final_grade(percentage)
        result_status = "Pass" if percentage >= 35 else "Fail"

        summary = StudentResultSummary.objects.filter(
            student=student,
            exam=exam
        ).first()

        class_rank = summary.rank if summary else "-"

        attendance_percentage = 0
        try:
            from attendance.models import StudentAttendance

            attendance_records = StudentAttendance.objects.filter(student=student)
            total_days = attendance_records.count()
            present_days = attendance_records.filter(status__iexact="Present").count()

            if total_days > 0:
                attendance_percentage = round((present_days / total_days) * 100, 2)
        except Exception:
            attendance_percentage = 0

        roll_no = getattr(student, "roll_no", "") or "-"
        registration_no = getattr(student, "registration_no", "") or "-"
        result_no = f"ARM-RESULT-{student.id}-{exam.id}"

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
            "class_rank": class_rank,

            "roll_no": roll_no,
            "registration_no": registration_no,
            "result_no": result_no,
            "attendance_percentage": attendance_percentage,
            "academic_session": exam.academic_session,

            "classes": classes,
            "selected_class": selected_class,

            "settings_obj": settings_obj,
            "header_url": get_setting_image_url(settings_obj, "school_header", "/static/images/header.jpg"),
            "logo_url": get_setting_image_url(settings_obj, "school_logo", "/static/images/logo.png"),
            "principal_sign": get_setting_image_url(settings_obj, "principal_signature", "/static/images/principal_sign.png"),
            "qr_code": "/static/images/qr.png",
        })

    return render(request, "exams/report_card_select.html", {
        "students": students,
        "exams": exams,
        "classes": classes,
        "selected_class": selected_class,
        "settings_obj": settings_obj,
    })


# ================================
# BULK REPORT CARD
# ================================

@login_required
def report_card_bulk_select(request):
    exams = Exam.objects.all().order_by("-id")
    classes = get_all_classes()

    return render(request, "exams/report_card_bulk_select.html", {
        "exams": exams,
        "classes": classes,
        "settings_obj": get_general_settings(),
    })


@login_required
def report_card_bulk_print(request):
    exam_id = request.GET.get("exam")
    selected_class = request.GET.get("class")

    exam = Exam.objects.filter(id=exam_id).first() if exam_id else None
    cards = []

    students = Student.objects.all().order_by("roll_no", "student_name")

    # ✅ Safe class filter: class_assigned FK er name field na thakleo error hobe na
    if selected_class:
        filtered_students = []

        for student in students:
            student_class_obj = getattr(student, "class_assigned", None)

            student_class_id = str(getattr(student_class_obj, "id", ""))
            student_class_text = str(student_class_obj).strip()

            if selected_class == student_class_id or selected_class.strip().lower() == student_class_text.lower():
                filtered_students.append(student)

        students = filtered_students

    for student in students:
        results = ExamResult.objects.filter(
            student=student,
            exam_id=exam_id
        )

        if not results.exists():
            continue

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

        final_grade = "D"
        if percentage >= 90:
            final_grade = "AA"
        elif percentage >= 80:
            final_grade = "A+"
        elif percentage >= 60:
            final_grade = "A"
        elif percentage >= 45:
            final_grade = "B+"
        elif percentage >= 40:
            final_grade = "B"
        elif percentage >= 35:
            final_grade = "C+"
        elif percentage >= 24:
            final_grade = "C"

        result_status = "PASS" if percentage >= 34 else "FAIL"

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
            "result_status": result_status,

            "attendance_percentage": 95,
            "class_rank": "-",
            "academic_session": exam.academic_session if exam and exam.academic_session else "2025-26",
        })

    return render(request, "exams/report_card_bulk_print.html", {
        "cards": cards,
        "exam": exam,
        "selected_class": selected_class,
        "settings_obj": get_general_settings(),
    })
# =====================================
# MERIT LIST / TOPPER SYSTEM
# =====================================

@login_required
def merit_list(request):

    from django.db.models import F, IntegerField, ExpressionWrapper

    exams = Exam.objects.all().order_by("-id")
    classes = get_all_classes()

    exam_id = request.GET.get("exam")
    class_name = request.GET.get("class")

    selected_exam = None
    merit_students = []
    subject_toppers = []

    school_topper = None
    pass_count = 0
    fail_count = 0
    avg_percentage = 0
    total_students = 0
    highest_percentage = 0

    if exam_id:
        selected_exam = get_object_or_404(Exam, id=exam_id)

        summaries = StudentResultSummary.objects.filter(
            exam=selected_exam
        ).select_related("student")

        if class_name:
            try:
                summaries = summaries.filter(
                    student__class_assigned__class_name=class_name
                )
            except Exception:
                summaries = summaries.filter(
                    student__class_assigned=class_name
                )

        summaries = summaries.order_by("-percentage", "-total_marks")

        result_qs = ExamResult.objects.filter(
            exam=selected_exam
        ).select_related("student")

        if class_name:
            try:
                result_qs = result_qs.filter(
                    student__class_assigned__class_name=class_name
                )
            except Exception:
                result_qs = result_qs.filter(
                    student__class_assigned=class_name
                )

        subject_names = result_qs.values_list(
            "subject",
            flat=True
        ).distinct()

        for subject in subject_names:

            top_result = result_qs.filter(
                subject=subject
            ).annotate(
                calculated_total=ExpressionWrapper(
                    F("written_marks") + F("oral_marks"),
                    output_field=IntegerField()
                )
            ).order_by("-calculated_total").first()

            if top_result:
                subject_toppers.append({
                    "subject": subject,
                    "marks": top_result.written_marks + top_result.oral_marks,
                    "student": top_result.student,
                })

        total_students = summaries.count()

        if summaries.exists():
            top_summary = summaries.first()

            school_topper = {
                "student": top_summary.student,
                "percentage": top_summary.percentage,
                "grade": top_summary.grade,
                "total": top_summary.total_marks,
            }

            highest_percentage = top_summary.percentage or 0

        pass_count = summaries.filter(
            result_status="Pass"
        ).count()

        fail_count = summaries.filter(
            result_status="Fail"
        ).count()

        total_percentage = 0

        for s in summaries:
            total_percentage += s.percentage or 0

        if total_students > 0:
            avg_percentage = round(
                total_percentage / total_students,
                2
            )

        rank = 1

        for s in summaries:
            merit_students.append({
                "rank": rank,
                "student": s.student,
                "percentage": s.percentage,
                "grade": s.grade,
                "status": s.result_status,
                "total": s.total_marks,
            })
            rank += 1

    return render(request, "exams/merit_list.html", {
        "exams": exams,
        "classes": classes,
        "selected_exam": selected_exam,
        "selected_class": class_name,
        "merit_students": merit_students,
        "subject_toppers": subject_toppers,

        "school_topper": school_topper,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "avg_percentage": avg_percentage,
        "total_students": total_students,
        "highest_percentage": highest_percentage,
    })
# ================================
# TOPPER RESULT
# ================================

@login_required
def topper_result(request):

    exam_id = request.GET.get("exam")
    class_name = request.GET.get("class")

    exams = Exam.objects.all().order_by("-id")
    classes = get_all_classes()

    selected_exam = None
    toppers = []

    if exam_id:

        selected_exam = get_object_or_404(Exam, id=exam_id)

        summaries = StudentResultSummary.objects.filter(
            exam=selected_exam
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
    })


# ================================
# ADMIT CARD
# ================================

@login_required
def admit_card_select(request):
    settings_obj = get_general_settings()

    exams = Exam.objects.all().order_by("-id")
    classes = get_all_classes()

    exam_id = request.GET.get("exam")
    class_name = request.GET.get("class")
    student_id = request.GET.get("student")
    search = request.GET.get("search", "").strip()

    selected_exam = None
    selected_student = None

    students = get_students_queryset()
    students = filter_students_by_class(students, class_name)
    students = apply_student_search(students, search)

    if exam_id:
        selected_exam = get_object_or_404(Exam, id=exam_id)

    if student_id:
        selected_student = get_object_or_404(Student, id=student_id)

    routines = ExamRoutine.objects.none()

    if selected_exam:
        routines = ExamRoutine.objects.filter(
            exam=selected_exam
        ).order_by("date", "start_time")

        if class_name:
            routines = routines.filter(school_class=class_name)

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
            "academic_session": selected_exam.academic_session,
            "selected_class": class_name,
            "classes": classes,
            "search": search,

            "settings_obj": settings_obj,
            "header_url": header_url,
            "logo_url": logo_url,
            "principal_sign": principal_sign,
        })

    return render(request, "exams/admit_card_select.html", {
        "exams": exams,
        "students": students,
        "classes": classes,
        "selected_exam": selected_exam,
        "selected_exam_id": exam_id,
        "selected_class": class_name,
        "search": search,
        "settings_obj": settings_obj,
    })


@login_required
def admit_card_bulk_print(request):
    settings_obj = get_general_settings()

    exams = Exam.objects.all().order_by("-id")
    classes = get_all_classes()


    exam_id = request.POST.get("exam") or request.GET.get("exam")

    if exam_id in [None, "", "None"]:
        messages.error(request, "Please select exam first.")
        return redirect("desk_slip_select")

    class_name = request.POST.get("class") or request.GET.get("class")
    

    selected_ids = request.POST.getlist("students") or request.GET.getlist("students")

    selected_exam = None
    students = Student.objects.none()
    routines = ExamRoutine.objects.none()

    if exam_id:
        selected_exam = get_object_or_404(Exam, id=exam_id)

        students = get_students_queryset()
        students = filter_students_by_class(students, class_name)

        if selected_ids:
            students = students.filter(id__in=selected_ids)

        routines = ExamRoutine.objects.filter(
            exam=selected_exam
        ).order_by("date", "start_time")

        if class_name:
            routines = routines.filter(school_class=class_name)

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
        "students": students,
        "routines": routines,
        "academic_session": selected_exam.academic_session if selected_exam else "",

        "settings_obj": settings_obj,
        "header_url": header_url,
        "logo_url": logo_url,
        "principal_sign": principal_sign,
    })

# ================================
# DESK SLIP
# ================================

@login_required
def desk_slip_select(request):

    settings_obj = get_general_settings()

    exams = Exam.objects.all().order_by("-id")
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
            id=exam_id
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
    })


@login_required
def desk_slip_bulk_print(request):

    settings_obj = get_general_settings()

    exams = Exam.objects.all().order_by("-id")
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
            id=exam_id
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
        }
    )


# ================================
# BLANK MARKS SHEET
# ================================

@login_required
def blank_marks_sheet_select(request):
    settings_obj = get_general_settings()

    exams = Exam.objects.all().order_by("-id")
    classes = get_all_classes()

    return render(request, "exams/blank_marks_sheet_select.html", {
        "exams": exams,
        "classes": classes,
        "settings_obj": settings_obj,
    })


@login_required
def blank_marks_sheet_print(request):
    settings_obj = get_general_settings()

    exam_id = request.GET.get("exam")
    class_name = request.GET.get("class")

    if exam_id in [None, "", "None"]:
        messages.error(request, "Please select exam first.")
        return redirect("blank_marks_sheet_select")

    selected_exam = get_object_or_404(Exam, id=exam_id)

    students = get_students_queryset()
    students = filter_students_by_class(students, class_name)

    subjects = []

    if class_name:
        try:
            from academics.models import Class, ClassSubject

            class_obj = Class.objects.filter(class_name=class_name).first()

            if class_obj:
                subjects = ClassSubject.objects.filter(
                    school_class=class_obj,
                    is_active=True
                ).select_related("subject").order_by("subject__subject_name")

        except Exception:
            subjects = []

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
    })

# =====================================
# PREMIUM ONLINE RESULT PORTAL
# =====================================

def online_result_portal(request):

    result_data = None
    error = None

    if request.method == "POST":

        student_id = request.POST.get("student_id")
        exam_id = request.POST.get("exam")
        dob = request.POST.get("dob")
        student_class = request.POST.get("student_class")

        try:

            # ✅ SID + DOB + CLASS SECURITY
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
                id=exam_id
            )

            summary = StudentResultSummary.objects.filter(
                student=student,
                exam=exam
            ).first()

            results = ExamResult.objects.filter(
                student=student,
                exam=exam
            )

            # ✅ CLASS RANK CALCULATION
            class_rank = "-"

            try:
                class_students = StudentResultSummary.objects.filter(
                    exam=exam,
                    student__class_assigned__class_name=student_class
                ).order_by("-percentage", "-total_marks")
            except Exception:
                class_students = StudentResultSummary.objects.filter(
                    exam=exam,
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
        "exams": Exam.objects.all().order_by("-id"),
        "classes": get_all_classes(),
        "result_data": result_data,
        "error": error,
        "settings_obj": get_general_settings(),
    })