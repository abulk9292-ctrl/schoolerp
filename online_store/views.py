from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import ProductCategory, Product, Sale, SaleItem
from .forms import ProductCategoryForm, ProductForm, SaleForm


def _can_manage_store(request):
    user = request.user
    if user.is_superuser or user.is_staff:
        return True
    employee = getattr(user, "employee", None)
    return bool(employee and getattr(employee, "is_erp_admin", False))


@login_required
def store_dashboard(request):
    today = timezone.localdate()
    total_products = Product.objects.count()
    low_stock = Product.objects.filter(stock_quantity__lte=5).count()
    today_sales = Sale.objects.filter(sale_date__date=today).aggregate(total=Sum("grand_total"))["total"] or 0
    total_due = Sale.objects.aggregate(total=Sum("due_amount"))["total"] or 0
    recent_sales = Sale.objects.order_by("-sale_date")[:10]
    low_stock_products = Product.objects.filter(stock_quantity__lte=5).order_by("stock_quantity")[:10]

    return render(request, "online_store/dashboard.html", {
        "total_products": total_products,
        "low_stock": low_stock,
        "today_sales": today_sales,
        "total_due": total_due,
        "recent_sales": recent_sales,
        "low_stock_products": low_stock_products,
        "can_manage_store": _can_manage_store(request),
    })


@login_required
def category_list(request):
    categories = ProductCategory.objects.all()
    return render(request, "online_store/category_list.html", {"categories": categories, "can_manage_store": _can_manage_store(request)})


@login_required
def category_add(request):
    form = ProductCategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Category added.")
        return redirect("store_category_list")
    return render(request, "online_store/category_form.html", {"form": form, "title": "Add Category"})


@login_required
def category_edit(request, pk):
    obj = get_object_or_404(ProductCategory, pk=pk)
    form = ProductCategoryForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Category updated.")
        return redirect("store_category_list")
    return render(request, "online_store/category_form.html", {"form": form, "title": "Edit Category"})


@login_required
def category_delete(request, pk):
    obj = get_object_or_404(ProductCategory, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Category deleted.")
        return redirect("store_category_list")
    return render(request, "online_store/confirm_delete.html", {"object": obj, "back_url": "store_category_list"})


@login_required
def product_list(request):
    q = request.GET.get("q", "").strip()
    products = Product.objects.select_related("category")
    if q:
        products = products.filter(Q(name__icontains=q) | Q(product_code__icontains=q))
    return render(request, "online_store/product_list.html", {"products": products, "q": q, "can_manage_store": _can_manage_store(request)})


@login_required
def product_add(request):
    form = ProductForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Product added.")
        return redirect("store_product_list")
    return render(request, "online_store/product_form.html", {"form": form, "title": "Add Product"})


@login_required
def product_edit(request, pk):
    obj = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Product updated.")
        return redirect("store_product_list")
    return render(request, "online_store/product_form.html", {"form": form, "title": "Edit Product"})


@login_required
def product_delete(request, pk):
    obj = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Product deleted.")
        return redirect("store_product_list")
    return render(request, "online_store/confirm_delete.html", {"object": obj, "back_url": "store_product_list"})


@login_required
def pos_sale_create(request):
    products = Product.objects.filter(is_active=True).order_by("name")
    form = SaleForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        product_ids = request.POST.getlist("product_id")
        quantities = request.POST.getlist("quantity")

        sale = form.save(commit=False)
        sale.sold_by = request.user
        sale.subtotal = Decimal("0.00")
        sale.save()

        subtotal = Decimal("0.00")
        for pid, qty in zip(product_ids, quantities):
            if not pid or not qty:
                continue
            product = Product.objects.filter(id=pid).first()
            if not product:
                continue
            qty = int(qty)
            if qty <= 0:
                continue
            if product.stock_quantity < qty:
                messages.error(request, f"Not enough stock for {product.name}.")
                sale.delete()
                return redirect("store_pos")

            item = SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=qty,
                price=product.selling_price,
            )
            subtotal += item.total
            product.stock_quantity -= qty
            product.save()

        sale.subtotal = subtotal
        sale.save()
        messages.success(request, "Sale completed.")
        return redirect("store_sale_invoice", pk=sale.pk)

    return render(request, "online_store/pos.html", {"form": form, "products": products})


@login_required
def sale_list(request):
    q = request.GET.get("q", "").strip()
    sales = Sale.objects.all()
    if q:
        sales = sales.filter(Q(invoice_no__icontains=q) | Q(customer_name__icontains=q) | Q(customer_mobile__icontains=q))
    return render(request, "online_store/sale_list.html", {"sales": sales, "q": q, "can_manage_store": _can_manage_store(request)})


@login_required
def sale_invoice(request, pk):
    sale = get_object_or_404(Sale.objects.prefetch_related("items", "items__product"), pk=pk)
    return render(request, "online_store/invoice.html", {"sale": sale})


@login_required
def sale_delete(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == "POST":
        for item in sale.items.all():
            product = item.product
            product.stock_quantity += item.quantity
            product.save()
        sale.delete()
        messages.success(request, "Sale deleted and stock restored.")
        return redirect("store_sale_list")
    return render(request, "online_store/confirm_delete.html", {"object": sale, "back_url": "store_sale_list"})
