from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import AssetRoom, AssetCategory, AssetItem, AssetMaintenance, create_default_asset_categories
from .forms import AssetRoomForm, AssetCategoryForm, AssetItemForm, AssetMaintenanceForm


def _can_manage_assets(request):
    user = request.user
    if user.is_superuser or user.is_staff:
        return True
    employee = getattr(user, "employee", None)
    if employee and getattr(employee, "is_erp_admin", False):
        return True
    return False


@login_required
def asset_dashboard(request):
    create_default_asset_categories()
    total_rooms = AssetRoom.objects.count()
    active_rooms = AssetRoom.objects.filter(is_active=True).count()
    total_categories = AssetCategory.objects.count()
    total_items = AssetItem.objects.aggregate(total=Sum("quantity"))["total"] or 0
    repair_needed = AssetItem.objects.filter(condition__in=["REPAIR_NEEDED", "DAMAGED"]).aggregate(total=Sum("quantity"))["total"] or 0
    repair_needed_count = AssetMaintenance.objects.filter(status="PENDING").count()
    under_repair_count = AssetMaintenance.objects.filter(status="UNDER_REPAIR").count()
    completed_repair_count = AssetMaintenance.objects.filter(status="COMPLETED").count()
    pending_maintenance = under_repair_count

    category_totals_qs = AssetItem.objects.values("category__name").annotate(total=Sum("quantity")).order_by("category__name")
    category_totals_map = {
        row["category__name"]: row["total"] or 0
        for row in category_totals_qs
    }

    fixed_category_names = [
        "Bench", "Chair", "Board", "Duster", "Marker",
        "Fan", "Bulb", "Toilet", "Table", "Room", "Other",
    ]

    category_cards = []
    for name in fixed_category_names:
        category_cards.append({
            "name": name,
            "total": category_totals_map.get(name, 0),
            "url": f"/assets/items/?category_name={name}",
        })

    category_summary = category_cards
    room_summary = AssetRoom.objects.annotate(asset_count=Sum("assets__quantity")).order_by("room_no")[:12]
    recent_maintenance = AssetMaintenance.objects.select_related("asset", "asset__room").order_by("-reported_date", "-id")[:10]

    context = {
        "total_rooms": total_rooms,
        "active_rooms": active_rooms,
        "total_categories": total_categories,
        "total_items": total_items,
        "repair_needed": repair_needed,
        "repair_needed_count": repair_needed_count,
        "under_repair_count": under_repair_count,
        "completed_repair_count": completed_repair_count,
        "pending_maintenance": pending_maintenance,
        "category_cards": category_cards,
        "category_summary": category_summary,
        "room_summary": room_summary,
        "recent_maintenance": recent_maintenance,
        "can_manage_assets": _can_manage_assets(request),
    }
    return render(request, "school_assets/dashboard.html", context)


@login_required
def room_list(request):
    q = request.GET.get("q", "").strip()
    room_type = request.GET.get("room_type", "").strip()

    rooms = AssetRoom.objects.annotate(total_assets=Sum("assets__quantity")).order_by("room_no")

    if q:
        rooms = rooms.filter(Q(room_no__icontains=q) | Q(room_name__icontains=q) | Q(building__icontains=q))
    if room_type:
        rooms = rooms.filter(room_type=room_type)

    context = {
        "rooms": rooms,
        "q": q,
        "room_type": room_type,
        "room_type_choices": AssetRoom.ROOM_TYPE_CHOICES,
        "can_manage_assets": _can_manage_assets(request),
    }
    return render(request, "school_assets/room_list.html", context)


@login_required
def room_add(request):
    if not _can_manage_assets(request):
        messages.error(request, "You do not have permission.")
        return redirect("asset_room_list")

    form = AssetRoomForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Room added successfully.")
        return redirect("asset_room_list")
    return render(request, "school_assets/room_form.html", {"form": form, "title": "Add Room"})


@login_required
def room_edit(request, pk):
    if not _can_manage_assets(request):
        messages.error(request, "You do not have permission.")
        return redirect("asset_room_list")

    room = get_object_or_404(AssetRoom, pk=pk)
    form = AssetRoomForm(request.POST or None, instance=room)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Room updated successfully.")
        return redirect("asset_room_list")
    return render(request, "school_assets/room_form.html", {"form": form, "title": "Edit Room"})


