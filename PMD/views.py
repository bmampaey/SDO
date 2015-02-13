from datetime import datetime

from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseServerError, HttpResponseForbidden
from django.views.decorators.http import require_safe

from PMD.models import DataSeries, DataDownloadRequest
from PMD.tasks import get_preview, get_data

# Assert we only have get
@require_safe
def download_data(request, data_series_name, recnum):
	# Create a data download request
	data_series = get_object_or_404(DataSeries, pk=data_series_name)
	record = get_object_or_404(data_series.record, recnum=recnum)
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
		response = HttpResponse(open(path,"rb").read(), content_type="application/x-download")
		response["Content-Disposition"] = "attachment;filename="+record.filename
		return response


# Assert we only have get
@require_safe
def preview_data(request, data_series_name, recnum):
	# Create a data download request
	data_series = get_object_or_404(DataSeries, pk=data_series_name)
	print "found", data_series_name
	record = get_object_or_404(data_series.record, recnum=recnum)
	data_download_request = DataDownloadRequest.create_from_record(record)
	
	# Set a very short lifetime to the data to allow quick deletion (if someone tries to make a lot of these)
	data_download_request.expiration_date = datetime.now()
	
	# Execute a preview task to get the path to the preview image
	try:
		path = get_preview(data_download_request)
	except Exception, why:
		# In case of problem with the request return error message
		print why
		return HttpResponseServerError(str(why))
	else:
		# Redirect to the image
		return redirect(path, permanent=False)
