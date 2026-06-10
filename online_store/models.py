from django.db import models
from django.conf import settings
from django.utils import timezone

try:
    from students.models import Student
except Exception:
    Student = None


class ProductCategory(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, blank=True, null=True, related_name="products")
    name = models.CharField(max_length=180)
    product_code = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True, null=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_alert = models.PositiveIntegerField(default=5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.product_code})"

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.low_stock_alert


class Sale(models.Model):
    PAYMENT_CHOICES = [
        ("CASH", "Cash"),
        ("UPI", "UPI"),
        ("CARD", "Card"),
        ("DUE", "Due"),
        ("MIXED", "Mixed"),
    ]

    invoice_no = models.CharField(max_length=80, unique=True, blank=True, null=True)
    sale_date = models.DateTimeField(default=timezone.now)
    customer_name = models.CharField(max_length=150, blank=True, null=True)
    customer_mobile = models.CharField(max_length=20, blank=True, null=True)
    student = models.ForeignKey("students.Student", on_delete=models.SET_NULL, blank=True, null=True, related_name="store_sales")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default="CASH")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    due_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remarks = models.TextField(blank=True, null=True)
    sold_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        ordering = ["-sale_date", "-id"]

    def __str__(self):
        return self.invoice_no or f"Sale {self.id}"

    def save(self, *args, **kwargs):
        if not self.invoice_no:
            today = timezone.localdate().strftime("%Y%m%d")
            last = Sale.objects.filter(invoice_no__startswith=f"POS-{today}").order_by("-id").first()
            next_no = 1
            if last and last.invoice_no:
                try:
                    next_no = int(last.invoice_no.split("-")[-1]) + 1
                except Exception:
                    next_no = last.id + 1
            self.invoice_no = f"POS-{today}-{next_no:04d}"
        self.grand_total = max(self.subtotal - self.discount, 0)
        self.due_amount = max(self.grand_total - self.paid_amount, 0)
        super().save(*args, **kwargs)


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="sale_items")
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
