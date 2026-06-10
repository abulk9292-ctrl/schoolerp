from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from students.models import Student
from .forms import StudentQuestionForm, TeacherAnswerForm
from .models import StudentQuestion


def _student_field_names():
    return {field.name for field in Student._meta.get_fields()}


def _student_from_user(user):
    """
    Safe student finder for AL RAHMAN MISSION ERP.
    Your Student model has login_username/login_password, not user ForeignKey.
    So this function avoids Student.objects.filter(user=user) FieldError.
    """
    if not user or not user.is_authenticated:
        return None

    fields = _student_field_names()
    query = Q()

    if "user" in fields:
        query |= Q(user=user)
    if "login_username" in fields:
        query |= Q(login_username=user.username)
    if "student_id" in fields:
        query |= Q(student_id=user.username)
    if "admission_no" in fields:
        query |= Q(admission_no=user.username)
    if "registration_no" in fields:
        query |= Q(registration_no=user.username)

    if not query:
        return None

    return Student.objects.filter(query).first()


def _students_for_parent_user(user):
    """
    Safe parent-student finder.
    Supports parent_user if exists, otherwise parent_login/login_username style.
    """
    if not user or not user.is_authenticated:
        return Student.objects.none()

    fields = _student_field_names()
    query = Q()

    if "parent_user" in fields:
        query |= Q(parent_user=user)
    if "parent_login" in fields:
        query |= Q(parent_login=user.username)
    if "guardian_username" in fields:
        query |= Q(guardian_username=user.username)
    if "login_username" in fields:
        query |= Q(login_username=user.username)

    if not query:
        return Student.objects.none()

    return Student.objects.filter(query).distinct()


@login_required
def question_list(request):
    questions = StudentQuestion.objects.select_related(
        "student", "class_assigned", "answered_by"
    )

    status = request.GET.get("status", "").strip()
    q = request.GET.get("q", "").strip()

    if status:
        questions = questions.filter(status=status)
    if q:
        questions = questions.filter(
            Q(title__icontains=q) |
            Q(question_text__icontains=q) |
            Q(subject__icontains=q) |
            Q(student__student_name__icontains=q)
        )

    context = {
        "questions": questions,
        "total_questions": questions.count(),
        "pending_count": questions.filter(status="PENDING").count(),
        "answered_count": questions.filter(status="ANSWERED").count(),
        "closed_count": questions.filter(status="CLOSED").count(),
    }
    return render(request, "question_answers/question_list.html", context)


@login_required
def question_ask(request):
    student = _student_from_user(request.user)

    if request.method == "POST":
        form = StudentQuestionForm(request.POST, request.FILES)
        if form.is_valid():
            question = form.save(commit=False)
            if student:
                question.student = student
                if not question.class_assigned:
                    question.class_assigned = student.class_assigned
            else:
                messages.error(request, "Student profile not found for this login.")
                return redirect("question_answers:student_question_list")
            question.save()
            messages.success(request, "Question submitted successfully.")
            return redirect("question_answers:student_question_list")
    else:
        initial = {}
        if student:
            initial["class_assigned"] = student.class_assigned
        form = StudentQuestionForm(initial=initial)

    return render(request, "question_answers/question_form.html", {
        "form": form,
        "title": "Ask Question",
    })


@login_required
def question_answer(request, pk):
    question = get_object_or_404(StudentQuestion, pk=pk)

    if request.method == "POST":
        form = TeacherAnswerForm(request.POST, request.FILES, instance=question)
        if form.is_valid():
            answer = form.save(commit=False)
            if answer.answer_text or answer.answer_file:
                answer.answered_by = request.user
                answer.answered_at = timezone.now()
                if answer.status == "PENDING":
                    answer.status = "ANSWERED"
            answer.save()
            messages.success(request, "Answer saved successfully.")
            return redirect("question_answers:question_list")
    else:
        form = TeacherAnswerForm(instance=question)

    return render(request, "question_answers/question_answer.html", {
        "form": form,
        "question": question,
    })


@login_required
def question_detail(request, pk):
    question = get_object_or_404(StudentQuestion, pk=pk)
    return render(request, "question_answers/question_detail.html", {"question": question})


@login_required
def question_delete(request, pk):
    question = get_object_or_404(StudentQuestion, pk=pk)

    if request.method == "POST":
        question.delete()
        messages.success(request, "Question deleted successfully.")
        return redirect("question_answers:question_list")

    return render(request, "question_answers/question_confirm_delete.html", {
        "question": question,
    })


@login_required
def student_question_list(request):
    student = _student_from_user(request.user)
    questions = StudentQuestion.objects.none()

    if student:
        questions = StudentQuestion.objects.filter(student=student)

    return render(request, "question_answers/student_question_list.html", {
        "student": student,
        "questions": questions,
    })


@login_required
def parent_question_list(request):
    students = _students_for_parent_user(request.user)
    questions = StudentQuestion.objects.filter(
        student__in=students,
        is_visible_to_parent=True
    )

    return render(request, "question_answers/parent_question_list.html", {
        "students": students,
        "questions": questions,
    })
