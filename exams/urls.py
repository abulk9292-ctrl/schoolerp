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

    path(
        'edit/<int:pk>/',
        views.exam_edit,
        name='exam_edit'
    ),

    path(
        'delete/<int:pk>/',
        views.exam_delete,
        name='exam_delete'
    ),

    # =========================================
    # EXAM ROUTINE
    # =========================================
    path('routine/', views.exam_routine, name='exam_routine'),

    path(
        'routine/edit/<int:pk>/',
        views.exam_routine_edit,
        name='exam_routine_edit'
    ),

    path(
        'routine/delete/<int:pk>/',
        views.exam_routine_delete,
        name='exam_routine_delete'
    ),

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

    path(
        'merit-list/',
        views.merit_list,
        name='merit_list'
    ),

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

    # =====================================
    # PREMIUM ONLINE RESULT PORTAL
    # =====================================
    path(
        'online-result-portal/',
        views.online_result_portal,
        name='online_result_portal'
    ),

    path(
        "routine/select-print/",
        views.exam_routine_select_print,
        name="exam_routine_select_print"
    ),

    # =====================================
    # CLASS TESTS
    # =====================================
    path(
        'class-tests/',
        views.class_test_dashboard,
        name='class_test_dashboard'
    ),

    path(
        'class-tests/list/',
        views.class_test_list,
        name='class_test_list'
    ),

    path(
        'class-tests/add/',
        views.add_class_test,
        name='add_class_test'
    ),

    path(
        "class-tests/edit/<int:pk>/",
        views.edit_class_test,
        name="edit_class_test"
    ),

    path(
        "class-tests/delete/<int:pk>/",
        views.delete_class_test,
        name="delete_class_test"
    ),

    path(
        'class-tests/results/',
        views.class_test_result_list,
        name='class_test_result_list'
    ),

    path(
        'class-tests/results/add/',
        views.add_class_test_result,
        name='add_class_test_result'
    ),

    path(
        "class-test-result/edit/<int:pk>/",
        views.edit_class_test_result,
        name="edit_class_test_result"
    ),

    path(
        "class-test-result/delete/<int:pk>/",
        views.delete_class_test_result,
        name="delete_class_test_result"
    ),
]