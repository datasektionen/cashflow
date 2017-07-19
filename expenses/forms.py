from django import forms

from .models import Profile


class UserForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bank_account', 'sorting_number', 'bank_name', 'default_account']
