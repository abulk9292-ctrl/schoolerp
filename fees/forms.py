from django import forms
from django.utils import timezone

from .models import FeeCollection, FeeStructure, FeeFollowUp
from academics.models import AcademicSession


class FeeStructureForm(forms.ModelForm):

    SECTION_CHOICES = [
        ("", "No Section"),
        ("A", "A"),
        ("B", "B"),
        ("C", "C"),
        ("D", "D"),
    ]

    section = forms.ChoiceField(
        choices=SECTION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = FeeStructure

        fields = [
            'class_assigned',
            'section',
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

        active_session = AcademicSession.objects.filter(
            is_active=True
        ).first()

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

            'student': forms.Select(
                attrs={'class': 'form-select student-select'}
            ),

            'session': forms.Select(
                attrs={'class': 'form-select'}
            ),

            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),

            'monthly_fee': forms.NumberInput(attrs={
                'class': 'form-control fee-input',
                'step': '0.01',
                'placeholder': 'Monthly Fee'
            }),

            'admission_fee': forms.NumberInput(attrs={
                'class': 'form-control fee-input',
                'step': '0.01',
                'placeholder': 'Admission Fee'
            }),

            'registration_fee': forms.NumberInput(attrs={
                'class': 'form-control fee-input',
                'step': '0.01',
                'placeholder': 'Registration Fee'
            }),

            'art_material': forms.NumberInput(attrs={
                'class': 'form-control fee-input',
                'step': '0.01',
                'placeholder': 'Art Material'
            }),

            'transport_fee': forms.NumberInput(attrs={
                'class': 'form-control fee-input',
                'step': '0.01',
                'placeholder': 'Transport Fee'
            }),

            'books_fee': forms.NumberInput(attrs={
                'class': 'form-control fee-input',
                'step': '0.01',
                'placeholder': 'Books Fee'
            }),

            'uniform_fee': forms.NumberInput(attrs={
                'class': 'form-control fee-input',
                'step': '0.01',
                'placeholder': 'Uniform Fee'
            }),

            'fine': forms.NumberInput(attrs={
                'class': 'form-control fee-input',
                'step': '0.01',
                'placeholder': 'Fine'
            }),

            'others': forms.NumberInput(attrs={
                'class': 'form-control fee-input',
                'step': '0.01',
                'placeholder': 'Others'
            }),

            'previous_balance': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'readonly': 'readonly'
            }),

            'discount_percent': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),

            'deposit_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),

            'payment_mode': forms.Select(
                attrs={'class': 'form-select'}
            ),

            'operator_name': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
        }

    def __init__(self, *args, **kwargs):

        self.user = kwargs.pop('user', None)

        super().__init__(*args, **kwargs)

        active_session = AcademicSession.objects.filter(
            is_active=True
        ).first()

        if active_session and not self.instance.pk:
            self.fields['session'].initial = active_session

        if not self.instance.pk:
            self.fields['payment_date'].initial = timezone.now().date()

        if self.user and not self.user.has_perm('fees.can_change_fee_date'):
            self.fields['payment_date'].widget.attrs['readonly'] = 'readonly'

        if self.instance and self.instance.pk:
            self.fields['session'].widget.attrs['readonly'] = 'readonly'


# =========================================================
# FEE FOLLOW-UP / PROMISE FORM
# =========================================================

class FeeFollowUpForm(forms.ModelForm):
    class Meta:
        model = FeeFollowUp
        fields = [
            'student',
            'session',
            'parent_name',
            'mobile',
            'due_amount',
            'promise_amount',
            'promise_date',
            'followup_type',
            'priority',
            'status',
            'next_action',
            'remark',
            'result_note',
        ]

        widgets = {
            'student': forms.Select(attrs={'class': 'form-select student-select'}),
            'session': forms.Select(attrs={'class': 'form-select'}),

            'parent_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Parent / Guardian Name'
            }),

            'mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mobile Number'
            }),

            'due_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Current Due Amount'
            }),

            'promise_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Amount promised to pay'
            }),

            'promise_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),

            'followup_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),

            'next_action': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Example: Call today / Visit home / Send reminder'
            }),

            'remark': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'What did the parent say?'
            }),

            'result_note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'After call / visit result note'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        active_session = AcademicSession.objects.filter(is_active=True).first()

        if active_session and not self.instance.pk:
            self.fields['session'].initial = active_session

        if not self.instance.pk:
            self.fields['promise_date'].initial = timezone.now().date()
            self.fields['status'].initial = 'PENDING'
            self.fields['followup_type'].initial = 'CALL'
            self.fields['priority'].initial = 'NORMAL'
