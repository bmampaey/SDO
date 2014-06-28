from django.shortcuts import render, get_object_or_404, get_list_or_404
from django.core import serializers
from django.http import HttpResponse
# Create your views here.

from DRMS.models import DRMSDataSeries

def data_series_list(request):
	data_series = get_list_or_404(DRMSDataSeries)
	return HttpResponse(serializers.serialize('json', data_series), mimetype='application/json')

def data_series(request, data_series):
	data_series_object = get_object_or_404(DRMSDataSeries, name=data_series)
	data_series_keywords = get_list_or_404(data_series_object.fits_keyword_model)
	return HttpResponse(serializers.serialize('json', data_series_keywords), mimetype='application/json')

def recnum(request, data_series, recnum):
	data_series_object = get_object_or_404(DRMSDataSeries, name=data_series)
	fits_header = get_object_or_404(data_series_object.fits_header_model, recnum=recnum)
	return HttpResponse(serializers.serialize('json', [fits_header]), mimetype='application/json')

