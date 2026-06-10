from django.urls import path
from . import views

urlpatterns = [
    path("", views.store_dashboard, name="store_dashboard"),
    path("categories/", views.category_list, name="store_category_list"),
    path("categories/add/", views.category_add, name="store_category_add"),
    path("categories/<int:pk>/edit/", views.category_edit, name="store_category_edit"),
    path("categories/<int:pk>/delete/", views.category_delete, name="store_category_delete"),

    path("products/", views.product_list, name="store_product_list"),
    path("products/add/", views.product_add, name="store_product_add"),
    path("products/<int:pk>/edit/", views.product_edit, name="store_product_edit"),
    path("products/<int:pk>/delete/", views.product_delete, name="store_product_delete"),

    path("pos/", views.pos_sale_create, name="store_pos"),
    path("sales/", views.sale_list, name="store_sale_list"),
    path("sales/<int:pk>/invoice/", views.sale_invoice, name="store_sale_invoice"),
    path("sales/<int:pk>/delete/", views.sale_delete, name="store_sale_delete"),
]
