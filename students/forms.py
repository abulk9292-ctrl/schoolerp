from django import forms
from .models import Student
from academics.models import AcademicSession


class StudentForm(forms.ModelForm):

    SECTION_CHOICES = [
        ("", "Select Section"),
        ("A", "A"),
        ("B", "B"),
        ("C", "C"),
        ("D", "D"),
    ]

    section = forms.ChoiceField(
        choices=SECTION_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            "class": "form-select"
        })
    )

    class Meta:
        model = Student

        fields = [
            'student_name',
            'admission_no',
            'admission_date',

            'current_session',

            'class_assigned',
            'section',
            'roll_no',

            'father_name',
            'mother_name',
            'guardian_name',
            'phone',

            'gender',
            'date_of_birth',
            'aadhaar_number',

            'transport_required',
            'transport_details',

            'previous_school',
            'address',
            'photo',
            'is_active',
        ]

        widgets = {
            'student_name': forms.TextInput(attrs={'class': 'form-control'}),
            'admission_no': forms.TextInput(attrs={'class': 'form-control'}),
            'admission_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),

            'current_session': forms.Select(attrs={'class': 'form-select'}),

            'class_assigned': forms.Select(attrs={'class': 'form-select'}),

            'section': forms.Select(
                choices=[
                ("", "Select Section"),
                ("A", "A"),
                ("B", "B"),
                ("C", "C"),
                ("D", "D"),
           ],
           attrs={'class': 'form-select'}
        ),

            'roll_no': forms.NumberInput(attrs={'class': 'form-control'}),

            'father_name': forms.TextInput(attrs={'class': 'form-control'}),
            'mother_name': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),

            'gender': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'aadhaar_number': forms.TextInput(attrs={'class': 'form-control'}),

            'transport_required': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'transport_details': forms.TextInput(attrs={'class': 'form-control'}),

            'previous_school': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        active_session = AcademicSession.objects.filter(is_active=True).first()

        if active_session and not self.instance.pk:
            self.fields['current_session'].initial = active_session


class StudentImportForm(forms.Form):
    excel_file = forms.FileField(
        label="Upload Student Excel File",
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls'
        })
    )