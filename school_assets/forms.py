from django import forms
from .models import AssetRoom, AssetCategory, AssetItem, AssetMaintenance


class AssetRoomForm(forms.ModelForm):
    class Meta:
        model = AssetRoom
        fields = [
            "room_no", "room_name", "room_type", "floor", "building",
            "capacity", "is_active", "remarks",
        ]
        widgets = {
            "room_no": forms.TextInput(attrs={"class": "form-control", "placeholder": "Example: Room 101"}),
            "room_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Example: Class VI Room"}),
            "room_type": forms.Select(attrs={"class": "form-select"}),
            "floor": forms.TextInput(attrs={"class": "form-control"}),
            "building": forms.TextInput(attrs={"class": "form-control"}),
            "capacity": forms.NumberInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class AssetCategoryForm(forms.ModelForm):
    class Meta:
        model = AssetCategory
        fields = ["name", "icon", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Bench / Chair / Fan / Board"}),
            "icon": forms.TextInput(attrs={"class": "form-control", "placeholder": "bi bi-box"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class AssetItemForm(forms.ModelForm):
    class Meta:
        model = AssetItem
        fields = [
            "category", "room", "item_name", "item_code", "serial_no",
            "quantity", "condition", "status", "purchase_date",
            "purchase_price", "supplier_name", "last_checked_date", "remarks",
        ]
        widgets = {
            "category": forms.Select(attrs={"class": "form-select select2"}),
            "room": forms.Select(attrs={"class": "form-select select2"}),
            "item_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Example: Wooden Bench"}),
            "item_code": forms.TextInput(attrs={"class": "form-control", "placeholder": "Example: BENCH-101-01"}),
            "serial_no": forms.TextInput(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "condition": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "purchase_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "purchase_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "supplier_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_checked_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class AssetMaintenanceForm(forms.ModelForm):
    class Meta:
        model = AssetMaintenance
        fields = [
            "asset", "issue_title", "issue_description", "priority", "status",
            "reported_date", "completed_date", "repair_cost",
            "vendor_or_mechanic", "assigned_to", "remarks",
        ]
        widgets = {
            "asset": forms.Select(attrs={"class": "form-select select2"}),
            "issue_title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Example: Fan not working"}),
            "issue_description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "reported_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "completed_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "repair_cost": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "vendor_or_mechanic": forms.TextInput(attrs={"class": "form-control"}),
            "assigned_to": forms.TextInput(attrs={"class": "form-control", "placeholder": "Technician / Staff Name"}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
