import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from academics.models import Class, Subject
from teachers.models import Employee

from .models import Period, ClassTimetable, TimetableHoliday
from .forms import PeriodForm, ClassTimetableForm, TimetableHolidayForm


def _can_manage_timetable(request):
    user = request.user
    if user.is_superuser or user.is_staff:
        return True
    employee = getattr(user, "employee", None)
    return bool(employee and getattr(employee, "is_erp_admin", False))


def _get_ordered_classes():
    qs = Class.objects.all()
    for field in ["order", "class_order", "id"]:
        try:
            return qs.order_by(field)
        except Exception:
            continue
    return qs


def _get_ordered_subjects():
    qs = Subject.objects.all()
    for field in ["subject_name", "name", "id"]:
        try:
            return qs.order_by(field)
        except Exception:
            continue
    return qs


def _get_ordered_teachers():
    qs = Employee.objects.all()
    for field in ["name", "employee_name", "teacher_name", "id"]:
        try:
            return qs.order_by(field)
        except Exception:
            continue
    return qs


def _get_sections_from_request(request):
    sections_text = request.GET.get("sections", "").strip()
    if not sections_text:
        sections_text = request.POST.get("sections", "").strip()
    sections = [s.strip() for s in sections_text.split(",") if s.strip()]
    if not sections:
        sections = [""]
    return sections_text, sections


def _is_holiday_day(day_code):
    return TimetableHoliday.objects.filter(day=day_code, is_holiday=True).first()


@login_required
def timetable_dashboard(request):
    total_periods = Period.objects.count()
    total_entries = ClassTimetable.objects.count()
    active_entries = ClassTimetable.objects.filter(is_active=True).count()
    teacher_count = ClassTimetable.objects.values("teacher").exclude(teacher=None).distinct().count()
    holiday_count = TimetableHoliday.objects.filter(is_holiday=True).count()
    break_count = Period.objects.filter(is_break=True).count()
    recent_entries = ClassTimetable.objects.select_related("class_assigned", "period", "subject", "teacher")[:12]

    return render(request, "timetable/dashboard.html", {
        "total_periods": total_periods,
        "total_entries": total_entries,
        "active_entries": active_entries,
        "teacher_count": teacher_count,
        "holiday_count": holiday_count,
        "break_count": break_count,
        "recent_entries": recent_entries,
        "can_manage_timetable": _can_manage_timetable(request),
    })


@login_required
def weekly_timetable(request):
    can_manage = _can_manage_timetable(request)
    days = ClassTimetable.DAY_CHOICES
    periods = Period.objects.all()
    classes = _get_ordered_classes()
    subjects = _get_ordered_subjects()
    teachers = _get_ordered_teachers()
    sections_text, sections = _get_sections_from_request(request)

    if request.method == "POST":
        if not can_manage:
            messages.error(request, "You do not have permission to update timetable.")
            return redirect("weekly_timetable")

        created_count = 0
        updated_count = 0
        deleted_count = 0
        conflict_count = 0
        holiday_skipped = 0

        for day, _day_label in days:
            if _is_holiday_day(day):
                holiday_skipped += 1
                continue

            for period in periods:
                if period.is_break:
                    continue

                for cls in classes:
                    for section in sections:
                        prefix = f"cell_{day}_{period.id}_{cls.id}_{section}"
                        subject_id = request.POST.get(f"{prefix}_subject", "").strip()
                        teacher_id = request.POST.get(f"{prefix}_teacher", "").strip()
                        room_no = request.POST.get(f"{prefix}_room", "").strip()

                        existing = ClassTimetable.objects.filter(
                            day=day,
                            period=period,
                            class_assigned=cls,
                            section=section or None,
                        ).first()

                        if not subject_id and not teacher_id and not room_no:
                            if existing:
                                existing.delete()
                                deleted_count += 1
                            continue

                        teacher = Employee.objects.filter(id=teacher_id).first() if teacher_id else None
                        subject = Subject.objects.filter(id=subject_id).first() if subject_id else None

                        if teacher:
                            conflict = ClassTimetable.objects.filter(
                                day=day,
                                period=period,
                                teacher=teacher,
                                is_active=True,
                            )
                            if existing:
                                conflict = conflict.exclude(id=existing.id)

                            conflict_obj = conflict.select_related("class_assigned", "period").first()
                            if conflict_obj:
                                conflict_count += 1
                                messages.warning(
                                    request,
                                    f"{teacher} already selected on {day} / {period.name} "
                                    f"for {conflict_obj.class_assigned} {conflict_obj.section or ''}. Skipped."
                                )
                                continue

                        if existing:
                            existing.subject = subject
                            existing.teacher = teacher
                            existing.room_no = room_no
                            existing.is_active = True
                            existing.save()
                            updated_count += 1
                        else:
                            ClassTimetable.objects.create(
                                class_assigned=cls,
                                section=section or None,
                                day=day,
                                period=period,
                                subject=subject,
                                teacher=teacher,
                                room_no=room_no,
                                is_active=True,
                            )
                            created_count += 1

        messages.success(
            request,
            f"Weekly timetable saved. Created: {created_count}, Updated: {updated_count}, Deleted: {deleted_count}, Conflicts skipped: {conflict_count}."
        )
        url = "/timetable/weekly/"
        if sections_text:
            url += f"?sections={sections_text}"
        return redirect(url)

    entries = ClassTimetable.objects.select_related(
        "class_assigned", "period", "subject", "teacher"
    ).filter(is_active=True)

    holidays = TimetableHoliday.objects.filter(is_holiday=True)
    holiday_map = {h.day: h for h in holidays}

    weekly_saved_data = []
    for entry in entries:
        weekly_saved_data.append({
            "day": entry.day,
            "period_id": entry.period_id,
            "class_id": entry.class_assigned_id,
            "section": entry.section or "",
            "subject_id": entry.subject_id or "",
            "teacher_id": entry.teacher_id or "",
            "room_no": entry.room_no or "",
        })

    return render(request, "timetable/weekly.html", {
        "days": days,
        "periods": periods,
        "classes": classes,
        "subjects": subjects,
        "teachers": teachers,
        "sections": sections,
        "sections_text": sections_text,
        "entries": entries,
        "weekly_saved_data_json": json.dumps(weekly_saved_data),
        "holiday_map": holiday_map,
        "can_manage_timetable": can_manage,
    })


