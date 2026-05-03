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
    # 🔥 Student Panel URLs
    path('login/', views.student_login, name='student_login'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('logout/', views.student_logout, name='student_logout'),
    # 🔥 Parent Panel
    path('parent/login/', views.parent_login, name='parent_login'),
    path('parent/dashboard/', views.parent_dashboard, name='parent_dashboard'),
    path('parent/logout/', views.parent_logout, name='parent_logout'),
    path('forgot/', views.student_forgot_password, name='student_forgot'),
    path('verify/', views.student_verify_otp, name='student_verify_otp'),
    path('reset/', views.student_reset_password, name='student_reset_password'),
    path('portal-login/', views.combined_login, name='combined_login'),
    path('result-check/', views.public_result_check, name='public_result_check'),
    path('student/change-password/', views.student_change_password, name='student_change_password'),
]