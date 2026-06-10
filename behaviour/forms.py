from django import forms

from .models import (
    BehaviourRecord,
    SkillEvaluation
)


# =====================================================
# BEHAVIOUR RECORD FORM
# =====================================================

class BehaviourRecordForm(forms.ModelForm):

    class Meta:

        model = BehaviourRecord

        fields = [
            'student',
            'behaviour_type',
            'title',
            'description',
            'points',
            'action_taken',
            'parent_notified',
        ]

        widgets = {

            'student': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'behaviour_type': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'title': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter behaviour title'
                }
            ),

            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Write behaviour details'
                }
            ),

            'points': forms.NumberInput(
                attrs={
                    'class': 'form-control'
                }
            ),

            'action_taken': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Action taken'
                }
            ),

            'parent_notified': forms.CheckboxInput(
                attrs={
                    'class': 'form-check-input'
                }
            ),
        }


# =====================================================
# SKILL EVALUATION FORM
# =====================================================

class SkillEvaluationForm(forms.ModelForm):

    class Meta:

        model = SkillEvaluation

        fields = [

            'student',

            'month',
            'year',

            'discipline',
            'punctuality',
            'cleanliness',
            'communication',
            'teamwork',
            'leadership',
            'homework_habit',
            'class_participation',

            'teacher_remarks',
        ]

        widgets = {

            'student': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'month': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Example: May'
                }
            ),

            'year': forms.NumberInput(
                attrs={
                    'class': 'form-control'
                }
            ),

            'discipline': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'punctuality': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'cleanliness': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'communication': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'teamwork': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'leadership': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'homework_habit': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'class_participation': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'teacher_remarks': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Teacher remarks'
                }
            ),
        }