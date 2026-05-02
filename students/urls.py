from django.urls import path
from . import views

urlpatterns = [
    # ======================
    # 🔹 BASIC CRUD
    # ======================
    path('', views.student_list, name='student_list'),
    path('add/', views.student_add, name='student_add'),

    path('<int:pk>/', views.student_detail, name='student_detail'),

    path('edit/<int:pk>/', views.student_edit, name='student_edit'),
    path('delete/<int:pk>/', views.student_delete, name='student_delete'),

    path('add-sibling/<int:pk>/', views.add_sibling, name='add_sibling'),

    # ======================
    # 🔹 STATUS MANAGEMENT
    # ======================
    path('discontinue/<int:pk>/', views.student_discontinue, name='student_discontinue'),
    path('readmit/<int:pk>/', views.student_readmit, name='student_readmit'),

    # ======================
    # 🔹 CLASS MOVEMENT
    # ======================
    path('promote/<int:pk>/', views.student_promote, name='student_promote'),
    path('demote/<int:pk>/', views.student_demote, name='student_demote'),
    path('bulk-promotion/', views.bulk_promotion, name='bulk_promotion'),

    # ======================
    # 🔹 EXPORT
    # ======================
    path('export-excel/', views.export_students_excel, name='export_students_excel'),

    # ======================
    # 🔹 ID CARD & QR
    # ======================
    path('id-card/<int:pk>/', views.student_id_card, name='student_id_card'),
    path('id-cards-print/', views.student_id_cards_print, name='student_id_cards_print'),
    path('qr-profile/<int:pk>/', views.student_qr_profile, name='student_qr_profile'),

    # ======================
    # 🔥 IMPORT SYSTEM (FULL)
    # ======================
    path('import/', views.student_import, name='student_import'),

    # 🔥 STEP 1 → PREVIEW
    path('import-preview/', views.student_import_preview, name='student_import_preview'),

    # 🔥 STEP 2 → CONFIRM
    path('import-confirm/', views.student_import_confirm, name='student_import_confirm'),

    # 🔥 DEMO DOWNLOAD
    path('download-demo/', views.download_student_demo, name='download_student_demo'),
]