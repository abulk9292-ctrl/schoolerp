from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)

from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import (
    BehaviourRecord,
    SkillEvaluation
)

from .forms import (
    BehaviourRecordForm,
    SkillEvaluationForm
)

from students.models import Student
from teachers.models import Employee


# =====================================================
# GET LOGGED TEACHER
# =====================================================

def get_logged_teacher(request):

    teacher_id = request.session.get("teacher_id")

    if teacher_id:
        try:
            return Employee.objects.get(
                id=teacher_id
            )
        except Employee.DoesNotExist:
            return None

    return None


# =====================================================
# DASHBOARD
# =====================================================

@login_required
def behaviour_dashboard(request):

    total_behaviour_records = BehaviourRecord.objects.count()

    total_skill_evaluations = SkillEvaluation.objects.count()

    positive_records = BehaviourRecord.objects.filter(
        behaviour_type="Positive"
    ).count()

    negative_records = BehaviourRecord.objects.filter(
        behaviour_type="Negative"
    ).count()

    recent_behaviours = BehaviourRecord.objects.select_related(
        "student"
    ).order_by("-id")[:10]

    return render(
        request,
        "behaviour/dashboard.html",
        {

            "total_behaviour_records": total_behaviour_records,

            "total_skill_evaluations": total_skill_evaluations,

            "positive_records": positive_records,

            "negative_records": negative_records,

            "recent_behaviours": recent_behaviours,
        }
    )


# =====================================================
# BEHAVIOUR RECORD LIST
# =====================================================

@login_required
def behaviour_record_list(request):

    records = BehaviourRecord.objects.select_related(
        "student"
    ).order_by("-date", "-id")

    return render(
        request,
        "behaviour/record_list.html",
        {
            "records": records
        }
    )


# =====================================================
# ADD BEHAVIOUR RECORD
# =====================================================

@login_required
def behaviour_record_add(request):

    if request.method == "POST":

        form = BehaviourRecordForm(request.POST)

        if form.is_valid():

            behaviour = form.save(commit=False)

            teacher = get_logged_teacher(request)

            if teacher:
                behaviour.teacher = teacher

            behaviour.save()

            messages.success(
                request,
                "Behaviour record added successfully."
            )

            return redirect("behaviour_record_list")

    else:

        form = BehaviourRecordForm()

    return render(
        request,
        "behaviour/record_form.html",
        {
            "form": form,
            "page_title": "Add Behaviour Record"
        }
    )


# =====================================================
# EDIT BEHAVIOUR RECORD
# =====================================================

@login_required
def behaviour_record_edit(request, pk):

    record = get_object_or_404(
        BehaviourRecord,
        pk=pk
    )

    if request.method == "POST":

        form = BehaviourRecordForm(
            request.POST,
            instance=record
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Behaviour record updated successfully."
            )

            return redirect("behaviour_record_list")

    else:

        form = BehaviourRecordForm(
            instance=record
        )

    return render(
        request,
        "behaviour/record_form.html",
        {
            "form": form,
            "page_title": "Edit Behaviour Record"
        }
    )


# =====================================================
# DELETE BEHAVIOUR RECORD
# =====================================================

@login_required
def behaviour_record_delete(request, pk):

    record = get_object_or_404(
        BehaviourRecord,
        pk=pk
    )

    if request.method == "POST":

        record.delete()

        messages.success(
            request,
            "Behaviour record deleted successfully."
        )

        return redirect("behaviour_record_list")

    return render(
        request,
        "behaviour/record_delete.html",
        {
            "record": record
        }
    )


# =====================================================
# SKILL EVALUATION LIST
# =====================================================

@login_required
def skill_evaluation_list(request):

    evaluations = SkillEvaluation.objects.select_related(
        "student"
    ).order_by("-year", "-id")

    return render(
        request,
        "behaviour/skill_list.html",
        {
            "evaluations": evaluations
        }
    )


# =====================================================
# ADD SKILL EVALUATION
# =====================================================

@login_required
def skill_evaluation_add(request):

    if request.method == "POST":

        form = SkillEvaluationForm(request.POST)

        if form.is_valid():

            evaluation = form.save(commit=False)

            teacher = get_logged_teacher(request)

            if teacher:
                evaluation.teacher = teacher

            evaluation.save()

            messages.success(
                request,
                "Skill evaluation added successfully."
            )

            return redirect("skill_evaluation_list")

    else:

        form = SkillEvaluationForm()

    return render(
        request,
        "behaviour/skill_form.html",
        {
            "form": form,
            "page_title": "Add Skill Evaluation"
        }
    )


# =====================================================
# EDIT SKILL EVALUATION
# =====================================================

@login_required
def skill_evaluation_edit(request, pk):

    evaluation = get_object_or_404(
        SkillEvaluation,
        pk=pk
    )

    if request.method == "POST":

        form = SkillEvaluationForm(
            request.POST,
            instance=evaluation
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Skill evaluation updated successfully."
            )

            return redirect("skill_evaluation_list")

    else:

        form = SkillEvaluationForm(
            instance=evaluation
        )

    return render(
        request,
        "behaviour/skill_form.html",
        {
            "form": form,
            "page_title": "Edit Skill Evaluation"
        }
    )


# =====================================================
# DELETE SKILL EVALUATION
# =====================================================

@login_required
def skill_evaluation_delete(request, pk):

    evaluation = get_object_or_404(
        SkillEvaluation,
        pk=pk
    )

    if request.method == "POST":

        evaluation.delete()

        messages.success(
            request,
            "Skill evaluation deleted successfully."
        )

        return redirect("skill_evaluation_list")

    return render(
        request,
        "behaviour/skill_delete.html",
        {
            "evaluation": evaluation
        }
    )


# =====================================================
# STUDENT BEHAVIOUR PROFILE
# =====================================================

@login_required
def student_behaviour_profile(request, student_id):

    student = get_object_or_404(
        Student,
        id=student_id
    )

    behaviour_records = BehaviourRecord.objects.filter(
        student=student
    ).order_by("-date", "-id")

    skill_evaluations = SkillEvaluation.objects.filter(
        student=student
    ).order_by("-year", "-id")

    positive_points = BehaviourRecord.objects.filter(
        student=student,
        behaviour_type="Positive"
    ).count()

    negative_points = BehaviourRecord.objects.filter(
        student=student,
        behaviour_type="Negative"
    ).count()

    return render(
        request,
        "behaviour/student_profile.html",
        {

            "student": student,

            "behaviour_records": behaviour_records,

            "skill_evaluations": skill_evaluations,

            "positive_points": positive_points,

            "negative_points": negative_points,
        }
    )