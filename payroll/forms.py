from django import forms
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
            'absent_days',   # ✅ ADD
            'extra_deduction',
            'paid_amount',
            'payment_date',
        ]

        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'month': forms.Select(attrs={'class': 'form-select'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2026'}),

            'basic_salary': forms.NumberInput(attrs={'class': 'form-control'}),

            'bonus': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly'   # 🔥 auto bonus
            }),

            'absent_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),

            'extra_deduction': forms.NumberInput(attrs={'class': 'form-control'}),

            'paid_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'New payment amount'
            }),

            'payment_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
        }