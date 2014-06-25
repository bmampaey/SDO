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
	start_date = forms.DateTimeField(required=False, initial = datetime(2010, 03, 29))
	#end_date = forms.DateTimeField(required=False, initial = datetime.utcnow())
	end_date = forms.DateTimeField(required=False, initial = datetime(2010, 05, 15))
	cadence = forms.IntegerField(required=False, min_value = 1)
	cadence_multiplier = forms.TypedChoiceField(required=False, coerce=int, choices=[
		(1,  "second(s)"),
		(60, "minute(s)"),
		(3600, "hour(s)"),
		(86400, "day(s)")
	])
	
	@classmethod
	def initials(cls):
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
		
		request_session['start_date'] = start_date.isoformat()
		request_session['end_date'] = end_date.isoformat()
		request_session['cadence'] = cadence
		return {"start_date": start_date, "end_date": end_date, "cadence": cadence}

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
	def initials(cls):
		data = dict()
		for name, field in cls.base_fields.iteritems():
			data[name] = field.initial
		return data
	
	@classmethod
	def get_paginator(cls, query_set, limit, cadence = 0):
		# When cadence is specified we need a custom implementation of paginator
		# But only if cadence is big enough
		if cadence and cadence > cls.minimal_cadence:
			raise Exception("Not yet implemented")
		else:
			return EstimatedCountPaginator(query_set, limit, allow_empty_first_page = False, orphans = limit/2)

	@classmethod
	def get_result_table(cls, request_data, request_session, page = None):
		"""Return a dict with all the necessary info to create a table of results"""
		# THIS COULD GO INTO THE VIEW
		# Get the query set
		query_set = cls.get_query_set(request_data, request_session)
		
		# Get the paginator and get the page
		paginator = cls.get_paginator(query_set, request_session["limit"], request_session["cadence"])
		try:
			page = paginator.page(page)
		except PageNotAnInteger:
			page = paginator.page(1)
		except EmptyPage:
			raise Exception("No result found for your search criteria")
		
		# Result table
		table = {'data_series_name': cls.record_table}
		
		# Make the record list from the page objects
		table['records'], table['headers'] = cls.get_records_headers(page.object_list)
		
		# Set up the pages navigation # TODO use urlencode and store full url
		table['first_page_number'] = 1 if page.number > 1 else None
		table['previous_page_number'] = page.previous_page_number() if page.has_previous() else None
		table['current_page_number'] = page.number
		table['next_page_number'] = page.next_page_number() if page.has_next() else None
		table['last_page_number'] = paginator.num_pages if page.number < paginator.num_pages else None
		table['limit'] = request_session['limit']
		
		return table
	
	@property
	def data_series_name(self):
		return self.record_table

WAVELENGTHS = [94, 131, 171, 193, 211, 304, 335, 1600, 1700, 4500]
class AiaLev1SearchForm(DataSeriesSearchForm):
	record_table = "aia_lev1"
	tab_name = "AIA Lev1"
	minimal_cadence = 12
	best_quality = forms.BooleanField(required=True, initial = False, help_text="Search results will only display data for which the quality keyword is 0")
	wavelengths = forms.MultipleChoiceField(required=True, widget=forms.SelectMultiple(), initial = WAVELENGTHS, choices=[(w, u'%sÅ'%w) for w in WAVELENGTHS])
	
	@classmethod
	def get_query_set(cls, request_data, request_session = {}):
		
		# Parse the request data
		form = cls(request_data)
		form.is_valid()
		
		# For each parameter we try to get the values from the form or else from the session or else from the initials value
		query_parameters = cls.initials()
		query_parameters.update(request_session)
		query_parameters.update(form.cleaned_data)
		
		# Update the request session
		request_session.update(query_parameters)
		
		# Add the time range parameters
		query_parameters.update(TimeRangeForm.get_time_range(request_data, request_session))
		
		# Make the QuerySet
		query_set = DataSeries.objects.get(record_table = cls.record_table).record.objects.filter()
		
		if query_parameters['best_quality']:
			query_set = query_set.filter(quality=0)
		
		# Do not add the condition if we take all wavelengths
		if set(WAVELENGTHS) - set(query_parameters['wavelengths']):
			query_set = query_set.filter(wavelnth__in=query_parameters['wavelengths'])
		
		if query_parameters['start_date']:
			query_set = query_set.filter(date_obs__gte = query_parameters['start_date'])
		
		if query_parameters['end_date']:
			query_set = query_set.filter(date_obs__lt = query_parameters['end_date'])
		
		return query_set
		
	
	@classmethod
	def get_records_headers(cls, objects):
		headers = ["Date", "Wavelength", "Quality"]
		records = list()
		for obj in objects:
			record_title = u"%s %dÅ %s" % (cls.tab_name, obj.wavelnth, obj.date_obs.strftime("%Y-%m-%d %H:%M:%S"))
			records.append({'recnum': obj.recnum, 'title': record_title, 'fields': [obj.date_obs, obj.wavelnth, obj.quality]})
		
		return records, headers


