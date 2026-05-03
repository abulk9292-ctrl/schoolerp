from django.contrib import admin
from .models import (
    Admission,
    ContactMessage,
    HomeSlider,
    Notice,
    Gallery,
    SchoolEvent,
    Infrastructure,
    WhyChoose,
    DownloadFile   # ✅ NEW
)


# 🔥 Admission Admin
@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = (
        'admission_no',
        'student_name',
        'student_class',
        'mobile',
        'status',
        'created_at'
    )
    list_filter = ('status', 'student_class')
    search_fields = ('student_name', 'father_name', 'mobile', 'admission_no')
    readonly_fields = ('admission_no', 'student_id', 'registration_no', 'created_at')
    ordering = ('-created_at',)


# 🔥 Contact Message Admin
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'mobile', 'subject', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'mobile', 'subject', 'message')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


# 🔥 Slider Admin
@admin.register(HomeSlider)
class HomeSliderAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'order', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'subtitle')
    list_editable = ('is_active', 'order')
    ordering = ('order',)
    readonly_fields = ('created_at',)


# 🔥 Notice Admin
@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'notice_date',
        'is_important',
        'is_active',
        'order',
        'created_at'
    )
    list_filter = ('is_important', 'is_active', 'notice_date')
    search_fields = ('title', 'description')
    list_editable = ('is_important', 'is_active', 'order')
    ordering = ('order', '-created_at')
    readonly_fields = ('created_at',)


# 🔥 Gallery Admin (UPGRADED → VIDEO SUPPORT)
@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_active', 'order', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('title', 'description')

    # ✅ VIDEO + IMAGE SHOW IN FORM
    fields = (
        'title',
        'category',
        'image',
        'video',   # ✅ NEW
        'description',
        'is_active',
        'order',
        'created_at'
    )

    list_editable = ('is_active', 'order')
    ordering = ('order', '-id')
    readonly_fields = ('created_at',)


# 🔥 School Event Admin
@admin.register(SchoolEvent)
class SchoolEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_date', 'is_active', 'order')
    list_filter = ('event_date', 'is_active')
    search_fields = ('title', 'description')
    list_editable = ('is_active', 'order')
    ordering = ('order', '-event_date')


# 🔥 Infrastructure Admin
@admin.register(Infrastructure)
class InfrastructureAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'order')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')
    list_editable = ('is_active', 'order')
    ordering = ('order', '-id')


# 🔥 Why Choose Admin
@admin.register(WhyChoose)
class WhyChooseAdmin(admin.ModelAdmin):
    list_display = ('title', 'icon', 'is_active', 'order')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')
    list_editable = ('is_active', 'order')
    ordering = ('order', '-id')


# 🔥 NEW: Download Section Admin
@admin.register(DownloadFile)
class DownloadFileAdmin(admin.ModelAdmin):
    list_display = ('title', 'file_type', 'is_active', 'order', 'created_at')
    list_filter = ('file_type', 'is_active')
    search_fields = ('title', 'description')

    list_editable = ('is_active', 'order')
    ordering = ('order', '-created_at')

    readonly_fields = ('created_at',)