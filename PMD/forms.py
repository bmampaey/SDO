# -*- coding: utf-8 -*-
from datetime import datetime
import dateutil.parser as date_parser

from django import forms
from django.core.paginator import EmptyPage, PageNotAnInteger

# See http://django-tastypie.readthedocs.org/en/latest/paginator.html why it is important for postgres to have a special paginator
from PMD.paginators import EstimatedCountPaginator
from PMD.models import DataSeries


class LoginForm(forms.Form):
	email = forms.EmailField(required=False, label="Some functionalities require an email address", widget=forms.EmailInput(attrs={'placeholder': 'my.email@address.com'}))
	username = forms.CharField(required=False, label = "If you are a member of ROB, use your usual username/password to login", widget=forms.TextInput(attrs={'placeholder': 'username'}))
	password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'placeholder': 'password'}))


class TimeRangeForm(forms.Form):
	start_date = forms.DateTimeField(required=False, initial = datetime(2010, 03, 01))
	#end_date = forms.DateTimeField(required=False, initial = datetime.utcnow())
	end_date = forms.DateTimeField(required=False, initial = datetime(2010, 06, 01))
	cadence = forms.IntegerField(required=False, min_value = 1)
	cadence_multiplier = forms.TypedChoiceField(required=False, coerce=int, choices=[
		(1,  "second(s)"),
		(60, "minute(s)"),
		(3600, "hour(s)"),
		(86400, "day(s)")
	])
	
	@classmethod
	def defaults(cls):
		data = dict()
		for name, field in cls.base_fields.iteritems():
			data[name] = field.initial
		return data

	@classmethod
	def get_time_range(cls, request_data, request_session):
		"""Parse the time range from a request"""
		form = cls(request_data)
		if not form.is_valid():
			raise Exception(str(form.errors))
		
		cleaned_data = form.cleaned_data
		
		# For each field we try to get the values from the form else from the session else from the initials value
		if 'start_date' in cleaned_data and cleaned_data['start_date'] is not None:
			start_date = cleaned_data['start_date']
		elif 'start_date' in request_session and request_session['start_date'] is not None:
			start_date = date_parser.parse(request_session['start_date'])
		else:
			start_date = cls.base_fields['start_date'].initial
			
		if 'end_date' in cleaned_data and cleaned_data['end_date'] is not None:
			end_date = cleaned_data['end_date']
		elif 'end_date' in request_session and request_session['end_date'] is not None:
			end_date = date_parser.parse(request_session['end_date'])
		else:
			end_date = cls.base_fields['end_date'].initial
		
		if 'cadence' in cleaned_data and cleaned_data['cadence'] is not None:
			cadence = cleaned_data['cadence']
			# Cadence could be specified as a multiple (for example of hours)
			if 'cadence_multiplier' in cleaned_data and cleaned_data['cadence_multiplier'] is not None:
				cadence *= cleaned_data['cadence_multiplier']
		elif 'cadence' in request_session:
			cadence = request_session['cadence']
		else:
			cadence = cls.base_fields['cadence'].initial
		
		# Update the session
		request_session['start_date'] = start_date.isoformat()
		request_session['end_date'] = end_date.isoformat()
		request_session['cadence'] = None
		
		return start_date, end_date, cadence

class ResultActionForm(forms.Form):
	all_selected = forms.BooleanField(required=True)
	selected = forms.MultipleChoiceField(required=True)
	search_query = forms.CharField(required=True)

class DataSeriesSearchForm(forms.Form):
	limit = forms.IntegerField(required=False, initial=20, widget=forms.HiddenInput())
	
	def clean_limit(self):
		# Make sure that the default value for limit is set to it's initial value
		if not self['limit'].html_name in self.data:
			return self.fields['limit'].initial
		return self.cleaned_data['limit']
	
	@classmethod
	def sub_forms(cls):
		return dict([(form.record_table, form) for form in cls.__subclasses__()])
	
	@classmethod
	def defaults(cls):
		data = dict()
		for name, field in cls.base_fields.iteritems():
			data[name] = field.initial
		return data
	
	@property
	def data_series_name(self):
		return self.record_table


