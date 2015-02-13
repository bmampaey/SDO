# -*- coding: utf-8 -*-
from django import forms

class EmailLoginForm(forms.Form):
	email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'my.email@address.com'}))
