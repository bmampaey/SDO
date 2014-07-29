# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import dateutil.parser as date_parser

from django import forms
from django.core.paginator import EmptyPage, PageNotAnInteger
from django.http import QueryDict


from PMD.paginators import EstimatedCountPaginator, CadencePaginator
from PMD.models import DataSeries, GlobalConfig
from PMD.cadence_field import CadenceField

AIA_WAVELENGTHS = [94, 131, 171, 193, 211, 304, 335, 1600, 1700, 4500]


class LoginForm(forms.Form):
	username = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'username'}))
	password = forms.CharField(required=True, widget=forms.PasswordInput(attrs={'placeholder': 'password'}))

class EmailLoginForm(forms.Form):
	email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'my.email@address.com'}))

class DataSeriesSearchForm(forms.Form):
	""" Common class for all data series search form. Must be inherited for each data series """
	start_date = forms.DateTimeField(required=False, initial = datetime(2010, 03, 29), widget=forms.DateTimeInput(format = "%Y-%m-%d %H:%M:%S", attrs={'class': 'date_time_input'}))
	#end_date = forms.DateTimeField(required=False, initial = datetime.utcnow(), widget=forms.DateTimeInput(format = "%Y-%m-%d %H:%M:%S", attrs={'class': 'date_time_input'}))
	end_date = forms.DateTimeField(required=False, initial = datetime(2010, 05, 15), widget=forms.DateTimeInput(format = "%Y-%m-%d %H:%M:%S", attrs={'class': 'date_time_input'}))
	cadence = CadenceField(required=False, min_value = 1)
	
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
	def get_cleaned_data(cls, request_data):
		""" Clean up the request data and return a dictionnary of clean values """
		# Parse the request data
		form = cls(request_data)
		if not form.is_valid():
			raise Exception(str(form.errors))
		
		# For each parameter we try to get the values from the form or else from the initials value
		cleaned_data = cls.initials()
		cleaned_data.update(form.cleaned_data)
		
		return cleaned_data
	
	@classmethod
	def get_paginator(cls, cleaned_data, limit):
		""" Create a paginator of records """
		# When cadence is specified we need a custom implementation of paginator
		# But only if cadence is big enough
		cadence = cleaned_data.get('cadence', 0)
		if cadence > cls.minimal_cadence:
			return CadencePaginator(cls.get_cadence_query_sets(cleaned_data), timedelta(seconds=cadence), limit, allow_empty_first_page = False, orphans = limit/2)
		else:
			return EstimatedCountPaginator(cls.get_query_set(cleaned_data), limit, allow_empty_first_page = False, orphans = limit/2)
	
	@classmethod
	def get_search_result_table(cls, request_data):
		"""Return a dict with all the necessary info to create a table of results"""
		# THIS COULD GO INTO THE VIEW
		#import pdb; pdb.set_trace()
		# Get the cleaned data from the request_data
		cleaned_data = cls.get_cleaned_data(request_data)
		
		# Get the paginator
		paginator = cls.get_paginator(cleaned_data, request_data.get("limit", GlobalConfig.get("search_result_table_row_limit", 12)))
		
		# Get the page
		page_number = request_data.get("page", 1)
		try:
			page = paginator.page(page_number)
		except PageNotAnInteger:
			page = paginator.page(1)
		except EmptyPage:
			raise Exception("No result found for your search criteria")
		
		# Result table
		table = {'data_series_name': cls.record_table}
		
		# Make the header and rows from the page objects
		table['headers'], table['rows'] = cls.get_headers_rows(page.object_list)
		
		# Set up the pages navigation by encoding the request data with the corresponding page
		# The request data from a request is immutable, therefore we need to copy it
		query_dict = QueryDict("", mutable = True)
		query_dict.update(request_data)
		
		if page.number > 1:
			query_dict["page"] = 1
			table['first_page_url_query'] = query_dict.urlencode()
		else:
			table['first_page_url_query'] = None
		
		if page.has_previous():
			query_dict["page"] = page.previous_page_number()
			table['previous_page_url_query'] = query_dict.urlencode()
		else:
			table['previous_page_url_query'] = None
		
		if page.has_next():
			query_dict["page"] = page.next_page_number()
			table['next_page_url_query'] = query_dict.urlencode()
		else:
			table['next_page_url_query'] = None
		
		if page.number < paginator.num_pages:
			query_dict["page"] = paginator.num_pages
			table['last_page_url_query'] = query_dict.urlencode()
		else:
			table['last_page_url_query'] = None
		
		# For informative purpose we add the search query
		query_dict["page"] = None
		query_dict.pop("page")
		table['search_query'] = query_dict.urlencode()
		
		return table
	
	@property
	def data_series_name(self):
		return self.record_table


