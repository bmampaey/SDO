from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseServerError, HttpResponseForbidden
from django.contrib.auth import authenticate, login as user_login
from django.contrib.auth.models import User, UserManager, Group
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_safe, require_POST, require_http_methods

from PMD.models import DataSeries, DataDownloadRequest, ExportDataRequest
from PMD.forms import LoginForm, EmailLoginForm, DataSeriesSearchForm
from PMD.tasks import get_preview, get_data, execute_bring_online_request, execute_export_data_request, execute_export_meta_data_request

# Assert we only have post
@require_POST
def login(request):
	# Check if we got username/password
	form = LoginForm(request.POST)
	if form.is_valid():
		user = authenticate(username=form.cleaned_data["username"], password=form.cleaned_data["password"])
		if user is None:
			return HttpResponse("Invalid password", content_type="text/plain", status=401)
		elif user.is_active:
			user_login(request, user)
			return HttpResponse(user.username)
		else:
			return HttpResponse("Your account is disabled. Please contact the website administrator", content_type="text/plain", status=401)
	
	# Check if we got an email
	form = EmailLoginForm(request.POST)
	if form.is_valid():
		# We split the email address to get the user
		username, password = form.cleaned_data["email"].split("@", 1)
		user = authenticate(username=username, password=password)
		if user is None:
			# Register the user
			group = Group.objects.get("external_users")
			UserManager.create_user(username, email=form.cleaned_data["email"], password=password, is_staff = False)
			user = authenticate(username=username, password=password)
		if user.is_active:
			user_login(request, user)
			return HttpResponse(user.username)
		else:
			return HttpResponse("Your account is disabled. Please contact the website administrator", content_type="text/plain", status=401)
	else:
		return HttpResponseBadRequest(str(form.errors))


# Assert we only have get
@require_safe
def index(request):
	data_series_search_forms = DataSeriesSearchForm.sub_forms()
	context = {
		'login_form': LoginForm(label_suffix=''),
		'email_login_form': EmailLoginForm(label_suffix=''),
		'data_series_search_forms': [data_series_search_forms[name](label_suffix='') for name in sorted(data_series_search_forms)],
	}
	
	return render(request, 'PMD/index.html', context)

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
	return render(request, 'PMD/search_result_table.html', search_result_table)


# Assert we only have get
@require_safe
def preview_data(request, data_series_name, recnum):
	# Create a data download request
	data_series = get_object_or_404(DataSeries, pk=data_series_name)
	print "found", data_series_name
	record = get_object_or_404(data_series.record, recnum=recnum)
	data_download_request = DataDownloadRequest.create_from_record(record)

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


# Assert we only have get
@require_safe
def download_data(request, data_series_name, recnum):
	# Create a data download request
	data_series = get_object_or_404(DataSeries, pk=data_series_name)
	print "found", data_series_name
	record = get_object_or_404(data_series.record, recnum=recnum)
	data_download_request = DataDownloadRequest.create_from_record(record)
	
	# Execute a get_data task to get the path to the data
	try:
		path = get_data(data_download_request)
	except Exception, why:
		# In case of problem with the request return error message
		return HttpResponseServerError(str(why))
	else:
		# Send the file
		response = HttpResponse(open(path,"rb").read(), mimetype="application/x-download")
		response["Content-Disposition"] = "attachment;filename="+record.filename
		return response

# Assert we only have post and that we are logged in
@require_POST
@login_required
def search_result_action(request, action_type, data_series_name):
	
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
	
	# Parse the POST data
	try:
		all_selected = request.POST.get("all_selected", "false").lower() == "true"
		recnums = [int(recnum) for recnum in request.POST.getlist("selected")]
	except Exception:
		HttpResponseBadRequest("Data selection parameters are invalid: %s" % str(why))
	
	# If all is selected , we create a paginator like for the search to extract the recnums 
	if all_selected:
		# Get the query set coresponding to the data search 
		try:
			cleaned_data = data_series_search_form.get_cleaned_data(request.GET)
			query_set = data_series_search_form.get_query_set(cleaned_data)
			if recnums:
				# Exclude the (un)selected recnums
				query_set = query_set.exclude(recnum__in=recnums)
			# Get the paginator
			paginator = data_series_search_form.get_paginator(query_set, request.GET.get("limit", 100), request.GET.get("cadence", 0))
			recnums = []
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
	""" Create a ExportDataRequest and execute it asynchronously """
	
	# Create the request
	data_series = get_object_or_404(DataSeries, pk=data_series_name)
	export_data_request = ExportDataRequest(user = request.user, data_series = data_series, recnums = recnums)
	
	# Execute the request
	#execute_export_data_request.delay(export_data_request, paginator)
	execute_export_data_request(export_data_request, paginator)
	
	# Return message about request
	return render(request, 'PMD/export_data_request_message.html',  { "ftp_path" : export_data_request.ftp_path })


def export_keywords(request, data_series_name, recnums, paginator):
	return HttpResponseNotFound("Not yet implemented")

def bring_online(request, data_series_name, recnums, paginator):
	return HttpResponseNotFound("Not yet implemented")

def export_cutout(request, data_series_name, recnums, paginator):
	return HttpResponseNotFound("Not yet implemented")

# Assert we only have get and that we are logged in
@require_safe
@login_required
def export_data_request_table(request):
	#import pprint; print pprint.pformat(request.GET, depth=6)
	#import pdb; pdb.set_trace()
	# Verify user is authenticated and active
	if not request.user.is_authenticated():
		return HttpResponseForbidden("You must first login to get your export requests")
	if not request.user.is_active:
		return HttpResponseForbidden("Your account has been disabled, please contact sdoadmins@oma.be")
	
	# Get the request table
	headers = ["Requested", "Data Series", "Size", "Expires", "Status"]
	rows = list()
	for export_data_request in ExportDataRequest.objects.filter(user = request.user):
		rows.append({'request_id': export_data_request.id, 'ftp_path': export_data_request.ftp_path, 'fields': [
			export_data_request.requested.strftime("%Y-%m-%d %H:%M:%S"),
			export_data_request.data_series.name,
			export_data_request.estimated_size(human_readable =True),
			export_data_request.expiration_date.strftime("%Y-%m-%d %H:%M:%S"),
			export_data_request.status.lower()
		]})
	
	# Send the response
	return render(request, 'PMD/export_data_request_table.html', {"headers": headers, "rows": rows})


# Assert we only have delete and that we are logged in
#@require_http_methods(["DELETE"])
@login_required
def delete_export_data_request(request, request_id):
	
	# Verify user is authenticated and active
	if not request.user.is_authenticated():
		return HttpResponseForbidden("You must first login to get your export requests")
	if not request.user.is_active:
		return HttpResponseForbidden("Your account has been disabled, please contact sdoadmins@oma.be")
	
	# Search the request
	export_request = get_object_or_404(ExportDataRequest, id=request_id)
	
	# Check that the user is allowed to delete the request, and delete it
	if request.user != export_request.user:
		return HttpResponseForbidden("You are not allowed to delete that request")
	else:
		# Files are deleted automatically by django signal http://stackoverflow.com/questions/1534986/how-do-i-override-delete-on-a-model-and-have-it-still-work-with-related-delete
		# Do the same for localdatalocation
		export_request.delete() 
	
	return HttpResponse("The request %s has been deleted. Thank you for freeing some disk space." % export_request.name)
