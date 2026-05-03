from django import forms
from .models import Admission, ContactMessage


# 🔥 Admission Form (same as before)
class AdmissionForm(forms.ModelForm):
    class Meta:
        model = Admission
        fields = [
            'student_name',
            'father_name',
            'mother_name',
            'date_of_birth',
            'gender',
            'student_class',
            'aadhaar_no',
            'mobile',
            'guardian_mobile',
            'address',
            'previous_school',
            'transport_required',
            'hostel_required',
            'student_photo',
        ]

        widgets = {
            'student_name': forms.TextInput(attrs={'class': 'form-control'}),
            'father_name': forms.TextInput(attrs={'class': 'form-control'}),
            'mother_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'student_class': forms.TextInput(attrs={'class': 'form-control'}),
            'aadhaar_no': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'previous_school': forms.TextInput(attrs={'class': 'form-control'}),
            'transport_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'hostel_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'student_photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()

        student_name = cleaned_data.get('student_name')
        father_name = cleaned_data.get('father_name')
        mobile = cleaned_data.get('mobile')
        student_class = cleaned_data.get('student_class')

        if student_name and father_name and mobile and student_class:
            existing = Admission.objects.filter(
                student_name__iexact=student_name.strip(),
                father_name__iexact=father_name.strip(),
                mobile=mobile.strip(),
                student_class__iexact=student_class.strip(),
                status__in=['Pending', 'Approved']
            ).first()

            if existing:
                self.existing_admission = existing
                raise forms.ValidationError(
                    f"⚠️ Already Applied! Your Admission No: {existing.admission_no}"
                )

        return cleaned_data


# 🔥 NEW: Contact Form
class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'mobile', 'email', 'subject', 'message']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
        }