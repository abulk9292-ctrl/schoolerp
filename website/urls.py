from django.urls import path
from . import views

urlpatterns = [
    path('', views.website_home, name='website_home'),
    path('about/', views.website_about, name='website_about'),
    path('admission/', views.website_admission, name='website_admission'),
    path('contact/', views.website_contact, name='website_contact'),
    path('admission-list/', views.admission_list, name='admission_list'),
    path('admission-print/<int:pk>/', views.admission_print, name='admission_print'),
    path('admission-approve/<int:pk>/', views.admission_approve, name='admission_approve'),
    path('contact-messages/', views.contact_message_list, name='contact_message_list'),
    path('contact-message-read/<int:pk>/', views.contact_mark_read, name='contact_mark_read'),
    path('contact-message-delete/<int:pk>/', views.contact_delete, name='contact_delete'),
    path('gallery/', views.gallery_page, name='gallery_page'),
    path('downloads/', views.download_list, name='download_list'),
    path('gallery/', views.gallery_list, name='gallery_list'),
    
]