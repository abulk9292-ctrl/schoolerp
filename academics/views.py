from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import Class, Subject, ClassSubject
from .forms import ClassForm, SubjectForm, ClassSubjectAssignForm


# 🔐 Permission Helper
def has_academics_permission(request):
    if request.user.is_superuser or request.user.is_staff:
        return True

    emp = getattr(request.user, 'employee', None)

    if not emp:
        return False

    if getattr(emp, 'is_erp_admin', False):
        return True

    return getattr(emp, 'can_access_academics', False)


# ✅ CLASS LIST + ADD
@login_required
def class_list(request):
    if not has_academics_permission(request):
        messages.error(request, "❌ Permission Denied")
        return redirect('/teacher-dashboard/')

    if request.method == 'POST':
        form = ClassForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "✅ Class added successfully.")
            return redirect('class_list')
    else:
        form = ClassForm()

    classes = Class.objects.select_related('class_teacher').all().order_by('class_name')

    return render(request, 'academics/class_list.html', {
        'classes': classes,
        'form': form,
    })


# ✅ CLASS EDIT
@login_required
def class_edit(request, pk):
    if not has_academics_permission(request):
        messages.error(request, "❌ Permission Denied")
        return redirect('/teacher-dashboard/')

    class_obj = get_object_or_404(Class, pk=pk)

    if request.method == 'POST':
        form = ClassForm(request.POST, instance=class_obj)

        if form.is_valid():
            form.save()
            messages.success(request, "✅ Class updated successfully.")
            return redirect('class_list')
    else:
        form = ClassForm(instance=class_obj)

    classes = Class.objects.select_related('class_teacher').all().order_by('class_name')

    return render(request, 'academics/class_list.html', {
        'classes': classes,
        'form': form,
        'edit_mode': True,
        'class_obj': class_obj,
    })


# ✅ CLASS DELETE
@login_required
def class_delete(request, pk):
    if not has_academics_permission(request):
        messages.error(request, "❌ Permission Denied")
        return redirect('/teacher-dashboard/')

    class_obj = get_object_or_404(Class, pk=pk)

    if request.method == 'POST':
        class_obj.delete()
        messages.success(request, "🗑 Class deleted successfully.")
        return redirect('class_list')

    return render(request, 'academics/class_confirm_delete.html', {
        'class_obj': class_obj
    })


# ✅ SUBJECT LIST + ADD
@login_required
def subject_list(request):
    if not has_academics_permission(request):
        messages.error(request, "❌ Permission Denied")
        return redirect('/teacher-dashboard/')

    if request.method == 'POST':
        form = SubjectForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "✅ Subject added successfully.")
            return redirect('subject_list')
    else:
        form = SubjectForm()

    subjects = Subject.objects.all().order_by('subject_name')

    return render(request, 'academics/subject_list.html', {
        'subjects': subjects,
        'form': form,
    })


# ✅ SUBJECT EDIT
@login_required
def subject_edit(request, pk):
    if not has_academics_permission(request):
        messages.error(request, "❌ Permission Denied")
        return redirect('/teacher-dashboard/')

    subject = get_object_or_404(Subject, pk=pk)

    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)

        if form.is_valid():
            form.save()
            messages.success(request, "✅ Subject updated successfully.")
            return redirect('subject_list')
    else:
        form = SubjectForm(instance=subject)

    subjects = Subject.objects.all().order_by('subject_name')

    return render(request, 'academics/subject_list.html', {
        'subjects': subjects,
        'form': form,
        'edit_mode': True,
        'subject_obj': subject,
    })


# ✅ SUBJECT DELETE
@login_required
def subject_delete(request, pk):
    if not has_academics_permission(request):
        messages.error(request, "❌ Permission Denied")
        return redirect('/teacher-dashboard/')

    subject = get_object_or_404(Subject, pk=pk)

    if request.method == 'POST':
        subject.delete()
        messages.success(request, "🗑 Subject deleted successfully.")
        return redirect('subject_list')

    return render(request, 'academics/subject_confirm_delete.html', {
        'subject': subject
    })


# ✅ CLASS WISE SUBJECT ASSIGN
@login_required
def class_subject_assign(request):
    if not has_academics_permission(request):
        messages.error(request, "❌ Permission Denied")
        return redirect('/teacher-dashboard/')

    selected_class_id = request.GET.get('class') or request.POST.get('school_class')
    selected_class = None
    assigned_subject_ids = []

    if selected_class_id:
        selected_class = get_object_or_404(Class, id=selected_class_id)

        assigned_subject_ids = list(
            ClassSubject.objects.filter(
                school_class=selected_class,
                is_active=True
            ).values_list('subject_id', flat=True)
        )

    if request.method == 'POST':
        form = ClassSubjectAssignForm(request.POST)

        if form.is_valid():
            school_class = form.cleaned_data['school_class']
            selected_subjects = form.cleaned_data['subjects']

            full_marks = form.cleaned_data['full_marks']
            pass_marks = form.cleaned_data['pass_marks']
            written_marks = form.cleaned_data['written_marks']
            oral_marks = form.cleaned_data['oral_marks']
            practical_marks = form.cleaned_data['practical_marks']

            # old assigned inactive
            ClassSubject.objects.filter(
                school_class=school_class
            ).update(is_active=False)

            # selected subject active/create
            for subject in selected_subjects:
                ClassSubject.objects.update_or_create(
                    school_class=school_class,
                    subject=subject,
                    defaults={
                        'full_marks': full_marks,
                        'pass_marks': pass_marks,
                        'written_marks': written_marks,
                        'oral_marks': oral_marks,
                        'practical_marks': practical_marks,
                        'is_active': True,
                    }
                )

            messages.success(request, "✅ Class-wise subjects assigned successfully.")
            return redirect(f"{request.path}?class={school_class.id}")
    else:
        initial_data = {}

        if selected_class:
            initial_data['school_class'] = selected_class
            initial_data['subjects'] = assigned_subject_ids

            first_assigned = ClassSubject.objects.filter(
                school_class=selected_class,
                is_active=True
            ).first()

            if first_assigned:
                initial_data['full_marks'] = first_assigned.full_marks
                initial_data['pass_marks'] = first_assigned.pass_marks
                initial_data['written_marks'] = first_assigned.written_marks
                initial_data['oral_marks'] = first_assigned.oral_marks
                initial_data['practical_marks'] = first_assigned.practical_marks

        form = ClassSubjectAssignForm(initial=initial_data)

    class_subjects = ClassSubject.objects.select_related(
        'school_class',
        'subject'
    ).filter(is_active=True).order_by(
        'school_class__class_name',
        'subject__subject_name'
    )

    if selected_class:
        class_subjects = class_subjects.filter(school_class=selected_class)

    return render(request, 'academics/class_subject_assign.html', {
        'form': form,
        'classes': Class.objects.all().order_by('class_name'),
        'subjects': Subject.objects.all().order_by('subject_name'),
        'class_subjects': class_subjects,
        'selected_class': selected_class,
        'assigned_subject_ids': assigned_subject_ids,
    })