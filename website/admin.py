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
    DownloadFile,
    WebsiteSetting,
    WebsiteTeacher,
    WebsiteTopper,
    WebsiteCounter,
    Testimonial,
    PopupNotice,
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
    search_fields = (
        'student_name',
        'father_name',
        'mobile',
        'admission_no'
    )
    readonly_fields = (
        'admission_no',
        'student_id',
        'registration_no',
        'created_at'
    )
    ordering = ('-created_at',)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if obj.status == 'Approved':
            from students.models import Student
            from academics.models import Class, AcademicSession
            from datetime import date

            if not Student.objects.filter(
                admission_no=obj.admission_no
            ).exists():

                class_obj = Class.objects.filter(
                    class_name__iexact=obj.student_class
                ).first()

                active_session = AcademicSession.objects.filter(
                    is_active=True
                ).first()

                if class_obj:
                    Student.objects.create(
                        admission_no=obj.admission_no,
                        student_name=obj.student_name,
                        father_name=obj.father_name,
                        mother_name=obj.mother_name,
                        phone=obj.mobile,
                        address=obj.address,
                        date_of_birth=obj.date_of_birth,
                        gender=obj.gender,
                        aadhaar_number=obj.aadhaar_no,
                        previous_school=obj.previous_school,
                        transport_required=obj.transport_required,
                        photo=obj.student_photo,
                        class_assigned=class_obj,
                        current_session=active_session,
                        admission_date=date.today(),
                    )


# 🔥 Contact Message Admin
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'mobile',
        'subject',
        'is_read',
        'created_at'
    )
    list_filter = ('is_read', 'created_at')
    search_fields = (
        'name',
        'mobile',
        'subject',
        'message'
    )
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


# 🔥 Slider Admin
@admin.register(HomeSlider)
class HomeSliderAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'is_active',
        'order',
        'created_at'
    )
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
    list_filter = (
        'is_important',
        'is_active',
        'notice_date'
    )
    search_fields = ('title', 'description')
    list_editable = (
        'is_important',
        'is_active',
        'order'
    )
    ordering = ('order', '-created_at')
    readonly_fields = ('created_at',)


# 🔥 Gallery Admin
@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'is_active',
        'order',
        'created_at'
    )
    list_filter = ('category', 'is_active')
    search_fields = ('title', 'description')

    fields = (
        'title',
        'category',
        'image',
        'video',
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
    list_display = (
        'title',
        'event_date',
        'is_active',
        'order'
    )
    list_filter = ('event_date', 'is_active')
    search_fields = ('title', 'description')
    list_editable = ('is_active', 'order')
    ordering = ('order', '-event_date')


# 🔥 Infrastructure Admin
@admin.register(Infrastructure)
class InfrastructureAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'is_active',
        'order'
    )
    list_filter = ('is_active',)
    search_fields = ('title', 'description')
    list_editable = ('is_active', 'order')
    ordering = ('order', '-id')


# 🔥 Why Choose Admin
@admin.register(WhyChoose)
class WhyChooseAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'icon',
        'is_active',
        'order'
    )
    list_filter = ('is_active',)
    search_fields = ('title', 'description')
    list_editable = ('is_active', 'order')
    ordering = ('order', '-id')


# 🔥 Download Section Admin
@admin.register(DownloadFile)
class DownloadFileAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'file_type',
        'is_active',
        'order',
        'created_at'
    )
    list_filter = ('file_type', 'is_active')
    search_fields = ('title', 'description')
    list_editable = ('is_active', 'order')
    ordering = ('order', '-created_at')
    readonly_fields = ('created_at',)

# 🔥 Website Setting Admin
@admin.register(WebsiteSetting)
class WebsiteSettingAdmin(admin.ModelAdmin):
    list_display = (
        'school_name',
        'phone',
        'email',
        'maintenance_mode'
    )

# ==========================================
# WEBSITE TEACHER
# ==========================================

@admin.register(WebsiteTeacher)
class WebsiteTeacherAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'designation',
        'is_active',
        'order'
    )
    list_filter = ('is_active',)
    search_fields = (
        'name',
        'designation',
        'qualification'
    )
    list_editable = (
        'is_active',
        'order'
    )
    ordering = ('order',)


# ==========================================
# WEBSITE TOPPER
# ==========================================

@admin.register(WebsiteTopper)
class WebsiteTopperAdmin(admin.ModelAdmin):
    list_display = (
        'student_name',
        'exam_name',
        'percentage',
        'is_active',
        'order'
    )
    list_filter = ('is_active',)
    search_fields = (
        'student_name',
        'exam_name'
    )
    list_editable = (
        'is_active',
        'order'
    )
    ordering = ('order',)


# ==========================================
# WEBSITE COUNTER
# ==========================================

@admin.register(WebsiteCounter)
class WebsiteCounterAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'value',
        'order'
    )
    list_editable = (
        'value',
        'order'
    )
    ordering = ('order',)


# ==========================================
# TESTIMONIAL
# ==========================================

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'designation',
        'rating',
        'is_active'
    )
    list_filter = (
        'rating',
        'is_active'
    )
    search_fields = (
        'name',
        'review'
    )


# ==========================================
# POPUP NOTICE
# ==========================================

@admin.register(PopupNotice)
class PopupNoticeAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'is_active'
    )
    list_editable = (
        'is_active',
    )