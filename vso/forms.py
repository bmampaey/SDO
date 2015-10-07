from django import forms

class DrmsExportForm(forms.Form):
	series = forms.ChoiceField(required=True, choices = [('aia__lev1', 'aia.lev1'), ('hmi__Ic_45s', 'hmi.ic_45s'), ('hmi__M_45s', 'hmi.m_45s')])
	compress = forms.ChoiceField(required=False, choices = [('rice', 'rice')], initial = None)
	record = forms.CharField(required=True)

