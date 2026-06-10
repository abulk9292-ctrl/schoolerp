from django.urls import path
from . import views

urlpatterns = [
    path("", views.asset_dashboard, name="asset_dashboard"),

    path("rooms/", views.room_list, name="asset_room_list"),
    path("rooms/add/", views.room_add, name="asset_room_add"),
    path("rooms/<int:pk>/edit/", views.room_edit, name="asset_room_edit"),
    path("rooms/<int:pk>/delete/", views.room_delete, name="asset_room_delete"),
    path("rooms/<int:pk>/details/", views.room_details, name="asset_room_details"),

    path("categories/", views.category_list, name="asset_category_list"),
    path("categories/seed-default/", views.seed_default_categories, name="asset_seed_default_categories"),
    path("categories/add/", views.category_add, name="asset_category_add"),
    path("categories/<int:pk>/edit/", views.category_edit, name="asset_category_edit"),
    path("categories/<int:pk>/delete/", views.category_delete, name="asset_category_delete"),

    path("items/", views.item_list, name="asset_item_list"),
    path("items/add/", views.item_add, name="asset_item_add"),
    path("items/<int:pk>/edit/", views.item_edit, name="asset_item_edit"),
    path("items/<int:pk>/delete/", views.item_delete, name="asset_item_delete"),

    path("maintenance/", views.maintenance_list, name="asset_maintenance_list"),
    path("maintenance/add/", views.maintenance_add, name="asset_maintenance_add"),
    path("maintenance/print/", views.maintenance_print_report, name="asset_maintenance_print_report"),
    path("maintenance/<int:pk>/edit/", views.maintenance_edit, name="asset_maintenance_edit"),
    path("maintenance/<int:pk>/delete/", views.maintenance_delete, name="asset_maintenance_delete"),

    path("report/room-wise/", views.room_wise_report, name="asset_room_wise_report"),
    path("report/print/", views.asset_print_report, name="asset_print_report"),
]
