from django.urls import path
from . import views

urlpatterns = [

    path(
        '',
        views.expense_list,
        name='expense_list'
    ),

    path(
        'add/',
        views.expense_add,
        name='expense_add'
    ),

    path(
        'edit/<int:pk>/',
        views.expense_edit,
        name='expense_edit'
    ),

    path(
        'delete/<int:pk>/',
        views.expense_delete,
        name='expense_delete'
    ),

    # =========================
    # EXPENSE RECYCLE BIN
    # =========================

    path(
        'recycle-bin/',
        views.expense_recycle_bin,
        name='expense_recycle_bin'
    ),

    path(
        'restore/<int:pk>/',
        views.expense_restore,
        name='expense_restore'
    ),

    path(
        'permanent-delete/<int:pk>/',
        views.expense_permanent_delete,
        name='expense_permanent_delete'
    ),
]