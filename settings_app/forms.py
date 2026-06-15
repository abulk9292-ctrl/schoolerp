from django import forms
from .models import GeneralSetting


class GeneralSettingForm(forms.ModelForm):

    class Meta:
        model = GeneralSetting

        fields = [
            'school_name',
            'principal_name',

            'principal_signature',
            'school_logo',
            'school_header',

            # Holiday Settings
            'weekly_holiday',
            'half_day_enabled',
            'half_day',
            'count_holiday_attendance',
        ]

        widgets = {
            'school_name': forms.TextInput(
                attrs={'class': 'form-control'}
            ),

            'principal_name': forms.TextInput(
                attrs={'class': 'form-control'}
            ),

            'weekly_holiday': forms.Select(
                attrs={'class': 'form-select'}
            ),

            'half_day': forms.Select(
                attrs={'class': 'form-select'}
            ),

            'half_day_enabled': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),

            'count_holiday_attendance': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
        }