class AiaLev1SearchForm(DataSeriesSearchForm):
	record_table = "aia_lev1"
	tab_name = "AIA Lev1"
	minimal_cadence = 12
	best_quality = forms.BooleanField(required=False, initial = False, help_text="Search results will only display data for which the quality keyword is 0")
	wavelengths = forms.TypedMultipleChoiceField(required=True, coerce=int, widget=forms.SelectMultiple(), initial = AIA_WAVELENGTHS, choices=[(w, u'%sÅ'%w) for w in AIA_WAVELENGTHS])
	
	@classmethod
	def get_query_set(cls, cleaned_data):
		""" Creates a QuerySet for the data series with record table corresponding to the form record_table"""
		
		query_set = DataSeries.objects.get(record_table = cls.record_table).record.objects.filter()
		
		if cleaned_data.get('best_quality', False):
			query_set = query_set.filter(quality=0)
		
		if cleaned_data.get('start_date', False):
			query_set = query_set.filter(date_obs__gte = cleaned_data['start_date'])
		
		if cleaned_data.get('end_date', False):
			query_set = query_set.filter(date_obs__lt = cleaned_data['end_date'])
		
		# Verify that at least 1 wavelength was selected
		wavelengths = set(cleaned_data.get('wavelengths', []))
		if len(wavelengths) == 0:
			raise Exception("For AIA you need to select at least one wavelength")
		
		# Add a condition if only a subset of the wavelength was selected
		elif len(set(AIA_WAVELENGTHS) - wavelengths) > 0:
			query_set = query_set.filter(wavelnth__in=wavelengths)
		
		return query_set
	
	
	@classmethod
	def get_cadence_query_sets(cls, cleaned_data):
		""" Creates a QuerySet for the data series with record table corresponding to the form record_table"""
		
		query_set = cls.get_query_set(cleaned_data)
		
		wavelengths = set(cleaned_data.get('wavelengths', []))
		if len(wavelengths) == 0:
			raise Exception("For AIA you need to select at least one wavelength")
		
		query_sets = list()
		# For aia.lev1 it is 1 query_set per wavelength
		
		for wavelength in wavelengths:
			query_sets.append(query_set.filter(wavelnth = wavelength))
		
		return query_sets
	
	
	@classmethod
	def get_headers_rows(cls, records):
		headers = ["Date", "Wavelength", "Quality"]
		rows = list()
		for record in records:
			record_title = u"%s %dÅ %s" % (cls.tab_name, record.wavelnth, record.date_obs.strftime("%Y-%m-%d %H:%M:%S"))
			rows.append({'recnum': record.recnum, 'title': record_title, 'fields': [record.date_obs, record.wavelnth, record.quality]})
		
		return headers, rows


class HmiM45SSearchForm(DataSeriesSearchForm):
	record_table =  "hmi_m_45s"
	tab_name = "HMI Magnetogram"
	minimal_cadence = 45
	best_quality = forms.BooleanField(required=False, initial = False, help_text="Search results will only display data for which the quality keyword is 0")
	
	@classmethod
	def get_query_set(cls, cleaned_data):
		""" Creates a QuerySet for the data series with record table corresponding to the form record_table"""
		
		query_set = DataSeries.objects.get(record_table = cls.record_table).record.objects.filter()
		
		if cleaned_data.get('best_quality', False):
			query_set = query_set.filter(quality=0)
		
		if cleaned_data.get('start_date', False):
			query_set = query_set.filter(date_obs__gte = cleaned_data['start_date'])
		
		if cleaned_data.get('end_date', False):
			query_set = query_set.filter(date_obs__lt = cleaned_data['end_date'])
		
		return query_set
	
	@classmethod
	def get_cadence_query_sets(cls, cleaned_data):
		""" Creates a QuerySet for the data series with record table corresponding to the form record_table"""
		
		return [cls.get_query_set(cleaned_data)]
	
	@classmethod
	def get_headers_rows(cls, records):
		headers = ["Date", "Quality"]
		rows = list()
		for record in records:
			record_title = u"%s %s" % (cls.tab_name, record.date_obs.strftime("%Y-%m-%d %H:%M:%S"))
			rows.append({'recnum': record.recnum, 'title': record_title, 'fields': [record.date_obs, record.quality]})
		
		return headers, rows

class HmiIc45SSearchForm(DataSeriesSearchForm):
	record_table =  "hmi_ic_45s"
	tab_name = "HMI Continuum"
	minimal_cadence = 45
	best_quality = forms.BooleanField(required=False, initial = False, help_text="Search results will only display data for which the quality keyword is 0")
	
	@classmethod
	def get_query_set(cls, cleaned_data):
		""" Creates a QuerySet for the data series with record table corresponding to the form record_table"""
		
		query_set = DataSeries.objects.get(record_table = cls.record_table).record.objects.filter()
		
		if cleaned_data.get('best_quality', False):
			query_set = query_set.filter(quality=0)
		
		if cleaned_data.get('start_date', False):
			query_set = query_set.filter(date_obs__gte = cleaned_data['start_date'])
		
		if cleaned_data.get('end_date', False):
			query_set = query_set.filter(date_obs__lt = cleaned_data['end_date'])
		
		return query_set
	
	@classmethod
	def get_cadence_query_sets(cls, cleaned_data):
		""" Creates a QuerySet for the data series with record table corresponding to the form record_table"""
		
		return [cls.get_query_set(cleaned_data)]
	
	@classmethod
	def get_headers_rows(cls, records):
		headers = ["Date", "Wavelength", "Quality"]
		rows = list()
		for record in records:
			record_title = u"%s %s" % (cls.tab_name, record.date_obs.strftime("%Y-%m-%d %H:%M:%S"))
			rows.append({'recnum': record.recnum, 'title': record_title, 'fields': [record.date_obs, record.wavelnth, record.quality]})
		
		return headers, rows