class HmiM45SSearchForm(DataSeriesSearchForm):
	record_table =  "hmi_m_45s"
	tab_name = "HMI Magnetogram"
	minimal_cadence = 45
	best_quality = forms.BooleanField(required=True, initial = False, help_text="Search results will only display data for which the quality keyword is 0")
	
	@classmethod
	def get_query_set(cls, request_data, request_session = {}):
		
		# Parse the request data
		form = cls(request_data)
		form.is_valid()
		
		# For each parameter we try to get the values from the form or else from the session or else from the initials value
		query_parameters = cls.initials()
		query_parameters.update(request_session)
		query_parameters.update(form.cleaned_data)
		
		# Update the request session
		request_session.update(query_parameters)
		
		# Add the time range parameters
		query_parameters.update(TimeRangeForm.get_time_range(request_data, request_session))
		
		# Make the QuerySet
		query_set = DataSeries.objects.get(record_table = cls.record_table).record.objects.filter()
		
		if query_parameters['best_quality']:
			query_set = query_set.filter(quality=0)
		
		if query_parameters['start_date']:
			query_set = query_set.filter(date_obs__gte = query_parameters['start_date'])
		
		if query_parameters['end_date']:
			query_set = query_set.filter(date_obs__lt = query_parameters['end_date'])
			
			return query_set
	
	@classmethod
	def get_records_headers(cls, objects):
		headers = ["Date", "Quality"]
		records = list()
		for obj in objects:
			record_title = u"%s %s" % (cls.tab_name, obj.date_obs.strftime("%Y-%m-%d %H:%M:%S"))
			records.append({'recnum': obj.recnum, 'title': record_title, 'fields': [obj.date_obs, obj.quality]})
		
		return records, headers

class HmiIc45SSearchForm(DataSeriesSearchForm):
	record_table =  "hmi_ic_45s"
	tab_name = "HMI Continuum"
	minimal_cadence = 45
	best_quality = forms.BooleanField(required=True, initial = False, help_text="Search results will only display data for which the quality keyword is 0")
	
	@classmethod
	def get_query_set(cls, request_data, request_session = {}):
		
		# Parse the request data
		form = cls(request_data)
		form.is_valid()
		
		# For each parameter we try to get the values from the form or else from the session or else from the initials value
		query_parameters = cls.initials()
		query_parameters.update(request_session)
		query_parameters.update(form.cleaned_data)
		
		# Update the request session
		request_session.update(query_parameters)
		
		# Add the time range parameters
		query_parameters.update(TimeRangeForm.get_time_range(request_data, request_session))
		
		# Make the QuerySet
		query_set = DataSeries.objects.get(record_table = cls.record_table).record.objects.filter()
		
		if query_parameters['best_quality']:
			query_set = query_set.filter(quality=0)
		
		if query_parameters['start_date']:
			query_set = query_set.filter(date_obs__gte = query_parameters['start_date'])
		
		if query_parameters['end_date']:
			query_set = query_set.filter(date_obs__lt = query_parameters['end_date'])
			
		return query_set
	
	@classmethod
	def get_records_headers(cls, objects):
		headers = ["Date", "Quality"]
		records = list()
		for obj in objects:
			record_title = u"%s %s" % (cls.tab_name, obj.date_obs.strftime("%Y-%m-%d %H:%M:%S"))
			records.append({'recnum': obj.recnum, 'title': record_title, 'fields': [obj.date_obs, obj.quality]})
		
		return records, headers
