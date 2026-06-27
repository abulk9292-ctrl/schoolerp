from django.urls import path
from . import views

urlpatterns = [


    # =========================
    # 🔥 FEE FOLLOW-UP / PROMISE TO PAY
    # =========================
    path('followup/dashboard/', views.fee_followup_dashboard, name='fee_followup_dashboard'),
    path('followup/', views.fee_followup_list, name='fee_followup_list'),
    path('followup/add/', views.fee_followup_add, name='fee_followup_add'),
    path('followup/add/<int:student_id>/', views.fee_followup_add, name='fee_followup_add_student'),
    path('followup/edit/<int:pk>/', views.fee_followup_edit, name='fee_followup_edit'),
    path('followup/delete/<int:pk>/', views.fee_followup_delete, name='fee_followup_delete'),
    path('followup/mark/<int:pk>/<str:status>/', views.fee_followup_mark_status, name='fee_followup_mark_status'),
    path('followup/print/', views.fee_followup_print, name='fee_followup_print'),


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
    path('check-paid-month/', views.check_paid_month),
    path('check-paid-month/', views.check_paid_month, name='check_paid_month'),

    # =========================
    # 🔥 REPORTS
    # =========================
    path('defaulters/', views.defaulters_list, name='defaulters_list'),
    path('pending-amount/', views.pending_amount_list, name='pending_amount_list'),

    # =========================
    # 🔥 PAYMENT STATEMENT
    # =========================
    path(
        'student-payment-statement/<int:student_id>/',
        views.student_payment_statement,
        name='student_payment_statement'
    ),
    
    # =========================
    # FEE RECYCLE BIN
    # =========================

    path(
        'recycle-bin/',
        views.fee_recycle_bin,
        name='fee_recycle_bin'
    ),

    path(
        'restore/<int:pk>/',
        views.fee_restore,
        name='fee_restore'
    ),

    path(
        'permanent-delete/<int:pk>/',
        views.fee_permanent_delete,
        name='fee_permanent_delete'
    ),

    path(
        'fee-card/<int:student_id>/',
        views.student_fee_card,
        name='student_fee_card'
    ),

    # path(
    #     'student-fee-card-print/<int:student_id>/',
    #     views.student_fee_card_print,
    #     name='student_fee_card_print'
    # ),

    path(
        'student-fee-card/<int:student_id>/',
        views.student_fee_card,
        name='student_fee_card'
    ),
]