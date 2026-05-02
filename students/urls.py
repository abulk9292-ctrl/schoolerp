from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_list, name='student_list'),
    path('add/', views.student_add, name='student_add'),

    path('<int:pk>/', views.student_detail, name='student_detail'),

    path('edit/<int:pk>/', views.student_edit, name='student_edit'),
    path('delete/<int:pk>/', views.student_delete, name='student_delete'),

    path('add-sibling/<int:pk>/', views.add_sibling, name='add_sibling'),

    # 🔥 NEW FEATURES
    path('discontinue/<int:pk>/', views.student_discontinue, name='student_discontinue'),
    path('readmit/<int:pk>/', views.student_readmit, name='student_readmit'),

    path('promote/<int:pk>/', views.student_promote, name='student_promote'),
    path('demote/<int:pk>/', views.student_demote, name='student_demote'),
    path('bulk-promotion/', views.bulk_promotion, name='bulk_promotion'),

    path('export-excel/', views.export_students_excel, name='export_students_excel'),

    # 🆔 ID CARD
    path('id-card/<int:pk>/', views.student_id_card, name='student_id_card'),
    path('id-cards-print/', views.student_id_cards_print, name='student_id_cards_print'),
    path('qr-profile/<int:pk>/', views.student_qr_profile, name='student_qr_profile'),

    # 🔥 NEW 👉 IMPORT SYSTEM
    path('import/', views.student_import, name='student_import'),

    # 🔥 NEW 👉 DEMO EXCEL DOWNLOAD
    path('download-demo/', views.download_student_demo, name='download_student_demo'),
]