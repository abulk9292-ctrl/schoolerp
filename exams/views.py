from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from students.models import Student
from .models import Exam, ExamRoutine, ExamResult, StudentResultSummary
from .forms import ExamForm, ExamRoutineForm, ExamResultForm


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


def generate_rank(exam):
    summaries = StudentResultSummary.objects.filter(
        exam=exam
    ).order_by('-total_marks')

    rank = 1
    for summary in summaries:
        summary.rank = rank
        summary.save()
        rank += 1


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

    generate_rank(exam)


@login_required
def exam_dashboard(request):
    total_exams = Exam.objects.count()
    total_results = ExamResult.objects.count()
    passed = StudentResultSummary.objects.filter(result_status="Pass").count()
    failed = StudentResultSummary.objects.filter(result_status="Fail").count()

    return render(request, "exams/exam_dashboard.html", {
        "total_exams": total_exams,
        "total_results": total_results,
        "passed": passed,
        "failed": failed,
    })


@login_required
def exam_add(request):
    form = ExamForm(request.POST or None)

    if form.is_valid():
        form.save()
        messages.success(request, "Exam saved successfully.")
        return redirect("exam_dashboard")

    return render(request, "exams/exam_form.html", {
        "form": form
    })


@login_required
def exam_routine(request):
    form = ExamRoutineForm(request.POST or None)

    if form.is_valid():
        form.save()
        messages.success(request, "Exam routine saved successfully.")
        return redirect("exam_routine")

    routines = ExamRoutine.objects.select_related("exam").all().order_by("date", "start_time")

    return render(request, "exams/exam_routine.html", {
        "form": form,
        "routines": routines
    })


@login_required
def result_add(request):
    form = ExamResultForm(request.POST or None)

    if form.is_valid():
        result = form.save()
        update_student_summary(result.student, result.exam)

        messages.success(request, "Marks saved successfully.")
        return redirect("result_list")

    return render(request, "exams/result_form.html", {
        "form": form
    })


@login_required
def result_list(request):
    results = ExamResult.objects.select_related("student", "exam").all().order_by(
        "student__id", "exam__id", "subject"
    )

    return render(request, "exams/result_list.html", {
        "results": results
    })


@login_required
def report_card_select(request):
    students = Student.objects.all()
    exams = Exam.objects.all()

    student_id = request.GET.get("student_id")
    exam_id = request.GET.get("exam_id")

    if student_id and exam_id:
        student = get_object_or_404(Student, id=student_id)
        exam = get_object_or_404(Exam, id=exam_id)

        update_student_summary(student, exam)

        results = ExamResult.objects.filter(student=student, exam=exam).order_by("id")
        summary = StudentResultSummary.objects.filter(student=student, exam=exam).first()

        # Auto details
        roll_no = getattr(student, "roll_no", "") or "-"
        registration_no = getattr(student, "registration_no", "") or "-"
        student_class = getattr(student, "school_class", "") or "CLASS"
        section = getattr(student, "section", "") or ""

        # Result No auto generate
        result_no = f"ARM-{student_class}{section}-R{roll_no}-E{exam.id}-S{student.id}"

        # Attendance percentage
        attendance_percentage = 0
        try:
            from attendance.models import StudentAttendance
            attendance_records = StudentAttendance.objects.filter(student=student)
            total_days = attendance_records.count()
            present_days = attendance_records.filter(status="Present").count()

            if total_days > 0:
                attendance_percentage = round((present_days / total_days) * 100, 2)
        except Exception:
            attendance_percentage = 0

        return render(request, "exams/report_card.html", {
            "student": student,
            "exam": exam,
            "results": results,

            "grand_total": summary.total_marks if summary else 0,
            "max_total": summary.max_total_marks if summary else 0,
            "percentage": summary.percentage if summary else 0,
            "final_grade": summary.grade if summary else "-",
            "result_status": summary.result_status if summary else "-",
            "class_rank": summary.rank if summary else "-",

            "roll_no": roll_no,
            "registration_no": registration_no,
            "result_no": result_no,
            "attendance_percentage": attendance_percentage,

            "academic_session": exam.academic_session,

            "header_url": "/static/images/header.jpg",
            "logo_url": "/static/images/logo.png",
            "principal_sign": "/static/images/principal_sign.png",
            "qr_code": "/static/images/qr.png",
        })

    return render(request, "exams/report_card_select.html", {
        "students": students,
        "exams": exams
    })
@login_required
def bulk_result_entry(request):
    students = Student.objects.all()
    subjects = set(ExamResult.objects.values_list('subject', flat=True))

    exam_id = request.GET.get('exam')

    if request.method == "POST":
        exam_id = request.POST.get("exam")

        for student in students:
            for subject in subjects:
                key = f"{student.id}_{subject}"
                mark = request.POST.get(key)

                if mark:
                    ExamResult.objects.update_or_create(
                        student=student,
                        exam_id=exam_id,
                        subject=subject,
                        defaults={
                            "written_marks": int(mark),
                            "oral_marks": 0
                        }
                    )

        return redirect("bulk_result_entry")

    return render(request, "exams/bulk_entry.html", {
        "students": students,
        "subjects": subjects,
        "exams": Exam.objects.all()
    })
@login_required
def popup_result_entry(request):
    students = Student.objects.all().order_by("id")
    exams = Exam.objects.all().order_by("-id")

    selected_exam_id = request.GET.get("exam") or request.POST.get("exam")
    selected_exam = None

    if selected_exam_id:
        selected_exam = get_object_or_404(Exam, id=selected_exam_id)

    if request.method == "POST":
        exam_id = request.POST.get("exam")
        student_id = request.POST.get("student")
        subject = request.POST.get("subject")
        written_marks = int(request.POST.get("written_marks") or 0)
        oral_marks = int(request.POST.get("oral_marks") or 0)
        max_marks = int(request.POST.get("max_marks") or 100)

        student = get_object_or_404(Student, id=student_id)
        exam = get_object_or_404(Exam, id=exam_id)

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

        messages.success(request, "Marks saved successfully.")
        return redirect(f"/exams/popup-entry/?exam={exam.id}")

    summaries = []
    if selected_exam:
        for student in students:
            update_student_summary(student, selected_exam)
            summary = StudentResultSummary.objects.filter(
                student=student,
                exam=selected_exam
            ).first()

            summaries.append({
                "student": student,
                "summary": summary,
            })

    return render(request, "exams/popup_entry.html", {
        "students": students,
        "exams": exams,
        "selected_exam": selected_exam,
        "summaries": summaries,
    })
@login_required
def topper_result(request):
    exams = Exam.objects.all().order_by("-id")
    exam_id = request.GET.get("exam")
    selected_exam = None
    toppers = []

    if exam_id:
        selected_exam = get_object_or_404(Exam, id=exam_id)
        toppers = StudentResultSummary.objects.filter(
            exam=selected_exam
        ).select_related("student").order_by("rank")[:10]

    return render(request, "exams/topper_result.html", {
        "exams": exams,
        "selected_exam": selected_exam,
        "toppers": toppers,
    })


@login_required
def print_bulk_result(request):
    exams = Exam.objects.all().order_by("-id")
    exam_id = request.GET.get("exam")
    selected_exam = None
    summaries = []

    if exam_id:
        selected_exam = get_object_or_404(Exam, id=exam_id)
        summaries = StudentResultSummary.objects.filter(
            exam=selected_exam
        ).select_related("student").order_by("rank")

    return render(request, "exams/print_bulk_result.html", {
        "exams": exams,
        "selected_exam": selected_exam,
        "summaries": summaries,
    })