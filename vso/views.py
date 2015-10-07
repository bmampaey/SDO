from datetime import datetime
import re
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseServerError, HttpResponseNotFound
from django.views.decorators.http import require_safe
from PMD.models import DataSeries, DataDownloadRequest
from tasks import get_data

from vso.forms import DrmsExportForm


vso_registry = {
	'aia__lev1': {'name': 'aia_lev1', 'record_regex': re.compile(r'(?P<wavelnth>\d+)_(?P<t_rec_index__gte>\d+)-(?P<t_rec_index__lte>\d+)')},
	'hmi__M_45s': {'name': 'hmi_m_45s', 'record_regex': re.compile(r'(?P<t_rec_index__gte>\d+)-(?P<t_rec_index__lte>\d+)')},
	'hmi__Ic_45s': {'name': 'hmi_ic_45s', 'record_regex': re.compile(r'(?P<t_rec_index__gte>\d+)-(?P<t_rec_index__lte>\d+)')},
}

# Assert we only have get
@require_safe
def drms_export(request):
	#import pdb; pdb.set_trace()
	# Parse request data
	form = DrmsExportForm(request.GET)
	
	if form.is_valid():
		# Find the record
		try:
			vso_entry = vso_registry[form.cleaned_data['series']]
		except KeyError:
			return HttpResponseNotFound('Series not found')
		
		data_series = get_object_or_404(DataSeries, pk=vso_entry['name'])
		
		record_filters = vso_entry['record_regex'].match(form.cleaned_data['record'])
		if record_filters is None:
			return HttpResponseNotFound('Record not found')
		try:
			record = get_object_or_404(data_series.record, **record_filters.groupdict())
		except Exception, why:
			return HttpResponseServerError(str(why))
		
		# Create a data download request
		data_download_request = DataDownloadRequest.create_from_record(record)
	
		# Set a very short lifetime to the data to allow quick deletion (if someone tries to make a lot of these)
		data_download_request.expiration_date = datetime.now()
	
		# Execute a get_data task to get the path to the data
		try:
			path = get_data(data_download_request)
		except Exception, why:
			# In case of problem with the request return error message
			return HttpResponseServerError(str(why))
		else:
			# Send the file
			response = HttpResponse(open(path,"rb").read())
#Content-Length:12335040
			response['Content-transfer-encoding'] = 'binary'
			response['Content-Type'] = 'application/octet-stream'
			response['Content-Disposition'] = 'attachment; filename="%s"' % record.filename
			return response
	else:
		return HttpResponseNotFound(form.errors.as_text())
