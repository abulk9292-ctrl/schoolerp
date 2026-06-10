from django.urls import path
from . import views

urlpatterns = [
    path("", views.timetable_dashboard, name="timetable_dashboard"),

    path("weekly/", views.weekly_timetable, name="weekly_timetable"),

    path("holidays/", views.holiday_list, name="timetable_holiday_list"),
    path("holidays/add/", views.holiday_add, name="timetable_holiday_add"),
    path("holidays/<int:pk>/edit/", views.holiday_edit, name="timetable_holiday_edit"),
    path("holidays/<int:pk>/delete/", views.holiday_delete, name="timetable_holiday_delete"),

    path("periods/", views.period_list, name="period_list"),
    path("periods/add/", views.period_add, name="period_add"),
    path("periods/<int:pk>/edit/", views.period_edit, name="period_edit"),
    path("periods/<int:pk>/delete/", views.period_delete, name="period_delete"),

    path("entries/", views.timetable_entry_list, name="timetable_entry_list"),
    path("entries/add/", views.timetable_entry_add, name="timetable_entry_add"),
    path("entries/<int:pk>/edit/", views.timetable_entry_edit, name="timetable_entry_edit"),
    path("entries/<int:pk>/delete/", views.timetable_entry_delete, name="timetable_entry_delete"),

    path("class-view/", views.class_timetable_view, name="class_timetable_view"),
    path("teacher-view/", views.teacher_timetable_view, name="teacher_timetable_view"),
    path("day-view/", views.day_timetable_view, name="day_timetable_view"),

    path("print-select/", views.print_select, name="timetable_print_select"),
    path("print/", views.timetable_print, name="timetable_print"),
]
