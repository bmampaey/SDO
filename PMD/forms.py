# -*- coding: utf-8 -*-
from datetime import datetime
import dateutil.parser as date_parser

from django import forms
from django.core.paginator import EmptyPage, PageNotAnInteger#, Paginator
from paginators import EstimatedCountPaginator
from PMD.models import AiaLev1, HmiIc45S, HmiM45S

class TimeRangeForm(forms.Form):
	start_date = forms.DateTimeField(required=False, initial = datetime(2010, 03, 01))
	end_date = forms.DateTimeField(required=False, initial = datetime.utcnow())
	cadence = forms.IntegerField(required=False, min_value = 1)
	cadence_multiplier = forms.TypedChoiceField(required=False, coerce=int, choices=[
		(1,  "second(s)"),
		(60, "minute(s)"),
		(3600, "hour(s)"),
		(86400, "day(s)")
	])
	
	@classmethod
	def get_time_range(cls, request_data, request_session):
		"""Parse the time range from a request"""
		form = cls(request_data)
		if not form.is_valid():
			raise Exception(str(form.errors))
		
		cleaned_data = form.cleaned_data
		
		if 'start_date' in cleaned_data and cleaned_data['start_date'] is not None:
			start_date = cleaned_data['start_date']
			request_session['start_date'] = start_date.isoformat()
		elif 'start_date' in request_session:
			start_date = date_parser.parse(request_session['start_date'])
		else:
			# start_date is not required, and None by default
			start_date = None
			request_session['start_date'] = None
			
		if 'end_date' in cleaned_data and cleaned_data['end_date'] is not None:
			end_date = cleaned_data['end_date']
			request_session['end_date'] = end_date.isoformat()
		elif 'end_date' in request_session:
			end_date = date_parser.parse(request_session['end_date'])
		else:
			# end_date is not required, and None by default
			end_date = None
			request_session['end_date'] = None
		
		if 'cadence' in cleaned_data and cleaned_data['cadence'] is not None:
			cadence = cleaned_data['cadence']
			
			# Cadence could be specified as a multiple (for example hours)
			if 'cadence_multiplier' in cleaned_data and cleaned_data['cadence_multiplier'] is not None:
				cadence *= cleaned_data['cadence_multiplier']
			
			request_session['cadence'] = cadence
		elif 'cadence' in request_session:
			cadence = request_session['cadence']
		else:
			# Cadence is not required, and None by default
			cadence = None
			request_session['cadence'] = None
		
		return start_date, end_date, cadence

class DataSeriesForm(forms.Form):
	limit = forms.IntegerField(required=False, initial=20, widget=forms.HiddenInput())
	
	def clean_limit(self):
		if not self['limit'].html_name in self.data:
			return self.fields['limit'].initial
		return self.cleaned_data['limit']

class AiaLev1SearchForm(DataSeriesForm):
	data_series = "aia_lev1"
	pretty_name = "AIA Lev1"
	best_quality = forms.BooleanField(required=False, help_text="Search results will only display data for which the quality keyword is 0")
	wavelengths = forms.MultipleChoiceField(required=False, widget=forms.SelectMultiple(), initial = [171, 193], choices=[
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
	
	@classmethod
	def get_result_table(cls, request_data, request_session, page = None):
		"""Return a dict with all the necessary info to create a table of results"""
		#import pdb; pdb.set_trace()
		# Table to be returned
		table = {
			'headers' : ["Date", "Wavelength", "Quality"],
			'records' : [],
			'first_page_number' : None,
			'previous_page_number' : None,
			'next_page_number' : None,
			'current_page_number' : None,
			'last_page_number': None,
			'data_series': cls.data_series,
		}
		
		# Parse the request data
		form = cls(request_data)
		if not form.is_valid():
			raise Exception(str(form.errors))
		
		cleaned_data = form.cleaned_data
		
		if 'best_quality' in cleaned_data and cleaned_data['best_quality'] is not None:
			request_session['best_quality'] = cleaned_data['best_quality']
		elif 'best_quality' not in request_session:
			# best_quality is not required, and False by default
			request_session['best_quality'] = False
		
		if 'wavelengths' in cleaned_data and cleaned_data['wavelengths']:
			request_session['wavelengths'] = cleaned_data['wavelengths']
		elif 'wavelengths' not in request_session:
			raise Exception("For AIA, you need to select at least 1 wavelength")
		
		# Parse the time range
		start_date, end_date, cadence = TimeRangeForm.get_time_range(request_data, request_session)
		
		# Make the QuerySet
		query_set = AiaLev1.objects.filter()
		
		if request_session['best_quality']:
			query_set = query_set.filter(quality=0)
		
		query_set = query_set.filter(wavelnth__in=request_session['wavelengths'])
		#import pdb; pdb.set_trace()
		# When cadence is specified we need a custom implementation
		# But only if cadence is larger than 12s as this is the minimal cadence for AIA
		if cadence and cadence > 12:
			raise Exception("Not yet implemented")
		
		else:
			if start_date:
				query_set = query_set.filter(date_obs__gte = start_date)
			
			if end_date:
				query_set = query_set.filter(date_obs__lt = end_date)
			
			# We make the paginator and get the records
			paginator =  EstimatedCountPaginator(query_set, cleaned_data['limit'], allow_empty_first_page = False)
			try:
				page = paginator.page(page)
			except PageNotAnInteger:
				page = paginator.page(1)
			except EmptyPage:
				raise Exception("No result found for your search criteria")
			
			for record in page.object_list:
				table['records'].append({'recnum': record.recnum, 'sunum': record.sunum, 'slotnum': record.slotnum, 'fields': [record.date_obs, record.wavelnth, record.quality]})
			
			# Set up the pages navigation
			if page.number > 1:
				table['first_page_number'] = 1
			if page.has_previous():
				table['previous_page_number'] = page.previous_page_number()
			table['current_page_number'] = page.number
			if page.has_next():
				table['next_page_number'] = page.next_page_number()
			table['last_page_number'] = paginator.num_pages
		
		return table


class HmiM45SSearchForm(DataSeriesForm):
	data_series = "hmi_m_45s"
	pretty_name = "HMI M 45s"
	best_quality = forms.BooleanField(required=False, help_text="Search results will only display data for which the quality keyword is 0")


class HmiIc45SSearchForm(DataSeriesForm):
	data_series = "hmi_ic_45s"
	pretty_name = "HMI Ic 45s"
	best_quality = forms.BooleanField(required=False, help_text="Search results will only display data for which the quality keyword is 0")