@login_required
def room_delete(request, pk):
    if not _can_manage_assets(request):
        messages.error(request, "You do not have permission.")
        return redirect("asset_room_list")

    room = get_object_or_404(AssetRoom, pk=pk)
    if request.method == "POST":
        room.delete()
        messages.success(request, "Room deleted successfully.")
        return redirect("asset_room_list")
    return render(request, "school_assets/confirm_delete.html", {"object": room, "back_url": "asset_room_list"})


@login_required
def room_details(request, pk):
    room = get_object_or_404(AssetRoom, pk=pk)
    assets = room.assets.select_related("category").order_by("category__name", "item_name")
    total_assets = assets.aggregate(total=Sum("quantity"))["total"] or 0
    repair_assets = assets.filter(condition__in=["REPAIR_NEEDED", "DAMAGED"]).aggregate(total=Sum("quantity"))["total"] or 0
    return render(request, "school_assets/room_details.html", {
        "room": room,
        "assets": assets,
        "total_assets": total_assets,
        "repair_assets": repair_assets,
        "can_manage_assets": _can_manage_assets(request),
    })


@login_required
def category_list(request):
    create_default_asset_categories()
    categories = AssetCategory.objects.annotate(item_count=Count("items"), total_quantity=Sum("items__quantity")).order_by("name")
    return render(request, "school_assets/category_list.html", {
        "categories": categories,
        "can_manage_assets": _can_manage_assets(request),
    })


@login_required
def category_add(request):
    if not _can_manage_assets(request):
        messages.error(request, "You do not have permission.")
        return redirect("asset_category_list")

    form = AssetCategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Category added successfully.")
        return redirect("asset_category_list")
    return render(request, "school_assets/category_form.html", {"form": form, "title": "Add Category"})


@login_required
def category_edit(request, pk):
    if not _can_manage_assets(request):
        messages.error(request, "You do not have permission.")
        return redirect("asset_category_list")

    category = get_object_or_404(AssetCategory, pk=pk)
    form = AssetCategoryForm(request.POST or None, instance=category)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Category updated successfully.")
        return redirect("asset_category_list")
    return render(request, "school_assets/category_form.html", {"form": form, "title": "Edit Category"})


@login_required
def category_delete(request, pk):
    if not _can_manage_assets(request):
        messages.error(request, "You do not have permission.")
        return redirect("asset_category_list")

    category = get_object_or_404(AssetCategory, pk=pk)
    if request.method == "POST":
        category.delete()
        messages.success(request, "Category deleted successfully.")
        return redirect("asset_category_list")
    return render(request, "school_assets/confirm_delete.html", {"object": category, "back_url": "asset_category_list"})


@login_required
def item_list(request):
    q = request.GET.get("q", "").strip()
    room = request.GET.get("room", "").strip()
    category = request.GET.get("category", "").strip()
    condition = request.GET.get("condition", "").strip()

    items = AssetItem.objects.select_related("category", "room").order_by("room__room_no", "category__name", "item_name")

    if q:
        items = items.filter(Q(item_name__icontains=q) | Q(item_code__icontains=q) | Q(serial_no__icontains=q))
    if room:
        items = items.filter(room_id=room)
    category_name = request.GET.get("category_name", "").strip()

    if category:
        items = items.filter(category_id=category)
    if category_name:
        items = items.filter(category__name__iexact=category_name)
    if condition:
        items = items.filter(condition=condition)

    context = {
        "items": items,
        "rooms": AssetRoom.objects.all(),
        "categories": AssetCategory.objects.all(),
        "condition_choices": AssetItem.CONDITION_CHOICES,
        "q": q,
        "room": room,
        "category": category,
        "category_name": request.GET.get("category_name", "").strip(),
        "condition": condition,
        "can_manage_assets": _can_manage_assets(request),
    }
    return render(request, "school_assets/item_list.html", context)


@login_required
def item_add(request):
    create_default_asset_categories()
    if not _can_manage_assets(request):
        messages.error(request, "You do not have permission.")
        return redirect("asset_item_list")

    form = AssetItemForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.created_by = request.user
        if not item.last_checked_date:
            item.last_checked_date = timezone.localdate()
        item.save()
        messages.success(request, "Asset item added successfully.")
        return redirect("asset_item_list")
    return render(request, "school_assets/item_form.html", {"form": form, "title": "Add Asset Item"})


@login_required
def item_edit(request, pk):
    if not _can_manage_assets(request):
        messages.error(request, "You do not have permission.")
        return redirect("asset_item_list")

    item = get_object_or_404(AssetItem, pk=pk)
    form = AssetItemForm(request.POST or None, instance=item)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Asset item updated successfully.")
        return redirect("asset_item_list")
    return render(request, "school_assets/item_form.html", {"form": form, "title": "Edit Asset Item"})


