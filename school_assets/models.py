from django.db import models
from django.conf import settings
from django.utils import timezone

DEFAULT_ASSET_CATEGORIES = [
    ("Bench", "bi bi-box"),
    ("Chair", "bi bi-person-seat"),
    ("Board", "bi bi-easel"),
    ("Duster", "bi bi-eraser"),
    ("Marker", "bi bi-pen"),
    ("Room", "bi bi-building"),
    ("Fan", "bi bi-fan"),
    ("Bulb", "bi bi-lightbulb"),
    ("Toilet", "bi bi-droplet"),
    ("Table", "bi bi-table"),
    ("Other", "bi bi-grid"),
]


def create_default_asset_categories():
    for name, icon in DEFAULT_ASSET_CATEGORIES:
        AssetCategory.objects.get_or_create(
            name=name,
            defaults={
                "icon": icon,
                "description": f"Default category for {name}",
            }
        )



class AssetRoom(models.Model):
    ROOM_TYPE_CHOICES = [
        ("CLASS_ROOM", "Class Room"),
        ("OFFICE", "Office"),
        ("STAFF_ROOM", "Staff Room"),
        ("HOSTEL_ROOM", "Hostel Room"),
        ("TOILET", "Toilet"),
        ("STORE_ROOM", "Store Room"),
        ("LAB", "Lab"),
        ("LIBRARY", "Library"),
        ("OTHER", "Other"),
    ]

    room_no = models.CharField(max_length=50, unique=True)
    room_name = models.CharField(max_length=150, blank=True, null=True)
    room_type = models.CharField(max_length=30, choices=ROOM_TYPE_CHOICES, default="CLASS_ROOM")
    floor = models.CharField(max_length=50, blank=True, null=True)
    building = models.CharField(max_length=100, blank=True, null=True)
    capacity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["room_no"]
        verbose_name = "Room"
        verbose_name_plural = "Rooms"

    def __str__(self):
        return f"{self.room_no} - {self.room_name or self.get_room_type_display()}"


class AssetCategory(models.Model):
    name = models.CharField(max_length=120, unique=True)
    icon = models.CharField(max_length=50, blank=True, null=True, help_text="Example: bi bi-lamp")
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Asset Category"
        verbose_name_plural = "Asset Categories"

    def __str__(self):
        return self.name


class AssetItem(models.Model):
    CONDITION_CHOICES = [
        ("GOOD", "Good"),
        ("AVERAGE", "Average"),
        ("REPAIR_NEEDED", "Repair Needed"),
        ("DAMAGED", "Damaged"),
        ("LOST", "Lost"),
    ]

    STATUS_CHOICES = [
        ("AVAILABLE", "Available"),
        ("IN_USE", "In Use"),
        ("UNDER_REPAIR", "Under Repair"),
        ("DISPOSED", "Disposed"),
    ]

    category = models.ForeignKey(AssetCategory, on_delete=models.CASCADE, related_name="items")
    room = models.ForeignKey(AssetRoom, on_delete=models.SET_NULL, blank=True, null=True, related_name="assets")

    item_name = models.CharField(max_length=150)
    item_code = models.CharField(max_length=80, blank=True, null=True, unique=True)
    serial_no = models.CharField(max_length=100, blank=True, null=True)

    quantity = models.PositiveIntegerField(default=1)
    condition = models.CharField(max_length=30, choices=CONDITION_CHOICES, default="GOOD")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="IN_USE")

    purchase_date = models.DateField(blank=True, null=True)
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    supplier_name = models.CharField(max_length=150, blank=True, null=True)

    last_checked_date = models.DateField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="created_assets"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["room__room_no", "category__name", "item_name"]
        verbose_name = "Asset Item"
        verbose_name_plural = "Asset Items"

    def __str__(self):
        room = self.room.room_no if self.room else "No Room"
        return f"{self.item_name} ({self.quantity}) - {room}"


class AssetMaintenance(models.Model):
    PRIORITY_CHOICES = [
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
        ("URGENT", "Urgent"),
    ]

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("UNDER_REPAIR", "Under Repair"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    asset = models.ForeignKey(AssetItem, on_delete=models.CASCADE, related_name="maintenance_records")
    issue_title = models.CharField(max_length=200)
    issue_description = models.TextField(blank=True, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="MEDIUM")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    reported_date = models.DateField(default=timezone.localdate)
    completed_date = models.DateField(blank=True, null=True)
    repair_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vendor_or_mechanic = models.CharField(max_length=150, blank=True, null=True)
    assigned_to = models.CharField(max_length=150, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="asset_maintenance_reports"
    )

    class Meta:
        ordering = ["-reported_date", "-id"]
        verbose_name = "Asset Maintenance"
        verbose_name_plural = "Asset Maintenance"

    def __str__(self):
        return f"{self.asset.item_name} - {self.issue_title}"
