from django.contrib import admin
from .models import Class, Subject, AcademicSession


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('class_name', 'class_teacher')