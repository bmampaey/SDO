# -*- coding: utf-8 -*-
from django import forms

class TimeRangeForm(forms.Form):
	start_date = forms.DateTimeField()
	cadence = forms.DateTimeField()
	cadence = forms.IntegerField(min_value = 1)
	cadence_multiplier = forms.ChoiceField(required=False, choices=[
		("s", "second(s)"),
		("m", "minute(s)"),
		("h", "hour(s)"),
		("d", "day(s)")
	])

class DataSeriesForm(forms.Form):
	limit = forms.IntegerField(required=False, initial=20)
	def __init__(self, data_series_name,  *args, **kwargs):
		super(DataSeriesForm, self).__init__(*args, **kwargs)
		self.fields['data_series_name'] = forms.CharField(initial=data_series_name, widget=forms.HiddenInput())

class AiaLev1SearchForm(DataSeriesForm):
	name = "aia_lev1"
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
	name = "hmi_m_45s"
	best_quality = forms.BooleanField(required=False, help_text="Search results will only display data for which the quality keyword is 0")

class HmiIc45SSearchForm(DataSeriesForm):
	name = "hmi_ic_45s"
	best_quality = forms.BooleanField(required=False, help_text="Search results will only display data for which the quality keyword is 0")

class SearchResultForm(forms.Form):
	def __init__(self, data_series_name, search_results,  *args, **kwargs):
		super(SearchResultForm, self).__init__(*args, **kwargs)
		self.fields['data_series_name'] = forms.CharField(initial=data_series_name, widget=forms.HiddenInput())
		for search_result in search_results:
			self.fields[search_result.recnum] = BooleanField(required=False, label = "<td>{date_obs}</td><td>{wavelnth}Å</td>".format(search_result))
