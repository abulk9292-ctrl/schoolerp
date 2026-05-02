from django.urls import path
from . import views

urlpatterns = [
    path('', views.exam_dashboard, name='exam_dashboard'),
    path('add/', views.exam_add, name='exam_add'),
    path('routine/', views.exam_routine, name='exam_routine'),
    path('results/add/', views.result_add, name='result_add'),
    path('results/', views.result_list, name='result_list'),
    path('report-card/', views.report_card_select, name='report_card_select'),
    path('bulk-entry/', views.bulk_result_entry, name='bulk_result_entry'),
    path('popup-entry/', views.popup_result_entry, name='popup_result_entry'),
    path('topper/', views.topper_result, name='topper_result'),
    path('print-bulk/', views.print_bulk_result, name='print_bulk_result'),
]