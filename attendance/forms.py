from django import forms
from .models import Holiday


class HolidayForm(forms.ModelForm):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=True
    )

    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False
    )

    class Meta:
        model = Holiday
        fields = [
            'title',
            'start_date',
            'end_date',
            'holiday_type',
            'is_half_day',
            'note',
        ]

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'holiday_type': forms.Select(attrs={'class': 'form-select'}),
            'is_half_day': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }