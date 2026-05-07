from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import Notice
from .forms import NoticeForm


@login_required
def notice_list(request):
    notices = Notice.objects.select_related(
        "published_by"
    ).all().order_by("-is_pinned", "-id")

    notice_type = request.GET.get("type")
    target = request.GET.get("target")
    class_name = request.GET.get("class")
    status = request.GET.get("status")
    search = request.GET.get("search")

    if notice_type:
        notices = notices.filter(notice_type=notice_type)

    if target:
        notices = notices.filter(target=target)

    if class_name:
        notices = notices.filter(school_class__icontains=class_name)

    if status:
        notices = notices.filter(status=status)

    if search:
        notices = notices.filter(title__icontains=search)

    return render(request, "notices/notice_list.html", {
        "notices": notices,
        "notice_type": notice_type,
        "target": target,
        "class_name": class_name,
        "status": status,
        "search": search,
    })


@login_required
def notice_add(request):
    if request.method == "POST":
        form = NoticeForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, "Notice added successfully.")
            return redirect("notice_list")
    else:
        form = NoticeForm()

    return render(request, "notices/notice_form.html", {
        "form": form,
        "page_title": "Add Notice",
    })


@login_required
def notice_edit(request, pk):
    notice = get_object_or_404(Notice, pk=pk)

    if request.method == "POST":
        form = NoticeForm(request.POST, request.FILES, instance=notice)

        if form.is_valid():
            form.save()
            messages.success(request, "Notice updated successfully.")
            return redirect("notice_list")
    else:
        form = NoticeForm(instance=notice)

    return render(request, "notices/notice_form.html", {
        "form": form,
        "page_title": "Edit Notice",
    })


@login_required
def notice_delete(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    notice.delete()
    messages.success(request, "Notice deleted successfully.")
    return redirect("notice_list")