@login_required
def item_delete(request, pk):
    if not _can_manage_assets(request):
        messages.error(request, "You do not have permission.")
        return redirect("asset_item_list")

    item = get_object_or_404(AssetItem, pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Asset item deleted successfully.")
        return redirect("asset_item_list")
    return render(request, "school_assets/confirm_delete.html", {"object": item, "back_url": "asset_item_list"})


@login_required
def maintenance_list(request):
    status = request.GET.get("status", "").strip()
    records = AssetMaintenance.objects.select_related("asset", "asset__room", "asset__category").order_by("-reported_date", "-id")
    if status:
        records = records.filter(status=status)
    return render(request, "school_assets/maintenance_list.html", {
        "records": records,
        "status": status,
        "status_choices": AssetMaintenance.STATUS_CHOICES,
        "can_manage_assets": _can_manage_assets(request),
    })


@login_required
def maintenance_add(request):
    if not _can_manage_assets(request):
        messages.error(request, "You do not have permission.")
        return redirect("asset_maintenance_list")

    form = AssetMaintenanceForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        record = form.save(commit=False)
        record.reported_by = request.user
        record.save()
        if record.status in ["PENDING", "UNDER_REPAIR"]:
            record.asset.condition = "REPAIR_NEEDED"
            record.asset.status = "UNDER_REPAIR"
            record.asset.save()
        messages.success(request, "Maintenance record added successfully.")
        return redirect("asset_maintenance_list")
    return render(request, "school_assets/maintenance_form.html", {"form": form, "title": "Add Maintenance"})


@login_required
def maintenance_edit(request, pk):
    if not _can_manage_assets(request):
        messages.error(request, "You do not have permission.")
        return redirect("asset_maintenance_list")

    record = get_object_or_404(AssetMaintenance, pk=pk)
    form = AssetMaintenanceForm(request.POST or None, instance=record)
    if request.method == "POST" and form.is_valid():
        record = form.save()
        if record.status == "COMPLETED":
            record.asset.condition = "GOOD"
            record.asset.status = "IN_USE"
            record.asset.last_checked_date = timezone.localdate()
            record.asset.save()
        messages.success(request, "Maintenance record updated successfully.")
        return redirect("asset_maintenance_list")
    return render(request, "school_assets/maintenance_form.html", {"form": form, "title": "Edit Maintenance"})


@login_required
def maintenance_delete(request, pk):
    if not _can_manage_assets(request):
        messages.error(request, "You do not have permission.")
        return redirect("asset_maintenance_list")

    record = get_object_or_404(AssetMaintenance, pk=pk)
    if request.method == "POST":
        record.delete()
        messages.success(request, "Maintenance record deleted successfully.")
        return redirect("asset_maintenance_list")
    return render(request, "school_assets/confirm_delete.html", {"object": record, "back_url": "asset_maintenance_list"})


@login_required
def room_wise_report(request):
    rooms = AssetRoom.objects.prefetch_related("assets", "assets__category").order_by("room_no")
    return render(request, "school_assets/room_wise_report.html", {"rooms": rooms})


@login_required
def asset_print_report(request):
    items = AssetItem.objects.select_related("category", "room").order_by("room__room_no", "category__name", "item_name")
    total_quantity = items.aggregate(total=Sum("quantity"))["total"] or 0
    return render(request, "school_assets/asset_print_report.html", {
        "items": items,
        "total_quantity": total_quantity,
        "print_date": timezone.localtime(),
    })


@login_required
def seed_default_categories(request):
    if not _can_manage_assets(request):
        messages.error(request, "You do not have permission.")
        return redirect("asset_dashboard")

    create_default_asset_categories()
    messages.success(request, "Default asset categories added successfully: Bench, Chair, Board, Duster, Marker, Room, Fan, Bulb, Toilet, Table, Other.")
    return redirect("asset_category_list")


@login_required
def maintenance_print_report(request):
    status = request.GET.get("status", "").strip()
    records = AssetMaintenance.objects.select_related("asset", "asset__room", "asset__category").order_by("-reported_date", "-id")
    if status:
        records = records.filter(status=status)

    return render(request, "school_assets/maintenance_print_report.html", {
        "records": records,
        "status": status,
        "print_date": timezone.localtime(),
    })
