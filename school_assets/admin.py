from django.contrib import admin
from .models import AssetRoom, AssetCategory, AssetItem, AssetMaintenance


@admin.register(AssetRoom)
class AssetRoomAdmin(admin.ModelAdmin):
    list_display = ("room_no", "room_name", "room_type", "floor", "building", "capacity", "is_active")
    list_filter = ("room_type", "floor", "building", "is_active")
    search_fields = ("room_no", "room_name", "building")


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "icon")
    search_fields = ("name",)


@admin.register(AssetItem)
class AssetItemAdmin(admin.ModelAdmin):
    list_display = ("item_name", "category", "room", "quantity", "condition", "status", "last_checked_date")
    list_filter = ("category", "condition", "status", "room")
    search_fields = ("item_name", "item_code", "serial_no", "room__room_no")


@admin.register(AssetMaintenance)
class AssetMaintenanceAdmin(admin.ModelAdmin):
    list_display = ("asset", "issue_title", "priority", "status", "reported_date", "completed_date", "repair_cost")
    list_filter = ("priority", "status", "reported_date")
    search_fields = ("asset__item_name", "issue_title", "vendor_or_mechanic")
