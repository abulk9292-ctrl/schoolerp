from django.contrib import admin
from .models import ProductCategory, Product, Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "product_code", "category", "selling_price", "stock_quantity", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name", "product_code")


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("invoice_no", "sale_date", "customer_name", "grand_total", "paid_amount", "due_amount", "payment_method")
    list_filter = ("payment_method", "sale_date")
    search_fields = ("invoice_no", "customer_name", "customer_mobile")
    inlines = [SaleItemInline]