@login_required
def holiday_list(request):
    holidays = TimetableHoliday.objects.all()
    return render(request, "timetable/holiday_list.html", {
        "holidays": holidays,
        "can_manage_timetable": _can_manage_timetable(request),
    })


@login_required
def holiday_add(request):
    form = TimetableHolidayForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Holiday added.")
        return redirect("timetable_holiday_list")
    return render(request, "timetable/holiday_form.html", {"form": form, "title": "Add Holiday"})


@login_required
def holiday_edit(request, pk):
    obj = get_object_or_404(TimetableHoliday, pk=pk)
    form = TimetableHolidayForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Holiday updated.")
        return redirect("timetable_holiday_list")
    return render(request, "timetable/holiday_form.html", {"form": form, "title": "Edit Holiday"})


@login_required
def holiday_delete(request, pk):
    obj = get_object_or_404(TimetableHoliday, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Holiday deleted.")
        return redirect("timetable_holiday_list")
    return render(request, "timetable/confirm_delete.html", {"object": obj, "back_url": "timetable_holiday_list"})


@login_required
def period_list(request):
    periods = Period.objects.all()
    return render(request, "timetable/period_list.html", {
        "periods": periods,
        "can_manage_timetable": _can_manage_timetable(request),
    })


@login_required
def period_add(request):
    form = PeriodForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Period added.")
        return redirect("period_list")
    return render(request, "timetable/period_form.html", {"form": form, "title": "Add Period"})


@login_required
def period_edit(request, pk):
    obj = get_object_or_404(Period, pk=pk)
    form = PeriodForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Period updated.")
        return redirect("period_list")
    return render(request, "timetable/period_form.html", {"form": form, "title": "Edit Period"})


@login_required
def period_delete(request, pk):
    obj = get_object_or_404(Period, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Period deleted.")
        return redirect("period_list")
    return render(request, "timetable/confirm_delete.html", {"object": obj, "back_url": "period_list"})


@login_required
def timetable_entry_list(request):
    q = request.GET.get("q", "").strip()
    entries = ClassTimetable.objects.select_related("class_assigned", "period", "subject", "teacher")
    if q:
        entries = entries.filter(
            Q(section__icontains=q)
            | Q(room_no__icontains=q)
            | Q(subject__subject_name__icontains=q)
            | Q(subject__name__icontains=q)
        )
    return render(request, "timetable/entry_list.html", {
        "entries": entries,
        "q": q,
        "can_manage_timetable": _can_manage_timetable(request),
    })


@login_required
def timetable_entry_add(request):
    form = ClassTimetableForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Timetable entry added.")
        return redirect("timetable_entry_list")
    return render(request, "timetable/entry_form.html", {"form": form, "title": "Add Timetable Entry"})


@login_required
def timetable_entry_edit(request, pk):
    obj = get_object_or_404(ClassTimetable, pk=pk)
    form = ClassTimetableForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Timetable entry updated.")
        return redirect("timetable_entry_list")
    return render(request, "timetable/entry_form.html", {"form": form, "title": "Edit Timetable Entry"})


@login_required
def timetable_entry_delete(request, pk):
    obj = get_object_or_404(ClassTimetable, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Timetable entry deleted.")
        return redirect("timetable_entry_list")
    return render(request, "timetable/confirm_delete.html", {"object": obj, "back_url": "timetable_entry_list"})


@login_required
def class_timetable_view(request):
    class_id = request.GET.get("class", "").strip()
    section = request.GET.get("section", "").strip()

    classes = _get_ordered_classes()
    selected_class_obj = Class.objects.filter(id=class_id).first() if class_id else None
    periods = Period.objects.all()
    days = ClassTimetable.DAY_CHOICES

    entries = ClassTimetable.objects.select_related(
        "class_assigned", "period", "subject", "teacher"
    ).filter(is_active=True)

    if class_id:
        entries = entries.filter(class_assigned_id=class_id)
    if section:
        entries = entries.filter(section__iexact=section)

    holiday_map = {h.day: h for h in TimetableHoliday.objects.filter(is_holiday=True)}

    return render(request, "timetable/class_view.html", {
        "classes": classes,
        "selected_class": class_id,
        "selected_class_obj": selected_class_obj,
        "section": section,
        "days": days,
        "periods": periods,
        "entries": entries,
        "holiday_map": holiday_map,
    })


@login_required
def teacher_timetable_view(request):
    teacher_id = request.GET.get("teacher")
    teachers = _get_ordered_teachers()
    entries = ClassTimetable.objects.select_related("class_assigned", "period", "subject", "teacher").filter(is_active=True)

    if teacher_id:
        entries = entries.filter(teacher_id=teacher_id)

    return render(request, "timetable/teacher_view.html", {
        "teachers": teachers,
        "selected_teacher": teacher_id,
        "entries": entries,
    })


@login_required
def day_timetable_view(request):
    day = request.GET.get("day", "MONDAY")
    class_id = request.GET.get("class", "").strip()
    section = request.GET.get("section", "").strip()

    classes = _get_ordered_classes()
    periods = Period.objects.all()

    entries = ClassTimetable.objects.select_related(
        "class_assigned", "period", "subject", "teacher"
    ).filter(is_active=True, day=day)

    if class_id:
        entries = entries.filter(class_assigned_id=class_id)
    if section:
        entries = entries.filter(section__iexact=section)

    display_classes = classes
    if class_id:
        display_classes = classes.filter(id=class_id)

    return render(request, "timetable/day_view.html", {
        "day": day,
        "days": ClassTimetable.DAY_CHOICES,
        "classes": classes,
        "display_classes": display_classes,
        "selected_class": class_id,
        "section": section,
        "periods": periods,
        "entries": entries,
        "holiday": _is_holiday_day(day),
    })


@login_required
def timetable_print(request):
    print_type = request.GET.get("type", "all_weekly")
    day = request.GET.get("day", "")
    class_id = request.GET.get("class", "")
    teacher_id = request.GET.get("teacher", "")
    section = request.GET.get("section", "").strip()

    entries = ClassTimetable.objects.select_related(
        "class_assigned", "period", "subject", "teacher"
    ).filter(is_active=True)

    classes = _get_ordered_classes()
    display_classes = classes
    title = "Weekly All Class Timetable"
    grid_mode = False

    if print_type == "weekly_class" and class_id:
        entries = entries.filter(class_assigned_id=class_id)
        display_classes = classes.filter(id=class_id)
        if section:
            entries = entries.filter(section__iexact=section)
        title = "Weekly Class Wise Timetable"

    elif print_type == "day_all" and day:
        entries = entries.filter(day=day)
        title = f"Day Wise All Class Timetable - {day}"
        grid_mode = True

    elif print_type == "day_class" and day and class_id:
        entries = entries.filter(day=day, class_assigned_id=class_id)
        display_classes = classes.filter(id=class_id)
        if section:
            entries = entries.filter(section__iexact=section)
        title = f"Day Wise Class Timetable - {day}"
        grid_mode = True

    elif print_type == "teacher" and teacher_id:
        entries = entries.filter(teacher_id=teacher_id)
        title = "Teacher Wise Timetable"

    return render(request, "timetable/print.html", {
        "entries": entries,
        "title": title,
        "print_type": print_type,
        "days": ClassTimetable.DAY_CHOICES,
        "periods": Period.objects.all(),
        "classes": classes,
        "display_classes": display_classes,
        "grid_mode": grid_mode,
        "selected_day": day,
    })


@login_required
def print_select(request):
    return render(request, "timetable/print_select.html", {
        "classes": _get_ordered_classes(),
        "teachers": _get_ordered_teachers(),
        "days": ClassTimetable.DAY_CHOICES,
    })
