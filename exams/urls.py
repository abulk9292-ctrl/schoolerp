from django.urls import path
from . import views


urlpatterns = [

    # =========================================
    # EXAM DASHBOARD
    # =========================================
    path('', views.exam_dashboard, name='exam_dashboard'),

    # =========================================
    # EXAM SETUP
    # =========================================
    path('add/', views.exam_add, name='exam_add'),

    # =========================================
    # EXAM ROUTINE
    # =========================================
    path('routine/', views.exam_routine, name='exam_routine'),

    # =========================================
    # MARKS ENTRY
    # =========================================
    path('results/add/', views.result_add, name='result_add'),

    path('results/select/', views.result_sheet_select, name='result_sheet_select'),

    path('results/', views.result_list, name='result_list'),

    path('results/bulk-entry/', views.bulk_result_entry, name='bulk_result_entry'),

    path('results/popup-entry/', views.popup_result_entry, name='popup_result_entry'),

    # =========================================
    # REPORT CARD / RESULT PRINT
    # =========================================
    path('report-card/', views.report_card_select, name='report_card_select'),

    # =========================================
    # BULK REPORT CARD
    # =========================================
    path(
        'report-card/bulk/select/',
        views.report_card_bulk_select,
        name='report_card_bulk_select'
    ),

    path(
        'report-card/bulk/print/',
        views.report_card_bulk_print,
        name='report_card_bulk_print'
    ),

    # =========================================
    # TOPPER / MERIT
    # =========================================
    path('topper/', views.topper_result, name='topper_result'),

    # =========================================
    # ADMIT CARD
    # =========================================
    path('admit-card/', views.admit_card_select, name='admit_card_select'),

    path(
        'admit-card/bulk-print/',
        views.admit_card_bulk_print,
        name='admit_card_bulk_print'
    ),

    # =========================================
    # DESK SLIP
    # =========================================
    path('desk-slip/', views.desk_slip_select, name='desk_slip_select'),

    path(
        'desk-slip/bulk-print/',
        views.desk_slip_bulk_print,
        name='desk_slip_bulk_print'
    ),

    # =========================================
    # BLANK MARKS SHEET
    # =========================================
    path(
        'blank-marks-sheet/',
        views.blank_marks_sheet_select,
        name='blank_marks_sheet_select'
    ),

    path(
        'blank-marks-sheet/print/',
        views.blank_marks_sheet_print,
        name='blank_marks_sheet_print'
    ),


    path(
        'merit-list/',
        views.merit_list,
        name='merit_list'
    ),

# =====================================
# PREMIUM ONLINE RESULT PORTAL
# =====================================

    path(
        'online-result-portal/',
        views.online_result_portal,
        name='online_result_portal'
    ),

]