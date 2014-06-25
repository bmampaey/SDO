from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseServerError, HttpResponseForbidden, QueryDict
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_safe, require_POST

from PMD.models import DataSeries, DataDownloadRequest, ExportDataRequest
from PMD.forms import TimeRangeForm, LoginForm, DataSeriesSearchForm
from PMD.tasks import get_preview, get_data, execute_bring_online_request, execute_export_data_request, execute_export_meta_data_request

# Assert we only have get
@require_safe
def index(request):
	data_series_search_forms = DataSeriesSearchForm.sub_forms()
	context = {
		'time_range_form' : TimeRangeForm(label_suffix=''),
		'data_series_search_forms': [data_series_search_forms[name](label_suffix='') for name in sorted(data_series_search_forms)],
		'login_form': LoginForm(label_suffix=''),
	}
	
	return render(request, 'PMD/index.html', context)

# Assert we only have get
@require_safe
def result_table(request, data_series_name):
	#import pprint; print pprint.pformat(request.GET, depth=6)
	#import pdb; pdb.set_trace()
	# Get the request session for the requested data series
	if data_series_name not in request.session:
		request.session[data_series_name] = dict()
	request_session = request.session[data_series_name]
	
	# Get the result table
	data_series_search_forms = DataSeriesSearchForm.sub_forms()
	if data_series_name in data_series_search_forms:
		try:
			result_table = data_series_search_forms[data_series_name].get_result_table(request.GET, request_session, request.GET.get('page', 1))
		except Exception, why:
			return HttpResponseBadRequest(str(why))
	else:
		return HttpResponseNotFound("Unknown data series %s" % data_series_name)
	
	# Send the response
	return render(request, 'PMD/result_table.html', result_table)

@require_POST
def login(request):
	form = LoginForm(request.POST)
	if not form.is_valid():
		return HttpResponseBadRequest(str(form.errors))
	
	if form.cleaned_data["username"] and form.cleaned_data["password"]:
		user = authenticate(username=form.cleaned_data["username"], password=form.cleaned_data["password"])
	
	elif form.cleaned_data["email"]:
		pass
	
	else:
		return HttpResponse("You must provide a username an password or an email", content_type="text/plain", status=401)
	
	if user is not None:
		if user.is_active:
			login(request, user)
			# Send the table of request
		else:
			return HttpResponse("Your account is disabled. Please contact the website administrator", content_type="text/plain", status=401)
	else:
		return HttpResponse("Invalid password", content_type="text/plain", status=401)

# Assert we only have get
@require_safe
def preview(request, data_series_name, recnum):
	# Create the preview request
	data_series = get_object_or_404(DataSeries, pk=data_series_name)
	print "found", data_series_name
	record = get_object_or_404(data_series.record, recnum=recnum)
	preview_request = DataDownloadRequest.create_from_record(record)

	# Execute the request
	try:
		path = get_preview(preview_request)
	except Exception, why:
		# In case of problem with the request return error message
		print why
		return HttpResponseServerError(str(why))
	else:
		# Redirect to the image
		return redirect(path, permanent=False)


# Assert we only have get
@require_safe
def download(request, data_series_name, recnum):
	# Create the preview request
	data_series = get_object_or_404(DataSeries, pk=data_series_name)
	print "found", data_series_name
	record = get_object_or_404(data_series.record, recnum=recnum)
	download_request = DataDownloadRequest.create_from_record(record)
	
	# Execute the request
	try:
		path = get_data(download_request)
	except Exception, why:
		# In case of problem with the request return error message
		return HttpResponseServerError(str(why))
	else:
		# Send the file
		response = HttpResponse(open(path,"rb").read(), mimetype="application/x-download")
		response["Content-Disposition"] = "attachment;filename="+record.filename()
		return response

# Assert we only have post and that we are logged in
@require_POST
@login_required
def result_action(request, action_type, data_series_name):
	
	# Verify user is authenticated and active
	if not request.user.is_authenticated():
		return HttpResponseForbidden("You must first login to export data")
	if not request.user.is_active:
		return HttpResponseForbidden("Your account has been disabled, please contact sdoadmins@oma.be")
	
	# Get the data series search form
	data_series_search_forms = DataSeriesSearchForm.sub_forms()
	if data_series_name in data_series_search_forms:
		data_series_search_form = data_series_search_forms[data_series_name]
	else:
		return HttpResponseNotFound("Unknown data series %s" % data_series_name)
	
	# Get the request session for the requested data series
	if data_series_name not in request.session:
		request.session[data_series_name] = dict()
	request_session = request.session[data_series_name]
	
	# Parse the POST data
	try:
		all_selected = request.POST.get("all_selected", "false").lower() == "true"
		recnums = [int(recnum) for recnum in request.POST.getlist("selected")]
	except Exception:
		HttpResponseBadRequest("Data selection parameters are invalid: %s" % str(why))
	import pdb; pdb.set_trace()
	# If all is selected , we create a paginator like for the search to extract the recnums 
	if all_selected:
		# Get the query set of the data series 
		query_parameters = QueryDict("", mutable=True)
		query_parameters.update(request_session)
		query_parameters.update(request.GET)
		try:
			query_set = data_series_search_form.get_query_set(query_parameters)
			if recnums:
				# Exclude the (un)selected recnums
				query_set = query_set.exclude(recnum__in=recnums)
			# Get the paginator
			paginator = data_series_search_form.get_paginator(query_set, request.GET.get("limit", 100), request.GET.get("cadence", 0))
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
	elif action_type == "export_keywords":
		return export_keywords(request, data_series_name, recnums, paginator)
	elif action_type == "bring_online":
		return bring_online(request, data_series_name, recnums, paginator)
	elif action_type == "export_cutout":
		return export_cutout(request, data_series_name, recnums, paginator)
	else:
		return HttpResponseNotFound("Unknown action type " + action_type)


def download_bundle(request, data_series_name, recnums, paginator):
	return HttpResponseNotFound("Not yet implemented")


def export_data(request, data_series_name, recnums, paginator):
	import pdb; pdb.set_trace()
	# Create the request
	data_series = get_object_or_404(DataSeries, pk=data_series_name)
	export_data_request = ExportDataRequest(user = request.user, data_series = data_series, recnums = recnums)
	
	# Execute the request
	execute_export_data_request.delay(export_data_request, paginator)
	
	# Return message about request
	return render(request, 'PMD/export_request_message.txt',  { "export_path" : export_data_request.export_path })


def export_keywords(request, data_series_name, recnums, paginator):
	return HttpResponseNotFound("Not yet implemented")

def bring_online(request, data_series_name, recnums, paginator):
	return HttpResponseNotFound("Not yet implemented")

def export_cutout(request, data_series_name, recnums, paginator):
	return HttpResponseNotFound("Not yet implemented")

