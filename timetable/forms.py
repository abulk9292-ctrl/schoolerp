from django import forms
from .models import Period, ClassTimetable, TimetableHoliday


class PeriodForm(forms.ModelForm):
    class Meta:
        model = Period
        fields = ["name", "start_time", "end_time", "order", "is_break"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "start_time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "end_time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
            "is_break": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class TimetableHolidayForm(forms.ModelForm):
    class Meta:
        model = TimetableHoliday
        fields = ["day", "title", "is_holiday", "remarks"]
        widgets = {
            "day": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "is_holiday": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class ClassTimetableForm(forms.ModelForm):
    class Meta:
        model = ClassTimetable
        fields = [
            "class_assigned", "section", "day", "period",
            "subject", "teacher", "room_no", "remarks", "is_active",
        ]
        widgets = {
            "class_assigned": forms.Select(attrs={"class": "form-select select2"}),
            "section": forms.TextInput(attrs={"class": "form-control"}),
            "day": forms.Select(attrs={"class": "form-select"}),
            "period": forms.Select(attrs={"class": "form-select select2"}),
            "subject": forms.Select(attrs={"class": "form-select select2"}),
            "teacher": forms.Select(attrs={"class": "form-select select2"}),
            "room_no": forms.TextInput(attrs={"class": "form-control"}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        teacher = cleaned_data.get("teacher")
        day = cleaned_data.get("day")
        period = cleaned_data.get("period")
        instance_id = self.instance.id if self.instance else None

        if teacher and day and period:
            qs = ClassTimetable.objects.filter(
                teacher=teacher,
                day=day,
                period=period,
                is_active=True,
            )
            if instance_id:
                qs = qs.exclude(id=instance_id)

            conflict = qs.select_related("class_assigned", "period").first()
            if conflict:
                raise forms.ValidationError(
                    f"This teacher is already selected for {conflict.class_assigned} "
                    f"{conflict.section or ''} on {conflict.get_day_display()} "
                    f"at {conflict.period.name}."
                )

        return cleaned_data
