from django import forms
from .models import Employee


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'name',
            'designation',
            'qualification',
            'subject_specialization',
            'phone',
            'aadhaar_number',
            'joining_date',
            'salary',
            'photo',
            'is_active',

            # ✅ ERP Access Control
            'is_erp_admin',
            'can_access_students',
            'can_access_teachers',
            'can_access_academics',
            'can_access_attendance',
            'can_access_fees',
            'can_access_payroll',
            'can_access_exams',
            'can_access_reports',
            'can_access_admissions',
            'can_access_idcards',
            'can_access_communications',
            'can_access_expenses',
            'can_access_backup',
            'can_access_settings',
        ]

        widgets = {
            'joining_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),

            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'designation': forms.TextInput(attrs={'class': 'form-control'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'subject_specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'aadhaar_number': forms.TextInput(attrs={'class': 'form-control'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),

            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),

            'is_erp_admin': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_access_students': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_access_teachers': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_access_academics': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_access_attendance': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_access_fees': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_access_payroll': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_access_exams': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_access_reports': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_access_admissions': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_access_idcards': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_access_communications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_access_expenses': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_access_backup': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_access_settings': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }