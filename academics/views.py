from django.shortcuts import render, redirect
from .models import Class, Subject

# CLASS VIEW
def class_list(request):
    if request.method == 'POST':
        name = request.POST.get('class_name')
        if name:
            Class.objects.create(class_name=name)
            return redirect('class_list')

    classes = Class.objects.all()
    return render(request, 'academics/class_list.html', {'classes': classes})


# SUBJECT VIEW
def subject_list(request):
    if request.method == 'POST':
        name = request.POST.get('subject_name')
        if name:
            Subject.objects.create(subject_name=name)
            return redirect('subject_list')

    subjects = Subject.objects.all()
    return render(request, 'academics/subject_list.html', {'subjects': subjects})