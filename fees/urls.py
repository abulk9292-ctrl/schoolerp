from django.urls import path
from . import views

urlpatterns = [

    # =========================
    # 🔥 MAIN FEES
    # =========================
    path('', views.fee_list, name='fee_list'),
    path('add/', views.fee_add, name='fee_add'),
    path('edit/<int:pk>/', views.fee_edit, name='fee_edit'),
    path('delete/<int:pk>/', views.fee_delete, name='fee_delete'),
    path('receipt/<int:pk>/', views.fee_receipt, name='fee_receipt'),

    # =========================
    # 🔥 AJAX (AUTO LOAD)
    # =========================
    path('get-student-old-due/', views.get_student_old_due, name='get_student_old_due'),
    path('get-student-fee-structure/', views.get_student_fee_structure, name='get_student_fee_structure'),

    # =========================
    # 🔥 FEE STRUCTURE
    # =========================
    path('structure/', views.fee_structure_list, name='fee_structure_list'),
    path('structure/edit/<int:pk>/', views.fee_structure_edit, name='fee_structure_edit'),
    path('structure/delete/<int:pk>/', views.fee_structure_delete, name='fee_structure_delete'),

    # =========================
    # 🔥 REPORTS
    # =========================
    path('defaulters/', views.defaulters_list, name='defaulters_list'),
    path('pending-amount/', views.pending_amount_list, name='pending_amount_list'),

    # =========================
    # 🔥 DEMAND SLIP
    # =========================
    path('demand-slip/<int:student_id>/', views.fee_demand_slip, name='fee_demand_slip'),

    # =========================
    # 🔥 BULK DEMAND SLIP
    # =========================
    path('bulk-demand-slip/', views.bulk_demand_slip_page, name='bulk_demand_slip_page'),
    path('bulk-demand-slip/print/', views.bulk_demand_slip_print, name='bulk_demand_slip_print'),
]