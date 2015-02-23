from datetime import datetime
import uuid

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_safe, require_POST, require_http_methods

from PMD.models import DataSeries, DataDownloadRequest
from PMD.models import ExportDataRequest, ExportMetadataRequest

from wizard.forms import DataSeriesSearchForm
from account.forms import EmailLoginForm
from tasks import execute_export_data_request, execute_export_metadata_request


# Assert we only have get
@require_safe
def index(request):
	data_series_search_forms = DataSeriesSearchForm.sub_forms()
	context = {
		'email_login_form': EmailLoginForm(label_suffix=''),
		'data_series_search_forms': [data_series_search_forms[name](label_suffix='', auto_id="id_%s_"+name) for name in sorted(data_series_search_forms)],
	}
	
	return render(request, 'wizard/index.html', context)

# Assert we only have get
@require_safe
def search_result_table(request, data_series_name):
	#import pprint; print pprint.pformat(request.GET, depth=6)
	#import pdb; pdb.set_trace()
	
	# Get the result table
	data_series_search_forms = DataSeriesSearchForm.sub_forms()
	if data_series_name in data_series_search_forms:
		try:
			search_result_table = data_series_search_forms[data_series_name].get_search_result_table(request.GET)
		except Exception, why:
			return HttpResponseBadRequest(str(why))
	else:
		return HttpResponseNotFound("Unknown data series %s" % data_series_name)
	
	# Send the response
	return render(request, 'wizard/search_result_table.html', search_result_table)



# Assert we only have post and that we are logged in
@require_POST
@login_required
def search_result_action(request, action_type, data_series_name):
	
	# Verify user is authenticated and active
	if not request.user.is_authenticated():
		return HttpResponseForbidden("You must first login to export data")
	if not request.user.is_active:
		return HttpResponseForbidden("Your account has been disabled, please contact sdoadmins@oma.be")
	#import pdb; pdb.set_trace()
	# Get the data series search form
	data_series_search_forms = DataSeriesSearchForm.sub_forms()
	if data_series_name in data_series_search_forms:
		data_series_search_form = data_series_search_forms[data_series_name]
	else:
		return HttpResponseNotFound("Unknown data series %s" % data_series_name)
	
	# Parse the POST data
	try:
		all_selected = request.POST.get("all_selected", "false").lower() == "true"
		recnums = [int(recnum) for recnum in request.POST.getlist("selected")]
	except Exception:
		HttpResponseBadRequest("Data selection parameters are invalid: %s" % str(why))
	
	# If all is selected , we create a paginator like for the search to extract the recnums 
	if all_selected:
		try:
			cleaned_data = data_series_search_form.get_cleaned_data(request.GET)
			paginator = data_series_search_form.get_paginator(cleaned_data, request.GET.get("limit", 100))
		except Exception, why:
			return HttpResponseBadRequest(str(why))
	
	elif recnums:
		paginator = None
	
	else:
		return HttpResponseBadRequest("No data was selected for export")
	
	# Apply the correct action
	if action_type == "download_bundle":
		return download_bundle(request, data_series_name, recnums, paginator)
	elif action_type == "export_data":
		return export_data(request, data_series_name, recnums, paginator)
	elif action_type == "export_metadata":
		return export_metadata(request, data_series_name, recnums, paginator)
	elif action_type == "export_cutout":
		return export_cutout(request, data_series_name, recnums, paginator)
	else:
		return HttpResponseNotFound("Unknown action type " + action_type)


def download_bundle(request, data_series_name, recnums, paginator):
	return HttpResponseNotFound("Not yet implemented")


def export_data(request, data_series_name, recnums, paginator):
	""" Create a ExportDataRequest and execute it asynchronously """
	
	# Create the request
	data_series = get_object_or_404(DataSeries, pk=data_series_name)
	user_request = ExportDataRequest(user = request.user, data_series = data_series)
	user_request.save()
	
	# Execute the request
	async_result = execute_export_data_request.delay(user_request, recnums, paginator)
	
	# Return message about request
	return render(request, 'wizard/user_request_message.html', { "request": user_request })


def export_metadata(request, data_series_name, recnums, paginator):
	""" Create a ExportMetadataRequest and execute it asynchronously """
	
	# Create the request
	data_series = get_object_or_404(DataSeries, pk=data_series_name)
	user_request = ExportMetadataRequest(user = request.user, data_series = data_series, recnums = recnums)
	user_request.save()
	#import pdb; pdb.set_trace()
	# Execute the request
	async_result = execute_export_metadata_request.delay(user_request, recnums, paginator)
	
	# Return message about request
	return render(request, 'wizard/user_request_message.html', { "request": user_request })

def export_cutout(request, data_series_name, recnums, paginator):
	return HttpResponseNotFound("Not yet implemented")


# Assert we only have get and that we are logged in
@require_safe
@login_required
def user_request_table(request, request_type):
	
	#import pdb; pdb.set_trace()
	# Verify user is authenticated and active
	if not request.user.is_authenticated():
		return HttpResponseForbidden("You must first login to get your user requests")
	if not request.user.is_active:
		return HttpResponseForbidden("Your account has been disabled, please contact sdoadmins@oma.be")
	
	# Get the model for the request type
	if request_type == "export_data":
		user_request_model = ExportDataRequest
	elif request_type == "export_metadata":
		user_request_model = ExportMetadataRequest
	else:
		return HttpResponseNotFound("Unknown request type %s" % request_type)
	
	# Get the request table
	headers = user_request_model.column_headers
	rows = list()
	for user_request in user_request_model.objects.filter(user = request.user):
		rows.append({'request_id': user_request.id, 'ftp_path': user_request.ftp_path, 'fields': user_request.row_fields})
	
	# Send the response
	return render(request, 'wizard/user_request_table.html', {"request_type": request_type, "headers": headers, "rows": rows})


# Assert we only have delete and that we are logged in
@require_http_methods(["DELETE"])
@login_required
def delete_user_request(request, request_type, request_id):
	
	# Verify user is authenticated and active
	if not request.user.is_authenticated():
		return HttpResponseForbidden("You must first login to get your export requests")
	if not request.user.is_active:
		return HttpResponseForbidden("Your account has been disabled, please contact sdoadmins@oma.be")
	
	# Get the model for the request type
	if request_type == "export_data":
		user_request_model = ExportDataRequest
	elif request_type == "export_metadata":
		user_request_model = ExportMetadataRequest
	else:
		return HttpResponseNotFound("Unknown request type %s" % request_type)
	
	# Get the request to delete
	user_request = get_object_or_404(user_request_model, id=request_id)
	
	# Check that the user is allowed to delete the request, and delete it
	if request.user != user_request.user:
		return HttpResponseForbidden("You are not allowed to delete that request")
	else:
		# Files are deleted and task cancelled by django signal http://stackoverflow.com/questions/1534986/how-do-i-override-delete-on-a-model-and-have-it-still-work-with-related-delete
		user_request.delete() 
	
	# Send the response
	return render(request, 'wizard/delete_user_request.html', {"request": user_request})
