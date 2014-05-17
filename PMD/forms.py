# -*- coding: utf-8 -*-
from django import forms

class TimeRangeForm(forms.Form):
	start_date = forms.DateTimeField()
	end_date = forms.DateTimeField()
	cadence = forms.IntegerField(min_value = 1)
	cadence_unit = forms.ChoiceField(choices=[
		("s", "second(s)"),
		("m", "minute(s)"),
		("h", "hour(s)"),
		("d", "day(s)")
	])

class DataSeriesForm(forms.Form):
	pass

class AiaLev1SearchForm(DataSeriesForm):
	data_series = forms.CharField(initial="aia.lev1", widget=forms.HiddenInput())
	best_quality = forms.BooleanField(required=False, help_text="Search results will only display data for which the quality keyword is 0")
	wavelengths = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=[
		(94, '094Å'),
		(131, '131Å'),
		(171, '171Å'),
		(193, '193Å'),
		(211, '211Å'),
		(304, '304Å'),
		(335, '335Å'),
		(1700, '1600Å'),
		(1600, '1700Å'),
		(4500, '4500Å')
	])

class HmiM45SSearchForm(DataSeriesForm):
	data_series = forms.CharField(initial="hmi.m_45s", widget=forms.HiddenInput())
	best_quality = forms.BooleanField(required=False, help_text="Search results will only display data for which the quality keyword is 0")