class AiaLev1SearchForm(DataSeriesSearchForm):
	record_table = "aia_lev1"
	tab_name = "AIA Lev1"
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
			'data_series_name': cls.record_table,
		}
		
		# Parse the request data
		form = cls(request_data)
		if not form.is_valid():
			raise Exception(str(form.errors))
		
		cleaned_data = form.cleaned_data
		
		# For each field we try to get the values from the form else from the session else from the initials value
		if 'best_quality' in cleaned_data and cleaned_data['best_quality'] is not None:
			request_session['best_quality'] = cleaned_data['best_quality']
		elif 'best_quality' not in request_session:
			request_session['best_quality'] = cls.base_fields['best_quality'].initial
		
		if 'wavelengths' in cleaned_data and cleaned_data['wavelengths']:
			request_session['wavelengths'] = cleaned_data['wavelengths']
		elif 'wavelengths' not in request_session:
			request_session['wavelengths'] = cls.base_fields['wavelengths'].initial
		
		# Parse the time range
		start_date, end_date, cadence = TimeRangeForm.get_time_range(request_data, request_session)
		
		# Make the QuerySet
		query_set = DataSeries.objects.get(record_table = cls.record_table).record.objects.filter()
		
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
			paginator = EstimatedCountPaginator(query_set, cleaned_data['limit'], allow_empty_first_page = False)
			try:
				page = paginator.page(page)
			except PageNotAnInteger:
				page = paginator.page(1)
			except EmptyPage:
				raise Exception("No result found for your search criteria")
			
			for record in page.object_list:
				record_title = u"%s %dÅ %s" % (cls.tab_name, record.wavelnth, record.date_obs.strftime("%Y-%m-%d %H:%M:%S"))
				table['records'].append({'recnum': record.recnum, 'title': record_title, 'fields': [record.date_obs, record.wavelnth, record.quality]})
			
			# Set up the pages navigation
			if page.number > 1:
				table['first_page_number'] = 1
			if page.has_previous():
				table['previous_page_number'] = page.previous_page_number()
			table['current_page_number'] = page.number
			if page.has_next():
				table['next_page_number'] = page.next_page_number()
			if page.number < paginator.num_pages:
				table['last_page_number'] = paginator.num_pages
		
		return table


class HmiM45SSearchForm(DataSeriesSearchForm):
	record_table =  "hmi_m_45s"
	tab_name = "HMI Magnetogram"
	best_quality = forms.BooleanField(required=False, help_text="Search results will only display data for which the quality keyword is 0")
	
	@classmethod
	def get_result_table(cls, request_data, request_session, page = None):
		"""Return a dict with all the necessary info to create a table of results"""
		#import pdb; pdb.set_trace()
		# Table to be returned
		table = {
			'headers' : ["Date", "Quality"],
			'records' : [],
			'first_page_number' : None,
			'previous_page_number' : None,
			'next_page_number' : None,
			'current_page_number' : None,
			'last_page_number': None,
			'data_series_name': cls.record_table,
		}
		
		# Parse the request data
		form = cls(request_data)
		if not form.is_valid():
			raise Exception(str(form.errors))
		
		cleaned_data = form.cleaned_data
		
		# For each field we try to get the values from the form else from the session else from the initials value
		if 'best_quality' in cleaned_data and cleaned_data['best_quality'] is not None:
			request_session['best_quality'] = cleaned_data['best_quality']
		elif 'best_quality' not in request_session:
			request_session['best_quality'] = cls.base_fields['best_quality'].initial
		
		# Parse the time range
		start_date, end_date, cadence = TimeRangeForm.get_time_range(request_data, request_session)
		
		# Make the QuerySet
		query_set = DataSeries.objects.get(record_table = cls.record_table).record.objects.filter()
		
		if request_session['best_quality']:
			query_set = query_set.filter(quality=0)
		
		# When cadence is specified we need a custom implementation
		# But only if cadence is larger than 45s as this is the minimal cadence for HMI
		if cadence and cadence > 45:
			raise Exception("Not yet implemented")
		
		else:
			if start_date:
				query_set = query_set.filter(date_obs__gte = start_date)
			
			if end_date:
				query_set = query_set.filter(date_obs__lt = end_date)
			
			# We make the paginator and get the records
			paginator = EstimatedCountPaginator(query_set, cleaned_data['limit'], allow_empty_first_page = False)
			try:
				page = paginator.page(page)
			except PageNotAnInteger:
				page = paginator.page(1)
			except EmptyPage:
				raise Exception("No result found for your search criteria")
			
			for record in page.object_list:
				record_title = u"%s %s" % (cls.tab_name, record.date_obs.strftime("%Y-%m-%d %H:%M:%S"))
				table['records'].append({'recnum': record.recnum, 'title': record_title, 'fields': [record.date_obs, record.quality]})
			
			# Set up the pages navigation
			if page.number > 1:
				table['first_page_number'] = 1
			if page.has_previous():
				table['previous_page_number'] = page.previous_page_number()
			table['current_page_number'] = page.number
			if page.has_next():
				table['next_page_number'] = page.next_page_number()
			if page.number < paginator.num_pages:
				table['last_page_number'] = paginator.num_pages
		
		return table

