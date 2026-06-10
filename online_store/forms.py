from django import forms
from .models import ProductCategory, Product, Sale, SaleItem


class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "category", "name", "product_code", "description",
            "purchase_price", "selling_price", "stock_quantity",
            "low_stock_alert", "is_active",
        ]
        widgets = {
            "category": forms.Select(attrs={"class": "form-select select2"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "product_code": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "purchase_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "selling_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "stock_quantity": forms.NumberInput(attrs={"class": "form-control"}),
            "low_stock_alert": forms.NumberInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ["customer_name", "customer_mobile", "student", "payment_method", "discount", "paid_amount", "remarks"]
        widgets = {
            "customer_name": forms.TextInput(attrs={"class": "form-control"}),
            "customer_mobile": forms.TextInput(attrs={"class": "form-control"}),
            "student": forms.Select(attrs={"class": "form-select select2"}),
            "payment_method": forms.Select(attrs={"class": "form-select"}),
            "discount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "paid_amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }
