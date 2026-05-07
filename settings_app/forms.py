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
        ]