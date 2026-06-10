from django.urls import path
from . import views

urlpatterns = [

    # =====================================================
    # DASHBOARD
    # =====================================================

    path(
        '',
        views.certificate_dashboard,
        name='certificate_dashboard'
    ),

    # =====================================================
    # CERTIFICATE LIST
    # =====================================================

    path(
        'list/',
        views.certificate_list,
        name='certificate_list'
    ),

    # =====================================================
    # CREATE CERTIFICATE
    # =====================================================

    path(
        'create/',
        views.certificate_create,
        name='certificate_create'
    ),

    # =====================================================
    # DETAIL / PRINT
    # =====================================================

    path(
        'view/<int:pk>/',
        views.certificate_detail,
        name='certificate_detail'
    ),

    # =====================================================
    # DELETE
    # =====================================================

    path(
        'delete/<int:pk>/',
        views.certificate_delete,
        name='certificate_delete'
    ),

]