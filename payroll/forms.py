from django import forms
from django.utils import timezone

from .models import Salary


class SalaryForm(forms.ModelForm):
    class Meta:
        model = Salary
        fields = [
            'employee',
            'month',
            'year',
            'basic_salary',
            'bonus',
            'absent_days',
            'extra_deduction',
            'paid_amount',
            'payment_date',
        ]

        widgets = {
            'employee': forms.Select(attrs={
                'class': 'form-select'
            }),

            'month': forms.Select(attrs={
                'class': 'form-select'
            }),

            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '2026',
                'min': '2020',
                'max': '2100'
            }),

            'basic_salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Basic Salary'
            }),

            'bonus': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Auto bonus / manual bonus'
            }),

            'absent_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'style': 'background:#f1f5f9;font-weight:700;',
            }),

            'extra_deduction': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Extra Deduction'
            }),

            'paid_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Paid Amount'
            }),

            'payment_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        today = timezone.now().date()

        if not self.instance.pk:
            self.fields['year'].initial = today.year
            self.fields['payment_date'].initial = today

        for field_name, field in self.fields.items():
            field.required = False

        self.fields['employee'].required = True
        self.fields['month'].required = True
        self.fields['year'].required = True
        self.fields['payment_date'].required = True

        self.fields['absent_days'].disabled = True
        self.fields['absent_days'].help_text = "Auto calculated from teacher attendance."
        self.fields['bonus'].help_text = "Leave blank/0 for auto bonus calculation."
        self.fields['paid_amount'].help_text = "Enter amount paid for this salary month."

    def clean_basic_salary(self):
        value = self.cleaned_data.get('basic_salary')

        if value is None:
            return 0

        if value < 0:
            raise forms.ValidationError("Basic salary cannot be negative.")

        return value

    def clean_bonus(self):
        value = self.cleaned_data.get('bonus')

        if value is None:
            return 0

        if value < 0:
            raise forms.ValidationError("Bonus cannot be negative.")

        return value

    def clean_extra_deduction(self):
        value = self.cleaned_data.get('extra_deduction')

        if value is None:
            return 0

        if value < 0:
            raise forms.ValidationError("Extra deduction cannot be negative.")

        return value

    def clean_paid_amount(self):
        value = self.cleaned_data.get('paid_amount')

        if value is None:
            return 0

        if value < 0:
            raise forms.ValidationError("Paid amount cannot be negative.")

        return value