class HmiIc45SSearchForm(DataSeriesSearchForm):
	record_table =  "hmi_ic_45s"
	tab_name = "HMI Continuum"
	best_quality = forms.BooleanField(required=False, help_text="Search results will only display data for which the quality keyword is 0")
	
	@classmethod
	def get_result_table(cls, request_data, request_session, page = None):
		"""Return a dict with all the necessary info to create a table of results"""
		#import pdb; pdb.set_trace()
		# Table to be returned
		table = {
			'headers' : ["Date", "Quality"],
			'records' : [],
			'first_page_number' : None,
			'previous_page_number' : None,
			'next_page_number' : None,
			'current_page_number' : None,
			'last_page_number': None,
			'data_series_name': cls.record_table,
		}
		
		# Parse the request data
		form = cls(request_data)
		if not form.is_valid():
			raise Exception(str(form.errors))
		
		cleaned_data = form.cleaned_data
		
		# For each field we try to get the values from the form else from the session else from the initials value
		if 'best_quality' in cleaned_data and cleaned_data['best_quality'] is not None:
			request_session['best_quality'] = cleaned_data['best_quality']
		elif 'best_quality' not in request_session:
			request_session['best_quality'] = cls.base_fields['best_quality'].initial
		
		# Parse the time range
		start_date, end_date, cadence = TimeRangeForm.get_time_range(request_data, request_session)
		
		# Make the QuerySet
		query_set = DataSeries.objects.get(record_table = cls.record_table).record.objects.filter()
		
		if request_session['best_quality']:
			query_set = query_set.filter(quality=0)
		
		#import pdb; pdb.set_trace()
		# When cadence is specified we need a custom implementation
		# But only if cadence is larger than 45s as this is the minimal cadence for HMI
		if cadence and cadence > 45:
			raise Exception("Not yet implemented")
		
		else:
			if start_date:
				query_set = query_set.filter(date_obs__gte = start_date)
			
			if end_date:
				query_set = query_set.filter(date_obs__lt = end_date)
			
			# We make the paginator and get the records
			paginator = EstimatedCountPaginator(query_set, cleaned_data['limit'], allow_empty_first_page = False)
			try:
				page = paginator.page(page)
			except PageNotAnInteger:
				page = paginator.page(1)
			except EmptyPage:
				raise Exception("No result found for your search criteria")
			
			for record in page.object_list:
				record_title = u"%s %s" % (cls.tab_name, record.date_obs.strftime("%Y-%m-%d %H:%M:%S"))
				table['records'].append({'recnum': record.recnum, 'title': record_title, 'fields': [record.date_obs, record.quality]})
			
			# Set up the pages navigation
			if page.number > 1:
				table['first_page_number'] = 1
			if page.has_previous():
				table['previous_page_number'] = page.previous_page_number()
			table['current_page_number'] = page.number
			if page.has_next():
				table['next_page_number'] = page.next_page_number()
			if page.number < paginator.num_pages:
				table['last_page_number'] = paginator.num_pages
		
		return table
