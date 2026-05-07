from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import Homework
from .forms import HomeworkForm


@login_required
def homework_list(request):
    homeworks = Homework.objects.select_related(
        "given_by"
    ).all().order_by("-id")

    class_name = request.GET.get("class")
    status = request.GET.get("status")
    search = request.GET.get("search")

    if class_name:
        homeworks = homeworks.filter(school_class__icontains=class_name)

    if status:
        homeworks = homeworks.filter(status=status)

    if search:
        homeworks = homeworks.filter(title__icontains=search)

    return render(request, "homework/homework_list.html", {
        "homeworks": homeworks,
        "selected_class": class_name,
        "selected_status": status,
        "search": search,
    })


@login_required
def homework_add(request):
    if request.method == "POST":
        form = HomeworkForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, "Homework added successfully.")
            return redirect("homework_list")
    else:
        form = HomeworkForm()

    return render(request, "homework/homework_form.html", {
        "form": form,
        "page_title": "Add Homework",
    })


@login_required
def homework_edit(request, pk):
    homework = get_object_or_404(Homework, pk=pk)

    if request.method == "POST":
        form = HomeworkForm(request.POST, request.FILES, instance=homework)

        if form.is_valid():
            form.save()
            messages.success(request, "Homework updated successfully.")
            return redirect("homework_list")
    else:
        form = HomeworkForm(instance=homework)

    return render(request, "homework/homework_form.html", {
        "form": form,
        "page_title": "Edit Homework",
    })


@login_required
def homework_delete(request, pk):
    homework = get_object_or_404(Homework, pk=pk)
    homework.delete()
    messages.success(request, "Homework deleted successfully.")
    return redirect("homework_list")