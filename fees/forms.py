from django import forms
from django.utils import timezone

from .models import FeeCollection, FeeStructure
from academics.models import AcademicSession


class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = [
            'class_assigned',
            'session',
            'monthly_fee',
            'admission_fee',
            'registration_fee',
            'art_material',
            'transport_fee',
            'books_fee',
            'uniform_fee',
            'is_active',
        ]
        widgets = {
            'class_assigned': forms.Select(attrs={'class': 'form-select'}),
            'session': forms.Select(attrs={'class': 'form-select'}),
            'monthly_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'admission_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'registration_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'art_material': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'transport_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'books_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'uniform_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        active_session = AcademicSession.objects.filter(is_active=True).first()
        if active_session:
            self.fields['session'].initial = active_session


class FeeCollectionForm(forms.ModelForm):

    MONTH_CHOICES = [
        ('January', 'January'),
        ('February', 'February'),
        ('March', 'March'),
        ('April', 'April'),
        ('May', 'May'),
        ('June', 'June'),
        ('July', 'July'),
        ('August', 'August'),
        ('September', 'September'),
        ('October', 'October'),
        ('November', 'November'),
        ('December', 'December'),
    ]

    fees_month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = FeeCollection
        fields = [
            'student',
            'session',
            'fees_month',
            'payment_date',

            'monthly_fee',
            'admission_fee',
            'registration_fee',
            'art_material',
            'transport_fee',
            'books_fee',
            'uniform_fee',

            'fine',
            'others',
            'previous_balance',

            'discount_percent',
            'deposit_amount',

            'payment_mode',
            'operator_name',
        ]

        widgets = {
            'student': forms.Select(attrs={'class': 'form-select student-select'}),
            'session': forms.Select(attrs={'class': 'form-select'}),

            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),

            'monthly_fee': forms.NumberInput(attrs={'class': 'form-control fee-input', 'step': '0.01', 'placeholder': 'Monthly Fee'}),
            'admission_fee': forms.NumberInput(attrs={'class': 'form-control fee-input', 'step': '0.01', 'placeholder': 'Admission Fee'}),
            'registration_fee': forms.NumberInput(attrs={'class': 'form-control fee-input', 'step': '0.01', 'placeholder': 'Registration Fee'}),
            'art_material': forms.NumberInput(attrs={'class': 'form-control fee-input', 'step': '0.01', 'placeholder': 'Art'}),
            'transport_fee': forms.NumberInput(attrs={'class': 'form-control fee-input', 'step': '0.01', 'placeholder': 'Transport'}),
            'books_fee': forms.NumberInput(attrs={'class': 'form-control fee-input', 'step': '0.01', 'placeholder': 'Books'}),
            'uniform_fee': forms.NumberInput(attrs={'class': 'form-control fee-input', 'step': '0.01', 'placeholder': 'Uniform'}),

            'fine': forms.NumberInput(attrs={'class': 'form-control fee-input', 'step': '0.01', 'placeholder': 'Fine'}),
            'others': forms.NumberInput(attrs={'class': 'form-control fee-input', 'step': '0.01', 'placeholder': 'Others'}),

            'previous_balance': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'readonly': 'readonly'
            }),

            'discount_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'deposit_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),

            'payment_mode': forms.Select(attrs={'class': 'form-select'}),
            'operator_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        active_session = AcademicSession.objects.filter(is_active=True).first()

        # 🔥 AUTO SESSION
        if active_session and not self.instance.pk:
            self.fields['session'].initial = active_session

        # 🔥 AUTO DATE
        if not self.instance.pk:
            self.fields['payment_date'].initial = timezone.now().date()

        # 🔥 DATE LOCK
        if self.user and not self.user.has_perm('fees.can_change_fee_date'):
            self.fields['payment_date'].widget.attrs['readonly'] = 'readonly'

        # 🔥 OPTIONAL: disable session change after create
        if self.instance and self.instance.pk:
            self.fields['session'].widget.attrs['readonly'] = 'readonly'